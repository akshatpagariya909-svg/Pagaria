"""Make site/data/world.js: a small grey world map for the opened building.

Each country is one SVG path keyed by its two-letter code, so the page can turn
the building's country sunset red. Run it again only if the map itself changes.

Source: world-atlas 2.0.2, drawn from Natural Earth, which is public domain. Shapes come
from the light 1:110m file; countries too small for it (Singapore, Bahrain…) come from
the 1:50m file, and every country also gets a centre point so even Vatican City can be
marked with a ring. Get it with:
    curl -sSL https://registry.npmjs.org/world-atlas/-/world-atlas-2.0.2.tgz | tar xz
Country codes and names come from pycountry (pip install pycountry).

Usage:
    python tools/make_world.py package/countries-110m.json package/countries-50m.json
"""
import json
import math
import sys
from pathlib import Path

import pycountry

OUT = Path(__file__).resolve().parent.parent / 'site' / 'data' / 'world.js'
W = 1000          # map width in SVG units
LAT_TOP, LAT_BOTTOM = 84, -57   # crop Antarctica and the empty far north
MIN_STEP = 0.7    # drop points closer than this to the previous one (SVG units)

# Short, everyday names where the ISO name is long or formal.
NAMES = {
    'US': 'United States', 'GB': 'United Kingdom', 'RU': 'Russia', 'KR': 'South Korea', 'KP': 'North Korea',
    'IR': 'Iran', 'TW': 'Taiwan', 'VN': 'Vietnam', 'SY': 'Syria', 'LA': 'Laos', 'BO': 'Bolivia',
    'VE': 'Venezuela', 'TZ': 'Tanzania', 'MD': 'Moldova', 'PS': 'Palestine', 'VA': 'Vatican City',
    'CZ': 'Czechia', 'MK': 'North Macedonia', 'CD': 'DR Congo', 'CG': 'Congo', 'BN': 'Brunei',
    'XK': 'Kosovo', 'HK': 'Hong Kong', 'MO': 'Macao', 'CI': "Côte d'Ivoire", 'TR': 'Türkiye',
    'FM': 'Micronesia', 'SZ': 'Eswatini', 'CV': 'Cabo Verde',
}
# Shapes in the source without an ISO number.
BY_NAME = {'Kosovo': 'XK', 'N. Cyprus': 'CY', 'Somaliland': 'SO'}


def natural_earth(lon, lat):
    """Natural Earth I projection, in radians-based units."""
    p, l = math.radians(lat), math.radians(lon)
    p2 = p * p
    p4 = p2 * p2
    x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)))
    y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)))
    return x, y


X0 = natural_earth(-180, 0)[0]
X1 = natural_earth(180, 0)[0]
Y0 = natural_earth(0, LAT_TOP)[1]
Y1 = natural_earth(0, LAT_BOTTOM)[1]
S = W / (X1 - X0)
H = round((Y0 - Y1) * S)


def project(lon, lat):
    x, y = natural_earth(lon, max(LAT_BOTTOM, min(LAT_TOP, lat)))
    return (x - X0) * S, (Y0 - y) * S


def load(src):
    topo = json.loads(Path(src).read_text())
    sx, sy = topo['transform']['scale']
    tx, ty = topo['transform']['translate']
    arcs = []
    for arc in topo['arcs']:
        x = y = 0
        pts = []
        for dx, dy in arc:
            x += dx
            y += dy
            pts.append((x * sx + tx, y * sy + ty))
        arcs.append(pts)

    def ring(indexes):
        pts = []
        for i in indexes:
            a = arcs[i] if i >= 0 else arcs[~i][::-1]
            pts.extend(a if not pts else a[1:])
        return pts

    for g in topo['objects']['countries']['geometries']:
        num, label = g.get('id'), g['properties']['name']
        if num == '010':  # Antarctica
            continue
        code = BY_NAME.get(label)
        if not code and num:
            c = pycountry.countries.get(numeric=num)
            code = c.alpha_2 if c else None
        if not code:
            continue
        yield code, label, g, ring


