// Records phone-sized clips of the local site as 1080x1920 30fps MP4s.
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), { execFileSync } = require('child_process');
const OUT = process.env.OUT || path.join(__dirname, 'clips');
const URL = 'http://localhost:8765/';
const sleep = ms => new Promise(r => setTimeout(r, ms));

const TAP_CSS = `.__tap{position:fixed;z-index:99999;width:56px;height:56px;margin:-28px 0 0 -28px;border-radius:50%;
  background:rgba(17,17,16,.22);border:2px solid rgba(255,255,255,.9);pointer-events:none;animation:__t .5s ease-out forwards}
  @keyframes __t{0%{transform:scale(.4);opacity:0}30%{transform:scale(1);opacity:1}100%{transform:scale(1.25);opacity:0}}`;

async function tap(p, sel) {
  const el = p.locator(sel).first();
  await el.scrollIntoViewIfNeeded();
  const b = await el.boundingBox();
  const x = b.x + b.width / 2, y = b.y + b.height / 2;
  await p.evaluate(([x, y]) => { const d = document.createElement('div'); d.className = '__tap'; d.style.left = x + 'px'; d.style.top = y + 'px';
    document.body.appendChild(d); setTimeout(() => d.remove(), 600); }, [x, y]);
  await sleep(180);
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

async function record(browser, name, script) {
  const ctx = await browser.newContext({ viewport: { width: 390, height: 693 }, deviceScaleFactor: 2.77, isMobile: true, hasTouch: true });
  const p = await ctx.newPage();
  await p.goto(URL, { waitUntil: 'networkidle' });
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
  console.log(name, frames.length, 'frames', (t1 - t0).toFixed(1) + 's');
}

const CLIPS = {
  async wall(p) { await sleep(1000); await glide(p, 2600, 7000); await sleep(800); },
  async shuffle(p) { await sleep(900); await tap(p, '#shuffle'); await sleep(1600); await tap(p, '#shuffle'); await sleep(1600); },
  async surprise(p) {
    await sleep(900);
    const i = await p.evaluate(() => window.BUILDINGS.findIndex(b => b.id === 'chand-baori'));
    await p.evaluate(([i, n]) => { const r = Math.random; Math.random = () => (i + .5) / n; setTimeout(() => Math.random = r, 1500); }, [i, await p.evaluate(() => window.BUILDINGS.length)]);
    await tap(p, '#surprise'); await sleep(2800);
    await glide(p, 900, 4000, '.info'); await sleep(1500);
  },
  async filters(p) {
    await sleep(800); await tap(p, '#filterBtn'); await sleep(1200);
    await tap(p, '.fp-cell[data-v="Light from above"]'); await sleep(900);
    await tap(p, '.fp-tab[data-tab="types"]'); await sleep(1100);
    await tap(p, '.fp-tab[data-tab="movs"]'); await sleep(1100);
    await tap(p, '.fp-tab[data-tab="where"]'); await sleep(1300);
    await tap(p, '.fp-tab[data-tab="when"]'); await sleep(1100);
    await tap(p, '[data-show]'); await sleep(1200);
    await glide(p, 1200, 3000); await sleep(600);
  },
  async ending(p) { await sleep(600); await glide(p, 1400, 6000); await sleep(600); },
};

(async () => {
  fs.mkdirSync(OUT, { recursive: true });
  const b = await chromium.launch({ executablePath: '/opt/pw-browsers/chromium' });
  for (const [name, fn] of Object.entries(CLIPS)) if (!process.argv[2] || process.argv.slice(2).includes(name)) await record(b, name, fn);
  await b.close();
})().catch(e => { console.error(e); process.exit(1); });
