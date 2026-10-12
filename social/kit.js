// Draws the Instagram profile kit: profile picture options (1080 × 1080)
// and story highlight covers (1080 × 1920), into social/out/profile/.
//   node social/kit.js

const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');

const OUT = path.join(__dirname, 'out', 'profile');
const FONTS = `<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&display=block" rel="stylesheet">`;
const BASE = `* { margin:0; box-sizing:border-box; } body { font-family:'Archivo',sans-serif; -webkit-font-smoothing:antialiased; overflow:hidden; }
.c { position:absolute; inset:0; display:flex; align-items:center; justify-content:center; }
.mono { font-weight:850; font-stretch:125%; letter-spacing:-.04em; line-height:.8; text-transform:uppercase; text-align:center; }`;
const INK = '#111110', GROUND = '#EDEDE9', SIGNAL = '#2D3BF0';

// The wall: three equal columns of tiles, scrolling down, one tile in the site's blue.
function wall(fg, accent) {
  const cols = [[260, 380, 200, 330], [330, 180, 420, 250], [200, 340, 260, 380]];
  return `<div style="position:absolute;left:250px;top:0;width:580px;height:1080px;display:flex;gap:20px;overflow:hidden">${
    cols.map((col, i) => `<div style="flex:1;display:flex;flex-direction:column;gap:20px;margin-top:${[-90, -200, -40][i]}px">${
      col.map((h, j) => `<div style="height:${h}px;background:${i === 1 && j === 1 ? accent : fg}"></div>`).join('')}</div>`).join('')}</div>`;
}

const AVATARS = {
  'avatar-a-monogram': `<body style="background:${GROUND};color:${INK}"><div class="c"><div class="mono" style="font-size:360px">D<br>A</div></div></body>`,
  'avatar-b-wall': `<body style="background:${GROUND}">${wall(INK, SIGNAL)}</body>`,
  'avatar-c-monogram-dark': `<body style="background:${INK};color:${GROUND}"><div class="c"><div class="mono" style="font-size:360px">D<br>A</div></div></body>`,
};
const HIGHLIGHTS = ['Start here', 'Ideas', 'Guess', 'Architects'];

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const browser = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {});
  const tab = await browser.newPage();
  const shoot = async (name, html, w, h) => {
    await tab.setViewportSize({ width: w, height: h });
    await tab.setContent(`<!doctype html><html><head><meta charset="utf-8">${FONTS}<style>${BASE}</style></head>${html}</html>`, { waitUntil: 'networkidle' });
    await tab.evaluate(() => document.fonts.ready);
    await tab.screenshot({ path: path.join(OUT, name + '.png') });
  };
  for (const [name, html] of Object.entries(AVATARS)) await shoot(name, html, 1080, 1080);
  for (const word of HIGHLIGHTS) {
    // Highlights show only a circle from the middle, so the word stays inside ~640px.
    const size = 96;  // one size for all, set by the longest word, "Architects"
    await shoot('highlight-' + word.toLowerCase().replace(/\s+/g, '-'),
      `<body style="background:${GROUND};color:${INK}"><div class="c"><div class="mono" style="font-size:${size}px;line-height:.95;font-stretch:100%;letter-spacing:-.02em">${word.replace(' ', '<br>')}</div></div></body>`, 1080, 1920);
  }
  await browser.close();
  console.log('profile kit drawn');
})().catch(e => { console.error(e.message); process.exit(1); });
