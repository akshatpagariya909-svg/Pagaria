// Turns social/carousels.json into Instagram carousel slides (1080 × 1350 JPGs)
// and a ready-to-paste caption with photo credits.
//   node social/render.js                 all carousels
//   node social/render.js light-from-above   just one
// Output: social/out/<id>/01.jpg … and caption.txt

const fs = require('fs');
const path = require('path');
const { chromium } = require(process.env.PLAYWRIGHT || 'playwright');

const ROOT = path.resolve(__dirname, '..');
const OUT = path.join(__dirname, 'out');
global.window = {};
require(path.join(ROOT, 'site/data/buildings.js'));
const BY_ID = Object.fromEntries(window.BUILDINGS.map(b => [b.id, b]));
const SPEC = JSON.parse(fs.readFileSync(path.join(__dirname, 'carousels.json'), 'utf8'));

const esc = s => String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
const pad = n => String(n).padStart(2, '0');

function pick(ref) {
  const b = BY_ID[ref.b];
  if (!b) throw new Error('Unknown building ' + ref.b);
  const im = b.images[ref.img || 0];
  if (!im) throw new Error(`${ref.b} has no image ${ref.img}`);
  const local = path.join(ROOT, 'site', im.src);
  // Later buildings host their full photo on Wikimedia; fall back to the local thumbnail.
  const file = fs.existsSync(local) ? local : path.join(ROOT, 'site', im.thumb);
  return { b, im, url: 'file://' + file };
}

const CSS = `
:root { --ground:#FFFFFF; --paper:#F7F7F5; --ink:#111110; --graphite:#5D5C57; --hair:#E6E4DF; --stage:#FFFFFF; --signal:#DA3A26; --r:28px;
  --sans:'Archivo',sans-serif; --serif:'Newsreader',serif; --mono:'IBM Plex Mono',monospace; }
* { box-sizing:border-box; margin:0; }
html,body { width:1080px; height:1350px; overflow:hidden; }
body { background:var(--ground); color:var(--ink); font-family:var(--sans); -webkit-font-smoothing:antialiased; position:relative; }
body.dark { background:var(--stage); color:var(--ink); }
.top { position:absolute; left:56px; right:56px; top:48px; display:flex; justify-content:space-between; align-items:flex-start; }
.mark .accent { color:var(--signal); }
.mark { font-weight:850; font-stretch:125%; font-size:22px; line-height:.95; letter-spacing:-.02em; text-transform:uppercase; }
.count { font:500 18px var(--mono); letter-spacing:.08em; text-transform:uppercase; color:var(--graphite); text-align:right; }
.dark .count { color:var(--graphite); }
.photo { position:absolute; left:56px; right:56px; overflow:hidden; background:#ccc; }
.photo img { width:100%; height:100%; object-fit:cover; display:block; }
.pill { display:inline-flex; align-items:center; height:52px; padding:0 24px; border:2px solid currentColor; border-radius:var(--r);
  font-weight:650; font-size:24px; }
.pill.signal { background:var(--signal); border-color:var(--signal); color:#fff; }
.pill.solid { background:var(--ground); color:var(--ink); border-color:var(--ink); }
.big { font-weight:850; font-stretch:125%; text-transform:uppercase; letter-spacing:-.025em; line-height:.9; }
.sub { font-family:var(--serif); font-style:italic; font-size:42px; line-height:1.15; }
.credit { position:absolute; left:56px; right:56px; bottom:40px; font:400 16px var(--mono); color:var(--graphite); letter-spacing:.02em;
  white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.dark .credit { color:var(--graphite); }
.name { font-weight:750; font-stretch:105%; font-size:54px; line-height:1; letter-spacing:-.02em; }
.meta { display:flex; justify-content:space-between; gap:24px; margin-top:16px; font-size:28px; font-weight:550; }
.meta .when { font:400 22px var(--mono); color:var(--graphite); letter-spacing:.04em; align-self:center; white-space:nowrap; }
.label { font:500 17px var(--mono); letter-spacing:.1em; text-transform:uppercase; color:var(--graphite); margin-top:30px; }
.study { font-family:var(--serif); font-size:38px; line-height:1.2; margin-top:10px; }
`;

