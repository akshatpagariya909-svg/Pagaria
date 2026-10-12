#!/usr/bin/env python3
"""Curate candidate books into the shelf in batches. Used by Claude in the scheduled curation sessions.

  python3 tools/books_batch.py next 80          the next 80 candidates nobody has reviewed yet (compact JSON)
  python3 tools/books_batch.py add batch.json   check a batch and add it to tools/books_seed.json
  python3 tools/books_batch.py stats            write tools/books_progress.md

A batch file is {"add": [book, ...], "reject": ["candidate key", ...]}. Each book has the seed fields:
id, title, by, year, y, shelf, why, tags[], architects[], buildings[], and "key" (the candidate key it came from).
`add` refuses the whole batch if anything is wrong: unknown shelf, an architect name the wall does not use,
a building id that does not exist, a duplicate id or a book already on the shelf, a missing "why", or a "why"
longer than 200 characters. Reviewed candidate keys (added or rejected) go to tools/books_reviewed.json so
the next session skips them.
"""
import collections, json, re, sys, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / 'tools' / 'books_seed.json'
CANDS = ROOT / 'tools' / 'books_candidates.json'
REVIEWED = ROOT / 'tools' / 'books_reviewed.json'
PROGRESS = ROOT / 'tools' / 'books_progress.md'
SHELVES = ['Essentials', 'Theory', 'History', 'Manifestos', 'Monographs', 'Drawing', 'Construction', 'Cities', 'Landscape', 'India', 'Free to read']


def fold(s):
    return re.sub(r'[^a-z0-9 ]+', ' ', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower()).split()


def key_of(title, author):
    t = ' '.join(w for w in fold(re.split(r'[:(]', title or '')[0]) if w not in ('the', 'a', 'an'))
    return f"{t}|{(fold(author or '') or [''])[-1]}"


def wall():
    t = (ROOT / 'site' / 'data' / 'buildings.js').read_text()
    B = json.loads(t[t.index('['):t.rindex(']') + 1])
    return B, collections.Counter(a.strip() for b in B for a in b['by'].split(',')), {b['id'] for b in B}


def load(p, default):
    return json.loads(p.read_text()) if p.exists() else default


def first_author(by):
    return re.split(r',| and |\(', by)[0].strip()


def cmd_next(n):
    seed, reviewed = load(SEED, []), set(load(REVIEWED, []))
    have = {key_of(k['title'], first_author(k['by'])) for k in seed}
    out = []
    for c in load(CANDS, []):
        k = key_of(c['title'], (c.get('authors') or [''])[0])
        if k in reviewed or k in have:
            continue
        out.append({'key': k, 'title': c['title'], 'authors': c.get('authors', [])[:3], 'year': c.get('year'), 'editions': c.get('editions'),
                    'architects': c.get('architects', []), 'buildings': c.get('buildings', []), 'subjects': c.get('subjects', [])[:6],
                    'desc': (c.get('ol_desc') or c.get('wd_desc') or '')[:400], 'ol': c.get('ol'), 'isbn': c.get('isbn'), 'score': c.get('score')})
        if len(out) >= n:
            break
    print(json.dumps(out, ensure_ascii=False, indent=0))


def cmd_add(path):
    batch = json.loads(Path(path).read_text())
    seed, reviewed = load(SEED, []), load(REVIEWED, [])
    _, names, ids = wall()
    have_ids = {k['id'] for k in seed}
    have_keys = {key_of(k['title'], first_author(k['by'])) for k in seed}
    errors, new = [], []
    for k in batch.get('add', []):
        tag = k.get('id', '?')
        for f in ('id', 'title', 'by', 'year', 'shelf', 'why'):
            if not k.get(f):
                errors.append(f'{tag}: missing {f}')
        if k.get('shelf') not in SHELVES:
            errors.append(f'{tag}: unknown shelf {k.get("shelf")!r}')
        if len(k.get('why', '')) > 200:
            errors.append(f'{tag}: "why" is longer than 200 characters')
        for a in k.get('architects', []):
            if a not in names:
                errors.append(f'{tag}: the wall has no architect named {a!r}')
        for b in k.get('buildings', []):
            if b not in ids:
                errors.append(f'{tag}: no building with id {b!r}')
        if k.get('id') in have_ids or any(x['id'] == k.get('id') for x in new):
            errors.append(f'{tag}: id already used')
        if key_of(k.get('title', ''), first_author(k.get('by', ''))) in have_keys:
            errors.append(f'{tag}: already on the shelf')
        try:
            y = int(k.get('y', str(k.get('year', ''))[:4]))
        except ValueError:
            errors.append(f'{tag}: year {k.get("year")!r} is not a number; give "y"'); y = 0
        new.append({'id': k.get('id'), 'title': k.get('title'), 'by': k.get('by'), 'year': str(k.get('year')), 'y': y, 'shelf': k.get('shelf'),
                    'why': k.get('why'), 'tags': k.get('tags', []), 'architects': k.get('architects', []), 'buildings': k.get('buildings', [])})
    if errors:
        print('Batch refused, nothing added:\n  ' + '\n  '.join(errors)); sys.exit(1)
    seed += new
    keys = [k['key'] for k in batch.get('add', []) if k.get('key')] + list(batch.get('reject', []))
    reviewed = sorted(set(reviewed) | set(keys))
    SEED.write_text(json.dumps(seed, ensure_ascii=False, indent=1) + '\n')
    REVIEWED.write_text(json.dumps(reviewed, ensure_ascii=False, indent=0) + '\n')
    print(f'Added {len(new)}, rejected {len(batch.get("reject", []))}. The shelf has {len(seed)} books.')
    cmd_stats()


def cmd_stats():
    seed = load(SEED, [])
    B, names, _ = wall()
    linked_arch = {a for k in seed for a in k['architects']}
    named = {x for k in seed for x in k['buildings']}
    reach = sum(1 for b in B if b['id'] in named or any(a.strip() in linked_arch for a in b['by'].split(',')))
    big = [a for a, n in names.most_common() if n >= 4 and a not in linked_arch and not re.search(r'unknown|various', a, re.I)]
    reviewed = load(REVIEWED, [])
    cands = load(CANDS, [])
    lines = ['# Books progress', '',
             f'| | |', '|---|---|',
             f'| Books on the shelf | {len(seed)} |',
             f'| Buildings on the wall with at least one book | {reach} of {len(B)} |',
             f'| Buildings named in a book | {len(named)} |',
             f'| Architects with a book | {len(linked_arch)} |',
             f'| Candidates reviewed | {len(reviewed)} of {len(cands)} |', '',
             '## By shelf', ''] + [f'- {s}: {n}' for s, n in collections.Counter(k["shelf"] for k in seed).most_common()] + \
            ['', '## Architects with four or more buildings and no book yet', '', ', '.join(big) or 'None.']
    PROGRESS.write_text('\n'.join(lines) + '\n')
    print(f'{len(seed)} books; {reach} of {len(B)} buildings reach a book; {len(big)} big architects still without one.')


if __name__ == '__main__':
    a = sys.argv[1:]
    {'next': lambda: cmd_next(int(a[1]) if len(a) > 1 else 80), 'add': lambda: cmd_add(a[1]), 'stats': cmd_stats}[a[0] if a else 'stats']()
