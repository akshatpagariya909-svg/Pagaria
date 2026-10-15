/* Guess the building? Two games on one page: Daily five (the same five for everyone, picked from the date)
   and Endless (keep going until you miss one). No login and no server: scores live in this browser.
   Photos are fetched and shown from a temporary blob: address, and alt text never names the building,
   so the answer can't be read from a file name while you play. */
(() => {
  'use strict';

  const $ = id => document.getElementById(id);
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const first = s => String(s).split(',')[0].trim();
  const cityOf = b => first(b.place);
  const store = {
    get(k, d) { try { const v = localStorage.getItem(k); return v == null ? d : JSON.parse(v); } catch (e) { return d; } },
    set(k, v) { try { localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private windows can block storage */ } }
  };

  // Only buildings with a photo, a name, an architect and a city are asked about.
  const ALL = (window.BUILDINGS || []).filter(b => b.images && b.images.length && b.name && b.by && b.place);
  const byId = new Map(ALL.map(b => [b.id, b]));
  // "Unknown builders", "Nasrid builders", "Hadrian (attrib.)": not fair as a name-the-architect answer.
  const namedArchitect = b => !/builders|unknown|attrib|anonymous/i.test(b.by);
  const NAMES = [...new Set(ALL.map(b => b.name))];
  // One name per architect (data/names.js), so "Zaha Hadid" and "Zaha Hadid Architects" are never both offered.
  const architectOf = b => (window.NAMES ? window.NAMES.first(b.by) : first(b.by));
  const ARCHS = [...new Set(ALL.filter(namedArchitect).map(architectOf))];

  function hash(str) { let h = 2166136261; for (let k = 0; k < str.length; k++) { h ^= str.charCodeAt(k); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(seed) { let s = seed | 0; return () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function shuffled(a, r) { a = a.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(r() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }

  /* ---------- questions ---------- */
  const MODES = ['Name the building', 'Name the architect', 'Guess the decade', 'Zoomed-in detail', 'Which city'];
  const ASKS = ['Which building is this?', 'Who designed it?', 'When was it finished?', 'Which building is this a detail of?', 'Which city is it in?'];

  function photoFor(b, mode, r) {
    const ims = b.images, ext = ims.filter(im => im.kind === 'Exterior');
    if (mode === 3) { const close = ims.filter(im => im.kind === 'Detail' || im.kind === 'Interior'); if (close.length) return close[Math.floor(r() * close.length)]; }
    const pool = ext.length ? ext : ims;
    return pool[mode === 3 ? Math.floor(r() * pool.length) : 0];
  }
  // A mode that suits the building: no decade question before 1900, no architect question without a named architect.
  const fits = (b, mode) => !(mode === 2 && !(b.y >= 1900 && b.y <= 2029)) && !(mode === 1 && !namedArchitect(b));

  function makeQuestion(b, mode, seed, level) {
    const r = rng(seed);
    if (!fits(b, mode)) mode = 0;
    const three = (list, answer) => shuffled(list.filter(x => x !== answer), r).slice(0, 3);
    let answer, wrong;
    if (mode === 0 || mode === 3) { answer = b.name; wrong = three(NAMES, answer); }
    else if (mode === 1) { answer = architectOf(b); wrong = three(ARCHS, answer); }
    else if (mode === 2) {
      const dec = Math.floor(b.y / 10) * 10; answer = dec + 's';
      wrong = shuffled([-30, -20, -10, 10, 20, 30].map(x => dec + x).filter(x => x <= 2020 && x >= 1850), r).slice(0, 3).map(x => x + 's');
    } else {
      answer = cityOf(b);
      const near = [...new Set(ALL.filter(x => x.region === b.region).map(cityOf))];
      wrong = three(near.length > 4 ? near : [...new Set(ALL.map(cityOf))], answer);
    }
    const options = shuffled([answer, ...wrong], r);
    if (mode === 2) options.sort();
    const im = photoFor(b, mode, r);
    return { id: b.id, mode, answer, options, im, zoom: mode === 3 ? 2.6 : 1 + Math.min(level || 0, 3) * 0.3 };
  }

  /* ---------- the day ---------- */
  function today() {
    const d = new Date();
    const key = d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
    return { key, label: d.getDate() + ' ' + d.toLocaleString('en', { month: 'short' }) };
  }
  function yesterdayKey() { const d = new Date(); d.setDate(d.getDate() - 1); return d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0'); }
  // Each building gets a score from the date and its id; the top five win. Adding buildings rarely changes a day's five.
  function dailyFive(key) {
    const picked = ALL.map(b => ({ b, s: hash(key + '|' + b.id) })).sort((x, y) => x.s - y.s);
    const out = [];
    for (let mode = 0; mode < 5; mode++) {
      const hit = picked.find(p => !p.used && fits(p.b, mode));
      hit.used = true;
      out.push(makeQuestion(hit.b, mode, hash(key + '|q|' + mode), 0));
    }
    return out;
  }

  /* ---------- photos without their file names ---------- */
  let blobUrl = null;
  const abs = src => /^https?:/.test(src) ? src : '../' + src;
  // Full photo first; if its server refuses (no CORS), the small copy this site hosts itself. Never the raw address.
  async function asBlob(src) {
    const res = await fetch(abs(src), { mode: 'cors', credentials: 'omit' });
    if (!res.ok) throw new Error(res.status);
    return URL.createObjectURL(await res.blob());
  }
  async function showPhoto(img, im) {
    img.removeAttribute('src');
    let u = null;
    for (const src of [im.src, im.thumb]) { if (!src) continue; try { u = await asBlob(src); break; } catch (e) { /* try the next */ } }
    if (!u || !img.isConnected) return;
    if (blobUrl) URL.revokeObjectURL(blobUrl);
    blobUrl = u; img.src = u;
  }
  const warm = im => { try { fetch(abs(im.src), { mode: 'cors', credentials: 'omit' }).catch(() => {}); } catch (e) { /* ignore */ } };

  /* ---------- drawing ---------- */
  const main = $('game');
  let game = null; // the current game: { kind, questions | next(), i, picked, results, ... }

  function optionsHtml(q, picked) {
    return q.options.map((o, k) => {
      let cls = 'opt';
      if (picked != null && o === q.answer) cls += ' right';
      else if (picked != null && o === picked) cls += ' wrong';
      return `<button type="button" class="${cls}" data-k="${k}"${picked != null ? ' disabled' : ''}>${esc(o)}${picked != null && o === q.answer ? ' <span aria-hidden="true">✓</span>' : ''}</button>`;
    }).join('');
  }
  function revealHtml(q, right, verdict, nextLabel) {
    const b = byId.get(q.id);
    return `<div class="reveal">
      <span class="verdict${right ? '' : ' miss'}">${esc(verdict)}</span>
      <b class="rname">${esc(b.name)}</b>
      <span class="rmeta">${esc(b.by)} · ${esc(b.place)} · ${esc(b.year)}</span>
      ${b.study ? `<p class="rstudy"><span>Key features</span>${esc(b.study)}</p>` : ''}
      <div class="ractions"><button type="button" class="go" id="next">${esc(nextLabel)}</button>
      <a class="ghost" href="../buildings/${encodeURIComponent(b.id)}/" target="_blank" rel="noopener">Open this building</a></div></div>`;
  }
  function photoBlock(q, n, answered) {
    const im = q.im || {};
    const credit = (im.credit || '').replace(/\.$/, '');
    return `<div class="photo-wrap"><div class="photo"><img id="photo" alt="Mystery building, question ${n}" style="transform: scale(${answered ? 1 : q.zoom})">
      <span class="pill">${esc(MODES[q.mode])}</span></div>
      <p class="credit">${credit ? 'Photo: ' + esc(credit) + ' · ' : ''}${esc(im.license || '')}${answered && im.source ? ` · <a href="${esc(im.source)}" target="_blank" rel="noopener">source</a>` : ''}</p></div>`;
  }

  /* ---------- Daily five ---------- */
  function dailyState() {
    const t = today();
    let s = store.get('da-daily', null);
    if (!s || s.day !== t.key) s = { day: t.key, i: 0, picked: null, results: [], picks: [], score: 0, streak: 0, done: false, started: false };
    return s;
  }
  const dailyStats = () => store.get('da-daily-stats', { last: null, days: 0, best: 0 });

  function startDaily() {
    const t = today();
    game = { kind: 'daily', t, qs: dailyFive(t.key), s: dailyState() };
    drawDaily();
  }
  function drawDaily() {
    const { t, qs, s } = game, st = dailyStats();
    store.set('da-daily', s);
    if (!s.started) {
      main.innerHTML = `<section class="intro">
        <span class="kicker">Daily five · ${esc(t.label)}</span>
        <h1>Guess five buildings</h1>
        <ol class="rules"><li><b>01</b><span>Five photos. Pick one of four answers for each.</span></li>
        <li><b>02</b><span>Name it, its architect, its decade, a close-up, its city.</span></li>
        <li><b>03</b><span>Right answers in a row score more: 10, 20, 30…</span></li>
        <li><b>04</b><span>Everyone gets the same five today. A new five tomorrow.</span></li></ol>
        <button type="button" class="go big" id="begin">Play today's five</button>
        <p class="small">Days in a row ${st.last === t.key || st.last === yesterdayKey() ? st.days : 0} · best ${st.best} points. Kept in this browser, no sign-up.</p></section>`;
      $('begin').onclick = () => { s.started = true; drawDaily(); };
      return;
    }
    if (s.done) return drawDailyEnd();
    const q = qs[s.i], answered = s.picked != null, right = answered && s.picked === q.answer;
    const dots = qs.map((_, k) => `<i class="${k < s.results.length ? (s.results[k] ? 'hit' : 'miss') : k === s.i ? 'now' : ''}"></i>`).join('');
    main.innerHTML = `<section class="play">
      ${photoBlock(q, s.i + 1, answered)}
      <div class="panel">
        <div class="status"><span class="kicker">${s.i + 1} of 5 · ${esc(t.label)}</span><span class="dots">${dots}</span><span class="score">${s.score} pts</span></div>
        <h1>${esc(ASKS[q.mode])}</h1>
        <div class="opts">${optionsHtml(q, s.picked)}</div>
        ${answered ? revealHtml(q, right, right ? 'Right · +' + 10 * s.streak + ' points' : 'Not quite. It is', s.i === 4 ? 'See my score' : 'Next building →') : ''}
      </div></section>`;
    showPhoto($('photo'), q.im);
    if (s.i < 4) warm(qs[s.i + 1].im);
    main.querySelectorAll('.opt').forEach(btn => btn.onclick = () => {
      if (s.picked != null) return;
      const o = q.options[+btn.dataset.k], ok = o === q.answer;
      s.picked = o; s.picks.push(o); s.results.push(ok);
      s.streak = ok ? s.streak + 1 : 0; s.score += ok ? 10 * s.streak : 0;
      drawDaily();
    });
    const nx = $('next');
    if (nx) nx.onclick = () => {
      if (s.i < 4) { s.i++; s.picked = null; drawDaily(); window.scrollTo(0, 0); return; }
      s.done = true;
      const stt = dailyStats();
      if (stt.last !== t.key) { stt.days = stt.last === yesterdayKey() ? stt.days + 1 : 1; stt.last = t.key; }
      stt.best = Math.max(stt.best, s.score);
      store.set('da-daily-stats', stt);
      drawDaily(); window.scrollTo(0, 0);
    };
  }
  function drawDailyEnd() {
    const { t, qs, s } = game, st = dailyStats();
    const correct = s.results.filter(Boolean).length;
    const squares = s.results.map(x => (x ? '■' : '□')).join(' ');
    const rank = correct === 5 ? 'Five out of five. You could teach this.' : correct >= 3 ? correct + ' out of 5. A good eye for buildings.' : correct + ' out of 5. Every miss is a building to explore.';
    const mid = new Date(); mid.setHours(24, 0, 0, 0);
    const mins = Math.max(0, Math.round((mid - new Date()) / 60000));
    main.innerHTML = `<section class="end">
      <div class="end-main">
        <span class="kicker">Today's five, done</span>
        <h1>${s.score} points</h1>
        <p class="rank">${esc(rank)}</p>
        <div class="card-share"><b>Find Great Architecture<br>Daily five · ${esc(t.label)}</b><span class="sq">${squares}</span><span>${s.score} pts · ${correct}/5</span></div>
        <div class="row"><button type="button" class="go" id="share">Share result</button><a class="ghost" href="#endless">Try Endless</a></div>
        <p class="small">A new five in ${Math.floor(mins / 60)} h ${mins % 60} min. Days in a row ${st.days} · best ${st.best} points.</p>
      </div>
      <div class="recap"><h2>Explore today's five</h2>${qs.map((q, k) => recapRow(q, s.results[k])).join('')}</div></section>`;
    $('share').onclick = () => share('Find Great Architecture · Daily five · ' + t.label + '\n' + squares + '  ' + s.score + ' pts', $('share'));
    loadRecapThumbs();
  }
  function recapRow(q, ok) {
    const b = byId.get(q.id);
    return `<a class="rrow" href="../buildings/${encodeURIComponent(b.id)}/" target="_blank" rel="noopener"><span class="th"><img data-src="${esc(b.images[0].thumb || b.images[0].src)}" alt=""></span>
      <span class="rt"><b>${esc(b.name)}</b><small>${ok ? '■' : '□'} ${esc(MODES[q.mode])}</small></span><span aria-hidden="true">↗</span></a>`;
  }
  // The recap shows the answers anyway, so its thumbnails can load directly.
  const loadRecapThumbs = () => main.querySelectorAll('.recap img[data-src]').forEach(img => { img.src = abs(img.dataset.src); });

  /* ---------- Endless ---------- */
  const endlessStats = () => store.get('da-endless', { best: 0, runs: 0 });
  function startEndless(go) {
    const seed = Math.floor(Math.random() * 1e9);
    const order = shuffled(ALL.map((_, k) => k), rng(seed));
    game = { kind: 'endless', seed, order, i: 0, picked: null, results: [], over: false, started: !!go, newBest: false, q: null };
    drawEndless();
  }
  function endlessQ(i) {
    const g = game, b = ALL[g.order[i % g.order.length]], r = rng(hash(g.seed + '|m|' + i));
    return makeQuestion(b, Math.floor(r() * 5), hash(g.seed + '|q|' + i), Math.floor(i / 10));
  }
  function drawEndless() {
    const g = game, st = endlessStats();
    if (!g.started) {
      main.innerHTML = `<section class="intro">
        <span class="kicker">Endless</span>
        <h1>How many in a row?</h1>
        <ol class="rules"><li><b>01</b><span>One building after another, any of the five question types.</span></li>
        <li><b>02</b><span>Miss one and the run is over.</span></li>
        <li><b>03</b><span>Every 10 in a row, the photos are cropped closer.</span></li></ol>
        <div class="stats"><div><small>Your best</small><b>${st.best}</b></div><div><small>Runs played</small><b>${st.runs}</b></div></div>
        <button type="button" class="go big" id="begin">Start a run</button>
        <p class="small">Your best is kept in this browser. No sign-up.</p></section>`;
      $('begin').onclick = () => { g.started = true; drawEndless(); };
      return;
    }
    if (g.over) return drawEndlessEnd();
    if (!g.q) g.q = endlessQ(g.i);
    const q = g.q, answered = g.picked != null, right = answered && g.picked === q.answer;
    const run = g.results.filter(Boolean).length;
    const label = run > st.best ? 'New best!' : run === st.best && run > 0 ? 'Equals your best' : 'Best ' + st.best;
    const trail = g.results.slice(-40).map(x => `<i class="${x ? 'hit' : 'miss'}"></i>`).join('');
    main.innerHTML = `<section class="play">
      ${photoBlock(q, g.i + 1, answered)}
      <div class="panel">
        <div class="status"><span class="run"><b>${run}</b><small>in a row</small></span><span class="trail">${trail}</span><span class="score${run >= st.best && run > 0 ? ' on' : ''}">${esc(label)}</span></div>
        <h1>${esc(ASKS[q.mode])}</h1>
        <div class="opts">${optionsHtml(q, g.picked)}</div>
        ${answered ? revealHtml(q, right, right ? 'Right · ' + run + ' in a row' : 'Missed. It is', right ? 'Next building →' : 'See your run') : ''}
      </div></section>`;
    showPhoto($('photo'), q.im);
    main.querySelectorAll('.opt').forEach(btn => btn.onclick = () => {
      if (g.picked != null) return;
      g.picked = q.options[+btn.dataset.k]; g.results.push(g.picked === q.answer);
      if (g.picked === q.answer) warm(endlessQ(g.i + 1).im);
      drawEndless();
    });
    const nx = $('next');
    if (nx) nx.onclick = () => {
      if (g.picked === q.answer) { g.i++; g.picked = null; g.q = null; drawEndless(); window.scrollTo(0, 0); return; }
      const s2 = endlessStats(), runN = g.results.filter(Boolean).length;
      g.newBest = runN > s2.best; s2.best = Math.max(s2.best, runN); s2.runs++;
      store.set('da-endless', s2);
      g.over = true; drawEndless(); window.scrollTo(0, 0);
    };
  }
  function drawEndlessEnd() {
    const g = game, st = endlessStats(), run = g.results.filter(Boolean).length;
    const squares = g.results.map(x => (x ? '■' : '□')).join('');
    const missed = byId.get(g.q.id);
    const qs = g.results.map((_, k) => k === g.i ? g.q : endlessQ(k)).reverse().slice(0, 8);
    const oks = g.results.slice().reverse();
    main.innerHTML = `<section class="end">
      <div class="end-main">
        ${g.newBest ? '<span class="badge"><i></i>New personal best</span>' : `<span class="kicker">Run over · best ${st.best}</span>`}
        <h1>${run} in a row</h1>
        <p class="rank">Missed on ${esc(missed.name)} (${esc(MODES[g.q.mode].toLowerCase())}).</p>
        <div class="card-share"><b>Find Great Architecture<br>Endless</b><span class="sq wrap">${squares}</span><span>${run} in a row · best ${st.best}</span></div>
        <div class="row"><button type="button" class="go" id="again">Start again</button><button type="button" class="ghost" id="share">Share</button></div>
        <p class="small"><a href="#daily">Or play today's Daily five</a></p>
      </div>
      <div class="recap"><h2>This run's buildings</h2>${qs.map((q, k) => recapRow(q, oks[k])).join('')}</div></section>`;
    $('again').onclick = () => { startEndless(true); window.scrollTo(0, 0); };
    $('share').onclick = () => share('Find Great Architecture · Endless\n' + squares + '  ' + run + ' in a row', $('share'));
    loadRecapThumbs();
  }

  /* ---------- sharing ---------- */
  async function share(text, btn) {
    const url = new URL('./', location.href).href;
    const full = text + '\n' + url;
    try { if (navigator.share) { await navigator.share({ text: full }); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
    try { await navigator.clipboard.writeText(full); btn.textContent = 'Copied, paste it anywhere'; }
    catch (e) { window.prompt('Copy your result:', full); }
  }

  /* ---------- which game ---------- */
  function route() {
    const endless = location.hash === '#endless';
    $('gDaily').setAttribute('aria-pressed', !endless);
    $('gEndless').setAttribute('aria-pressed', endless);
    document.title = (endless ? 'Endless' : 'Daily five') + ' · Guess the building? · Find Great Architecture';
    if (endless) startEndless(false); else startDaily();
  }
  $('gDaily').onclick = () => { if (location.hash !== '#daily') location.hash = 'daily'; else route(); };
  $('gEndless').onclick = () => { if (location.hash !== '#endless') location.hash = 'endless'; else route(); };
  window.addEventListener('hashchange', route);
  if (!ALL.length) { main.innerHTML = '<p class="small">The buildings could not load. Try again in a moment.</p>'; return; }
  route();
})();
