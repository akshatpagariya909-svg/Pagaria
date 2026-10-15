/* Guess the building? Two games on one page: Daily five (the same five for everyone, picked from the date)
   and Endless (keep going until you miss one). No login and no server: scores live in this browser.
   Photos are fetched and shown from a temporary blob: address, and alt text never names the building,
   so the answer can't be read from a file name while you play.
   The look (v16 on the design canvas): green for right and sunset red for wrong, inside the game only;
   tiles that fill in as you play, a visible combo, a celebrated score, a stats sheet and one big Share button. */
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
  const buzz = p => { try { if (navigator.vibrate) navigator.vibrate(p); } catch (e) { /* not every phone */ } };
  const SITE = 'findgreatarchitecture.com';

  /* ---------- which photo the game may show ----------
     The wall can show any good photo; the game needs the building's clearest outside view:
     an exterior, wider than tall (1.2 to 1.9), at least 1,000 px wide, Wikidata's main photo first.
     Buildings without one sit out of the game (they stay on the wall). */
  const fitsGame = im => im && im.kind === 'Exterior' && im.w >= 1000 && im.h && im.w / im.h >= 1.2 && im.w / im.h <= 1.9;
  function gamePhoto(b) {
    const ims = b.images || [];
    const lead = b.lead && ims.find(im => im.file === b.lead);
    if (fitsGame(lead)) return lead;
    return ims.find(fitsGame) || null;
  }
  // Only buildings with a game photo, a name, an architect and a city are asked about.
  const LINKS = window.LINKS || {}, ARCH = window.ARCHITECTS || { people: {}, buildings: {} };
  const FACES = new Set(Object.keys(ARCH.people || {}).filter(q => ARCH.people[q].thumb));
  /* How well known a building is, from what the site already has: the hand-picked first hundred, pages on the
     big architecture sites, an English Wikipedia article, an architect famous enough to have a free portrait,
     and plenty of photos on Commons. A stand-in until the data carries Wikidata's own count. */
  function fame(b) {
    const l = LINKS[b.id] || {}, s = new Set((l.links || []).map(x => x.site));
    let v = 0;
    if (b.n <= 100) v += 6;
    if (s.has('WikiArquitectura')) v += 3;
    if (s.has('Docomomo')) v += 2;
    ['ArchDaily', 'archINFORM', 'Divisare'].forEach(k => { if (s.has(k)) v += 1; });
    if (s.has('Structurae')) v += 0.5;
    if (l.wiki) v += 1;
    if (((ARCH.buildings || {})[b.id] || []).some(q => FACES.has(q))) v += 2;
    if ((b.images || []).length >= 6) v += 1;
    return v + (b.fame || 0); // a real count from Wikidata, when the data has one, outweighs the rest
  }
  const ALL = (window.BUILDINGS || []).filter(b => b.name && b.by && b.place && (b.gamePhoto = gamePhoto(b)))
    .map(b => (b.fameScore = fame(b), b)).sort((x, y) => y.fameScore - x.fameScore || (x.n || 0) - (y.n || 0));
  // Daily five draws from the best-known; Endless starts there and widens as the run grows.
  const DAILY = ALL.slice(0, 400);
  const TIERS = [[0, 300], [300, 800], [800, ALL.length]];
  const byId = new Map(ALL.map(b => [b.id, b]));
  // "Unknown builders", "Nasrid builders", "Hadrian (attrib.)": not fair as a name-the-architect answer.
  const namedArchitect = b => !/builders|unknown|attrib|anonymous/i.test(b.by);
  const NAMES = [...new Set(ALL.map(b => b.name))];
  const ARCHS = [...new Set(ALL.filter(namedArchitect).map(b => first(b.by)))];

  function hash(str) { let h = 2166136261; for (let k = 0; k < str.length; k++) { h ^= str.charCodeAt(k); h = Math.imul(h, 16777619); } return h >>> 0; }
  function rng(seed) { let s = seed | 0; return () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function shuffled(a, r) { a = a.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(r() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }

  /* ---------- questions ---------- */
  const MODES = ['Name the building', 'Name the architect', 'Guess the decade', 'Zoomed-in detail', 'Which city'];
  const ASKS = ['Which building is this?', 'Who designed it?', 'When was it finished?', 'Which building is this a detail of?', 'Which city is it in?'];
  const RANKS = ['Tourist', 'First year', 'Student', 'Draughtsperson', 'Architect', 'Master builder'];
  // A mode that suits the building: no decade question before 1900, no architect question without a named architect.
  const fits = (b, mode) => !(mode === 2 && !(b.y >= 1900 && b.y <= 2029)) && !(mode === 1 && !namedArchitect(b));

  function makeQuestion(b, mode, seed, level) {
    const r = rng(seed);
    if (!fits(b, mode)) mode = 0;
    const three = (list, answer) => shuffled(list.filter(x => x !== answer), r).slice(0, 3);
    let answer, wrong;
    if (mode === 0 || mode === 3) { answer = b.name; wrong = three(NAMES, answer); }
    else if (mode === 1) { answer = first(b.by); wrong = three(ARCHS, answer); }
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
    // The close-up zooms into the same clear outside photo, so it is still the building you'd know.
    return { id: b.id, mode, answer, options, im: b.gamePhoto, zoom: mode === 3 ? 2.4 : 1 + Math.min(level || 0, 3) * 0.3 };
  }

  /* ---------- the day ---------- */
  const keyOf = d => d.getFullYear() + '-' + String(d.getMonth() + 1).padStart(2, '0') + '-' + String(d.getDate()).padStart(2, '0');
  function today() {
    const d = new Date(), noon = new Date(d); noon.setHours(12, 0, 0, 0);
    const no = Math.max(1, Math.round((noon - new Date(2026, 9, 13, 12)) / 864e5) + 1); // #1 was 13 Oct 2026, the day the game went live
    return { key: keyOf(d), no, label: d.getDate() + ' ' + d.toLocaleString('en', { month: 'short' }) };
  }
  function yesterdayKey() { const d = new Date(); d.setDate(d.getDate() - 1); return keyOf(d); }
  // Each building gets a score from the date and its id; the top five win. Adding buildings rarely changes a day's five.
  function dailyFive(key) {
    const picked = DAILY.map(b => ({ b, s: hash(key + '|' + b.id) })).sort((x, y) => x.s - y.s);
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

  /* ---------- shared pieces ---------- */
  const main = $('game');
  let game = null;

  function optionsHtml(q, picked) {
    return q.options.map((o, k) => {
      let cls = 'opt', mark = '';
      if (picked != null && o === q.answer) { cls += ' right'; mark = '✓'; }
      else if (picked != null && o === picked) { cls += ' wrong'; mark = '✕'; }
      else if (picked != null) cls += ' dim';
      return `<button type="button" class="${cls}" data-k="${k}"${picked != null ? ' disabled' : ''}><span>${esc(o)}</span>${mark ? `<b aria-hidden="true">${mark}</b>` : ''}</button>`;
    }).join('');
  }
  function revealHtml(q, right, verdict, nextLabel) {
    const b = byId.get(q.id);
    return `<div class="reveal ${right ? 'ok' : 'no'}">
      <span class="verdict">${esc(verdict)}</span>
      <b class="rname">${esc(b.name)}</b>
      <span class="rmeta">${esc(b.by)} · ${esc(b.place)} · ${esc(b.year)}</span>
      ${b.study ? `<p class="rstudy"><span>Key features</span>${esc(b.study)}</p>` : ''}
      <div class="ractions"><button type="button" class="go" id="next">${esc(nextLabel)}</button>
      <a class="ghost" href="../buildings/${encodeURIComponent(b.id)}/" target="_blank" rel="noopener">Open this building</a></div></div>`;
  }
  function photoBlock(q, label, answered) {
    const im = q.im || {};
    const credit = (im.credit || '').replace(/\.$/, '');
    return `<div class="photo-wrap"><div class="photo"><img id="photo" alt="Mystery building, ${esc(label)}" style="transform: scale(${answered ? 1 : q.zoom})">
      <span class="pill">${esc(label)} · ${esc(MODES[q.mode])}</span></div>
      <p class="credit">${credit ? 'Photo: ' + esc(credit) + ' · ' : ''}${esc(im.license || '')}${answered && im.source ? ` · <a href="${esc(im.source)}" target="_blank" rel="noopener">source</a>` : ''}</p></div>`;
  }
  const tileRow = (results, n, now) => Array.from({ length: n }, (_, k) => {
    const done = k < results.length;
    return `<i class="tile${done ? (results[k] ? ' hit' : ' miss') : k === now ? ' now' : ''}" style="--d:${k * 0.12}s">${done ? (results[k] ? '✓' : '✕') : ''}</i>`;
  }).join('');
  const SHARE_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M12 15V3M7 8l5-5 5 5M5 13v6a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-6"/></svg>';
  const BARS_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M5 20V12M12 20V5M19 20v-9"/></svg>';
  const PLAY_ICON = '<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 4.5v15l12.5-7.5z" fill="currentColor" stroke="none"/></svg>';
  const FLAME = '<svg class="flame" viewBox="0 0 24 24" aria-hidden="true"><path d="M12 2c1 3.5 5 5.6 5 10.2A5 5 0 0 1 12 17a5 5 0 0 1-5-4.8c0-1.9.9-3.2 2-4.2.2 1.5 1 2.5 2 2.8C10.5 8 11 4.8 12 2z"/></svg>';
  // The card people share ends with the site's small logo and address (v18 · New name, section 4, option A).
  const cardFoot = `<div class="card-foot"><span class="mini">Find great<br><span class="accent">Architecture.</span></span><span class="site">${SITE}</span></div>`;

  function confetti(host) {
    const colors = ['#DA3A26', '#15803D', '#111110', '#F2C14E', '#2D6CDF'];
    const layer = document.createElement('div'); layer.className = 'confetti'; layer.setAttribute('aria-hidden', 'true');
    for (let k = 0; k < 44; k++) {
      const s = document.createElement('i');
      s.style.cssText = `left:${Math.random() * 100}%;width:${6 + Math.random() * 6}px;height:${8 + Math.random() * 8}px;background:${colors[k % colors.length]};animation-duration:${1.8 + Math.random() * 1.6}s;animation-delay:${Math.random() * 0.6}s`;
      layer.appendChild(s);
    }
    host.appendChild(layer);
    setTimeout(() => layer.remove(), 4200);
  }
  // Count the score up from 0, so it lands with a little drama.
  function countUp(el, to) {
    if (!el) return;
    if (matchMedia('(prefers-reduced-motion: reduce)').matches) { el.textContent = to; return; }
    const t0 = performance.now(), dur = 1300;
    const step = t => { const p = Math.min(1, (t - t0) / dur), e = 1 - Math.pow(1 - p, 3); el.textContent = Math.round(to * e); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }
  function toast(text) {
    const t = $('toast'); t.textContent = text; t.hidden = false;
    clearTimeout(toast.timer); toast.timer = setTimeout(() => { t.hidden = true; }, 2400);
  }
  async function share(text) {
    const full = text + '\n' + SITE;
    try { if (navigator.share && matchMedia('(pointer: coarse)').matches) { await navigator.share({ text: full }); return; } } catch (e) { if (e && e.name === 'AbortError') return; }
    try { await navigator.clipboard.writeText(full); toast('Copied. Paste it in your group chat.'); }
    catch (e) { window.prompt('Copy your result:', full); }
  }

  /* ---------- Daily five ---------- */
  function dailyState() {
    const t = today();
    let s = store.get('da-daily', null);
    if (!s || s.day !== t.key) s = { day: t.key, i: 0, picked: null, results: [], gains: [], score: 0, streak: 0, bestCombo: 0, done: false, started: false };
    if (!s.gains) s.gains = [];
    return s;
  }
  function dailyStats() {
    const st = store.get('da-daily-stats', {});
    return Object.assign({ last: null, days: 0, maxDays: 0, best: 0, played: 0, right: 0, dist: [0, 0, 0, 0, 0, 0] }, st);
  }
  const liveDays = st => (st.last === today().key || st.last === yesterdayKey()) ? st.days : 0;

  function startDaily() {
    const t = today();
    game = { kind: 'daily', t, qs: dailyFive(t.key), s: dailyState() };
    drawDaily();
  }
  function drawDaily(justPicked) {
    const { t, qs, s } = game, st = dailyStats();
    store.set('da-daily', s);
    if (!s.started) {
      const d = liveDays(st);
      main.innerHTML = `<section class="intro">
        <div class="introtop"><span class="kicker">Daily five · #${t.no} · ${esc(t.label)}</span><span class="chip">${FLAME}${d} ${d === 1 ? 'day' : 'days'}</span></div>
        <h1>Guess the building?</h1>
        <div class="tiles big">${[1, 2, 3, 4, 5].map(k => `<i class="tile empty">${k}</i>`).join('')}</div>
        <div class="facts"><div><b>5</b>photos, four answers each</div><div><b>×2 ×3</b>right in a row scores more</div><div><b>1 a day</b>the same five for everyone</div></div>
        <button type="button" class="go big" id="begin">${PLAY_ICON}Play today's five</button>
        <p class="small centre">Kept in this browser. No sign-up.</p></section>`;
      $('begin').onclick = () => { s.started = true; drawDaily(); };
      return;
    }
    if (s.done) return drawDailyEnd();
    const q = qs[s.i], answered = s.picked != null, right = answered && s.picked === q.answer;
    const gain = s.gains[s.gains.length - 1] || 0;
    main.innerHTML = `<div class="hud">
        <div class="tiles">${tileRow(s.results, 5, s.i)}</div>
        <span class="grow"></span>
        ${s.streak >= 2 ? `<span class="combo">×${s.streak} in a row</span>` : ''}
        <span class="score"><b>${s.score}</b><small>pts</small>${justPicked && right ? `<em class="gain">+${gain}</em>` : ''}</span>
      </div>
      <section class="play">
      ${photoBlock(q, (s.i + 1) + ' / 5', answered)}
      <div class="panel">
        <h1>${esc(ASKS[q.mode])}</h1>
        <div class="opts">${optionsHtml(q, s.picked)}</div>
        ${answered ? revealHtml(q, right, right ? (s.streak >= 2 ? `Right! ×${s.streak} in a row, +${gain}` : `Right! +${gain}`) : 'Not this time. It is', s.i === 4 ? 'See my score' : 'Next building →') : ''}
      </div></section>`;
    if (justPicked) { const last = main.querySelectorAll('.hud .tile')[s.results.length - 1]; if (last) last.classList.add('flip'); }
    showPhoto($('photo'), q.im);
    if (s.i < 4) warm(qs[s.i + 1].im);
    main.querySelectorAll('.opt').forEach(btn => btn.onclick = () => {
      if (s.picked != null) return;
      const o = q.options[+btn.dataset.k], ok = o === q.answer;
      s.picked = o; s.results.push(ok);
      s.streak = ok ? s.streak + 1 : 0; s.bestCombo = Math.max(s.bestCombo || 0, s.streak);
      const g = ok ? 10 * s.streak : 0; s.gains.push(g); s.score += g;
      buzz(ok ? 20 : [40, 40, 40]);
      drawDaily(true);
    });
    const nx = $('next');
    if (nx) nx.onclick = () => {
      if (s.i < 4) { s.i++; s.picked = null; drawDaily(); window.scrollTo(0, 0); return; }
      s.done = true;
      const stt = dailyStats(), correct = s.results.filter(Boolean).length;
      if (stt.last !== t.key) {
        stt.days = stt.last === yesterdayKey() ? stt.days + 1 : 1; stt.last = t.key;
        stt.played++; stt.right += correct; stt.dist[correct]++;
        stt.maxDays = Math.max(stt.maxDays, stt.days);
      }
      stt.best = Math.max(stt.best, s.score);
      store.set('da-daily-stats', stt);
      game.celebrate = true;
      drawDaily(); window.scrollTo(0, 0);
    };
  }
  function drawDailyEnd() {
    const { t, qs, s } = game, st = dailyStats();
    const correct = s.results.filter(Boolean).length;
    const mid = new Date(); mid.setHours(24, 0, 0, 0);
    main.innerHTML = `<section class="end">
      <div class="end-main">
        <span class="kicker">Daily five #${t.no} · done</span>
        <div class="tiles big flipin">${tileRow(s.results, 5, -1)}</div>
        <b class="rank">${esc(RANKS[correct])}</b>
        <div class="total"><span id="total">${game.celebrate ? 0 : s.score}</span><small>points</small></div>
        <p class="sub">${correct} of 5 right · best run ×${s.bestCombo || 0} · ${s.score >= st.best ? 'your best yet' : 'best ' + st.best}</p>
        <div class="card-share">
          <div class="card-top"><b>Guess the building?<br>#${t.no} · ${esc(t.label)}</b><span class="chip">${FLAME}${st.days}</span></div>
          <div class="card-sq"><span class="sqs">${s.results.map(x => `<i class="sq ${x ? 'hit' : 'miss'}"></i>`).join('')}</span><b>${s.score} pts</b></div>
          ${cardFoot}
        </div>
        <div class="row2"><button type="button" class="go big" id="share">${SHARE_ICON}Share my score</button><button type="button" class="ghost big" id="stats2">${BARS_ICON}Stats</button></div>
        <div class="nextfive"><span><small>Next five in</small><b id="countdown"></b></span><a class="ghost" href="#endless">${PLAY_ICON}Play Endless</a></div>
      </div>
      <div class="recap"><h2>Explore today's five</h2>${qs.map((q, k) => recapRow(q, s.results[k])).join('')}</div></section>`;
    const sq = s.results.map(x => (x ? '🟩' : '🟥')).join('');
    $('share').onclick = () => share(`Guess the building? #${t.no}\n${sq}  ${s.score} pts  🔥${st.days}`);
    $('stats2').onclick = openStats;
    tick(mid);
    loadRecapThumbs();
    if (game.celebrate) {
      game.celebrate = false;
      countUp($('total'), s.score);
      if (correct >= 4) confetti(main);
    }
  }
  let ticker = null;
  function tick(mid) {
    clearInterval(ticker);
    const draw = () => {
      const el = $('countdown'); if (!el) return clearInterval(ticker);
      const secs = Math.max(0, Math.round((mid - new Date()) / 1000)), pad = n => String(n).padStart(2, '0');
      el.textContent = pad(Math.floor(secs / 3600)) + ':' + pad(Math.floor(secs / 60) % 60) + ':' + pad(secs % 60);
      if (!secs) { clearInterval(ticker); route(); }
    };
    draw(); ticker = setInterval(draw, 1000);
  }
  function recapRow(q, ok) {
    const b = byId.get(q.id);
    return `<a class="rrow" href="../buildings/${encodeURIComponent(b.id)}/" target="_blank" rel="noopener"><span class="bar ${ok ? 'hit' : 'miss'}"></span><span class="th"><img data-src="${esc((q.im && q.im.thumb) || b.images[0].thumb || b.images[0].src)}" alt=""></span>
      <span class="rt"><b>${esc(b.name)}</b><small>${esc(MODES[q.mode])} · ${esc(first(b.by))}</small></span><span aria-hidden="true">↗</span></a>`;
  }
  // The recap shows the answers anyway, so its thumbnails can load directly.
  const loadRecapThumbs = () => main.querySelectorAll('.recap img[data-src]').forEach(img => { img.src = abs(img.dataset.src); });

  /* ---------- stats ---------- */
  function openStats() {
    const st = dailyStats(), max = Math.max(1, ...st.dist);
    const todayRight = game && game.kind === 'daily' && game.s.done ? game.s.results.filter(Boolean).length : -1;
    const pct = st.played ? Math.round(st.right / (st.played * 5) * 100) : 0;
    $('sheetBody').innerHTML = `
      <div class="cells"><div><b>${st.played}</b><small>played</small></div><div><b>${pct}</b><small>% right</small></div>
      <div><b>${FLAME}${liveDays(st)}</b><small>day streak</small></div><div><b>${st.best}</b><small>best score</small></div></div>
      <h3>How many right, each day</h3>
      <div class="dist">${st.dist.map((n, k) => `<div><span>${k}</span><i class="${k === todayRight ? 'today' : ''}" style="width:${Math.max(7, Math.round(n / max * 100))}%">${n}</i></div>`).join('')}</div>
      <p class="small">Longest run of days: ${st.maxDays}. Counted in this browser only.</p>`;
    $('sheet').hidden = false;
    $('sheetClose').focus();
  }
  const closeStats = () => { $('sheet').hidden = true; };
  $('statsBtn').onclick = openStats;
  $('sheetClose').onclick = closeStats;
  $('sheet').addEventListener('click', e => { if (e.target === $('sheet')) closeStats(); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('sheet').hidden) closeStats(); });

  /* ---------- Endless ---------- */
  const endlessStats = () => store.get('da-endless', { best: 0, runs: 0 });
  function startEndless(go) {
    const seed = Math.floor(Math.random() * 1e9);
    const r = rng(seed), order = [].concat(...TIERS.map(([a, z]) => shuffled(ALL.slice(a, z).map((_, k) => a + k), r)));
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
        <div class="facts"><div><b>∞</b>one building after another</div><div><b>1 miss</b>and the run is over</div><div><b>×10</b>every 10 right, closer crops</div></div>
        <div class="stats"><div><small>Your best</small><b>${st.best}</b></div><div><small>Runs played</small><b>${st.runs}</b></div></div>
        <button type="button" class="go big" id="begin">${PLAY_ICON}Start a run</button>
        <p class="small centre">Your best is kept in this browser. No sign-up.</p></section>`;
      $('begin').onclick = () => { g.started = true; drawEndless(); };
      return;
    }
    if (g.over) return drawEndlessEnd();
    if (!g.q) g.q = endlessQ(g.i);
    const q = g.q, answered = g.picked != null, right = answered && g.picked === q.answer;
    const run = g.results.filter(Boolean).length;
    const label = run > st.best ? 'New best!' : run === st.best && run > 0 ? 'Equals your best' : 'Best ' + st.best;
    main.innerHTML = `<div class="hud">
        <span class="run"><b>${run}</b><small>in a row</small></span>
        <span class="trail">${g.results.slice(-24).map(x => `<i class="${x ? 'hit' : 'miss'}"></i>`).join('')}</span>
        <span class="best${run > st.best ? ' on' : ''}">${esc(label)}</span>
      </div>
      <section class="play">
      ${photoBlock(q, '#' + (g.i + 1), answered)}
      <div class="panel">
        <h1>${esc(ASKS[q.mode])}</h1>
        <div class="opts">${optionsHtml(q, g.picked)}</div>
        ${answered ? revealHtml(q, right, right ? `Right! ${run} in a row` : 'Missed. It is', right ? 'Next building →' : 'See your run') : ''}
      </div></section>`;
    showPhoto($('photo'), q.im);
    main.querySelectorAll('.opt').forEach(btn => btn.onclick = () => {
      if (g.picked != null) return;
      g.picked = q.options[+btn.dataset.k]; const ok = g.picked === q.answer; g.results.push(ok);
      buzz(ok ? 20 : [40, 40, 40]);
      if (ok) warm(endlessQ(g.i + 1).im);
      drawEndless();
    });
    const nx = $('next');
    if (nx) nx.onclick = () => {
      if (g.picked === q.answer) { g.i++; g.picked = null; g.q = null; drawEndless(); window.scrollTo(0, 0); return; }
      const s2 = endlessStats(), runN = g.results.filter(Boolean).length;
      g.newBest = runN > s2.best; s2.best = Math.max(s2.best, runN); s2.runs++;
      store.set('da-endless', s2);
      g.over = true; g.celebrate = true; drawEndless(); window.scrollTo(0, 0);
    };
  }
  function drawEndlessEnd() {
    const g = game, st = endlessStats(), run = g.results.filter(Boolean).length;
    const missed = byId.get(g.q.id);
    const qs = g.results.map((_, k) => k === g.i ? g.q : endlessQ(k)).reverse().slice(0, 8);
    const oks = g.results.slice().reverse();
    main.innerHTML = `<section class="end">
      <div class="end-main">
        ${g.newBest ? '<span class="badge"><i></i>New personal best</span>' : `<span class="kicker">Run over · best ${st.best}</span>`}
        <div class="total"><span id="total">${g.celebrate ? 0 : run}</span><small>in a row</small></div>
        <p class="sub">Missed on ${esc(missed.name)} (${esc(MODES[g.q.mode].toLowerCase())}).</p>
        <div class="card-share">
          <div class="card-top"><b>Guess the building?<br>Endless</b></div>
          <div class="card-sq"><span class="sqs wrap">${g.results.map(x => `<i class="sq small ${x ? 'hit' : 'miss'}"></i>`).join('')}</span></div>
          <div class="card-line"><b>${run} in a row</b><span>best ${st.best}</span></div>
          ${cardFoot}
        </div>
        <div class="row2"><button type="button" class="go big" id="again">${PLAY_ICON}Start again</button><button type="button" class="ghost big" id="share">${SHARE_ICON}Share</button></div>
        <p class="small"><a href="#daily">Or play today's Daily five</a></p>
      </div>
      <div class="recap"><h2>This run's buildings</h2>${qs.map((q, k) => recapRow(q, oks[k])).join('')}</div></section>`;
    $('again').onclick = () => { startEndless(true); window.scrollTo(0, 0); };
    const sq = g.results.map(x => (x ? '🟩' : '🟥')).join('');
    $('share').onclick = () => share(`Guess the building? Endless\n${sq}  ${run} in a row`);
    loadRecapThumbs();
    if (g.celebrate) { g.celebrate = false; countUp($('total'), run); if (g.newBest && run >= 5) confetti(main); }
  }

  /* ---------- which game ---------- */
  function route() {
    clearInterval(ticker);
    const endless = location.hash === '#endless';
    $('gDaily').setAttribute('aria-pressed', !endless);
    $('gEndless').setAttribute('aria-pressed', endless);
    $('statsBtn').hidden = endless;
    document.title = (endless ? 'Endless' : 'Daily five') + ' · Guess the building? · Find Great Architecture';
    if (endless) startEndless(false); else startDaily();
  }
  $('gDaily').onclick = () => { if (location.hash !== '#daily') location.hash = 'daily'; else route(); };
  $('gEndless').onclick = () => { if (location.hash !== '#endless') location.hash = 'endless'; else route(); };
  window.addEventListener('hashchange', route);
  if (!ALL.length) { main.innerHTML = '<p class="small">The buildings could not load. Try again in a moment.</p>'; return; }
  route();
})();
