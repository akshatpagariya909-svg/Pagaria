#!/usr/bin/env python3
"""Fetch the quality signals tools/score.py uses, then rescore.

  python -u tools/signals.py      # writes tools/harvest/signals.json, then runs tools/score.py

For every building in the scoring pool it records, from Wikidata:
  ids     which expert databases list it (archINFORM, Structurae, Docomomo, #SOSBrutalism, Archnet)
  n_ids   how many outside identifiers it has (catalogues, encyclopaedias, heritage registers)
  awards  the awards it received
Needs open internet access, so it runs on GitHub Actions (run-tool.yml).
"""
import json, re, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import api, WD  # noqa: E402
from harvest import labels  # noqa: E402
import score  # noqa: E402

OUT = score.H / 'signals.json'
WATCH = ('archinform', 'structurae', 'docomomo', 'sosbrutalism', 'archnet')


def main():
    recs, _ = score.pool()
    qids = sorted(r['qid'] for r in recs if not score.gate(r))
    print(f'{len(qids)} buildings to check', flush=True)
    raw, props, awards = {}, set(), set()
    for k in range(0, len(qids), 50):
        q = api(WD, action='wbgetentities', ids='|'.join(qids[k:k + 50]), props='claims')
        for qid, ent in q.get('entities', {}).items():
            claims = ent.get('claims', {})
            ext = [p for p, cs in claims.items() if cs and cs[0]['mainsnak'].get('datatype') == 'external-id']
            won = [c['mainsnak']['datavalue']['value']['id'] for c in claims.get('P166', []) if c['mainsnak'].get('snaktype') == 'value']
            raw[qid] = (ext, won)
            props.update(ext)
            awards.update(won)
        if k % 2000 == 0:
            print(f'  {k}/{len(qids)}', flush=True)
    print(f'resolving {len(props)} identifier and {len(awards)} award names', flush=True)
    names = labels(props | awards)
    key = {p: next((w for w in WATCH if w in re.sub(r'[^a-z]', '', names.get(p, '').lower())), None) for p in props}
    out = {qid: {'ids': sorted({key[p] for p in ext if key[p]}), 'n_ids': len(ext), 'awards': [names.get(a, a) for a in won]}
           for qid, (ext, won) in raw.items()}
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    print(f'Wrote signals for {len(out)} buildings; ' + ', '.join(f'{w} {sum(w in v["ids"] for v in out.values())}' for w in WATCH), flush=True)
    score.main()


if __name__ == '__main__':
    sys.exit(main())
