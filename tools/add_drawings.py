#!/usr/bin/env python3
"""Show our own line drawing for buildings that have no free photo.

  python tools/add_drawings.py

For every building whose `images` list is empty and that has `site/images/<id>/drawing.svg`,
sets the drawing as its only image, labelled "Drawing, not a photo" (the wall tile shows the
same label). Drawings follow the locked brief on the design canvas: a simple ink elevation,
400 x 260, pen #111110 only. When a free photo turns up later, fetch the building again with
`fetch_images.py --only <id> --force`; the photo replaces the drawing and the SVG stays as an archive.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save  # noqa: E402

SITE = Path(__file__).resolve().parent.parent / 'site'


def main():
    head, items = load()
    added = []
    for b in items:
        svg = SITE / 'images' / b['id'] / 'drawing.svg'
        if b.get('images') or not svg.exists():
            continue
        rel = f"images/{b['id']}/drawing.svg"
        b['images'] = [{'src': rel, 'thumb': rel, 'w': 400, 'h': 260, 'kind': 'Drawing', 'caption': 'Drawing, not a photo',
                        'credit': 'Drawing: Find Great Architecture', 'license': 'CC BY 4.0', 'source': None}]
        added.append(b['name'])
    save(head, items)
    print(f'{len(added)} drawings added: ' + ', '.join(added))


if __name__ == '__main__':
    sys.exit(main())