const page = (body, dark) => `<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&display=block" rel="stylesheet">
<style>${CSS}</style></head><body class="${dark ? 'dark' : ''}">${body}</body></html>`;

const top = (c, i, n, label) => `<div class="top"><div class="mark">Discover<br><span class="accent">Architecture.</span></div>
  <div class="count">${esc(label || c.idea || c.tag)}<br>${i} / ${n}</div></div>`;
const COUNT = `${(Math.floor(window.BUILDINGS.length / 100) * 100).toLocaleString('en-US')}+`;
const credit = p => `<div class="credit">Photo: ${esc(p.im.credit.replace(/\s+/g, ' ').trim())} · ${esc(p.im.license)} · Wikimedia Commons</div>`;

function cover(c, n) {
  const p = pick(c.cover);
  return page(`${top(c, 1, n)}
  <div class="photo" style="top:140px;height:760px"><img src="${p.url}"></div>
  <div style="position:absolute;left:56px;right:56px;top:936px">
    <span class="pill">${esc(c.tag)}</span>
    <div class="big" style="font-size:96px;margin-top:26px">${esc(c.title)}</div>
    <div class="sub" style="margin-top:20px">${esc(c.sub)}</div>
  </div>${credit(p)}`);
}

function building(c, ref, i, n, label) {
  const p = pick(ref), b = p.b;
  return page(`${top(c, i, n, label)}
  <div class="photo" style="top:140px;height:740px"><img src="${p.url}"></div>
  <div style="position:absolute;left:56px;right:56px;top:916px">
    <div class="name">${esc(b.name)}</div>
    <div class="meta"><span>${esc(b.by)}</span><span class="when">${esc(b.year)} · ${esc(b.place)}</span></div>
    <div class="label">Key features</div>
    <div class="study">${esc(b.study)}</div>
  </div>${credit(p)}`);
}

function end(c, i, n, lead) {
  return page(`${top(c, i, n)}
  <div style="position:absolute;left:56px;right:56px;top:380px">
    <div class="big" style="font-size:112px">${lead}</div>
    <div class="sub" style="margin-top:36px;color:var(--graphite)">Wander a wall of free photos, then follow links to plans, sections and essays.</div>
    <div style="margin-top:64px;display:flex;gap:16px;flex-wrap:wrap">
      <span class="pill solid">${esc(c.find || (c.idea ? 'Find more with: ' + c.idea : 'Play on the wall'))}</span>
      <span class="pill signal">Link in bio</span>
    </div>
  </div>
  <div class="credit" style="font-size:24px;color:var(--ink)">${SPEC.handle ? '@' + esc(SPEC.handle) : esc(SPEC.site)}</div>`, true);
}

function guessCover(c, n) {
  return page(`${top(c, 1, n)}
  <div style="position:absolute;left:56px;right:56px;top:300px">
    <span class="pill">${n - 3 === 4 ? 'Four' : n - 3} details</span>
    <div class="big" style="font-size:150px;margin-top:36px">Guess the building</div>
    <div class="sub" style="margin-top:36px;color:var(--graphite)">${esc(c.title)}. ${esc(c.sub)}.</div>
    <div class="sub" style="margin-top:24px;color:var(--graphite)">Comment your guesses ↓</div>
  </div>`, true);
}

function guessItem(c, it, k, i, n) {
  const p = pick(it), z = it.zoom || 1.5;
  return page(`${top(c, i, n)}
  <div class="photo" style="top:140px;height:968px"><img src="${p.url}" style="transform:scale(${z});transform-origin:${it.x ?? 50}% ${it.y ?? 50}%"></div>
  <div style="position:absolute;left:56px;right:56px;top:1132px;display:flex;justify-content:space-between;align-items:baseline">
    <div class="big" style="font-size:120px">${pad(k)}</div>
    <div class="sub" style="font-size:36px">Which building?</div>
  </div>${credit(p)}`);
}

