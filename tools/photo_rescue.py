#!/usr/bin/env python3
"""Photo rescue: look again for free photos of buildings held back for want of one.

  python tools/photo_rescue.py due    says whether a rescue round is due (every 300 buildings added)
  python tools/photo_rescue.py todo   writes tools/photo_rescue/todo.json, the buildings to look for
  python tools/photo_rescue.py mark   records that a round ran, at today's wall size

A round is due each time the wall has grown by 300 buildings since the last one. A daily Sonnet routine
runs `due`, and when it says yes, follows tools/photo_rescue/BRIEF.md: it searches Commons for each
building in todo.json and writes tools/illustrate/results/rescue_<date>.json on its own branch
(claude/photo-rescue). The data-collection chat (Opus) then checks every photo by eye, takes the
accepted buildings out of tools/illustrate/rejected.txt and runs the usual pipeline (add_illustrated,
fetch, links, build).

todo.json lists buildings that are off the wall only because no photo of the building itself was found:
held back in photo review, taken off the wall because their photos showed people or objects, or
proposed with "no free photo". Ordinary types held back for quality, duplicates, failed fact checks
and demolished buildings are left out. Each entry carries the facts in the results format, so a
rescued building can go straight back on the wall.
"""
import json, re, subprocess, sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
IL = ROOT / 'tools' / 'illustrate'
OUT = ROOT / 'tools' / 'photo_rescue'
STATE = OUT / 'state.json'
EVERY = 300
PHOTO = re.compile(r"photo|exterior|picture|image|night shot|crowd|people|showed other|another building", re.I)
NOT_PHOTO = re.compile(r'quality watch|duplicate|fact check|demolished|drawing|a bridge, not', re.I)
FACTS = ('name', 'by', 'city', 'cc', 'year', 'type', 'movement', 'concepts', 'features')


def wall():
    t = (ROOT / 'site' / 'data' / 'buildings.js').read_text(encoding='utf-8')
    return json.loads(t[t.index('['):t.rindex(']') + 1])


def state():
    return json.loads(STATE.read_text()) if STATE.exists() else {'last_wall': 0, 'rounds': []}


def from_wall(b):
    city, _, cc = b['place'].rpartition(', ')
    return {'name': b['name'], 'by': b['by'], 'city': city, 'cc': cc, 'year': b['year'], 'type': b['type'],
            'movement': b['movement'], 'concepts': b['concepts'], 'features': b.get('study', '')}


def old_wall_entries(ids):
    """Facts for buildings that were on the wall once, from the newest version of buildings.js that had them."""
    found, want = {}, set(ids)
    shas = subprocess.run(['git', 'log', '--format=%H', '-n', '60', '--', 'site/data/buildings.js'], cwd=ROOT,
                          capture_output=True, text=True).stdout.split()
    for sha in shas:
        if not want:
            break
        t = subprocess.run(['git', 'show', f'{sha}:site/data/buildings.js'], cwd=ROOT, capture_output=True, text=True).stdout
        try:
            for b in json.loads(t[t.index('['):t.rindex(']') + 1]):
                if b['id'] in want:
                    found[b['id']] = from_wall(b)
                    want.discard(b['id'])
        except ValueError:
            continue
    return found


def todo():
    on = {b['id'] for b in wall()}
    results = {}
    for p in sorted((IL / 'results').glob('*.json')):
        for r in json.loads(p.read_text(encoding='utf-8')):
            results[r['id']] = {**results.get(r['id'], {}), **{k: v for k, v in r.items() if v not in (None, '', [])}}
    cands = {c['id']: c for c in json.loads((IL / 'candidates.json').read_text(encoding='utf-8'))}
    why = {}
    for line in (IL / 'rejected.txt').read_text(encoding='utf-8').splitlines():
        i, _, note = line.partition('#')
        if i.strip():
            why[i.strip()] = note.strip()
    pick = {}
    for i, note in why.items():  # held back or taken off for want of a photo of the building
        if i not in on and PHOTO.search(note) and not NOT_PHOTO.search(note):
            pick[i] = note
    for i, r in results.items():  # proposed, but no free photo found
        if i not in on and i not in why and r.get('status') == 'unsure' and 'photo' in (r.get('note') or '').lower():
            pick[i] = r.get('note')
    facts = {}
    for i in pick:
        src = {**cands.get(i, {}), **results.get(i, {})}
        if all(src.get(k) for k in FACTS):
            facts[i] = {k: src[k] for k in FACTS}
    facts.update(old_wall_entries([i for i in pick if i not in facts]))
    tried = json.loads((OUT / 'tried.json').read_text()) if (OUT / 'tried.json').exists() else {}
    rows = [{'id': i, **facts[i], 'why': pick[i], 'tried': tried.get(i, [])} for i in pick if i in facts]
    rows.sort(key=lambda r: (len(r['tried']), r['id']))  # never-tried first
    OUT.mkdir(exist_ok=True)
    (OUT / 'todo.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{len(rows)} buildings to look for ({sum(1 for r in rows if not r["tried"])} never tried); '
          f'{len(pick) - len(rows)} skipped for missing facts')


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'due'
    s, n = state(), len(wall())
    if cmd == 'due':
        grown = n - s['last_wall']
        print(f"{'DUE' if grown >= EVERY else 'NOT DUE'}: wall {n}, last rescue at {s['last_wall']} (+{grown}, every {EVERY})")
    elif cmd == 'todo':
        todo()
    elif cmd == 'mark':
        s['last_wall'] = n
        s['rounds'].append({'date': date.today().isoformat(), 'wall': n})
        OUT.mkdir(exist_ok=True)
        STATE.write_text(json.dumps(s, indent=1) + '\n')
        print('marked at', n)


if __name__ == '__main__':
    main()
