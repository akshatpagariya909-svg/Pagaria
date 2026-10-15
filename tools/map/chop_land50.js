// Kept for remaking site/data/map (see tools/make_map_data.py). Run from a folder holding the unpacked npm packages
// world-atlas@2.0.2, topojson-client@3.1.0 and d3@7.9.0 under ./x/<name>/package, as the paths below expect.
// Cut the detailed land into 10° squares so a zoomed-in frame projects only the squares on screen.
const fs = require('fs'); const g = JSON.parse(fs.readFileSync('geo50.json'));
function clip(ring, edge, inside, cross) { const out = []; for (let i = 0; i < ring.length; i++) { const a = ring[i], b = ring[(i + 1) % ring.length];
  const ia = inside(a), ib = inside(b); if (ia) out.push(a); if (ia !== ib) out.push(cross(a, b)); } return out; }
function clipRect(ring, x0, y0, x1, y1) {
  let r = ring.slice(0, -1);
  const X = (a, b, x) => [x, +(a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0])).toFixed(2)], Y = (a, b, y) => [+(a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1])).toFixed(2), y];
  r = clip(r, 0, p => p[0] >= x0, (a, b) => X(a, b, x0)); if (!r.length) return null;
  r = clip(r, 0, p => p[0] <= x1, (a, b) => X(a, b, x1)); if (!r.length) return null;
  r = clip(r, 0, p => p[1] >= y0, (a, b) => Y(a, b, y0)); if (!r.length) return null;
  r = clip(r, 0, p => p[1] <= y1, (a, b) => Y(a, b, y1)); if (r.length < 3) return null;
  r.push(r[0]); return r;
}
const area = r => { let a = 0; for (let i = 0; i < r.length - 1; i++) a += r[i][0] * r[i + 1][1] - r[i + 1][0] * r[i][1]; return a; };
const SIGN = Math.sign(area(g.land.coordinates.reduce((m, p) => p[0].length > m[0].length ? p : m)[0]));
const S = 10, cells = [];
for (let x = -180; x < 180; x += S) for (let y = -90; y < 90; y += S) {
  const polys = [];
  for (const poly of g.land.coordinates) {
    const ring = poly[0];
    let bx0 = 999, bx1 = -999, by0 = 999, by1 = -999; for (const p of ring) { bx0 = Math.min(bx0, p[0]); bx1 = Math.max(bx1, p[0]); by0 = Math.min(by0, p[1]); by1 = Math.max(by1, p[1]); }
    if (bx1 < x || bx0 > x + S || by1 < y || by0 > y + S) continue;
    const outer = clipRect(ring, x, y, x + S, y + S); if (!outer) continue;
    const holes = poly.slice(1).map(h => clipRect(h, x, y, x + S, y + S)).filter(Boolean);  // lakes keep their own winding inside the same polygon
    polys.push([outer, ...holes]);
  }
  if (polys.length) cells.push({ b: [x, y], p: polys });
}
const out = { cells, borders: g.borders };
fs.writeFileSync('geo50.json', JSON.stringify(out)); console.log(cells.length, fs.statSync('geo50.json').size);
