/* Find Great Architecture: the wall (equal-width columns, scrolling down), photo galleries, the opened building, search, filters and Surprise me.
   Plain JavaScript, no build step. Data comes from data/buildings.js (window.BUILDINGS). */
(() => {
  'use strict';

  const LINKS = window.LINKS || {};
  const ALL = (window.BUILDINGS || []).map(b => ({ ...b, ...(LINKS[b.id] || {}) }));
  const TOTAL = ALL.length;
  // Books (data/books.js): each knows its shelf, its tags, the architects it is about and the buildings on the wall it goes with.
  // The books file is large, so it loads only when someone first opens Books or a book link; the buildings wall never waits for it.
  let BOOKS = [], SHELVES = [], booksReady = false, booksWaiting = [];
  function takeBooks() {
    BOOKS = (window.BOOKS || []).map(b => ({ ...b, kind: 'book' }));
    SHELVES = [...new Set(BOOKS.map(b => b.shelf))];
    booksReady = true;
    booksWaiting.splice(0).forEach(cb => cb());
  }
  function withBooks(cb) {
    if (booksReady) return cb();
    booksWaiting.push(cb);
    if (booksWaiting.length > 1) return;
    if (window.BOOKS) return takeBooks();
    const meta = document.querySelector('meta[name="books-data"]');
    const tag = document.createElement('script');
    tag.src = meta ? meta.content : 'data/books.js';
    tag.onload = takeBooks;
    tag.onerror = () => { booksWaiting = []; $('count').textContent = 'Books could not load'; };
    document.head.appendChild(tag);
  }
  // Shop links. Put an Amazon Associates tag here once the account is live; the disclosure line then shows itself.
  const SHOP = { amazon: 'amazon.in', tag: '' };
  // Filter groups. A building must have every chosen idea; in the other groups one match is enough.
  const GROUPS = [{ key: 'concepts', all: true }, { key: 'type' }, { key: 'movement' }, { key: 'region' }, { key: 'country' }, { key: 'arch' }];
  // Fields the filter panel uses: country code, first credited architect, and decade (0 = before 1880, 1 = 1880s … 15 = 2020s).
  const CODE_FIX = { UK: 'GB', 'Hong Kong': 'HK' };
  ALL.forEach(b => {
    const c = b.place.split(', ').pop();
    b.country = CODE_FIX[c] || c;
    b.arch = b.by.split(',')[0].trim();
    b.decade = b.y < 1880 ? 0 : Math.min(15, Math.floor((b.y - 1880) / 10) + 1);
  });

  const $ = id => document.getElementById(id);
  const cols = $('cols'), sheet = $('sheet'), card = $('card');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fold = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');

  const state = {
    q: '', seed: 11, ncols: 0, mode: 'buildings', shelf: null,
    filters: Object.fromEntries(GROUPS.map(g => [g.key, new Set()])), decades: null,
    open: null, shot: 0, seen: new Set(), lastTile: null,
    booting: true, unwinding: false
  };
  const tileShot = new Map(); // which photo each tile is showing

  /* ---------- a fresh wall on every visit ----------
     Every reload or new visit deals a new order, like a feed. The buildings that opened the wall last time move to the
     end, so a reload never lands on the same first screen. Coming back with the browser's back button keeps the
     same order and scroll position instead. Browser storage can be missing (private windows), so every use is guarded. */
  const NAV = ((performance.getEntriesByType && performance.getEntriesByType('navigation')[0]) || {}).type;
  const RETURNING = NAV === 'back_forward';
  const kept = (where, key) => { try { return window[where].getItem(key); } catch (e) { return null; } };
  const keep = (where, key, v) => { try { window[where].setItem(key, v); } catch (e) { /* ignore */ } };
  const newSeed = () => { state.seed = Math.floor(Math.random() * 1e6) + 1; keep('sessionStorage', 'da-seed', state.seed); };
  if (RETURNING && +kept('sessionStorage', 'da-seed')) state.seed = +kept('sessionStorage', 'da-seed'); else newSeed();
  let lastTop = new Set();
  if (!RETURNING) try { lastTop = new Set(JSON.parse(kept('localStorage', 'da-top') || '[]')); } catch (e) { /* ignore */ }
  window.addEventListener('pagehide', () => keep('sessionStorage', 'da-y', Math.round(window.scrollY)));

  /* ---------- layout: equal-width columns, scrolling down only ---------- */
  const MIN_COL = 240, GAP = 16;

  function rng(seed) {
    let s = seed | 0;
    return () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  function shuffled(arr, r) { const a = arr.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(r() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }
  // Height per unit of width. Kept between a wide 3:2 crop and a tall 2:3, so no tile turns into a sliver.
  function ratioOf(b) {
    if (b.kind === 'book') { const c = b.cover; return c && c.w ? Math.max(1.1, Math.min(1.75, c.h / c.w)) : 1.5; }
    const im = (b.images || [])[0];
    return im && im.w ? Math.max(2 / 3, Math.min(1.5, im.h / im.w)) : 0.75;
  }
  // Space a tile takes in its column, per unit of width: the photo or cover, plus a book's caption underneath.
  const heightOf = b => ratioOf(b) + (b.kind === 'book' ? 0.4 : 0.06);
  const keyOf = x => x.kind === 'book' ? 'book:' + x.id : x.id;
  const thumbOf = x => x.kind === 'book' ? (x.cover ? x.cover.thumb : '') : (x.images && x.images[0] ? x.images[0].thumb : '');
  const nameOf = x => x.kind === 'book' ? x.title : x.name;
  function columnCount() {
    const w = cols.clientWidth;
    return Math.max(2, Math.min(6, Math.floor((w + GAP) / (MIN_COL + GAP))));
  }

  /* ---------- filtering ---------- */
  const values = (b, key) => (Array.isArray(b[key]) ? b[key] : [b[key]]);
  // skip: leave one group out, so the filter panel can count what each of its options would add
  function matches(b, skip) {
    if (b.kind === 'book') return matchesBook(b);
    for (const g of GROUPS) {
      const set = state.filters[g.key];
      if (g.key === skip || !set.size) continue;
      const vals = values(b, g.key);
      if (g.all ? ![...set].every(v => vals.includes(v)) : !vals.some(v => set.has(v))) return false;
    }
    const d = state.decades;
    if (skip !== 'decades' && d && (b.decade < d[0] || b.decade > d[1])) return false;
    if (!state.q) return true;
    const hay = fold([b.name, b.by, b.place, b.year, b.type, b.movement, b.region, b.study, (b.concepts || []).join(' ')].join(' '));
    return state.q.split(/\s+/).every(w => hay.includes(w));
  }
  function matchesBook(b) {
    if (state.shelf && b.shelf !== state.shelf) return false;
    if (!state.q) return true;
    const hay = fold([b.title, b.by, b.year, b.shelf, b.why, (b.tags || []).join(' '), (b.architects || []).join(' ')].join(' '));
    return state.q.split(/\s+/).every(w => hay.includes(w));
  }
  const items = () => state.mode === 'books' ? BOOKS : ALL;
  const visible = () => items().filter(matches);

  /* ---------- tiles ---------- */
  const tiles = new Map();
  function tileImage(b, k) {
    const im = (b.images || [])[k];
    if (!im) return '';
    const tag = ''; // drawings stand in quietly on the wall; the note appears only once a building is opened
    return `<img src="${esc(im.thumb)}" alt="" loading="lazy" decoding="async">${tag}`;
  }
  // A book with no cover yet shows its title set in the site's own type.
  function coverHtml(b) {
    const c = b.cover;
    if (c) return `<img src="${esc(c.thumb)}" alt="" loading="lazy" decoding="async">`;
    return `<span class="standin"><span class="tt">${esc(b.title)}</span><span class="au">${esc(b.by)}</span></span>`;
  }
  function bookTileEl(b) {
    const el = document.createElement('div');
    el.className = 'bt';
    el.dataset.id = b.id;
    el.style.setProperty('--ar', ratioOf(b));
    el.innerHTML = `<button type="button" class="open" aria-label="${esc(b.title)}, ${esc(b.by)}, ${esc(b.year)}"><span class="cv">${coverHtml(b)}</span>` +
      `<span class="bcap"><b>${esc(b.title)}</b><span class="by">${esc(b.by)}</span><span class="r2">${esc(b.year)} · ${esc(b.shelf)}</span></span></button>`;
    el.querySelector('.open').addEventListener('click', () => openBook(b.id, false, el));
    return el;
  }
  function tileEl(b) {
    let el = tiles.get(keyOf(b));
    if (el) return el;
    if (b.kind === 'book') { el = bookTileEl(b); tiles.set(keyOf(b), el); return el; }
    const n = (b.images || []).length;
    const city = b.place.split(',')[0]; // the tile names the first credited architect; the full credit is in the opened view
    el = document.createElement('div');
    el.className = 't' + (n ? '' : ' empty-tile');
    el.dataset.id = b.id;
    el.style.aspectRatio = `1 / ${ratioOf(b)}`;
    el.innerHTML =
      `<button type="button" class="open" aria-label="${esc(b.name)}, ${esc(b.by)}, ${esc(b.year)}, ${esc(city)}">${tileImage(b, 0)}` +
      (n ? '' : `<span class="slot"><span class="k">No free photos yet</span></span>`) + `</button>` +
      (n > 1 ? `<button type="button" class="flip prev" aria-label="Previous photo of ${esc(b.name)}"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>` +
               `<button type="button" class="flip next" aria-label="Next photo of ${esc(b.name)}"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button>` +
               `<span class="dots">${Array.from({ length: n }, (_, k) => `<i class="${k ? '' : 'on'}"></i>`).join('')}</span>` : '') +
      `<span class="cap" aria-hidden="true"><span class="r1"><b>${esc(b.name)}</b><span class="by">${esc(b.by.split(',')[0])}</span></span>` +
      `<span class="r2">${esc(b.year)} · ${esc(city)}</span></span>`;
    el.querySelector('.open').addEventListener('click', () => openBuilding(b.id, false, el));
    el.querySelectorAll('.flip').forEach(btn => btn.addEventListener('click', e => {
      e.stopPropagation();
      flipTile(b, el, btn.classList.contains('next') ? 1 : -1);
    }));
    tiles.set(b.id, el);
    return el;
  }
  function flipTile(b, el, dir) {
    const n = b.images.length;
    const k = ((tileShot.get(b.id) || 0) + dir + n) % n;
    tileShot.set(b.id, k);
    el.querySelector('.open img').src = b.images[k].thumb;
    el.querySelectorAll('.dots i').forEach((d, j) => d.classList.toggle('on', j === k));
  }

  // Deal tiles into the shortest column, so every column ends at about the same height.
  // Tiles are added a batch at a time as the reader nears the bottom, so 1,000 buildings stay quick.
  const BATCH = 60;
  const feedState = { list: [], next: 0, heights: [], colEls: [] };
  function addBatch() {
    const f = feedState, end = Math.min(f.list.length, f.next + BATCH);
    for (; f.next < end; f.next++) {
      const b = f.list[f.next];
      const c = f.heights.indexOf(Math.min(...f.heights));
      f.colEls[c].appendChild(tileEl(b));
      f.heights[c] += heightOf(b);
    }
    $('more').hidden = f.next >= f.list.length;
  }
  function render(toTop) {
    let list = shuffled(visible(), rng(state.seed));
    if (lastTop.size) list = list.filter(b => !lastTop.has(keyOf(b))).concat(list.filter(b => lastTop.has(keyOf(b))));
    const C = columnCount();
    state.ncols = C;
    feedState.list = list; feedState.next = 0;
    feedState.heights = new Array(C).fill(0);
    feedState.colEls = Array.from({ length: C }, () => { const d = document.createElement('div'); d.className = 'col'; return d; });
    cols.style.setProperty('--n', C);
    cols.replaceChildren(...feedState.colEls);
    addBatch();
    $('empty').hidden = list.length > 0;
    const total = items().length, noun = state.mode === 'books' ? 'books' : 'buildings';
    $('allLink').dataset.tip = 'A huge, growing collection of buildings';
    $('count').textContent = list.length === total ? `${total.toLocaleString('en')} ${noun}` : `${list.length.toLocaleString('en')} of ${total.toLocaleString('en')}`;
    const nf = GROUPS.reduce((s, g) => s + state.filters[g.key].size, 0) + (state.decades ? 1 : 0);
    $('filterCount').textContent = nf ? String(nf) : '';
    renderIdeas();
    updateDock();
    if (toTop) window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  new IntersectionObserver(entries => { if (entries.some(en => en.isIntersecting)) addBatch(); }, { rootMargin: '1200px 0px' }).observe($('more'));
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { if (columnCount() !== state.ncols) render(false); }, 120);
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { if (!sheet.hidden) closeBuilding(); else toggleFilters(false); return; }
    if (!sheet.hidden) {
      // Arrow keys step through the wall; photos change with the arrows on the photo.
      if (e.key === 'ArrowLeft') stepBuilding(-1);
      if (e.key === 'ArrowRight') stepBuilding(1);
    }
  });

  /* ---------- opened building ---------- */
  const q = s => encodeURIComponent(s);
  const byOf = b => b.by.split(',').map(s => s.trim());
  const firstArchitect = b => byOf(b)[0];
  // Same type first by shared ideas, then a stable shuffle so each building gets a different few.
  const mix = (b, x) => ((x.n * 13 + b.n * 7) % 17) / 100;
  const sharedIdeas = (b, x) => (x.concepts || []).filter(c => (b.concepts || []).includes(c)).length;
  const byArchitect = b => ALL.filter(x => x.id !== b.id && byOf(x).includes(firstArchitect(b)));
  const sameType = b => ALL.filter(x => x.id !== b.id && x.type === b.type)
    .sort((x, y) => sharedIdeas(b, y) + mix(b, y) - sharedIdeas(b, x) - mix(b, x));

  /* ---------- who built it, and where ---------- */
  const ARCH = window.ARCHITECTS || { people: {}, buildings: {} };
  const WORLD = window.WORLD || null;
  const countryOf = b => b.country;
  const countryName = code => (WORLD && WORLD.names[code]) || code;
  function initials(name) {
    const words = name.split(/\s+/).filter(w => /\p{L}/u.test(w));
    if (words.length < 2) return (words[0] || '?').slice(0, 3).toUpperCase();
    return (words[0][0] + words[words.length - 1][0]).toUpperCase();
  }
  function portraitOf(b) {
    for (const qid of ARCH.buildings[b.id] || []) { const p = ARCH.people[qid]; if (p && p.thumb) return p; }
    return null;
  }
  // Pritzker Prize winners (data/pritzker.js, from the prize's own jury citations): a small gold medal on the portrait.
  // keys are the names a winner goes by on the wall (portrait names, by-line names, the firm); the medal follows the
  // face shown, else the first architect named.
  const LAUREATE = new Map();
  (window.PRITZKER || []).forEach(w => (w.keys || []).forEach(k => LAUREATE.set(fold(k), w)));
  const laureateOf = (p, who) => (p && LAUREATE.get(fold(p.name))) || (who && LAUREATE.get(fold(who))) || null;
  let medals = 0;
  const coin = id => `<svg viewBox="0 0 48 48" aria-hidden="true"><defs><radialGradient id="${id}" cx="36%" cy="30%" r="80%"><stop offset="0" stop-color="#FCEBB0"/><stop offset=".5" stop-color="#D9AE45"/><stop offset="1" stop-color="#9A7322"/></radialGradient></defs>` +
    `<circle cx="24" cy="24" r="23.5" fill="#fff"/><circle cx="24" cy="24" r="21.5" fill="url(#${id})" stroke="#7E5D17"/><circle cx="24" cy="24" r="17" fill="none" stroke="#8A671B" stroke-dasharray="1 1.5"/>` +
    `<text x="24" y="31.2" text-anchor="middle" font-family="'Big Shoulders Display', Impact, sans-serif" font-weight="900" font-size="20" fill="#5E4410">P</text></svg>`;
  function medalHtml(w, who, n) {
    const id = 'medal' + (++medals), title = `Pritzker Prize ${w.year}`;
    return `<button type="button" class="medal" aria-label="${title}" aria-expanded="false" aria-controls="${id}">${coin(id + 'a')}</button>` +
      `<div class="medal-card" id="${id}" role="dialog" aria-label="${title}" hidden><b class="mc-title">${coin(id + 'b')}${title}</b>` +
      (w.line ? `<p>“${esc(w.line)}”</p>` : '') +
      `<span class="mc-links">${n > 1 ? `<button type="button" data-arch="${esc(who)}">See all ${n} buildings →</button>` : '<span></span>'}` +
      `${w.url ? `<a href="${esc(w.url)}" target="_blank" rel="noopener">Jury citation ↗</a>` : ''}</span></div>`;
  }
  function bylineHtml(b) {
    const who = firstArchitect(b), p = portraitOf(b), n = byArchitect(b).length + 1;
    const face = p ? `<img class="face" src="${esc(p.thumb)}" alt="${esc(p.name)}">` : `<span class="face initials" aria-hidden="true">${esc(initials(who))}</span>`;
    const text = `<span class="by-text"><i>by</i><b${b.by.length > 28 || b.by.split(/[\s-]/).some(w => w.length > 10) ? ' class="long"' : ''}>${esc(b.by)}</b>${n > 1 ? `<span class="see">See all ${n} buildings →</span>` : ''}</span>`;
    const credit = p ? `<p class="face-credit">Portrait: ${p.credit ? esc(p.credit) + ' · ' : ''}${esc(p.license)}${p.source ? ` · <a href="${esc(p.source)}" target="_blank" rel="noopener">source</a>` : ''}</p>` : '';
    const w = laureateOf(p, who);
    const link = n > 1 ? `<button type="button" class="by-link" data-arch="${esc(who)}">${face}${text}</button>` : `<div class="by-link">${face}${text}</div>`;
    return `<div class="by-row">${link}${w ? medalHtml(w, who, n) : ''}</div>` + credit;
  }
  // Natural Earth projection, the same as tools/make_world.py; coords are [lat, lon].
  function project(lat, lon) {
    const [x0, s, y0, top, bottom] = WORLD.proj;
    const p = Math.max(bottom, Math.min(top, lat)) * Math.PI / 180, l = lon * Math.PI / 180, p2 = p * p, p4 = p2 * p2;
    const x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)));
    const y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)));
    return [(x - x0) * s, (y0 - y) * s];
  }
  let worldLand = '';
  function mapHtml(b) {
    const code = countryOf(b), name = countryName(code);
    if (!WORLD) return '';
    worldLand = worldLand || Object.values(WORLD.paths).join('');
    const here = WORLD.paths[code] || '';
    const pt = b.coords ? project(b.coords[0], b.coords[1]) : WORLD.centre[code];
    const c = pt || [WORLD.w / 2, WORLD.h / 2];
    const box = WORLD.box[code] || [c[0], c[1], c[0], c[1]]; // countries too small to draw: just their point
    // Frame the country with its neighbours around it: at least a sixth of the world wide, the whole world for the biggest.
    const ratio = WORLD.h / WORLD.w;
    const vw = box[2] - box[0] < WORLD.w / 2 ? Math.min(WORLD.w, Math.max(170, (box[2] - box[0]) * 2.4, (box[3] - box[1]) * 2.4 / ratio)) : WORLD.w;
    const vh = vw * ratio;
    const cx = vw < WORLD.w ? (box[0] + box[2]) / 2 : c[0], cy = vw < WORLD.w ? (box[1] + box[3]) / 2 : c[1];
    const vx = Math.max(0, Math.min(WORLD.w - vw, cx - vw / 2)), vy = Math.max(0, Math.min(WORLD.h - vh, cy - vh / 2));
    const u = vw / 190; // map units per screen pixel
    const tiny = (box[2] - box[0]) / u < 6; // still too small to see: ring it
    const at = pt ? `cx="${pt[0].toFixed(1)}" cy="${pt[1].toFixed(1)}"` : '';
    return `<svg viewBox="${vx.toFixed(1)} ${vy.toFixed(1)} ${vw.toFixed(1)} ${vh.toFixed(1)}" role="img" aria-label="World map with ${esc(name)} marked"><path class="land" d="${worldLand}"/>` +
      (here ? `<path class="here" d="${here}"/>` : '') +
      (pt && tiny ? `<circle class="ring" ${at} r="${(8 * u).toFixed(1)}"/>` : '') +
      (pt && b.coords ? `<circle class="pin" ${at} r="${(3.5 * u).toFixed(1)}"/>` : '') +
      `</svg><span class="where-name">${esc(name)}</span>`;
  }
  function mapUrl(b) {
    if (b.coords) { const [la, lo] = b.coords; return `https://www.openstreetmap.org/?mlat=${la}&mlon=${lo}#map=16/${la}/${lo}`; }
    return 'https://www.openstreetmap.org/search?query=' + q(b.name + ', ' + b.place.split(',')[0] + ', ' + countryName(countryOf(b)));
  }
  const relHtml = list => list.map(x => `<button type="button" data-id="${esc(x.id)}"><span class="ph">${x.images && x.images[0] ? `<img src="${esc(x.images[0].thumb)}" alt="" loading="lazy">` : ''}</span>${esc(x.name)}<small>${esc(x.year)} · ${esc(x.place.split(',')[0])}</small></button>`).join('');

  function showShot(k) {
    const b = state.open; if (!b || b.kind === 'book') return;
    const ims = b.images || [];
    const stage = $('stage');
    if (!ims.length) {
      stage.innerHTML = `<div class="slot"><span class="k">No free photos yet</span><span class="h">${esc(b.name)}</span><span class="s">See photos and drawings through the links →</span></div>`;
      $('gCap').innerHTML = ''; $('strip').innerHTML = '';
      stage.classList.remove('drawing');
      $('gPrev').hidden = $('gNext').hidden = true;
      return;
    }
    k = (k + ims.length) % ims.length;
    state.shot = k;
    const im = ims[k];
    // Show the small thumbnail at once, then swap in the full photo (often from Wikimedia) when it arrives.
    const drawing = im.kind === 'Drawing';
    stage.innerHTML = `<img src="${esc(im.thumb)}" alt="${esc(b.name)}: ${esc(drawing ? 'drawing' : im.caption)}">` +
      (drawing ? '<span class="nophoto">Photos unavailable</span>' : '');
    stage.classList.toggle('drawing', drawing);
    const full = new Image();
    full.onload = () => { const img = stage.querySelector('img'); if (img && img.getAttribute('src') === im.thumb) img.src = im.src; };
    full.src = im.src;
    const credit = (im.credit || '').replace(/\.$/, '');
    $('gCap').innerHTML = `<span class="c">${k + 1}/${ims.length}${drawing ? '' : ' · ' + esc(im.caption)}</span>` +
      `<span class="l">${credit ? (im.kind === 'Drawing' ? '' : 'Photo: ') + esc(credit) + ' · ' : ''}${esc(im.license)}${im.source ? ` · <a href="${esc(im.source)}" target="_blank" rel="noopener">source</a>` : ''}</span>`;
    $('strip').querySelectorAll('button').forEach((t, j) => t.setAttribute('aria-current', j === k));
    $('gPrev').hidden = $('gNext').hidden = ims.length < 2;
  }

  // Verified pages found by tools/find_links.py come first; the core sites fall back to their top search result.
  const CORE = [['Projects & drawings', 'ArchDaily', 'archdaily.com'], ['Plans & sections', 'WikiArquitectura', 'wikiarquitectura.com'], ['News & features', 'Dezeen', 'dezeen.com']];
  function linksFor(b) {
    const name = b.name, city = b.place.split(',')[0], found = b.links || [];
    const lucky = (domain) => 'https://duckduckgo.com/?q=' + q('\\ site:' + domain + ' ' + name + ' ' + b.by);
    const out = found.map((l) => [l.kind, l.site, l.url, true]);
    for (const [k, n, domain] of CORE) if (!found.some((l) => l.site === n)) out.push([k, n, lucky(domain), false]);
    out.push(['Read', 'Wikipedia', b.wiki || 'https://en.wikipedia.org/w/index.php?search=' + q(name + ' ' + city), !!b.wiki]);
    out.push(['Watch', 'YouTube', 'https://www.youtube.com/results?search_query=' + q(name + ' ' + b.by + ' architecture'), true]);
    out.push(['More photos', 'Wikimedia Commons', b.commons ? 'https://commons.wikimedia.org/wiki/' + q(b.commons.replace(/ /g, '_')) : 'https://commons.wikimedia.org/w/index.php?search=' + q(name), true]);
    return out;
  }

  /* Each building opened in a row is a step in the browser's history, so the phone's back gesture and the dock's
     Back arrow both walk back through them, and going back from the first one closes it. A step remembers its
     building, whether it was a surprise, how many steps came before it in this run (step) and the one before (prev). */
  const here = () => (history.state && history.state.da ? history.state : null);
  function remember(key, surprise, wasOpen) {
    const cur = wasOpen ? here() : null;
    const made = !here() && location.hash === '#' + key; // the browser already made this entry (the address was typed or linked)
    const entry = cur ? { da: true, id: key, surprise: !!surprise, step: cur.step + 1, prev: cur.id, pushed: cur.pushed }
                      : { da: true, id: key, surprise: !!surprise, step: 0, prev: null, pushed: !state.booting };
    try {
      if (state.booting || made) history.replaceState(entry, '', '#' + key);
      else history.pushState(entry, '', '#' + key);
    } catch (e) { /* some embedded frames forbid it */ }
  }

  function openBuilding(id, surprise, fromEl, fromHistory) {
    const b = ALL.find(x => x.id === id);
    if (!b) return;
    if (!fromHistory && !(state.open && state.open === b)) remember(b.id, surprise, !sheet.hidden);
    state.open = b; state.seen.add(b.id);
    state.lastTile = fromEl || tiles.get(b.id) || null;
    card.classList.remove('book');
    $('where').hidden = false; $('pageLink').hidden = false; $('shopNote').hidden = true;
    $('linksTitle').textContent = 'Go deeper';
    $('chipsHint').textContent = 'Each opens every building that shares the idea.';

    $('strip').innerHTML = (b.images || []).map((im, k) =>
      `<button type="button" data-k="${k}" aria-label="Photo ${k + 1}: ${esc(im.caption)}"><img src="${esc(im.thumb)}" alt=""></button>`).join('');
    showShot(tileShot.get(b.id) || 0);

    const kick = $('bKicker');
    kick.textContent = surprise ? 'You came looking for nothing. You found:' : `${b.type} · ${b.movement}`;
    kick.classList.toggle('surprise', !!surprise);
    $('bName').textContent = b.name;
    const city = b.place.split(',')[0], country = countryName(countryOf(b));
    $('byline').innerHTML = bylineHtml(b);
    $('where').innerHTML = mapHtml(b);
    $('where').href = mapUrl(b);
    $('where').setAttribute('aria-label', `Open map: ${city === country ? city : city + ', ' + country}`);
    $('bMeta').innerHTML = `${esc(city === country ? city : city + ', ' + country)} · ${esc(b.year)} · <a href="${esc(mapUrl(b))}" target="_blank" rel="noopener">Open map ↗</a>`;
    $('bStudy').innerHTML = `<span>Key features</span>${esc(b.study)}`;
    $('pageLink').href = 'buildings/' + b.id + '/';
    $('bChips').innerHTML = (b.concepts || []).map(c => `<button type="button" class="chip" data-g="concepts" data-v="${esc(c)}">${esc(c)} <span class="n">→</span></button>`).join('') +
      `<button type="button" class="chip quiet" data-g="type" data-v="${esc(b.type)}">${esc(b.type)} <span class="n">→</span></button>`;

    $('links').innerHTML = linksFor(b).map(([k, n, u, direct]) =>
      `<a href="${esc(u)}" target="_blank" rel="noopener"${direct ? '' : ' class="guess" title="Opens the top search result on this site"'}><span>${esc(k)}</span>${esc(n)} ↗</a>`).join('');

    const mine = byArchitect(b), kin = sameType(b);
    $('byArch').hidden = !mine.length;
    $('byArchTitle').textContent = 'More by ' + firstArchitect(b);
    $('byArchAll').textContent = `All ${mine.length + 1} →`;
    $('byArchAll').dataset.arch = firstArchitect(b);
    $('byArchRel').innerHTML = relHtml(mine.slice(0, 4));
    $('relBooks').hidden = true;
    withBooks(() => { if (state.open === b) showRelatedBooks(b); });
    $('sameType').hidden = !kin.length;
    $('sameTypeTitle').textContent = 'More · ' + b.type;
    $('sameTypeAll').textContent = `All ${kin.length + 1} →`;
    $('sameTypeAll').dataset.type = b.type;
    $('sameTypeRel').innerHTML = relHtml(kin.slice(0, 4));

    if (!sheet.hidden) { card.classList.remove('swap'); void card.offsetWidth; card.classList.add('swap'); } // a quick fade when one building replaces another
    sheet.hidden = false;
    document.body.classList.add('locked');
    updateDock();
    card.querySelector('.info').scrollTop = 0;
    card.focus({ preventScroll: true });
    updateStep();
  }

  /* ---------- related books in the opened building ---------- */
  // Books about this building first, then books about its architect, then a few general books on its movement.
  const MOVEMENT_BOOKS = 4, RELATED_MAX = 12;
  const BROAD = new Set(['Contemporary', 'Modernism', 'Late modernism']);
  const PLACE_TAGS = {
    India: (b, cc) => cc === 'IN', Japan: (b, cc) => cc === 'JP', China: (b, cc) => cc === 'CN',
    'Latin America': (b, cc) => b.region === 'Americas' && !['US', 'CA'].includes(cc),
    Africa: b => b.region === 'Africa', 'Southeast Asia': b => b.region === 'Southeast Asia'
  };
  function relatedBooks(b) {
    const out = [], add = k => { if (!out.includes(k)) out.push(k); };
    BOOKS.filter(k => (k.buildings || []).includes(b.id)).forEach(add);
    const names = byOf(b);
    BOOKS.filter(k => (k.architects || []).some(a => names.includes(a))).sort((x, y) => x.y - y.y).forEach(add);
    const words = new Set([b.type, ...(b.concepts || [])].map(fold));
    const shared = k => (k.tags || []).filter(t => words.has(fold(t))).length;
    // Movement books are general ones (surveys, theory); a monograph on another architect isn't related. A book about a
    // place only suits buildings there, and the broad movements also need a shared idea or type.
    const cc = countryOf(b), inPlace = t => !(t in PLACE_TAGS) || PLACE_TAGS[t](b, cc);
    BOOKS.filter(k => (k.tags || []).includes(b.movement) && !(k.architects || []).length && !out.includes(k)
        && (k.tags || []).every(inPlace) && (!BROAD.has(b.movement) || shared(k) > 0))
      .sort((x, y) => shared(y) - shared(x) || x.y - y.y)
      .slice(0, MOVEMENT_BOOKS).forEach(add);
    return out.slice(0, RELATED_MAX);
  }
  function showRelatedBooks(b) {
    const list = relatedBooks(b), row = $('relBooksRow');
    $('relBooks').hidden = !list.length;
    row.innerHTML = list.map(k => `<button type="button" data-book="${esc(k.id)}"><span class="cv">${coverHtml(k)}</span><b>${esc(k.title)}</b><small>${esc(k.year)}</small></button>`).join('');
    row.scrollLeft = 0;
    $('relBooksNav').hidden = list.length <= 6; // with six or fewer everything nearly fits: no arrows
    updateBookArrows();
  }
  function updateBookArrows() {
    const row = $('relBooksRow');
    $('relBooksPrev').disabled = row.scrollLeft <= 2;
    $('relBooksNext').disabled = row.scrollLeft + row.clientWidth >= row.scrollWidth - 2;
  }

  /* ---------- opened book ---------- */
  // Each book also knows the architects it is about and the buildings it names (architects[], buildings[] in data/books.js),
  // so the opened building can point to its books later. That page is not built yet.
  const relBooksHtml = list => list.map(k => `<button type="button" data-book="${esc(k.id)}"><span class="ph">${coverHtml(k)}</span>${esc(k.title)}<small>${esc(k.by)} · ${esc(k.year)}</small></button>`).join('');
  function portraitByName(name) {
    for (const p of Object.values(ARCH.people)) if (p.thumb && p.name === name) return p;
    return null;
  }
  function bylineBookHtml(k) {
    const who = (k.architects || [])[0], p = who ? portraitByName(who) : null;
    const n = who ? ALL.filter(x => byOf(x).includes(who)).length : 0;
    const face = p ? `<img class="face" src="${esc(p.thumb)}" alt="${esc(p.name)}">` : '';
    const text = `<span class="by-text"><i>by</i><b>${esc(k.by)}</b>${n ? `<span class="see">${esc(who)} on the wall: ${n} building${n > 1 ? 's' : ''} →</span>` : ''}</span>`;
    const credit = p ? `<p class="face-credit">Portrait: ${p.credit ? esc(p.credit) + ' · ' : ''}${esc(p.license)}${p.source ? ` · <a href="${esc(p.source)}" target="_blank" rel="noopener">source</a>` : ''}</p>` : '';
    const w = p ? laureateOf(p, who) : null;
    const link = n ? `<button type="button" class="by-link" data-arch="${esc(who)}">${face}${text}</button>` : `<div class="by-link">${face}${text}</div>`;
    return `<div class="by-row">${link}${w ? medalHtml(w, who, n) : ''}</div>` + credit;
  }
  function bookLinks(k) {
    const a = k.by.split(/,| and |\(/)[0].trim(), s = q(k.title + ' ' + a);
    return [
      ['Buy', 'Amazon', `https://www.${SHOP.amazon}/s?k=${s}&i=stripbooks${SHOP.tag ? '&tag=' + SHOP.tag : ''}`],
      ['Buy', 'Bookshop.org', `https://bookshop.org/search?keywords=${s}`],
      ['Borrow or read', 'Open Library', k.ol ? `https://openlibrary.org/works/${k.ol}` : `https://openlibrary.org/search?q=${s}`],
      ['Find in a library', 'WorldCat', `https://search.worldcat.org/search?q=${s}`],
      ['Preview', 'Google Books', `https://www.google.com/search?tbm=bks&q=${s}`]
    ];
  }
  function showCover(k) {
    const stage = $('stage'), c = k.cover;
    stage.innerHTML = c ? `<img src="${esc(c.thumb)}" alt="Cover of ${esc(k.title)}">` : coverHtml(k);
    if (c) { // the small thumbnail at once, then the full cover from Open Library when it arrives
      const full = new Image();
      full.onload = () => { const img = stage.querySelector('img'); if (img && img.getAttribute('src') === c.thumb) img.src = c.src; };
      full.src = c.src;
    }
    $('gCap').innerHTML = c ? `<span class="c">Cover</span><span class="l">From Open Library · <a href="${esc(c.source)}" target="_blank" rel="noopener">source</a></span>` : `<span class="l">No cover found yet</span>`;
    $('strip').innerHTML = '';
    $('gPrev').hidden = $('gNext').hidden = true;
  }
  // Buildings a book goes with: the ones it names, then everything on the wall by the architects it is about.
  function buildingsOf(k) {
    const out = (k.buildings || []).map(id => ALL.find(x => x.id === id)).filter(Boolean);
    for (const a of k.architects || []) for (const x of ALL) if (byOf(x).includes(a) && !out.includes(x)) out.push(x);
    return out;
  }
  const sameShelf = k => BOOKS.filter(x => x !== k && x.shelf === k.shelf)
    .sort((x, y) => (y.tags || []).filter(t => (k.tags || []).includes(t)).length - (x.tags || []).filter(t => (k.tags || []).includes(t)).length || x.y - y.y);

  function openBook(id, surprise, fromEl, fromHistory) {
    const k = BOOKS.find(x => x.id === id);
    if (!k) return;
    if (!fromHistory && !(state.open && state.open === k)) remember(keyOf(k), surprise, !sheet.hidden);
    state.open = k; state.seen.add(keyOf(k));
    state.lastTile = fromEl || tiles.get(keyOf(k)) || null;
    card.classList.add('book');
    showCover(k);
    const kick = $('bKicker');
    kick.textContent = surprise ? 'You came looking for nothing. You found:' : [k.shelf, (k.tags || [])[0]].filter(Boolean).join(' · ');
    kick.classList.toggle('surprise', !!surprise);
    $('bName').textContent = k.title;
    $('byline').innerHTML = bylineBookHtml(k);
    $('where').hidden = true;
    $('bMeta').innerHTML = `First published ${esc(k.year)}${k.isbn ? ` · ISBN ${esc(k.isbn)}` : ''}`;
    $('bStudy').innerHTML = `<span>Why read it</span>${esc(k.why)}`;
    $('pageLink').hidden = true;
    $('linksTitle').textContent = 'Get it';
    $('links').innerHTML = bookLinks(k).map(([kind, n, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener"><span>${esc(kind)}</span>${esc(n)} ↗</a>`).join('');
    $('shopNote').hidden = !SHOP.tag;
    const built = buildingsOf(k), who = (k.architects || [])[0];
    $('byArch').hidden = !built.length;
    $('byArchTitle').textContent = who ? `On the wall · by ${who}` : 'On the wall';
    $('byArchAll').hidden = !who;
    $('byArchAll').textContent = `All ${built.length} →`;
    $('byArchAll').dataset.arch = who || '';
    $('byArchRel').innerHTML = relHtml(built.slice(0, 4));
    const kin = sameShelf(k);
    $('relBooks').hidden = true;
    $('sameType').hidden = !kin.length;
    $('sameTypeTitle').textContent = 'More on this shelf · ' + k.shelf;
    $('sameTypeAll').textContent = `All ${kin.length + 1} →`;
    $('sameTypeAll').dataset.type = '';
    $('sameTypeAll').dataset.shelf = k.shelf;
    $('sameTypeRel').innerHTML = relBooksHtml(kin.slice(0, 3));
    $('bChips').innerHTML = `<button type="button" class="chip" data-shelf="${esc(k.shelf)}">${esc(k.shelf)} <span class="n">→</span></button>` +
      (k.tags || []).map(t => `<button type="button" class="chip quiet" data-tag="${esc(t)}">${esc(t)} <span class="n">→</span></button>`).join('');
    $('chipsHint').textContent = 'The shelf opens the books wall; each tag searches it.';

    if (!sheet.hidden) { card.classList.remove('swap'); void card.offsetWidth; card.classList.add('swap'); }
    sheet.hidden = false;
    document.body.classList.add('locked');
    updateDock();
    card.querySelector('.info').scrollTop = 0;
    card.focus({ preventScroll: true });
    updateStep();
  }
  // A step in the history, a hash or a tile key names either a building or a book ("book:<id>").
  const findAny = key => key && key.startsWith('book:') ? BOOKS.find(x => x.id === key.slice(5)) : ALL.find(x => x.id === key);
  function openAny(key, surprise, fromHistory) {
    if (key && key.startsWith('book:')) withBooks(() => { if (state.mode !== 'books') setMode('books'); openBook(key.slice(5), surprise, null, fromHistory); });
    else openBuilding(key, surprise, null, fromHistory);
  }

  // Previous and next follow the wall's own order, after filters and search.
  function updateStep() {
    const list = feedState.list, i = state.open ? list.indexOf(state.open) : -1;
    $('step').hidden = i < 0 || list.length < 2;
    if (i < 0) return;
    const noun = state.mode === 'books' ? 'book' : 'building';
    const fill = (btn, x, label) => {
      btn.disabled = !x;
      btn.setAttribute('aria-label', x ? `${label} ${noun}: ${nameOf(x)}` : `No ${label.toLowerCase()} ${noun}`);
      const img = btn.querySelector('img'), src = x ? thumbOf(x) : '';
      img.src = src; img.style.visibility = src ? '' : 'hidden';
      btn.querySelector('b').textContent = x ? nameOf(x) : (label === 'Next' ? 'End of the list' : 'Start of the list');
    };
    fill($('sPrev'), list[i - 1], 'Previous');
    fill($('sNext'), list[i + 1], 'Next');
    $('sPos').textContent = ''; // no totals on the site
  }
  function stepBuilding(dir) {
    const f = feedState, i = state.open ? f.list.indexOf(state.open) : -1, b = f.list[i + dir];
    if (i < 0 || !b) return;
    while (i + dir >= f.next) addBatch(); // keep the wall in step, so closing lands on this tile
    state.stepped = true;
    openAny(keyOf(b));
  }

  const dropHash = () => { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ } };
  function hideSheet() {
    sheet.hidden = true;
    document.body.classList.remove('locked');
    state.open = null;
    updateDock();
    if (state.lastTile && state.lastTile.isConnected) {
      if (state.stepped) state.lastTile.scrollIntoView({ block: 'center' });
      state.lastTile.querySelector('.open').focus({ preventScroll: true });
    }
    state.stepped = false;
  }
  // Closing (×, Escape, Home…) also rewinds the steps this run added, so the phone's back gesture afterwards leaves the wall
  // rather than reopening buildings.
  function closeBuilding() {
    hideSheet();
    const h = here(), n = h ? h.step + (h.pushed ? 1 : 0) : 0;
    if (n) { state.unwinding = true; history.go(-n); } else dropHash();
  }
  window.addEventListener('popstate', e => {
    if (state.unwinding) { state.unwinding = false; if (location.hash) dropHash(); return; }
    const h = e.state && e.state.da ? e.state : null;
    if (h) openAny(h.id, h.surprise, true);
    else if (!sheet.hidden) hideSheet();
  });

  $('veil').addEventListener('click', closeBuilding);
  $('close').addEventListener('click', closeBuilding);
  $('sPrev').addEventListener('click', () => stepBuilding(-1));
  $('sNext').addEventListener('click', () => stepBuilding(1));
  $('gPrev').addEventListener('click', () => showShot(state.shot - 1));
  $('gNext').addEventListener('click', () => showShot(state.shot + 1));
  $('strip').addEventListener('click', e => { const t = e.target.closest('button[data-k]'); if (t) showShot(+t.dataset.k); });
  // swipe between photos on touch screens
  let swipeX = null;
  $('stage').addEventListener('pointerdown', e => { swipeX = e.clientX; });
  $('stage').addEventListener('pointerup', e => { if (swipeX != null && Math.abs(e.clientX - swipeX) > 40) showShot(state.shot + (e.clientX < swipeX ? 1 : -1)); swipeX = null; });
  const BOOK_STEP = 3 * 84; // three covers (72px wide + 12px gap) per press
  $('relBooksPrev').addEventListener('click', () => $('relBooksRow').scrollBy({ left: -BOOK_STEP, behavior: 'smooth' }));
  $('relBooksNext').addEventListener('click', () => $('relBooksRow').scrollBy({ left: BOOK_STEP, behavior: 'smooth' }));
  $('relBooksRow').addEventListener('scroll', updateBookArrows, { passive: true });
  ['byArchRel', 'sameTypeRel', 'relBooksRow'].forEach(id => $(id).addEventListener('click', e => {
    const t = e.target.closest('button[data-id], button[data-book]'); if (!t) return;
    if (t.dataset.book) openBook(t.dataset.book); else openBuilding(t.dataset.id);
  }));
  // "See all" for an architect searches the wall for their name; "All" for a typology filters by it.
  function showOnWall(arch, type) {
    setMode('buildings', true);
    GROUPS.forEach(g => state.filters[g.key].clear()); state.decades = null;
    if (type) state.filters.type.add(type);
    $('q').value = arch || ''; state.q = fold(arch || '');
    closeBuilding(); refreshFilters(); render(true);
  }
  // The books wall, searched for a word or narrowed to one shelf.
  function showBooks(text, shelf) {
    setMode('books', true);
    state.shelf = shelf || null;
    $('q').value = text || ''; state.q = fold(text || '');
    closeBuilding(); render(true);
  }
  $('byline').addEventListener('click', e => { const t = e.target.closest('button[data-arch]'); if (t) showOnWall(t.dataset.arch); });
  // The Pritzker medal: tap (or Enter) opens and closes its card; on a computer pointing at it opens it too.
  function medalOpen(m, open) {
    const card = m && document.getElementById(m.getAttribute('aria-controls'));
    if (!card) return;
    m.setAttribute('aria-expanded', open);
    card.hidden = !open;
  }
  let medalTimer = 0;
  $('byline').addEventListener('click', e => {
    const m = e.target.closest('.medal');
    if (m) medalOpen(m, m.getAttribute('aria-expanded') !== 'true');
  });
  $('byline').addEventListener('pointerover', e => {
    const m = e.target.closest('.medal, .medal-card'), row = m && m.closest('.by-row');
    if (!m || e.pointerType !== 'mouse') return;
    clearTimeout(medalTimer);
    medalOpen(row.querySelector('.medal'), true);
  });
  $('byline').addEventListener('pointerout', e => {
    const m = e.target.closest('.medal, .medal-card'), row = m && m.closest('.by-row');
    if (!m || e.pointerType !== 'mouse' || (e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('.medal, .medal-card') && row.contains(e.relatedTarget))) return;
    medalTimer = setTimeout(() => medalOpen(row.querySelector('.medal'), false), 200);
  });
  document.addEventListener('click', e => { if (!e.target.closest('.by-row')) document.querySelectorAll('.medal[aria-expanded="true"]').forEach(m => medalOpen(m, false)); });
  document.addEventListener('keydown', e => {
    const m = document.querySelector('.medal[aria-expanded="true"]');
    if (e.key === 'Escape' && m) { e.stopPropagation(); medalOpen(m, false); m.focus(); }
  }, true);
  $('byArchAll').addEventListener('click', e => showOnWall(e.currentTarget.dataset.arch));
  $('sameTypeAll').addEventListener('click', e => { const d = e.currentTarget.dataset; if (d.shelf) showBooks('', d.shelf); else showOnWall('', d.type); });
  $('bChips').addEventListener('click', e => {
    const t = e.target.closest('.chip'); if (!t) return;
    if (t.dataset.shelf) return showBooks('', t.dataset.shelf);
    if (t.dataset.tag) return showBooks(t.dataset.tag);
    GROUPS.forEach(g => state.filters[g.key].clear()); state.decades = null;
    state.filters[t.dataset.g].add(t.dataset.v);
    state.q = ''; $('q').value = '';
    closeBuilding(); refreshFilters(); render(true);
  });

  /* ---------- search, ideas bar, filters, dock ---------- */
  let qTimer;
  $('q').addEventListener('input', e => {
    clearTimeout(qTimer);
    qTimer = setTimeout(() => { state.q = fold(e.target.value.trim()); render(true); }, 160);
  });

  const counts = key => {
    const c = new Map();
    ALL.forEach(b => values(b, key).forEach(v => c.set(v, (c.get(v) || 0) + 1)));
    return c;
  };
  function renderIdeas() {
    if (state.mode === 'books') {
      const n = new Map(); BOOKS.forEach(b => n.set(b.shelf, (n.get(b.shelf) || 0) + 1));
      $('ideasList').innerHTML = `<span class="lead">Shelves</span>` + SHELVES.map(v =>
        `<button type="button" class="idea" aria-pressed="${state.shelf === v}" data-shelf="${esc(v)}">${esc(v)} <small>${n.get(v)}</small></button>`).join('');
      return;
    }
    const c = counts('concepts');
    const top = [...c.entries()].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).map(([v]) => v);
    const on = state.filters.concepts;
    $('ideasList').innerHTML = `<span class="lead">Browse by idea</span>` + top.map(v =>
      `<button type="button" class="idea" aria-pressed="${on.has(v)}" data-v="${esc(v)}">${esc(v)}</button>`).join('');
  }
  $('ideas').addEventListener('click', e => {
    const t = e.target.closest('.idea'); if (!t) return;
    if (t.dataset.shelf) { state.shelf = state.shelf === t.dataset.shelf ? null : t.dataset.shelf; render(true); return; }
    const set = state.filters.concepts, v = t.dataset.v;
    const only = set.size === 1 && set.has(v);
    set.clear();
    if (!only) set.add(v);
    refreshFilters(); render(true);
  });

  // The filter panel itself lives in filter.js; it reads and changes state.filters and state.decades.
  const refreshFilters = () => { if (window.DAFilter) window.DAFilter.refresh(); };
  function toggleFilters(force) {
    const open = force == null ? $('filters').hidden : force;
    $('filters').hidden = !open;
    $('filterBtn').setAttribute('aria-expanded', open);
    document.body.classList.toggle('filtering', open);
    if (open) refreshFilters();
  }
  $('filterBtn').addEventListener('click', () => toggleFilters());
  // Buildings or Books: the same bar, search and dock work on whichever wall is on.
  function setMode(mode, quiet) {
    if (state.mode === mode) return;
    if (mode === 'books' && !booksReady) { $('count').textContent = 'Loading books…'; return withBooks(() => setMode(mode, quiet)); }
    state.mode = mode;
    const books = mode === 'books';
    $('modeBuildings').setAttribute('aria-pressed', !books);
    $('modeBooks').setAttribute('aria-pressed', books);
    $('q').placeholder = books ? 'Search a book, author or subject…' : 'Search a building, architect, city or idea…';
    $('filterBtn').hidden = books;
    $('allLink').hidden = books;
    toggleFilters(false);
    if (!quiet) render(true);
  }
  // Top panel A: the switch stays in the top bar; on a phone it sits on the bar's second row, beside Guess the building?.
  $('q').closest('.bar-mid').prepend(document.querySelector('.mode'));

  // Guess the building? opens a small menu with the two games.
  const playMenu = (open) => { $('playMenu').hidden = !open; $('playBtn').setAttribute('aria-expanded', open); };
  $('playBtn').addEventListener('click', e => { e.stopPropagation(); playMenu($('playMenu').hidden); });
  document.addEventListener('click', e => { if (!$('playMenu').hidden && !e.target.closest('#play')) playMenu(false); });
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('playMenu').hidden) { playMenu(false); $('playBtn').focus(); } });

  // The ideas row slides away while you scroll down and comes back as soon as you scroll up.
  let lastY = window.scrollY, ticking = false;
  window.addEventListener('scroll', () => {
    if (ticking) return; ticking = true;
    requestAnimationFrame(() => {
      const y = window.scrollY, d = y - lastY;
      if (Math.abs(d) > 6) { document.body.classList.toggle('ideas-away', d > 0 && y > 140); lastY = y; }
      if (y < 140) document.body.classList.remove('ideas-away');
      ticking = false;
    });
  }, { passive: true });
  $('modeBuildings').addEventListener('click', () => setMode('buildings'));
  $('modeBooks').addEventListener('click', () => setMode('books'));
  function clearAll() {
    GROUPS.forEach(g => state.filters[g.key].clear()); state.decades = null; state.shelf = null;
    state.q = ''; $('q').value = '';
    refreshFilters(); render(true);
  }
  $('emptyClear').addEventListener('click', clearAll);
  $('home').addEventListener('click', e => { e.preventDefault(); toggleFilters(false); setMode('buildings', true); clearAll(); });

  // The dock stays on top of everything. On the plain wall it offers Shuffle; anywhere else (an opened building,
  // a filtered or searched wall) Shuffle becomes Home. Surprise me works everywhere, even over an opened building.
  const atHome = () => sheet.hidden && !state.q && !state.shelf && !state.decades && GROUPS.every(g => !state.filters[g.key].size);
  function updateDock() {
    const home = atHome();
    $('shuffle').hidden = !home;
    $('goHome').hidden = home;
    const h = here(), prev = !sheet.hidden && h && h.step > 0 ? findAny(h.prev) : null;
    $('goBack').hidden = !prev;
    if (prev) { $('goBack').title = 'Back to ' + nameOf(prev); $('goBack').setAttribute('aria-label', 'Back to ' + nameOf(prev)); }
  }
  $('goBack').addEventListener('click', () => history.back());
  $('shuffle').addEventListener('click', () => { newSeed(); render(true); });
  $('goHome').addEventListener('click', () => {
    if (!sheet.hidden) closeBuilding();
    toggleFilters(false); clearAll();
  });
  function surprise() {
    const list = visible();
    const pool = list.filter(b => !state.seen.has(keyOf(b)) && b !== state.open);
    const from = pool.length ? pool : list.filter(b => b !== state.open);
    if (from.length) openAny(keyOf(from[Math.floor(Math.random() * from.length)]), true);
  }
  $('surprise').addEventListener('click', surprise);

  /* ---------- start ---------- */
  window.DA = { ALL, get BOOKS() { return BOOKS; }, withBooks, state, GROUPS, matches, esc, fold, countryName, project, world: WORLD,
    apply: () => render(false), close: () => { toggleFilters(false); window.scrollTo({ top: 0, behavior: 'smooth' }); } };
  render(false);
  if (RETURNING) { // back where we were: deal enough of the wall to reach the old scroll position
    const y = +kept('sessionStorage', 'da-y') || 0;
    while (document.documentElement.scrollHeight < y + innerHeight && feedState.next < feedState.list.length) addBatch();
    window.scrollTo(0, y);
  } else {
    try { history.scrollRestoration = 'manual'; } catch (e) { /* ignore */ }
    window.scrollTo(0, 0);
    keep('localStorage', 'da-top', JSON.stringify(feedState.list.slice(0, 40).map(keyOf)));
  }
  const openFromHash = () => {
    if (here() || state.unwinding) return; // moving through our own steps is handled by popstate
    const id = decodeURIComponent(location.hash.slice(1));
    if (id === 'surprise') surprise(); // Surprise me on a building page or the A–Z list lands here
    else if (id === 'books') { if (state.mode !== 'books') setMode('books'); dropHash(); } // a link straight to the books wall
    else if (id && (!state.open || keyOf(state.open) !== id)) openAny(id);
  };
  window.addEventListener('hashchange', openFromHash);
  const h0 = here(); // a reload, or coming back from another page, keeps the step we were on
  if (h0) openAny(h0.id, h0.surprise, true); else openFromHash();
  state.booting = false;
})();
