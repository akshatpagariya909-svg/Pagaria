#!/usr/bin/env python3
"""Fetch the sources for the architect write-ups: Wikidata facts and the Wikipedia article text.

  python -u tools/fetch_architect_sources.py --ranks 1-10
  python -u tools/fetch_architect_sources.py --only "Zaha Hadid,OMA"
  python -u tools/fetch_architect_sources.py --ranks 11-40 --qids "OMA=Q1416588"

Reads tools/architect_bios/todo.json. For each architect it finds the Wikidata item (the todo's qid, or a
search on the name when the qid is missing or "manual:"), then keeps: birth and death dates, citizenship,
awards with years, notable works, official website, and the English Wikipedia article (introduction plus the
plain text of the whole article, cut at about 6,000 words). Results are merged into
tools/architect_bios/sources.json (name -> record), so batches can be fetched one after another.
Needs network access to wikidata.org and en.wikipedia.org: runs on GitHub Actions (architect-bios.yml).
"""
import argparse, json, re, sys, time, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'tools' / 'architect_bios'
OUT = DIR / 'sources.json'
UA = 'FindGreatArchitecture/1.0 (https://findgreatarchitecture.com; architect write-ups script)'
WD = 'https://www.wikidata.org/w/api.php'
WP = 'https://en.wikipedia.org/w/api.php'
MAX_WORDS = 6000


def get(url, params):
    url = url + '?' + urllib.parse.urlencode({**params, 'format': 'json'})
    for attempt in range(6):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as err:
            print('  retry', attempt, err)
            if attempt == 5:
                raise
            time.sleep(5 * (attempt + 1))


def search_qid(name):
    res = get(WD, {'action': 'wbsearchentities', 'search': name, 'language': 'en', 'type': 'item', 'limit': 7})
    for hit in res.get('search', []):
        desc = (hit.get('description') or '').lower()
        if any(w in desc for w in ('architect', 'architecture', 'design', 'firm', 'practice', 'studio')):
            return hit['id'], hit.get('description')
    return None, None


def labels(qids):
    out = {}
    qids = list(dict.fromkeys(qids))
    for i in range(0, len(qids), 50):
        res = get(WD, {'action': 'wbgetentities', 'ids': '|'.join(qids[i:i + 50]), 'props': 'labels', 'languages': 'en'})
        for q, ent in res.get('entities', {}).items():
            out[q] = ent.get('labels', {}).get('en', {}).get('value', q)
    return out


def time_of(snak):
    try:
        t = snak['datavalue']['value']['time']
        prec = snak['datavalue']['value']['precision']
        return t[1:11] if prec >= 11 else t[1:5]
    except (KeyError, TypeError):
        return None


def entity(qid):
    ent = get(WD, {'action': 'wbgetentities', 'ids': qid, 'props': 'claims|sitelinks|descriptions|labels',
                   'languages': 'en'})['entities'][qid]
    claims = ent.get('claims', {})

    def items(p):
        return [c['mainsnak']['datavalue']['value']['id'] for c in claims.get(p, [])
                if c['mainsnak'].get('datavalue')]

    def times(p):
        return [time_of(c['mainsnak']) for c in claims.get(p, []) if time_of(c['mainsnak'])]

    awards = []
    for c in claims.get('P166', []):
        if not c['mainsnak'].get('datavalue'):
            continue
        year = None
        for q in c.get('qualifiers', {}).get('P585', []):
            year = time_of(q)
        awards.append((c['mainsnak']['datavalue']['value']['id'], year))
    refs = items('P27') + items('P800') + items('P31') + items('P17') + items('P159') + items('P112') + [a for a, _ in awards]
    lab = labels(refs) if refs else {}
    sites = [c['mainsnak']['datavalue']['value'] for c in claims.get('P856', []) if c['mainsnak'].get('datavalue')]
    return {
        'qid': qid,
        'label': ent.get('labels', {}).get('en', {}).get('value'),
        'description': ent.get('descriptions', {}).get('en', {}).get('value'),
        'instance_of': [lab.get(q, q) for q in items('P31')],
        'born': (times('P569') or [None])[0],
        'died': (times('P570') or [None])[0],
        'founded': (times('P571') or [None])[0],
        'citizenship': [lab.get(q, q) for q in items('P27')],
        'country': [lab.get(q, q) for q in items('P17')],
        'headquarters': [lab.get(q, q) for q in items('P159')],
        'founded_by': [lab.get(q, q) for q in items('P112')],
        'awards': [{'award': lab.get(a, a), 'year': y} for a, y in awards],
        'notable_works': [lab.get(q, q) for q in items('P800')],
        'website': sites,
        'enwiki': ent.get('sitelinks', {}).get('enwiki', {}).get('title'),
        'wikidata_url': f'https://www.wikidata.org/wiki/{qid}',
    }


def wikipedia(title):
    res = get(WP, {'action': 'query', 'prop': 'extracts', 'explaintext': 1, 'titles': title, 'redirects': 1,
                   'formatversion': 2})
    page = res['query']['pages'][0]
    text = page.get('extract', '')
    intro = text.split('\n==', 1)[0].strip()
    text = re.sub(r'\n==+ (References|Notes|Sources|Further reading|External links|Bibliography|See also) ==+.*',
                  '', text, flags=re.S)
    words = text.split(' ')
    if len(words) > MAX_WORDS:
        text = ' '.join(words[:MAX_WORDS]) + ' [...]'
    return {'title': page.get('title'), 'url': 'https://en.wikipedia.org/wiki/' + page.get('title', '').replace(' ', '_'),
            'intro': intro, 'text': text}


def pick(todo, ranks, only):
    if only:
        names = {n.strip() for n in only.split(',')}
        return [e for e in todo if e['name'] in names]
    if ranks:
        a, _, b = ranks.partition('-')
        return [e for e in todo if int(a) <= e['rank'] <= int(b or a)]
    return todo


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ranks')
    ap.add_argument('--only')
    ap.add_argument('--qids', help='overrides, "Name=Q123,Other=search phrase"')
    args = ap.parse_args()
    todo = json.loads((DIR / 'todo.json').read_text())
    over = dict(p.split('=', 1) for p in (args.qids or '').split(',') if '=' in p)
    out = json.loads(OUT.read_text()) if OUT.exists() else {}
    for e in pick(todo, args.ranks, args.only):
        name = e['name']
        qid = over.get(name) or e.get('qid')
        note = None
        if not qid or not re.fullmatch(r'Q\d+', str(qid)):
            # "manual:Name", a missing qid or an override that is a search phrase: search Wikidata
            text = str(qid)[7:] if str(qid).startswith('manual:') else (qid if qid else name)
            qid, note = search_qid(text)
        print(f"{e['rank']:>3} {name}: {qid} {note or ''}")
        rec = {'name': name, 'rank': e['rank'], 'qid_found_by_search': bool(note)}
        if qid:
            try:
                rec['wikidata'] = entity(qid)
                if rec['wikidata'].get('enwiki'):
                    rec['wikipedia'] = wikipedia(rec['wikidata']['enwiki'])
            except Exception as err:
                rec['error'] = str(err)
        out[name] = rec
        time.sleep(1)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + '\n')
    print('wrote', OUT, len(out))


if __name__ == '__main__':
    main()
