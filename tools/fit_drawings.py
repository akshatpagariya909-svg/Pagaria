#!/usr/bin/env python3
"""Fit our line drawings into the part of a wall tile the caption doesn't cover.

  python tools/fit_drawings.py            every site/images/<id>/drawing.svg
  python tools/fit_drawings.py id1 id2    just these

A wall tile puts a dark caption fade over the bottom of the image, so a drawing standing on a
ground line near the bottom lost its base under it. This scales each drawing (never up) and moves
it so the whole thing sits inside BOX, centred, standing on BOX's bottom edge. The drawing itself
is untouched: one transform on its <g>. Running it again refits from scratch.

Measures each drawing by rendering it with the headless Chromium that comes with this sandbox.
"""
import re, subprocess, sys, tempfile
from pathlib import Path
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parent.parent
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
BOX = (24, 14, 376, 168)  # x0, y0, x1, y1 in the 400 x 260 drawing: clear of the caption fade


def bbox(svg_text):
    with tempfile.TemporaryDirectory() as d:
        src, png = Path(d) / 'd.svg', Path(d) / 'd.png'
        src.write_text(svg_text, encoding='utf-8')
        # a tall window: headless Chrome cuts off the bottom of a 400 x 260 one
        subprocess.run([CHROME, '--headless', '--no-sandbox', '--disable-gpu', '--hide-scrollbars',
                        '--window-size=400,400', f'--screenshot={png}', src.as_uri()], capture_output=True)
        im = Image.open(png).convert('L').crop((0, 0, 400, 260))
        return ImageOps.invert(im).point(lambda v: 255 if v > 40 else 0).getbbox()


def fit(path):
    s = path.read_text(encoding='utf-8')
    s = re.sub(r'<g transform="[^"]*" fill="none"', '<g fill="none"', s)  # undo an earlier fit
    box = bbox(s)
    if not box:
        return None
    x0, y0, x1, y1 = box
    sc = min((BOX[2] - BOX[0]) / (x1 - x0), (BOX[3] - BOX[1]) / (y1 - y0), 1.0)
    tx, ty = (BOX[0] + BOX[2]) / 2 - sc * (x0 + x1) / 2, BOX[3] - sc * y1
    path.write_text(s.replace('<g fill="none"', f'<g transform="translate({tx:.1f},{ty:.1f}) scale({sc:.3f})" fill="none"', 1),
                    encoding='utf-8')
    return sc


def main():
    ids = sys.argv[1:]
    files = [ROOT / 'site' / 'images' / i / 'drawing.svg' for i in ids] if ids else sorted((ROOT / 'site' / 'images').glob('*/drawing.svg'))
    for f in files:
        sc = fit(f)
        print(f'{f.parent.name}: ' + ('nothing drawn' if sc is None else f'scale {sc:.2f}'))


if __name__ == '__main__':
    sys.exit(main())
