"""Which buildings get photo dots on the wall ("Worth the swipe").

  python tools/worth_swipe.py sheets [out_dir]   contact sheets of every candidate, for a check by eye
  python tools/worth_swipe.py stats              how many pass the rule, and how many are dropped

The rule (owner's choice, 15 Oct 2026): at least 5 photos, at least one inside, and at least one
close-up or drawing (plan, section, elevation, model, sketch). Our own line drawings don't count.
tools/worth_swipe.txt holds the hand decisions: "- id  reason" drops a building after the check
by eye, "+ id  reason" adds one the rule misses. Works offline from the wall thumbnails.
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
LIST = ROOT / 'tools' / 'worth_swipe.txt'
DRAWN = {'Drawing', 'Plan', 'Section', 'Elevation', 'Model', 'Sketch'}
MIN_PHOTOS = 5


def buildings():
    text = (SITE / 'data' / 'buildings.js').read_text(encoding='utf-8')
    return json.loads(text[text.index('['):text.rindex(']') + 1])


def photos(b):
    return [i for i in b.get('images') or [] if not str(i.get('src', '')).endswith('drawing.svg')]


def passes(b):
    im = photos(b)
    kinds = {i.get('kind') for i in im}
    return len(im) >= MIN_PHOTOS and 'Interior' in kinds and bool(kinds & (DRAWN | {'Detail'}))


def decisions():
    add, drop = {}, {}
    for line in LIST.read_text(encoding='utf-8').splitlines() if LIST.exists() else []:
        m = re.match(r'\s*([+-])\s*(\S+)\s*(.*)', line)
        if m and not line.lstrip().startswith('#'):
            (add if m[1] == '+' else drop)[m[2]] = m[3]
    return add, drop


def chosen(bs=None):
    add, drop = decisions()
    return [b['id'] for b in bs or buildings() if (passes(b) or b['id'] in add) and b['id'] not in drop]


def sheets(out):
    out.mkdir(parents=True, exist_ok=True)
    cands = [b for b in buildings() if passes(b)]
    font = ImageFont.truetype(str(ROOT / 'tools' / 'fonts' / 'BarlowCondensed-SemiBold.ttf'), 22)
    small = ImageFont.truetype(str(ROOT / 'tools' / 'fonts' / 'BarlowCondensed-SemiBold.ttf'), 15)
    TH, rows, cols, W = 170, 8, 8, 230
    for s in range(0, len(cands), rows):
        part = cands[s:s + rows]
        sheet = Image.new('RGB', (cols * W + 10, len(part) * (TH + 40) + 10), 'white')
        d = ImageDraw.Draw(sheet)
        for r, b in enumerate(part):
            y = 10 + r * (TH + 40)
            d.text((10, y), f"{s + r}  {b['id']}  ({b.get('by', '')})"[:110], fill='black', font=font)
            for c, i in enumerate(photos(b)[:cols]):
                try:
                    im = Image.open(SITE / (i.get('thumb') or i['src'])).convert('RGB')
                    im.thumbnail((W - 10, TH - 20))
                    sheet.paste(im, (10 + c * W, y + 28))
                except Exception as e:
                    d.text((10 + c * W, y + 60), f'failed: {e}'[:30], fill='red', font=small)
                d.text((10 + c * W, y + TH + 8), f"{c} {i.get('kind', '')}", fill='#555', font=small)
        sheet.save(out / f'sheet_{s // rows:03d}.jpg', quality=80)
    print(f'{len(cands)} candidates on {(len(cands) + rows - 1) // rows} sheets in {out}')


def stats():
    bs = buildings()
    add, drop = decisions()
    n = sum(passes(b) for b in bs)
    print(f'{n} pass the rule ({100 * n / len(bs):.1f}%), {len(drop)} dropped by eye, {len(add)} added by hand, {len(chosen(bs))} get dots')


if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'stats'
    if cmd == 'sheets':
        sheets(Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / 'tools' / 'worth_swipe_sheets')
    else:
        stats()
