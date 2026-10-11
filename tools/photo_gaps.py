"""Lists the buildings we can't yet show well, so we can target them later.

Reads site/data/buildings.js and writes tools/photo_gaps.md. No network needed:
    python tools/photo_gaps.py
"""
import json
from pathlib import Path
from urllib.parse import quote

ROOT = Path(__file__).resolve().parent.parent


def load():
    s = (ROOT / 'site' / 'data' / 'buildings.js').read_text(encoding='utf-8')
    return json.loads(s[s.index('=', s.index('window.BUILDINGS')) + 1:].strip().rstrip(';'))


def row(b):
    kinds = ', '.join(i['kind'] for i in b['images']) or 'none'
    cat = b.get('commons')
    commons = f"[{cat}](https://commons.wikimedia.org/wiki/{quote(cat.replace(' ', '_'), safe=':/')})" if cat else 'none found'
    return f"| {b['n']} | {b['name']} | {b['by']} | {b['place']} | {kinds} | {commons} |"


def table(title, note, rows):
    head = ['', f'## {title} ({len(rows)})', '', note, '',
            '| # | Building | Architect | Place | Photos now | Commons |', '|---|---|---|---|---|---|']
    return head + [row(b) for b in rows]


def main():
    B = load()
    none = [b for b in B if not b['images']]
    no_ext = [b for b in B if b['images'] and not any(i['kind'] == 'Exterior' for i in b['images'])]
    thin = [b for b in B if 0 < len(b['images']) < 4 and b not in no_ext]
    out = ['# Photo gaps', '', 'Buildings we can\'t show well with free photos yet. Made by `tools/photo_gaps.py`; rerun it after fetching photos.']
    out += table('No free photo at all', 'Commons has no usable free photo. Target later with licensed photos (owner decides how).', none)
    out += table('No exterior photo', 'They have photos, but none of the outside. Check Commons by hand first: some may be mislabelled.', no_ext)
    out += table('Fewer than 4 photos', 'They show, but the gallery is thin.', thin)
    (ROOT / 'tools' / 'photo_gaps.md').write_text('\n'.join(out) + '\n', encoding='utf-8')
    print(f'{len(none)} with no photo, {len(no_ext)} with no exterior, {len(thin)} with fewer than 4 photos')


if __name__ == '__main__':
    main()
