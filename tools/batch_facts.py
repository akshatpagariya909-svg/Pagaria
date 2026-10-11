#!/usr/bin/env python3
"""Fetch the facts a batch needs checked before it goes on the wall.

  python -u tools/batch_facts.py batch1     # reads tools/batches/batch1.json, writes tools/batches/batch1_facts.json

For each building: every year Wikidata gives it (inception, opening, start, service entry),
its architects' birth years, and its country's two-letter code. tools/merge_batch.py uses these
to check the curated year (a building can't be older than its architect's twentieth birthday,
and should match a year Wikidata gives) and the country.
Needs open internet access, so it runs on GitHub Actions (run-tool.yml).
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import api, WD  # noqa: E402
from harvest import value  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
YEARS = ('P571', 'P1619', 'P580', 'P729')  # inception, official opening, start time, service entry


def claims(qids, props):
    out = {}
    qids = sorted(set(qids))
    for k in range(0, len(qids), 50):
        q = api(WD, action='wbgetentities', ids='|'.join(qids[k:k + 50]), props='claims')
        for qid, ent in q.get('entities', {}).items():
            c = ent.get('claims', {})
            out[qid] = {p: [value(s['mainsnak']) for s in c.get(p, []) if s['mainsnak'].get('snaktype') == 'value'] for p in props}
    return out


def year_of(v):
    return int(v) if isinstance(v, str) and v.lstrip('-').isdigit() else None


def main():
    name = sys.argv[1]
    batch = json.loads((ROOT / 'tools' / 'batches' / f'{name}.json').read_text(encoding='utf-8'))
    items = claims([b['qid'] for b in batch], YEARS + ('P84', 'P17'))
    people = claims({a for c in items.values() for a in c['P84'] if isinstance(a, str)}, ('P569',))
    countries = claims({c for v in items.values() for c in v['P17'] if isinstance(c, str)}, ('P297',))
    out = {}
    for qid, c in items.items():
        births = [year_of(y) for a in c['P84'] for y in people.get(a, {}).get('P569', [])]
        out[qid] = {
            'years': sorted({y for p in YEARS for y in map(year_of, c[p]) if y}),
            'born': sorted({y for y in births if y}),
            'cc': sorted({x for k in c['P17'] for x in countries.get(k, {}).get('P297', []) if isinstance(x, str)}),
        }
    path = ROOT / 'tools' / 'batches' / f'{name}_facts.json'
    path.write_text(json.dumps(out, ensure_ascii=False, indent=0))
    print(f'Wrote facts for {len(out)} buildings to {path.relative_to(ROOT)}')


if __name__ == '__main__':
    sys.exit(main())