function guessAnswers(c, i, n) {
  const cells = c.items.map((it, k) => {
    const p = pick(it), b = p.b;
    return `<div><div style="height:372px;overflow:hidden"><img src="${p.url}" style="width:100%;height:100%;object-fit:cover;display:block"></div>
      <div style="font:500 18px var(--mono);color:var(--graphite);margin-top:14px">${pad(k + 1)}</div>
      <div style="font-weight:750;font-size:32px;line-height:1.05;margin-top:4px">${esc(b.name)}</div>
      <div style="font-size:22px;margin-top:6px">${esc(b.by)} · <span style="font-family:var(--mono);font-size:18px;color:var(--graphite)">${esc(b.year)}</span></div></div>`;
  }).join('');
  return page(`${top(c, i, n)}
  <div style="position:absolute;left:56px;right:56px;top:140px">
    <div class="big" style="font-size:72px">Answers</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:36px 32px;margin-top:32px">${cells}</div>
  </div>
  <div class="credit">Photos: see caption for credits and licences</div>`);
}

// "Start here": what the site is and how to use it, for the pinned first post.
const IDEAS = (() => {
  const n = {};
  window.BUILDINGS.forEach(b => b.concepts.forEach(k => n[k] = (n[k] || 0) + 1));
  return Object.entries(n).sort((a, b) => b[1] - a[1]).slice(0, 14).map(e => e[0]);
})();
const DEEPER = [['Drawings & photos', 'ArchDaily'], ['Plans & sections', 'WikiArquitectura'], ['Photo essays', 'Divisare'],
  ['News & features', 'Dezeen'], ['The building', 'Official website'], ['Getting there', 'Map']];

function textSlide(c, i, n, label, title, sub, body, dark) {
  return page(`${top(c, i, n, label)}
  <div style="position:absolute;left:56px;right:56px;top:220px">
    <div class="big" style="font-size:96px">${title}</div>
    <div class="sub" style="margin-top:28px;max-width:900px${dark ? ';color:var(--graphite)' : ''}">${sub}</div>
    ${body}
  </div>`, dark);
}

function creditSlide(c, i, n) {
  const p = pick(c.creditExample);
  return page(`${top(c, i, n, 'How it works')}
  <div style="position:absolute;left:56px;right:56px;top:160px">
    <div class="big" style="font-size:80px">Free photos, always credited</div>
    <div class="sub" style="margin-top:20px;font-size:36px">Public domain or Creative Commons, from Wikimedia Commons.</div>
  </div>
  <div class="photo" style="top:520px;height:620px"><img src="${p.url}"></div>
  <div style="position:absolute;left:56px;right:56px;top:1160px;font:400 26px/1.4 var(--mono);color:var(--ink)">
    Photo: ${esc(p.im.credit.replace(/\s+/g, ' ').trim())}<br>${esc(p.im.license)} · ${esc(p.b.name)}</div>`);
}

function introSlides(c) {
  const n = 6;
  const pills = IDEAS.map(k => `<span class="pill" style="height:64px;padding:0 28px;font-size:30px">${esc(k)}</span>`).join('');
  const rows = DEEPER.map(([what, where]) => `<div style="display:flex;justify-content:space-between;gap:24px;padding:22px 0;border-bottom:2px solid var(--hair)">
    <span style="font-weight:700;font-size:36px">${esc(where)}</span><span style="font:400 26px var(--mono);color:var(--graphite);align-self:center">${esc(what)}</span></div>`).join('');
  return [
    textSlide(c, 1, n, c.tag, `${COUNT} buildings worth knowing`, esc(c.sub),
      `<div style="margin-top:56px"><span class="pill solid">Swipe to see how it works →</span></div>`, true),
    textSlide(c, 2, n, 'How it works', 'Browse by idea', 'Pick an idea and the wall shows every building that uses it.',
      `<div style="margin-top:48px;display:flex;flex-wrap:wrap;gap:14px">${pills}</div>`),
    building(c, c.example, 3, n, 'Open any building'),
    textSlide(c, 4, n, 'How it works', 'Go deeper', 'Every building links out to the best places to study it.',
      `<div style="margin-top:40px;border-top:2px solid var(--ink)">${rows}</div>`),
    creditSlide(c, 5, n),
    end(c, n, n, 'Start wandering'),
  ];
}

