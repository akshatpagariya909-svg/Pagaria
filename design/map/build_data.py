"""Build the data and photo sheets for the map prototype (design/map/).

Reads site/data/buildings.js and site/data/world.js and writes, into OUT:
  data.js      window.MAPDATA: one compact row per building, plus the world map
  sprite.webp  every building's first photo as a 128 px square (40 per row), for the map tiles
  m<k>.webp    the same photos as 320 x 240 crops, 160 per sheet, for the opened card

118 buildings (mostly the hand-picked first 100) have no coordinates yet. They are placed
at city level: the mean of other buildings in the same city, or a small table of city
centres below. They carry approx=1 so the prototype can say so. The real site should
fetch exact coordinates (Wikidata P625) through the data-collection chat.

Usage: python3 design/map/build_data.py [out_dir] [drawings_dir] [--no-images]
  drawings_dir holds <id>.png for the ten buildings whose stand-in is an SVG drawing
"""
import json
import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SITE = ROOT / 'site'
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'design' / 'map' / 'out'
OUT.mkdir(parents=True, exist_ok=True)

TILE = 128          # map tile sprite, px square
COLS = 40
MW, MH = 320, 240   # card photo
PER_SHEET = 160     # 16 x 10

# City centres for places with no building that has coordinates. City level only.
CITY = {
    'Poissy, FR': (48.929, 2.046), 'Ronchamp, FR': (47.703, 6.637), 'Éveux, FR': (45.820, 4.620),
    'Brno, CZ': (49.195, 16.608), 'Plano, US': (41.663, -88.537), 'Mill Run, US': (39.906, -79.468),
    'Racine, US': (42.726, -87.783), 'Dessau, DE': (51.835, 12.247), 'Paimio, FI': (60.457, 22.687),
    'Noormarkku, FI': (61.592, 21.868), 'New Canaan, US': (41.147, -73.495), 'Hiroshima, JP': (34.385, 132.455),
    'Puducherry, IN': (11.934, 79.830), 'La Jolla, US': (32.843, -117.274), 'Exeter, US': (42.981, -70.948),
    'Montréal, CA': (45.509, -73.554), 'London, UK': (51.507, -0.128), 'Indore, IN': (22.720, 75.858),
    'Dambulla, LK': (7.868, 80.651), 'Luxor, EG': (25.687, 32.640), 'Gando, BF': (11.80, -0.65),
    'Matosinhos, PT': (41.182, -8.689), 'Mallorca, ES': (39.570, 2.650), 'Verona, IT': (45.438, 10.993),
    "San Vito d'Altivole, IT": (45.73, 11.92), 'Vals, CH': (46.617, 9.180), 'Mechernich, DE': (50.593, 6.652),
    'Ningbo, CN': (29.868, 121.544), 'Iquique, CL': (-20.214, -70.152), 'Ibaraki, JP': (34.816, 135.568),
    'Sendai, JP': (38.268, 140.869), 'Atsugi, JP': (35.443, 139.362), 'Teshima, JP': (34.49, 134.09),
    'Hong Kong': (22.302, 114.177), 'Seville, ES': (37.389, -5.984), 'Cape Town, ZA': (-33.925, 18.424),
    'Granada, ES': (37.177, -3.599), 'Abhaneri, IN': (27.007, 76.607), 'Vicenza, IT': (45.546, 11.548),
    'Gaibandha, BD': (25.33, 89.54), 'Sri Jayawardenepura Kotte, LK': (6.887, 79.918), 'Koudougou, BF': (12.252, -2.362),
    'Atizapán de Zaragoza, MX': (19.558, -99.260), 'Padalarang, ID': (-6.84, 107.48),
}


def load_js(path, prefix):
    text = path.read_text(encoding='utf-8')
    i = text.index(prefix) + len(prefix)
    body = text[i:].strip()
    if body.endswith(';'):
        body = body[:-1]
    return json.loads(body)


B = load_js(SITE / 'data' / 'buildings.js', 'window.BUILDINGS =')
W = load_js(SITE / 'data' / 'world.js', 'window.WORLD =')

# city-level fallbacks from siblings with coordinates
sib = {}
for b in B:
    if b.get('coords'):
        sib.setdefault(b['place'], []).append(b['coords'])
