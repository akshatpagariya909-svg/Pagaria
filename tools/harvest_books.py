#!/usr/bin/env python3
"""Collect candidate books for the books shelf from Wikidata and Open Library. Writes tools/books_candidates.json.

  python3 tools/harvest_books.py

Nothing here reaches the site. Claude curates the candidates into tools/books_seed.json (shelf, tags, links,
"why read it"), and tools/fetch_books.py then fetches covers. Sources, all public:

  1. Wikidata: the architects of the wall's buildings (P84), then written works whose main subject (P921)
     is one of those architects or buildings, and written works those architects wrote (P50).
  2. Open Library: the most-published books in architecture subjects, and books about or by each
     architect on the wall with three or more buildings.

Every candidate keeps where it came from, which architects and buildings it matched, its edition count,
ISBN, Open Library work and, for the strongest candidates, Open Library's own description, so that the
"why read it" line can be written from a source rather than invented.

Needs network access, so it runs on GitHub Actions (first line of tools/books_request.txt:
python -u tools/harvest_books.py). Writes tools/books_harvest_report.md.
"""
import collections, json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILDINGS = ROOT / 'site' / 'data' / 'buildings.js'
SEED = ROOT / 'tools' / 'books_seed.json'
OUT = ROOT / 'tools' / 'books_candidates.json'
REPORT = ROOT / 'tools' / 'books_harvest_report.md'
UA = 'DiscoverArchitecture/1.0 (https://akshatpagariya909-svg.github.io/Pagaria/; akshatpagariya909@gmail.com; books shelf harvest)'
SPARQL = 'https://query.wikidata.org/sparql'
OL = 'https://openlibrary.org'

WRITTEN = ['Q571', 'Q7725634', 'Q47461344', 'Q193495', 'Q1279564', 'Q3331189', 'Q234460', 'Q17518461', 'Q1371849', 'Q5185279', 'Q1667921', 'Q8261']
SUBJECTS = ['architecture', 'architecture, modern', 'architecture, modern -- 20th century', 'architects', 'architectural design', 'architecture -- philosophy',
            'architecture -- history', 'architectural drawing', 'architecture, domestic', 'city planning', 'urban design', 'landscape architecture',
            'vernacular architecture', 'sustainable architecture', 'architecture and society', 'architecture -- india', 'architecture, japanese',
            'architecture -- japan', 'architecture, islamic', 'architecture, gothic', 'architecture, classical', 'architecture, renaissance',
            'building', 'building materials', 'structural engineering', 'interior architecture', 'architecture -- composition, proportion, etc.',
            'brutalism (architecture)', 'modern movement (architecture)', 'architecture -- latin america', 'architecture -- africa',
            'architecture -- china', 'architecture -- southeast asia', 'architectural criticism', 'architectural photography', 'housing']


def get(url, data=None, timeout=90, accept='application/json'):
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, data=data, headers={'User-Agent': UA, 'Accept': accept})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                out = r.read()
            time.sleep(0.4)
            return out
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code not in (429, 500, 502, 503, 504) or attempt == 5:
                print('   give up', url[:120], e)
                return None
            wait = int(e.headers.get('Retry-After') or 0) or min(120, 4 * 2 ** attempt)
            print(f'   {e.code}, waiting {wait}s'); time.sleep(wait)
        except Exception as e:
            if attempt == 5:
                print('   give up', url[:120], e); return None
            time.sleep(5 * (attempt + 1))


def sparql(q):
    data = urllib.parse.urlencode({'query': q, 'format': 'json'}).encode()
    raw = get(SPARQL, data=data, accept='application/sparql-results+json')
    if not raw:
        return []
    try:
        return json.loads(raw)['results']['bindings']
    except Exception:
        return []


def val(row, k):
    v = row.get(k, {}).get('value')
    return v.rsplit('/', 1)[-1] if v and v.startswith('http://www.wikidata.org/entity/') else v


def fold(s):
    return re.sub(r'[^a-z0-9 ]+', ' ', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()).split()


def key_of(title, author):
    t = ' '.join(w for w in fold(re.split(r'[:(]', title or '')[0]) if w not in ('the', 'a', 'an'))
    a = (fold(author or '') or [''])[-1]
    return f'{t}|{a}'


