#!/usr/bin/env python3
"""Apply fact checks to the illustration results and the wall.

  python tools/apply_verify.py tools/illustrate/verify_b_result.json [more files]

Each check is {id, verdict: ok|fixed|drop, by?, year?, features?, sources, note}, written by a
fact-checking pass over entries whose notes said some facts were unconfirmed.
  fixed  the given by / year / features replace the old ones, in the results file the building came
         from and, if it's already on the wall, in site/data/buildings.js (features is the "study" line).
  drop   no source gives the architect or year: the building goes on tools/illustrate/rejected.txt
         and comes off the wall if it's there.
The checks themselves stay in tools/illustrate/ as the record of what was confirmed and where.
"""
import glob, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IL = ROOT / 'tools' / 'illustrate'


def main():
    checks = {c['id']: c for f in sys.argv[1:] for c in json.loads(Path(f).read_text(encoding='utf-8'))}
    for p in sorted((IL / 'results').glob('*.json')):  # fix the results the buildings came from
        rs = json.loads(p.read_text(encoding='utf-8'))
        for r in rs:
            c = checks.get(r['id'])
            if c and c['verdict'] == 'fixed':
                r.update({k: c[k] for k in ('by', 'year', 'features') if c.get(k)})
        p.write_text(json.dumps(rs, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    head, items = load()
    keep, dropped, fixed = [], [], 0
    for b in items:
        c = checks.get(b['id'])
        if c and c['verdict'] == 'drop':
            dropped.append(b['name'])
            shutil.rmtree(ROOT / 'site' / 'images' / b['id'], ignore_errors=True)
            continue
        if c and c['verdict'] == 'fixed':
            if c.get('by'):
                b['by'] = c['by']
            if c.get('year'):
                b['year'] = str(c['year'])
                b['y'] = int(re.search(r'\d{3,4}', str(c['year'])).group())
            if c.get('features'):
                b['study'] = c['features']
            fixed += 1
        keep.append(b)
    for n, b in enumerate(keep, 1):
        b['n'] = n
    save(head, keep)
    drops = [i for i, c in checks.items() if c['verdict'] == 'drop']
    with (IL / 'rejected.txt').open('a', encoding='utf-8') as f:
        f.writelines(f'{i}  # fact check: architect or year not found in any source\n' for i in drops)
    print(f'{fixed} on the wall corrected, {len(dropped)} taken off the wall ({", ".join(dropped)}), {len(drops)} dropped in all')


if __name__ == '__main__':
    sys.exit(main())
