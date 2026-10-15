"""Data for the globe map (site/map.js), still behind the hidden ?map switch.

  python tools/make_map_data.py

Writes site/data/map/order.json: building ids, best known first (the hand-picked first hundred,
then Wikipedia pageviews from tools/pageviews.json), so the map shows their photos first.

The shapes in site/data/map are made once, from Natural Earth (public domain) via the world-atlas
2.0.2 package: land110.json and land50.json (land and borders; land50 is cut into 10° squares
by tools/map/chop_land50.js so a zoomed-in frame draws only what is on screen) and labels.json
(country names and where to place them, tools/map/make_labels.js). They need Node and the npm
packages world-atlas, topojson-client and d3; they rarely need remaking.
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main():
    text = (ROOT / 'site' / 'data' / 'buildings.js').read_text(encoding='utf-8')
    bs = json.loads(text[text.index('['):text.rindex(']') + 1])
    views = json.loads((ROOT / 'tools' / 'pageviews.json').read_text())
    bs.sort(key=lambda b: (b.get('n', 9999) > 100, -(views.get(b['id']) or 0)))
    (ROOT / 'site' / 'data' / 'map' / 'order.json').write_text(json.dumps([b['id'] for b in bs], separators=(',', ':')))
    print(len(bs), 'buildings ranked')


if __name__ == '__main__':
    main()