function slidesFor(c) {
  if (c.kind === 'intro') return introSlides(c);
  if (c.kind === 'guess') {
    const n = c.items.length + 3;
    return [guessCover(c, n), ...c.items.map((it, k) => guessItem(c, it, k + 1, k + 2, n)),
      guessAnswers(c, n - 1, n), end(c, n, n, 'How many did you get?')];
  }
  const n = c.slides.length + 2;
  return [cover(c, n), ...c.slides.map((s, k) => building(c, s, k + 2, n)),
    end(c, n, n, `${COUNT} buildings to wander`)];
}

function caption(c) {
  const refs = c.kind === 'guess' ? c.items : c.kind === 'intro' ? [c.example, c.creditExample] : [c.cover, ...c.slides];
  const list = (c.kind === 'guess' ? c.items : c.kind === 'intro' ? [] : c.slides).map((r, k) => {
    const b = BY_ID[r.b];
    return `${pad(k + 1)} ${b.name}, ${b.by} (${b.year}, ${b.place})`;
  });
  const seen = new Set(), credits = [];
  for (const r of refs) {
    const { im, b } = pick(r);
    if (seen.has(im.source)) continue;
    seen.add(im.source);
    credits.push(`${b.name}: ${im.credit.replace(/\s+/g, ' ').trim()}, ${im.license}, ${im.source}`);
  }
  const more = c.find ? `${c.find} on the site` : `Find more precedents with "${c.idea}" on the site`;
  const head = c.kind === 'intro'
    ? `${COUNT} buildings worth knowing. ${c.sub}\n\nBrowse by idea, open any building, then follow links to drawings, plans, sections and essays. Every photo is free and credited.\n\nNew precedents here every week. The wall: link in bio.`
    : c.kind === 'guess'
    ? `${c.title}. Answers on the last slide, no peeking.\n\nComment your guesses, then play the full wall: link in bio.`
    : `${c.title}: ${c.sub.charAt(0).toLowerCase() + c.sub.slice(1)}.\n\n${list.join('\n')}\n\nSave this for later. ${more}: link in bio.`;
  return `${head}\n\n${c.hashtags}\n\n.\n.\n.\nPhoto credits (cropped, text added):\n${credits.join('\n')}\n`;
}

(async () => {
  const only = process.argv[2];
  const list = SPEC.carousels.filter(c => !only || c.id === only);
  if (!list.length) throw new Error('No carousel called ' + only);
  const browser = await chromium.launch(fs.existsSync('/opt/pw-browsers/chromium') ? { executablePath: '/opt/pw-browsers/chromium' } : {});
  const tab = await browser.newPage({ viewport: { width: 1080, height: 1350 } });
  for (const c of list) {
    const dir = path.join(OUT, c.id);
    fs.rmSync(dir, { recursive: true, force: true });
    fs.mkdirSync(dir, { recursive: true });
    const slides = slidesFor(c);
    for (let k = 0; k < slides.length; k++) {
      const html = path.join(dir, `.slide.html`);
      fs.writeFileSync(html, slides[k]);
      await tab.goto('file://' + html, { waitUntil: 'networkidle' });
      await tab.evaluate(() => document.fonts.ready);
      await tab.screenshot({ path: path.join(dir, `${pad(k + 1)}.jpg`), type: 'jpeg', quality: 90 });
    }
    fs.rmSync(path.join(dir, '.slide.html'));
    fs.writeFileSync(path.join(dir, 'caption.txt'), caption(c));
    console.log(`${c.id}: ${slides.length} slides`);
  }
  await browser.close();
})().catch(e => { console.error(e.message); process.exit(1); });