rows = []
missing = []
for b in B:
    c = b.get('coords')
    approx = 0
    if not c:
        approx = 1
        if b['place'] in sib:
            pts = sib[b['place']]
            c = [sum(p[0] for p in pts) / len(pts), sum(p[1] for p in pts) / len(pts)]
        elif b['place'] in CITY:
            c = list(CITY[b['place']])
        else:
            missing.append(b['place'])
            continue
    im = (b.get('images') or [{}])[0]
    code = b['place'].split(', ')[-1]
    code = {'UK': 'GB', 'Hong Kong': 'HK'}.get(code, code)
    rows.append([
        b['id'], b['name'], b['by'], b['place'], b.get('year', ''), round(c[0], 4), round(c[1], 4), code,
        b.get('type', ''), b.get('movement', ''), b.get('study', ''),
        re.sub(r'\s+', ' ', im.get('credit', '') or '').strip()[:90], im.get('license', ''), im.get('source', ''),
        approx, len(b.get('images') or []), b['n'],
    ])
if missing:
    print('still no place for', sorted(set(missing)))
print(len(rows), 'buildings on the map,', sum(r[14] for r in rows), 'at city level')

# ---- data.js
fields = 'id,name,by,place,year,lat,lon,cc,type,movement,study,credit,license,source,approx,nimg,n'.split(',')
world = {k: W[k] for k in ('w', 'h', 'proj', 'paths', 'centre', 'names', 'box')}
data = {'fields': fields, 'b': rows, 'world': world, 'sprite': {'tile': TILE, 'cols': COLS}, 'card': {'w': MW, 'h': MH, 'per': PER_SHEET, 'sheets': (len(rows) + PER_SHEET - 1) // PER_SHEET}}
(OUT / 'data.js').write_text('window.MAPDATA = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n', encoding='utf-8')
print('data.js', (OUT / 'data.js').stat().st_size // 1024, 'KB')


def crop(img, w, h):
    s = max(w / img.width, h / img.height)
    im = img.resize((max(w, round(img.width * s)), max(h, round(img.height * s))), Image.LANCZOS)
    x = (im.width - w) // 2
    y = (im.height - h) // 2
    return im.crop((x, y, x + w, y + h))


DRAWINGS = Path(sys.argv[2]) if len(sys.argv) > 2 and not sys.argv[2].startswith('--') else None  # PNGs of the SVG drawings


def thumb_of(b):
    p = SITE / (b.get('images') or [{}])[0].get('thumb', '')
    if p.suffix == '.svg' and DRAWINGS:
        p = DRAWINGS / (b['id'] + '.png')  # the stand-in drawing, rendered in a browser (tools can't rasterise SVG here)
        try:
            im = Image.open(p).convert('RGB')
            w, h = im.width * 0.6, im.height * 0.6  # keep the middle of the drawing so its lines stay visible when small
            return im.crop((round((im.width - w) / 2), round((im.height - h) / 2), round((im.width + w) / 2), round((im.height + h) / 2)))
        except Exception:
            pass
    try:
        return Image.open(p).convert('RGB')
    except Exception:
        return Image.new('RGB', (TILE, TILE), (220, 219, 213))


byid = {b['id']: b for b in B}
if '--no-images' not in sys.argv:
    n = len(rows)
    sheet = Image.new('RGB', (COLS * TILE, ((n + COLS - 1) // COLS) * TILE), (247, 247, 245))
    cards = []
    for i, r in enumerate(rows):
        img = thumb_of(byid[r[0]])
        sheet.paste(crop(img, TILE, TILE), ((i % COLS) * TILE, (i // COLS) * TILE))
        k, j = divmod(i, PER_SHEET)
        if j == 0:
            cards.append(Image.new('RGB', (16 * MW, 10 * MH), (247, 247, 245)))
        cards[k].paste(crop(img, MW, MH), ((j % 16) * MW, (j // 16) * MH))
    sheet.save(OUT / 'sprite.webp', 'WEBP', quality=78, method=6)
    print('sprite.webp', sheet.size, (OUT / 'sprite.webp').stat().st_size // 1024, 'KB')
    for k, c in enumerate(cards):
        c.save(OUT / f'm{k}.webp', 'WEBP', quality=72, method=4)
    print(len(cards), 'card sheets,', sum((OUT / f'm{k}.webp').stat().st_size for k in range(len(cards))) // 1024, 'KB')
