#!/usr/bin/env python3
"""Add the buildings from tools/illustrate/ to the wall.

  python tools/add_illustrated.py            add them to site/data/buildings.js
  python tools/add_illustrated.py --dry-run  just report what would happen

tools/illustrate/candidates.json lists important buildings, from the hand lists and batches, that
had no free photo; tools/illustrate/results/*.json says what was found for each (see
tools/illustrate/BRIEF.md):

  drawn   our line drawing goes up as the cover (site/images/<id>/drawing.svg), tagged
          "Drawing, not a photo". Free plans, sections or models found on Commons are hand-picked
          in tools/image_choices.json, to be fetched next to it.
  photo   Commons does have free photos after all: the building goes up with them as hand picks,
          fetched like any other (fetch_images.py --only <ids>).
  unsure  left off, listed in tools/illustrate/no_free_photo.md for later.

Buildings already on the wall that are listed in tools/illustrate/covers.txt get their drawing
(tools/illustrate/svg/<id>.svg) as the cover, in front of their photos.

Buildings in tools/illustrate/rejected.txt (one id per line, # for notes) are left off too.
Writes tools/illustrate/fetch_ids.txt: the buildings that need fetch_images.py --only.
Afterwards run tools/fit_drawings.py, which fits the drawings above the wall tile's caption.
"""
import argparse, json, re, shutil, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save  # noqa: E402
from merge_1000 import entry, fold  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IL = ROOT / 'tools' / 'illustrate'
CHOICES = ROOT / 'tools' / 'image_choices.json'
DRAWING = {'kind': 'Drawing', 'caption': 'Drawing, not a photo', 'credit': 'Drawing: Find Great Architecture',
           'license': 'CC BY 4.0', 'source': None, 'w': 400, 'h': 260}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    cands = {c['id']: c for c in json.loads((IL / 'candidates.json').read_text(encoding='utf-8'))}
    results = {}
    for p in sorted((IL / 'results').glob('*.json')):  # later files (e.g. rescue_*) add to an earlier entry, not replace it
        for r in json.loads(p.read_text(encoding='utf-8')):
            results[r['id']] = {**results.get(r['id'], {}), **{k: v for k, v in r.items() if v not in (None, '', [])}}
    for i, r in results.items():  # round 2 proposed its own buildings, with their facts in the result
        if i not in cands and all(r.get(k) for k in ('name', 'by', 'city', 'cc', 'year', 'type', 'movement', 'concepts', 'features')):
            cands[i] = {**{k: r[k] for k in ('name', 'by', 'city', 'cc', 'year', 'type', 'movement', 'concepts', 'features')}, 'id': i, 'qid': None}
    rej = IL / 'rejected.txt'
    why_rej = {l.split('#')[0].strip(): (l.split('#', 1)[1].strip() if '#' in l else 'turned down in review')
               for l in rej.read_text(encoding='utf-8').splitlines()} if rej.exists() else {}
    rejected = set(why_rej) - {''}
    choices = json.loads(CHOICES.read_text(encoding='utf-8'))
    head, items = load()
    have = {fold(b['name']) for b in items} | {b.get('qid') for b in items if b.get('qid')}
    ids = {b['id'] for b in items}
    same = lambda cat, year: (str(cat or '').replace('Category:', '').strip().lower(), str(year)[:4])
    have_cat = {same(b['commons'], b['year']) for b in items if b.get('commons')}  # the same building under another name
    words = lambda n: {w for w in re.sub(r'[^a-z0-9 ]', ' ', fold(n)).split() if len(w) > 2 and w not in {'the', 'and', 'building', 'mausoleum', 'museum', 'house', 'hall'}}
    sig = lambda by, year, place: (((by or '').split(',')[0].split('(')[0].split()[-1:] or [''])[0].lower(), str(year)[:4], place)
    have_sig = {}  # architect's surname, year and place: the same building with its name worded differently
    for b in items:
        have_sig.setdefault(sig(b['by'], b['year'], b['place']), []).append(words(b['name']))
    def reworded(c):
        w = words(c['name'])
        return any(w and o and len(w & o) / min(len(w), len(o)) >= 0.6 for o in have_sig.get(sig(c['by'], c['year'], f"{c['city']}, {c['cc']}"), []))
    added, fetch, left = [], [], []
    for i, c in cands.items():
        r = results.get(i, {'status': 'unsure', 'note': 'not checked yet'})
        if i in ids or fold(c['name']) in have or (c.get('qid') and c['qid'] in have) \
                or (r.get('commons_category') and same(r['commons_category'], c['year']) in have_cat) or reworded(c):
            continue
        svg = IL / 'svg' / f'{i}.svg'
        if i in rejected or r['status'] not in ('drawn', 'photo') or (r['status'] == 'drawn' and not svg.exists()):
            left.append((c, r, why_rej[i] if i in rejected else r.get('note') or r['status']))
            continue
        photos = [p['file'] for p in r.get('photos', [])]
        extras = [[x['file'], x['kind']] for x in r.get('extras', [])]
        b = entry({**c, 'qid': c.get('qid'), 'commons': (r.get('commons_category') or '').replace('Category:', '') or None,
                   'lead': photos[0].replace('File:', '') if photos else None}, len(items) + 1, ids)
        b['id'] = i  # the id the drawing was made under
        if r['status'] == 'drawn':
            rel = f'images/{i}/drawing.svg'
            b['images'] = [{'src': rel, 'thumb': rel, **DRAWING}]
            after = r.get('after')
            if after:  # drawn after one free photo: credit it; CC BY-SA covers both a BY and a BY-SA source
                f = after.get('file') if isinstance(after, dict) else str(after).split(' (')[0]
                b['images'][0].update(credit=f'Drawing: Find Great Architecture, after {f}', license='CC BY-SA 4.0')
            if not args.dry_run:
                (ROOT / 'site' / 'images' / i).mkdir(parents=True, exist_ok=True)
                shutil.copyfile(svg, ROOT / 'site' / 'images' / i / 'drawing.svg')
            if extras:
                choices[i] = {'pick': extras}
                fetch.append(i)
        else:
            choices[i] = {**({'category': r['commons_category']} if r.get('commons_category') else {}), 'add': photos}
            fetch.append(i)
            if r.get('drawing_kept') and svg.exists():  # a small photo leads; our drawing follows it in the gallery
                rel = f'images/{i}/drawing.svg'
                b['images'] = [{'src': rel, 'thumb': rel, **DRAWING}]
                b['photo_first'] = True
                if not args.dry_run:
                    (ROOT / 'site' / 'images' / i).mkdir(parents=True, exist_ok=True)
                    shutil.copyfile(svg, ROOT / 'site' / 'images' / i / 'drawing.svg')
        items.append(b)
        ids.add(i)
        have.add(fold(c['name']))
        if b.get('commons'):
            have_cat.add(same(b['commons'], b['year']))
        added.append((b, r['status']))
    cov = IL / 'covers.txt'  # buildings already on the wall that get our drawing as the cover, photos after it
    covers = {l.split('#')[0].strip() for l in cov.read_text(encoding='utf-8').splitlines()} - {''} if cov.exists() else set()
    for b in items:
        svg = IL / 'svg' / f"{b['id']}.svg"
        if b['id'] in covers and svg.exists() and not any(i['src'].endswith('.svg') for i in b.get('images', [])):
            rel = f"images/{b['id']}/drawing.svg"
            b['images'] = [{'src': rel, 'thumb': rel, **DRAWING}] + b.get('images', [])
            if not args.dry_run:
                shutil.copyfile(svg, ROOT / 'site' / 'images' / b['id'] / 'drawing.svg')
            print('cover drawing:', b['name'])
    print(f"{sum(s == 'drawn' for _, s in added)} drawn, {sum(s == 'photo' for _, s in added)} with photos found, "
          f'{len(left)} left off; {len(fetch)} to fetch')
    if args.dry_run:
        return
    save(head, items)
    CHOICES.write_text(json.dumps(choices, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (IL / 'fetch_ids.txt').write_text(','.join(fetch) + '\n', encoding='utf-8')
    L = ['# Important buildings with no free photo yet', '',
         'Not on the wall yet: no free photo on Wikimedia Commons, and no drawing of ours (we could not establish '
         'the form with confidence, or the drawing was turned down). Made by `tools/add_illustrated.py`.', '',
         '| Building | Architect | Year | Place | Why |', '|---|---|---|---|---|']
    L += [f"| {c['name']} | {c['by']} | {c['year']} | {c['city']}, {c['cc']} | {why} |" for c, r, why in left]
    (IL / 'no_free_photo.md').write_text('\n'.join(L) + '\n', encoding='utf-8')


if __name__ == '__main__':
    sys.exit(main())
