// Kept for remaking site/data/map (see tools/make_map_data.py). Run from a folder holding the unpacked npm packages
// world-atlas@2.0.2, topojson-client@3.1.0 and d3@7.9.0 under ./x/<name>/package, as the paths below expect.
const vm = require('vm'); const ctx = {}; vm.createContext(ctx); vm.runInContext(require('fs').readFileSync('./x/d3/package/dist/d3.min.js', 'utf8'), ctx); global.d3 = ctx.d3;
const topo = require('./x/topojson-client-3.1.0/package/dist/topojson-client.js');
const w = require('./x/world-atlas-2.0.2/package/countries-110m.json');
const fc = topo.feature(w, w.objects.countries);
const out = [];
const short = { 'United States of America': 'United States', 'Dem. Rep. Congo': 'DR Congo', 'Central African Rep.': 'Central African Rep.', 'Bosnia and Herz.': 'Bosnia', 'Dominican Rep.': 'Dominican Rep.', 'S. Sudan': 'South Sudan', 'Eq. Guinea': 'Eq. Guinea', 'W. Sahara': 'W. Sahara', 'Solomon Is.': 'Solomon Is.', 'Falkland Is.': 'Falklands', 'Fr. S. Antarctic Lands': '', 'N. Cyprus': '', 'Somaliland': '', 'Antarctica': '' };
for (const f of fc.features) {
  let name = f.properties.name; if (name in short) name = short[name]; if (!name) continue;
  const polys = f.geometry.type === 'Polygon' ? [f.geometry.coordinates] : f.geometry.coordinates;
  let best = null, ba = 0; for (const p of polys) { const a = d3.geoArea({ type: 'Polygon', coordinates: p }); if (a > ba && a < 6) { ba = a; best = p; } }
  if (!best) continue;
  let c = d3.geoCentroid({ type: 'Polygon', coordinates: best });
  const fix = { 'United States': [-98.5, 39.5], 'Canada': [-105, 58], 'Russia': [95, 62], 'Norway': [9, 61.5], 'Chile': [-71, -32], 'Indonesia': [114, -1], 'France': [2.4, 46.6], 'Vietnam': [106, 16], 'Malaysia': [102, 4], 'Croatia': [16, 45.3], 'Italy': [12.5, 42.8], 'Japan': [138.5, 36.5], 'Brazil': [-52, -10], 'Mexico': [-102, 23.5], 'Argentina': [-65, -35], 'India': [79, 22], 'China': [103, 35], 'Greenland': [-41, 73], 'Israel': [34.9, 31.3], 'Philippines': [122.5, 12] };
  if (fix[name]) c = fix[name];
  out.push([name, +c[0].toFixed(2), +c[1].toFixed(2), +Math.sqrt(ba).toFixed(4)]);
}
out.sort((a, b) => b[3] - a[3]);
require('fs').writeFileSync('../maptest/labels.json', JSON.stringify(out)); console.log(out.length, out.slice(0, 3));