def unwrap(pts):
    """Keep a ring on one side of the 180° line (Russia, Fiji): otherwise its edge is drawn
    straight back across the whole map. Points pushed past ±180 are held on the map's edge."""
    out, prev = [], None
    for lon, lat in pts:
        if prev is not None:
            while lon - prev > 180:
                lon -= 360
            while prev - lon > 180:
                lon += 360
        prev = lon
        out.append((lon, lat))
    mid = sum(p[0] for p in out) / len(out)  # a ring that starts just across the line belongs on the other side
    shift = -360 if mid > 180 else 360 if mid < -180 else 0
    return [(max(-180, min(180, lon + shift)), lat) for lon, lat in out]


def shapes(src):
    """Projected, simplified paths, bounding boxes and raw centres per country code."""
    paths, boxes, centres, labels = {}, {}, {}, {}
    for code, label, g, ring in load(src):
        labels.setdefault(code, label)
        polys = g['arcs'] if g['type'] == 'MultiPolygon' else [g['arcs']]
        d = []
        xs, ys = [], []
        for poly in polys:
            for r in poly:
                pts = unwrap(ring(r))
                if code == 'FR' and sum(p[0] for p in pts) / len(pts) < -30:
                    continue  # French Guiana: keep France's shape to Europe, so it isn't painted with it
                out = []
                for lon, lat in pts:
                    px, py = project(lon, lat)
                    if out and abs(px - out[-1][0]) < MIN_STEP and abs(py - out[-1][1]) < MIN_STEP:
                        continue
                    out.append((px, py))
                if len(out) < 3:
                    continue
                xs += [p[0] for p in out]
                ys += [p[1] for p in out]
                d.append('M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in out) + 'Z')
        # centre of the largest outline, from the unsimplified points
        big = max((ring(r) for poly in polys for r in poly), key=len)
        cx, cy = project(sum(p[0] for p in big) / len(big), sum(p[1] for p in big) / len(big))
        centres.setdefault(code, (round(cx, 1), round(cy, 1)))
        if not d:
            continue
        paths[code] = paths.get(code, '') + ''.join(d)
        b = boxes.get(code)
        nb = [min(xs), min(ys), max(xs), max(ys)]
        boxes[code] = nb if not b else [min(b[0], nb[0]), min(b[1], nb[1]), max(b[2], nb[2]), max(b[3], nb[3])]
    return paths, boxes, centres, labels


def main(light, detailed):
    paths, boxes, centres, labels = shapes(light)
    p50, b50, c50, l50 = shapes(detailed)
    for code in p50:
        if code not in paths:  # too small for the light file
            paths[code], boxes[code] = p50[code], b50[code]
    for code, c in c50.items():
        centres.setdefault(code, c)
    for code, l in l50.items():
        labels.setdefault(code, l)
    names = {}
    for code in centres:
        c = pycountry.countries.get(alpha_2=code)
        names[code] = NAMES.get(code) or ((getattr(c, 'common_name', None) or c.name) if c else labels[code])

    data = {
        'w': W, 'h': H,
        'proj': [round(X0, 6), round(S, 4), round(Y0, 6), LAT_TOP, LAT_BOTTOM],
        'box': {k: [round(v, 1) for v in b] for k, b in boxes.items()},
        'centre': centres,
        'names': names,
        'paths': paths,
    }
    OUT.write_text(
        '// World map for the opened building: one path per country, keyed by its two-letter code.\n'
        '// Generated by tools/make_world.py from Natural Earth (public domain) via world-atlas.\n'
        f'// Projection: Natural Earth I, {W} x {H}; proj = [x0, scale, y0, top lat, bottom lat] for placing a point (see app.js).\n'
        'window.WORLD = ' + json.dumps(data, ensure_ascii=False, separators=(',', ':')) + ';\n')
    print(f'{len(paths)} countries, {OUT.stat().st_size // 1024} KB -> {OUT}')


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
