#!/usr/bin/env python3
"""Pull candidate buildings from Wikidata for growing the list toward 1,000.

  python3 tools/harvest.py            # writes tools/harvest/candidates.json

Candidates are Wikidata items that name an architect (P84) and have enough Wikipedia
language editions to be well known. For each one it records the facts the site uses:
architect, year, country, city, coordinates, Commons category, lead image, type,
style, official website and heritage status, with English labels.
Needs open internet access, so it runs on GitHub Actions (run-tool.yml).
"""
import json, sys, time, urllib.parse, urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import fetch, api, WD  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tools' / 'harvest' / 'candidates.json'
SPARQL = 'https://query.wikidata.org/sparql'
MIN_SITELINKS = 6
PROPS = {'P84': 'architect', 'P571': 'inception', 'P1619': 'opened', 'P17': 'country', 'P131': 'located', 'P625': 'coords',
         'P373': 'commons', 'P18': 'image', 'P31': 'instance', 'P149': 'style', 'P856': 'website', 'P1435': 'heritage', 'P5816': 'state'}


def sparql(q):
    url = SPARQL + '?' + urllib.parse.urlencode({'query': q, 'format': 'json'})
    return json.loads(fetch(url, timeout=300))['results']['bindings']


def ids():
    q = f'''SELECT ?item ?n WHERE {{
      ?item wdt:P84 ?a; wikibase:sitelinks ?n .
      FILTER(?n >= {MIN_SITELINKS})
    }}'''
    rows = sparql(q)
    out = {}
    for r in rows:
        qid = r['item']['value'].rsplit('/', 1)[1]
        out[qid] = max(out.get(qid, 0), int(r['n']['value']))
    return out


def value(snak):
    dv = snak.get('datavalue', {})
    v = dv.get('value')
    t = dv.get('type')
    if t == 'wikibase-entityid':
        return v['id']
    if t == 'time':
        return v['time'][1:5] if v['time'].startswith('+') else '-' + v['time'][1:5]
    if t == 'globecoordinate':
        return [round(v['latitude'], 5), round(v['longitude'], 5)]
    return v


def entities(qids):
    out = {}
    for k in range(0, len(qids), 50):
        q = api(WD, action='wbgetentities', ids='|'.join(qids[k:k + 50]), props='labels|claims|sitelinks', languages='en', sitefilter='enwiki')
        for qid, ent in q.get('entities', {}).items():
            rec = {'qid': qid, 'label': ent.get('labels', {}).get('en', {}).get('value'),
                   'enwiki': ent.get('sitelinks', {}).get('enwiki', {}).get('title')}
            for p, name in PROPS.items():
                vals = [value(c['mainsnak']) for c in ent.get('claims', {}).get(p, []) if c['mainsnak'].get('snaktype') == 'value']
                if vals:
                    rec[name] = vals
            out[qid] = rec
        if k % 1000 == 0:
            print(f'  {k}/{len(qids)}', flush=True)
    return out


def labels(qids):
    out = {}
    qids = sorted(qids)
    for k in range(0, len(qids), 50):
        q = api(WD, action='wbgetentities', ids='|'.join(qids[k:k + 50]), props='labels', languages='en')
        for qid, ent in q.get('entities', {}).items():
            out[qid] = ent.get('labels', {}).get('en', {}).get('value') or qid
    return out


def main():
    found = ids()
    print(f'{len(found)} items with an architect and at least {MIN_SITELINKS} sitelinks', flush=True)
    recs = entities(sorted(found))
    refs = set()
    for r in recs.values():
        r['sitelinks'] = found.get(r['qid'], 0)
        for key in ('architect', 'country', 'located', 'instance', 'style', 'heritage', 'state'):
            refs.update(v for v in r.get(key, []) if isinstance(v, str) and v.startswith('Q'))
    print(f'resolving {len(refs)} labels', flush=True)
    names = labels(refs)
    for r in recs.values():
        for key in ('architect', 'country', 'located', 'instance', 'style', 'heritage', 'state'):
            if key in r:
                r[key] = [names.get(v, v) if isinstance(v, str) else v for v in r[key]]
    rows = sorted(recs.values(), key=lambda r: -r['sitelinks'])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
    print(f'Wrote {len(rows)} candidates to {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    sys.exit(main())
