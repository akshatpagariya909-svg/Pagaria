#!/usr/bin/env python3
"""Pull Wikidata buildings from the regions the wall is thin on, with a low fame bar.

  python -u tools/harvest_regions.py    # writes tools/harvest/regions.json, then runs signals.py and score.py

Africa, South and Southeast Asia, the Middle East and Central Asia, and Latin America: every item
with an architect (P84) and a free photo or Commons folder, in at least one Wikipedia. Records have
the same shape as tools/harvest/candidates.json, so tools/score.py treats every pool alike.
Needs open internet access, so it runs on GitHub Actions (run-tool.yml).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest import sparql, entities, labels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tools' / 'harvest' / 'regions.json'
# continents: Africa, Asia, South America; plus Mexico, Central America and the Caribbean
CONTINENTS = 'wd:Q15 wd:Q48 wd:Q18'
LATIN_NORTH = ('Q96 Q774 Q790 Q783 Q792 Q811 Q800 Q804 Q241 Q786 Q766 Q242 Q244 Q1183 Q754 Q778 Q757 Q760 Q769 Q784 Q781 Q763')
SKIP = 'wd:Q17 wd:Q148 wd:Q884 wd:Q865 wd:Q8646 wd:Q14773 wd:Q423 wd:Q159'  # Japan, China, S Korea, Taiwan, Hong Kong, Macau, N Korea, Russia


def ids():
    found = {}
    for where in (f'?c wdt:P30 ?k . VALUES ?k {{ {CONTINENTS} }} FILTER(?c NOT IN ({SKIP.replace(" ", ", ")}))',
                  'VALUES ?c { ' + ' '.join('wd:' + q for q in LATIN_NORTH.split()) + ' }'):
        rows = sparql(f'''SELECT ?item ?n WHERE {{
          ?item wdt:P84 ?a ; wdt:P17 ?c ; wikibase:sitelinks ?n .
          {where}
          FILTER(?n >= 1)
          FILTER EXISTS {{ {{ ?item wdt:P18 [] }} UNION {{ ?item wdt:P373 [] }} }}
        }}''')
        for r in rows:
            qid = r['item']['value'].rsplit('/', 1)[1]
            found[qid] = max(found.get(qid, 0), int(r['n']['value']))
        print(f'  {len(found)} so far', flush=True)
    return found


def main():
    found = ids()
    print(f'{len(found)} buildings with an architect and a free photo in the target regions', flush=True)
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
    OUT.write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
    print(f'Wrote {len(rows)} buildings to {OUT.relative_to(ROOT)}', flush=True)

    import signals  # fetch the new buildings' signals, then rescore every pool
    signals.main()


if __name__ == '__main__':
    sys.exit(main())
