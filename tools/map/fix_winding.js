// Puts every ring of site/data/map/land50.json the right way round for d3's sphere: land rings must enclose less than
// half the globe and lakes the opposite, or d3 fills the rest of the world instead (the whole screen turns to land).
// Usage: node tools/map/fix_winding.js <path to d3.min.js>
const fs = require('fs'), vm = require('vm');
const ctx = {}; vm.createContext(ctx); vm.runInContext(fs.readFileSync(process.argv[2], 'utf8'), ctx); const d3 = ctx.d3;
const file = __dirname + '/../../site/data/map/land50.json', g = JSON.parse(fs.readFileSync(file));
const big = ring => d3.geoArea({ type: 'Polygon', coordinates: [ring] }) > 2 * Math.PI;
let fixed = 0;
for (const cell of g.cells) for (const poly of cell.p) poly.forEach((ring, i) => {
  if (i === 0 ? big(ring) : !big(ring)) { ring.reverse(); fixed++; } // land small, lakes (holes) inside-out
});
fs.writeFileSync(file, JSON.stringify(g));
console.log('rings turned round:', fixed);
