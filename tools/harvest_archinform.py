#!/usr/bin/env python3
"""Pull every Wikidata building that archINFORM lists, as a second, better pool for the batches.

  python -u tools/harvest_archinform.py    # writes tools/harvest/archinform.json, then runs signals.py and score.py

archINFORM is a database of architecture kept by architects, so a listing there is a sign that
a building is worth studying, even when it has few Wikipedia articles. Records have the same
shape as tools/harvest/candidates.json, so tools/score.py treats both pools alike.
Needs open internet access, so it runs on GitHub Actions (run-tool.yml).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from harvest import sparql, entities, labels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tools' / 'harvest' / 'archinform.json'


def ids():
    rows = sparql('''SELECT ?item ?n WHERE {
      ?prop rdfs:label "archINFORM project ID"@en ; wikibase:directClaim ?d .
      ?item ?d [] .
      OPTIONAL { ?item wikibase:sitelinks ?n }
    }''')
    out = {}
    for r in rows:
        qid = r['item']['value'].rsplit('/', 1)[1]
        out[qid] = max(out.get(qid, 0), int(r.get('n', {}).get('value', 0)))
    return out


def main():
    found = ids()
    print(f'{len(found)} items listed in archINFORM', flush=True)
    if len(found) < 1000:
        sys.exit('Too few; check the property label in ids()')
    recs = entities(sorted(found))
    recs = {q: r for q, r in recs.items() if r.get('image') or r.get('commons')}
    print(f'{len(recs)} of them have a free photo or Commons folder', flush=True)
    refs = set()
    for r in recs.values():
        r['sitelinks'] = found.get(r['qid'], 0)
        r['archinform'] = True
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

    import signals  # rescore with the new pool: fetch its signals, then score everything
    signals.main()


if __name__ == '__main__':
    sys.exit(main())
