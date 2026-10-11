#!/usr/bin/env python3
"""Add a curated, checked batch of buildings to the wall.

  python tools/merge_batch.py batch1          add the batch's kept buildings to site/data/buildings.js
  python tools/merge_batch.py batch1 --trim   after fetching photos: drop the batch's buildings that got none

Reads tools/batches/:
  batch1.json               the scored list (tools/score.py), frozen when the batch was chosen
  batch1_curated_part*.json the curation: keep 0-3, name, architect, city, country, year, type,
                            movement, three ideas and the Key features line
  batch1_facts.json         Wikidata years, architects' birth years and country codes (tools/batch_facts.py)
  batch1_approved.txt       optional: Wikidata IDs the owner checked by hand, merged without the checks
  batch1_nophoto.txt        written by --trim: buildings dropped for having no free photo, never merged again
Writes tools/batches/batch1_report.md: what was added, held back for a check by hand, or turned down.

A building is held back when its year doesn't hold up: earlier than its architect's twentieth
birthday, or more than 3 years from every year Wikidata gives. It's also held back when its
country doesn't match Wikidata. Held buildings can be fixed in the curation file and merged again.
"""
import argparse, json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save  # noqa: E402
from merge_1000 import entry, fold  # noqa: E402
from score import pool  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
B = ROOT / 'tools' / 'batches'


def check(c, f):
    """Why a curated building's facts don't hold up, or None."""
    try:
        y = int(str(c['year'])[:4])
    except ValueError:
        return 'no year'
    if f.get('born') and y < min(f['born']) + 20:
        return f'year {y} is before the architect could have built it (born {min(f["born"])})'
    if f.get('years') and all(abs(y - w) > 3 for w in f['years']):
        return f'year {y} matches none of Wikidata\'s years ({", ".join(map(str, f["years"]))})'
    if f.get('cc') and c['cc'] not in f['cc']:
        return f'country {c["cc"]} but Wikidata says {", ".join(f["cc"])}'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('batch')
    ap.add_argument('--trim', action='store_true')
    args = ap.parse_args()
    head, items = load()
    batch = json.loads((B / f'{args.batch}.json').read_text(encoding='utf-8'))
    qids = {b['qid'] for b in batch}

    nophoto = B / f'{args.batch}_nophoto.txt'
    dropped = {l.split('#')[0].strip() for l in nophoto.read_text(encoding='utf-8').splitlines()} - {''} if nophoto.exists() else set()
    if args.trim:
        keep = [b for b in items if b.get('qid') not in qids or b.get('images')]
        gone = [b for b in items if b not in keep]
        if gone:  # remember them, so a later merge doesn't bring them back
            with nophoto.open('a', encoding='utf-8') as f:
                f.writelines(f"{b['qid']}  # {b['name']}\n" for b in gone)
        print(f'{len(gone)} batch buildings dropped for having no free photos')
        for n, b in enumerate(keep, 1):
            b['n'] = n
        save(head, keep)
        return

    curated = [c for p in sorted(B.glob(f'{args.batch}_curated_part*.json')) for c in json.loads(p.read_text(encoding='utf-8'))]
    facts = json.loads((B / f'{args.batch}_facts.json').read_text(encoding='utf-8'))
    ok = B / f'{args.batch}_approved.txt'
    approved = {l.split('#')[0].strip() for l in ok.read_text(encoding='utf-8').splitlines()} - {''} if ok.exists() else set()
    recs = {r['qid']: r for r in pool()[0]}
    have = {b.get('qid') for b in items} | {fold(b['name']) for b in items}
    ids = {b['id'] for b in items}
    added, held, down = [], [], []
    for c in sorted(curated, key=lambda c: -c['keep']):
        if c['keep'] < 1:
            down.append((c, c.get('note') or 'turned down in curation'))
            continue
        if c['qid'] in have or fold(c['name']) in have:
            continue  # added by an earlier run of this batch, or already there
        if c['qid'] in dropped:
            down.append((c, 'no free photo found'))
            continue
        why = None if c['qid'] in approved else check(c, facts.get(c['qid'], {}))
        if why:
            held.append((c, why))
            continue
        r = recs.get(c['qid'], {})
        c = {**c, 'commons': (r.get('commons') or [None])[0], 'lead': (r.get('image') or [None])[0], 'coords': (r.get('coords') or [None])[0]}
        if not (c['commons'] or c['lead']):
            down.append((c, 'no free photo'))
            continue
        b = entry(c, len(items) + 1, ids)
        items.append(b)
        ids.add(b['id'])
        have |= {c['qid'], fold(c['name'])}
        added.append(b)
    save(head, items)
    row = lambda c, why: f'| {c["name"]} | {c["by"]} | {c["year"]} | {c["city"]}, {c["cc"]} | {why} |'
    mine = {c['qid'] for c in curated}
    on = [b for b in items if b.get('qid') in mine]
    L = [f'# {args.batch}', '', f'- Curated: {len(curated)}', f'- On the wall from this batch: {len(on)} ({len(added)} added in the latest run, '
         f'{sum(b["qid"] in approved for b in on)} of them approved by hand)',
         f'- Held back for a check by hand: {len(held)}', f'- Turned down: {len(down)}', '',
         '## Held back', '', '| Building | Architect | Year | Place | Why |', '|---|---|---|---|---|']
    L += [row(c, w) for c, w in held]
    L += ['', '## Turned down', '', '| Building | Architect | Year | Place | Why |', '|---|---|---|---|---|']
    L += [row(c, w) for c, w in down]
    L += ['', '## On the wall', '', '| # | Building | Architect | Year | Place | Type | Movement |', '|---|---|---|---|---|---|---|']
    L += [f'| {b["n"]} | {b["name"]} | {b["by"]} | {b["year"]} | {b["place"]} | {b["type"]} | {b["movement"]} |' for b in on]
    (B / f'{args.batch}_report.md').write_text('\n'.join(L) + '\n', encoding='utf-8')
    print(f'{len(added)} added, {len(held)} held back, {len(down)} turned down; {len(items)} on the wall')


if __name__ == '__main__':
    sys.exit(main())