def main():
    t = BUILDINGS.read_text()
    B = json.loads(t[t.index('['):t.rindex(']') + 1])
    by_qid = {b['qid']: b for b in B if b.get('qid')}
    arch_count = collections.Counter(a.strip() for b in B for a in b['by'].split(','))
    seed = json.loads(SEED.read_text()) if SEED.exists() else []
    have = {key_of(k['title'], k['by'].split(',')[0].split(' and ')[0]) for k in seed}
    cands = {}

    def add(title, authors, src, **kw):
        if not title or len(title) > 200:
            return
        k = key_of(title, (authors or [''])[0])
        c = cands.setdefault(k, {'title': title, 'authors': authors or [], 'sources': [], 'architects': [], 'buildings': [], 'subjects': []})
        if src not in c['sources']:
            c['sources'].append(src)
        for f in ('architects', 'buildings', 'subjects'):
            for x in kw.pop(f, []) or []:
                if x not in c[f]:
                    c[f].append(x)
        for f, v in kw.items():
            if v and not c.get(f):
                c[f] = v

    # ---- 1. Wikidata: architects of the wall's buildings ----
    qids = list(by_qid)
    arch = {}  # architect qid -> name
    b_arch = collections.defaultdict(set)
    for i in range(0, len(qids), 250):
        vals = ' '.join('wd:' + q for q in qids[i:i + 250])
        rows = sparql(f'SELECT ?b ?a ?aLabel WHERE {{ VALUES ?b {{ {vals} }} ?b wdt:P84 ?a . SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }} }}')
        for r in rows:
            arch[val(r, 'a')] = val(r, 'aLabel'); b_arch[val(r, 'a')].add(val(r, 'b'))
        print(f'architects: {len(arch)} after {i + 250} buildings')
    # keep the names the wall uses where they agree
    wall_names = set(arch_count)
    # ---- written works about the architects or buildings, or by the architects ----
    types = ' '.join('wd:' + x for x in WRITTEN)
    subjects = list(arch) + qids
    def works(rel, ids, tag):
        for i in range(0, len(ids), 150):
            vals = ' '.join('wd:' + q for q in ids[i:i + 150])
            q = f'''SELECT ?w ?wLabel ?x ?title ?date ?isbn13 ?isbn10 ?ol ?wDescription (GROUP_CONCAT(DISTINCT ?authLabel; separator="|") AS ?authors) WHERE {{
  VALUES ?x {{ {vals} }} VALUES ?t {{ {types} }}
  ?w wdt:{rel} ?x ; wdt:P31 ?t .
  OPTIONAL {{ ?w wdt:P1476 ?title }} OPTIONAL {{ ?w wdt:P577 ?date }} OPTIONAL {{ ?w wdt:P212 ?isbn13 }} OPTIONAL {{ ?w wdt:P957 ?isbn10 }} OPTIONAL {{ ?w wdt:P648 ?ol }}
  OPTIONAL {{ ?w wdt:P50 ?auth . ?auth rdfs:label ?authLabel FILTER(LANG(?authLabel) = "en") }}
  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
}} GROUP BY ?w ?wLabel ?x ?title ?date ?isbn13 ?isbn10 ?ol ?wDescription'''
            for r in sparql(q):
                x = val(r, 'x'); title = val(r, 'title') or val(r, 'wLabel')
                if not title or re.fullmatch(r'Q\d+', title):
                    continue
                d = val(r, 'date') or ''
                kw = {'qid': val(r, 'w'), 'year': d[:4] if d[:4].isdigit() else None, 'isbn': val(r, 'isbn13') or val(r, 'isbn10'),
                      'ol': val(r, 'ol'), 'wd_desc': val(r, 'wDescription')}
                if x in by_qid:
                    kw['buildings'] = [by_qid[x]['id']]
                    kw['architects'] = [a.strip() for a in by_qid[x]['by'].split(',')][:2]
                elif x in arch:
                    kw['architects'] = [arch[x]]
                add(title, [a for a in (val(r, 'authors') or '').split('|') if a], tag, **kw)
            print(f'  wikidata {tag}: {len(cands)} candidates after {i + 150}')
    works('P921', subjects, 'wikidata-about')
    works('P50', list(arch), 'wikidata-by')

    # ---- 2. Open Library ----
    FIELDS = 'key,title,subtitle,author_name,first_publish_year,edition_count,cover_i,isbn,language,subject'
    def ol_search(params, tag, pages=1, **kw):
        for page in range(1, pages + 1):
            raw = get(f'{OL}/search.json?' + urllib.parse.urlencode({**params, 'fields': FIELDS, 'limit': 100, 'page': page}))
            docs = json.loads(raw).get('docs', []) if raw else []
            for d in docs:
                subj = [s for s in (d.get('subject') or []) if re.search(r'architect|building|urban|city planning|landscape|housing|design', s, re.I)][:12]
                title = d.get('title') + (': ' + d['subtitle'] if d.get('subtitle') else '')
                add(title, d.get('author_name') or [], tag, ol=d['key'].split('/')[-1], year=str(d.get('first_publish_year') or '') or None,
                    editions=d.get('edition_count'), cover=d.get('cover_i'), isbn=(d.get('isbn') or [None])[0],
                    lang=d.get('language') or [], subjects=subj, **kw)
            if len(docs) < 100:
                break
    for s in SUBJECTS:
        ol_search({'q': f'subject:"{s}"', 'sort': 'editions'}, 'ol-subject', pages=5)
        print(f'  open library subject {s!r}: {len(cands)} candidates')
    names = [a for a, n in arch_count.most_common() if n >= 3 and not re.search(r'\b(unknown|various|&|and partners|architects|studio|office)\b', a, re.I)]
    for a in names:
        ol_search({'q': f'subject:"{a}"', 'sort': 'editions'}, 'ol-about-architect', architects=[a])
        ol_search({'author': a, 'sort': 'editions'}, 'ol-by-architect', architects=[a])
    print(f'  open library architects: {len(cands)} candidates')

    # ---- score, drop what the shelf already has ----
    for k, c in list(cands.items()):
        if k in have:
            del cands[k]; continue
        s = min(c.get('editions') or 0, 60) / 6
        s += 6 * bool(c['buildings']) + 4 * bool(c['architects']) + 2 * bool(c.get('cover')) + 1.5 * ('eng' in (c.get('lang') or ['eng']))
        s += 2 * ('wikidata-about' in c['sources']) + 1 * len(c['sources'])
        c['score'] = round(s, 2)
    ranked = sorted(cands.values(), key=lambda c: -c['score'])

    # Save now, so a run that is cut short still leaves the candidates; descriptions are added on top.
    OUT.write_text(json.dumps(ranked, ensure_ascii=False, indent=0))
    print(f'{len(ranked)} candidates saved; adding descriptions.')
    # ---- Open Library's own description for the strongest candidates ----
    for i, c in enumerate(ranked[:900]):
        if c.get('ol') and re.fullmatch(r'OL\d+W', c['ol']):
            raw = get(f"{OL}/works/{c['ol']}.json", timeout=40)
            if raw:
                d = json.loads(raw).get('description')
                d = d.get('value') if isinstance(d, dict) else d
                if d:
                    c['ol_desc'] = re.sub(r'\s+', ' ', d)[:700]
        if i % 150 == 0:
            print(f'  descriptions: {i}')
            OUT.write_text(json.dumps(ranked, ensure_ascii=False, indent=0))
    OUT.write_text(json.dumps(ranked, ensure_ascii=False, indent=0))
    src = collections.Counter(s for c in ranked for s in c['sources'])
    REPORT.write_text('# Books harvest\n\n'
                      f'{len(ranked)} candidates not yet on the shelf, from {len(arch)} architects of {len(by_qid)} buildings.\n\n'
                      + '\n'.join(f'- {k}: {v}' for k, v in src.most_common()) + '\n\n'
                      + f"- with a matched building: {sum(1 for c in ranked if c['buildings'])}\n- with a matched architect: {sum(1 for c in ranked if c['architects'])}\n"
                      + f"- with a description: {sum(1 for c in ranked if c.get('ol_desc') or c.get('wd_desc'))}\n")
    print(f'{len(ranked)} candidates written.')


if __name__ == '__main__':
    main()
