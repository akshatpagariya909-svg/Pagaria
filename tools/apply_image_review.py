#!/usr/bin/env python3
"""Apply the hand review in tools/image_review.json to the wall.

  python tools/apply_image_review.py

image_review.json has two lists, made by looking at every plan, section, elevation, sketch and
model the photo upgrade picked:
  remove  {id, file}: not a drawing or model of this building (a ship, a portrait, a sign, another
          building). It's taken out of the gallery, its files are deleted, and it goes on the
          building's "skip" list in image_choices.json so a later fetch doesn't bring it back.
  kinds   {file: kind}: a photo the fetcher mislabelled as a drawing. Its label is corrected here,
          and fetch_images.py reads the same list, so the next fetch labels it right too.

It also puts each gallery back in its usual order, so positions read off a contact sheet change: turn them
into file names (the `file` of each picture) before running it.
"""
import json, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save, DRAWINGS, CHOICES  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REVIEW = ROOT / 'tools' / 'image_review.json'


def main():
    review = json.loads(REVIEW.read_text(encoding='utf-8'))
    gone = {(r['id'], r['file']) for r in review['remove']}
    kinds = review['kinds']
    choices = json.loads(CHOICES.read_text(encoding='utf-8'))
    head, items = load()
    removed = relabelled = 0
    for b in items:
        keep = []
        for im in b.get('images', []):
            if (b['id'], im.get('file')) in gone:
                for p in (im.get('src'), im.get('thumb')):  # files hosted here; hotlinked photos have a URL src
                    f = ROOT / 'site' / p if p and not p.startswith('http') else None
                    if f and f.exists() and not f.name.endswith('.svg'):
                        f.unlink()
                skip = choices.setdefault(b['id'], {}).setdefault('skip', [])
                if im['file'] not in skip:
                    skip.append(im['file'])
                removed += 1
                continue
            k = kinds.get(im.get('file'))
            if k and im['kind'] != k:
                old = im['kind']
                im['kind'] = k
                im['caption'] = k + im['caption'][len(old):] if im.get('caption', '').startswith(old) else k
                relabelled += 1
            keep.append(im)
        if 'images' in b:
            order = {'Exterior': 0, 'Interior': 1, 'Detail': 2, 'Context': 3, **{k: 4 + i for i, k in enumerate(DRAWINGS)}}
            b['images'] = keep[:1] + sorted(keep[1:], key=lambda i: order.get(i['kind'], 9))  # relabelled photos move before the drawings
            b['has'] = [k for k in DRAWINGS if any(i['kind'] == k for i in keep)]
    save(head, items)
    CHOICES.write_text(json.dumps(choices, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(f'{removed} removed, {relabelled} relabelled')


if __name__ == '__main__':
    sys.exit(main())
