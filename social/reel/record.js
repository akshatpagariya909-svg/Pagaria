// Records phone-sized clips of the local site as 1080x1920 30fps MP4s.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = process.env.OUT || path.join(__dirname, 'clips');
const URL = 'http://localhost:8765/';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const TAP_CSS = `.__tap{position:fixed;z-index:99999;width:56px;height:56px;margin:-28px 0 0 -28px;border-radius:50%;
  background:rgba(17,17,16,.22);border:2px solid rgba(255,255,255,.9);pointer-events:none;animation:__t .5s ease-out forwards}
  @keyframes __t{0%{transform:scale(.4);opacity:0}30%{transform:scale(1);opacity:1}100%{transform:scale(1.25);opacity:0}}`;

async function tap(p, sel, label) {
  const el = p.locator(sel).first();
  await el.scrollIntoViewIfNeeded();
  const b = await el.boundingBox();
  const x = b.x + b.width / 2, y = b.y + b.height / 2;
  await p.evaluate(([x, y]) => { const d = document.createElement('div'); d.className = '__tap'; d.style.left = x + 'px'; d.style.top = y + 'px';
    document.body.appendChild(d); setTimeout(() => d.remove(), 600); }, [x, y]);
  await sleep(180);
  if (label && p.mark) p.mark(label);
  await el.click();
}
// Eased scroll of the window or of an element, in page, so it is smooth.
async function glide(p, to, ms, sel) {
  await p.evaluate(([to, ms, sel]) => new Promise(res => {
    const el = sel ? document.querySelector(sel) : document.scrollingElement;
    const from = el.scrollTop, t0 = performance.now();
    const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    (function step(now) { const t = Math.min(1, (now - t0) / ms); el.scrollTop = from + (to - from) * ease(t); t < 1 ? requestAnimationFrame(step) : res(); })(t0);
  }), [to, ms, sel || null]);
}

async function record(browser, name, script, scene) {
  const ctx = await browser.newContext(scene ? { viewport: { width: 1080, height: 1920 } } : { viewport: { width: 390, height: 693 }, deviceScaleFactor: 2.77, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  await p.goto(scene ? 'http://localhost:8766/scenes.html' : URL, { waitUntil: 'networkidle' });
  await p.evaluate(() => document.fonts.ready);
  const marks = []; p.mark = label => marks.push([label, Date.now() / 1000]);
  await p.addStyleTag({ content: TAP_CSS + ' ::-webkit-scrollbar{display:none}' });
  await sleep(1200);
  const dir = path.join(OUT, name + '_frames'); fs.rmSync(dir, { recursive: true, force: true }); fs.mkdirSync(dir, { recursive: true });
  const cdp = await ctx.newCDPSession(p); const frames = [];
  cdp.on('Page.screencastFrame', async f => {
    const file = path.join(dir, String(frames.length).padStart(5, '0') + '.jpg');
    fs.writeFileSync(file, Buffer.from(f.data, 'base64')); frames.push([file, f.metadata.timestamp]);
    try { await cdp.send('Page.screencastFrameAck', { sessionId: f.sessionId }); } catch (e) {}
  });
  await cdp.send('Page.startScreencast', { format: 'jpeg', quality: 92, maxWidth: 1080, maxHeight: 1920 });
  const t0 = Date.now() / 1000;
  await script(p);
  const t1 = Date.now() / 1000;
  await cdp.send('Page.stopScreencast');
  await ctx.close();
  // Hold each frame until the next one; last frame until the script ended.
  const list = frames.map(([f, t], i) => `file '${f}'\nduration ${Math.max(0.001, (i + 1 < frames.length ? frames[i + 1][1] : t1) - t).toFixed(4)}`).join('\n') + `\nfile '${frames[frames.length - 1][0]}'\n`;
  fs.writeFileSync(path.join(dir, 'list.txt'), list);
  execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(dir, 'list.txt'),
    '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:color=white,fps=30,format=yuv420p',
    '-c:v', 'libx264', '-crf', '16', '-preset', 'medium', path.join(OUT, name + '.mp4')]);
  const f0 = frames[0][1];
  const log = marks.map(([l, t]) => [l, +(t - f0).toFixed(3)]);
  fs.writeFileSync(path.join(OUT, name + '.json'), JSON.stringify({ duration: +(t1 - f0).toFixed(3), marks: log }));
  console.log(name, frames.length, 'frames', (t1 - f0).toFixed(2) + 's', JSON.stringify(log));
}


