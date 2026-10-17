// Compares tools/names_py.py with site/data/names.js on every building. Run from the repository root:
//   python3 tools/names_py.py > /tmp/names_py.json
//   node tools/check_names_parity.js /tmp/names_py.json
const fs = require('fs');
global.window = {};
const load = f => new Function('window', fs.readFileSync(f, 'utf8'))(global.window);
load('site/data/wall.js'); load('site/data/names.js');
const py = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const B = window.BUILDINGS; let bad = 0;
B.forEach((b, i) => {
  const a = JSON.stringify(window.NAMES.list(b.by)), c = JSON.stringify(py[i]);
  if (a !== c && bad++ < 10) console.log('DIFF', b.id, b.by, a, c);
});
console.log(bad ? bad + ' differences' : 'same on all ' + B.length + ' buildings');
process.exit(bad ? 1 : 0);