async function scrollInfoTo(p, sel, ms) {
  const to = await p.evaluate(sel => { const info = document.querySelector('.info'), el = document.querySelector(sel);
    return el.getBoundingClientRect().top - info.getBoundingClientRect().top + info.scrollTop - 24; }, sel);
  await glide(p, to, ms, '.info');
}
const SCENES = { intro: 8.6, mood: 7.4, search: 5.8, flip: 8.0, logo: 4.2, credit: 3.8, end: 6.6 };
const CLIPS = {
  async wall(p) { await sleep(1000); await glide(p, 2600, 7000); await sleep(800); },
  async shuffle(p) { await sleep(900); await tap(p, '#shuffle', 'shuffle1'); await sleep(1600); await tap(p, '#shuffle', 'shuffle2'); await sleep(1600); },
  async open(p) {
    await sleep(900);
    const [i, n] = await p.evaluate(() => [window.BUILDINGS.findIndex(b => b.id === 'chand-baori'), window.BUILDINGS.length]);
    await p.evaluate(([i, n]) => { const r = Math.random; Math.random = () => (i + .5) / n; setTimeout(() => Math.random = r, 1500); }, [i, n]);
    await tap(p, '#surprise', 'surprise'); await sleep(3300);
    await tap(p, '#gNext', 'photo2'); await sleep(700);
    await tap(p, '#gNext', 'photo3'); await sleep(900);
    p.mark('study'); await scrollInfoTo(p, '#bMeta', 900); await sleep(2300);
    p.mark('links'); await scrollInfoTo(p, '#links', 1100); await sleep(1200);
    await glide(p, await p.evaluate(() => document.querySelector('.info').scrollTop + 260), 2200, '.info'); await sleep(800);
  },
  async filters(p) {
    await sleep(800); await tap(p, '#filterBtn', 'filter'); await sleep(3300);
    await tap(p, '.fp-cell[data-v="Light from above"]', 'light'); await sleep(250);
    const to = await p.evaluate(() => { const b = document.querySelector('.fp-body'), el = document.querySelector('.fp-cell[data-v="Courtyard"]');
      return el.getBoundingClientRect().top - b.getBoundingClientRect().top + b.scrollTop - 220; });
    await glide(p, to, 500, '.fp-body');
    await tap(p, '.fp-cell[data-v="Courtyard"]', 'courtyard'); await sleep(600);
    await tap(p, '.fp-tab[data-tab="types"]', 'types'); await sleep(420);
    await tap(p, '.fp-tab[data-tab="movs"]', 'movs'); await sleep(420);
    await tap(p, '.fp-tab[data-tab="where"]', 'where'); await sleep(420);
    await tap(p, '.fp-tab[data-tab="when"]', 'when'); await sleep(900);
    await tap(p, '[data-show]', 'show'); await sleep(1600);
  },
  async ending(p) { await sleep(600); await glide(p, 1400, 6000); await sleep(600); },
};
for (const [k, d] of Object.entries(SCENES)) CLIPS['scene_' + k] = Object.assign(async p => { await p.evaluate(k => window.play(k), k); p.mark('start'); await sleep(d * 1000); }, { scene: true });

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const [name, fn] of Object.entries(CLIPS)) if (!process.argv[2] || process.argv.slice(2).includes(name)) await record(b, name, fn, fn.scene);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
