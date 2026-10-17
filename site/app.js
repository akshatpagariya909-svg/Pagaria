/* Find Great Architecture: the wall (equal-width columns, scrolling down), photo galleries, the opened building, search, filters and Surprise me.
   Plain JavaScript, no build step. Data comes from data/wall.js (window.BUILDINGS: one line per building, first photo only); a building's
   full photo list and links load from data/detail/<id>.json when it is opened. Both are made by tools/build_pages.py. */
(() => {
  'use strict';

  const ALL = window.BUILDINGS || [];
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
  const NAMES = window.NAMES || { list: by => by.split(',').map(s => s.trim()), canon: s => s };
  const GROUPS = [{ key: 'concepts', all: true }, { key: 'type' }, { key: 'movement' }, { key: 'region' }, { key: 'country' }, { key: 'arch' }];
  // Fields the filter panel uses: country code, every credited architect (one name each, from data/names.js), and decade (0 = before 1880, 1 = 1880s … 15 = 2020s).
  const CODE_FIX = { UK: 'GB', 'Hong Kong': 'HK' };
  ALL.forEach(b => {
    const c = b.place.split(', ').pop();
    b.country = CODE_FIX[c] || c;
    b.arch = NAMES.list(b.by);
    b.decade = b.y < 1880 ? 0 : Math.min(15, Math.floor((b.y - 1880) / 10) + 1);
  });

  const $ = id => document.getElementById(id);
  // The wall holds only each building's first photo. The rest (every photo, the links, the Commons category) is one
  // small file per building, fetched the first time it is needed and merged into the building.
  const detailReq = new Map();
  function loadDetail(b) {
    if (b.kind === 'book' || b.full) return Promise.resolve(b);
    let p = detailReq.get(b.id);
    if (!p) {
      p = fetch(`data/detail/${b.id}.json?v=${window.WALL_V || ''}`).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
        .then(d => { Object.assign(b, d); b.full = true; return b; })
        .catch(e => { detailReq.delete(b.id); throw e; });
      detailReq.set(b.id, p);
    }
    return p;
  }
  const photoCount = b => b.ni != null ? b.ni : (b.images || []).length;
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
  const SWIPE = new Set(window.SWIPE || []); // tiles that get photo dots, see dotsHtml
  const heightOf = b => ratioOf(b) + (b.kind === 'book' ? 0.4 : 0.06) + (SWIPE.has(b.id) ? 0.08 : 0);
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
    el.querySelector('.open').addEventListener('click', () => openBook(b.id, false, el, false, null));
    return el;
  }
  function tileEl(b) {
    let el = tiles.get(keyOf(b));
    if (el) return el;
    if (b.kind === 'book') { el = bookTileEl(b); tiles.set(keyOf(b), el); return el; }
    const n = photoCount(b);
    const city = b.place.split(',')[0]; // the tile names the first credited architect; the full credit is in the opened view
    const swipe = n > 1 && SWIPE.has(b.id); // only these get photo dots
    el = document.createElement('div');
    el.className = 't' + (n ? '' : ' empty-tile') + (swipe ? ' sw' : '') + (n > 1 ? ' sx' : '');
    el.dataset.id = b.id;
    el.style.aspectRatio = `1 / ${ratioOf(b)}`;
    el.innerHTML =
      `<button type="button" class="open" aria-label="${esc(b.name)}, ${esc(b.by)}, ${esc(b.year)}, ${esc(city)}">${tileImage(b, 0)}` +
      (n ? '' : `<span class="slot"><span class="k">No free photos yet</span></span>`) + `</button>` +
      (n > 1 ? `<button type="button" class="flip prev" aria-label="Previous photo of ${esc(b.name)}"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>` +
               `<button type="button" class="flip next" aria-label="Next photo of ${esc(b.name)}"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button>` +
               (swipe ? dotsHtml(n, 0) : '') : '') +
      `<span class="cap" aria-hidden="true"><span class="r1"><b>${esc(b.name)}</b><span class="by">${esc(b.by.split(',')[0])}</span></span>` +
      `<span class="r2">${esc(b.year)} · ${esc(city)}</span></span>`;
    el.querySelector('.open').addEventListener('click', () => { if (!swiped) openBuilding(b.id, false, el); swiped = false; });
    el.addEventListener('pointerenter', () => { loadDetail(b).catch(() => {}); }, { once: true }); // a finger or pointer arriving is a good sign it will open
    if (n > 1) { // on every tile with more than one photo the photo follows a sideways drag, then slides on to the next one;
      // a short drag springs back, up and down still scroll, and a tap still opens the building
      let x0 = null, y0 = 0, t0 = 0, dx = 0, sideways = false;
      const photo = () => el.querySelector('.open img:not(.peek)');
      const settle = () => {
        const i = photo(), p = el.querySelector('.open img.peek'), w = el.clientWidth;
        if (i) { i.style.transition = 'transform .2s ease-out'; i.style.transform = ''; }
        if (p) { p.style.transition = 'transform .2s ease-out'; p.style.transform = `translateX(${+p.dataset.dir * w}px)`; setTimeout(() => p.remove(), 220); }
      };
      el.addEventListener('pointerdown', e => { x0 = e.clientX; y0 = e.clientY; t0 = performance.now(); dx = 0; sideways = false; });
      el.addEventListener('pointermove', e => {
        if (x0 == null) return;
        dx = e.clientX - x0;
        if (!sideways && Math.abs(dx) > 8 && Math.abs(dx) > Math.abs(e.clientY - y0)) sideways = true;
        const i = photo();
        if (!sideways || !i) return;
        i.style.transition = 'none'; i.style.transform = `translateX(${dx}px)`;
        if (b.full) { // the neighbouring photo comes in with the finger, so there is never a gap
          const dir = dx < 0 ? 1 : -1, p = peekOf(b, el, dir);
          p.style.transition = 'none'; p.style.transform = `translateX(${dir * el.clientWidth + dx}px)`;
        }
      });
      el.addEventListener('pointerup', () => {
        if (x0 == null) return;
        x0 = null;
        if (!sideways) return;
        swiped = true; setTimeout(() => { swiped = false; }, 400);
        const flick = Math.abs(dx) > 25 && performance.now() - t0 < 250;
        if (flick || Math.abs(dx) > Math.min(70, el.clientWidth * .3)) slideTile(b, el, dx < 0 ? 1 : -1); else settle();
      });
      el.addEventListener('pointercancel', () => { x0 = null; settle(); });
    }
    el.querySelectorAll('.flip').forEach(btn => btn.addEventListener('click', e => {
      e.stopPropagation();
      slideTile(b, el, btn.classList.contains('next') ? 1 : -1);
    }));
    tiles.set(b.id, el);
    return el;
  }
  // Photo dots under the tile, only for buildings worth swiping through (data/swipe.js): sunset red for the photo
  // showing, light red for the rest. Past six photos the last dot shrinks, to say "and more".
  const MAXD = 6;
  let swiped = false;
  function dotsHtml(n, k) {
    const shown = Math.min(n, MAXD), at = Math.min(k, shown - 1);
    return `<span class="dots" aria-hidden="true">${Array.from({ length: shown }, (_, j) =>
      `<i class="${j === at ? 'on' : ''}${n > MAXD && j === shown - 1 && at < shown - 1 ? ' sm' : ''}"></i>`).join('')}</span>`;
  }
  // The next photo on a tile: the current one slides out the way it was pushed, the next slides in behind it.
  const stillMotion = matchMedia('(prefers-reduced-motion: reduce)');
  const shotAfter = (b, dir) => { const n = b.images.length; return ((tileShot.get(b.id) || 0) + dir + n) % n; };
  function peekOf(b, el, dir) { // the neighbouring photo, waiting just outside the frame on that side
    const open = el.querySelector('.open'), k = shotAfter(b, dir);
    let p = open.querySelector('img.peek');
    if (!p) { p = document.createElement('img'); p.className = 'peek'; p.alt = ''; p.decoding = 'async'; open.appendChild(p); }
    if (p.dataset.k !== String(k)) { p.src = b.images[k].thumb; p.dataset.k = k; }
    p.dataset.dir = dir;
    return p;
  }
  function slideTile(b, el, dir) {
    const img = el.querySelector('.open img:not(.peek)'), w = el.clientWidth;
    if (!img) return;
    (b.full ? Promise.resolve() : loadDetail(b)).then(() => {
      const k = shotAfter(b, dir), p = peekOf(b, el, dir);
      if (stillMotion.matches) { showTile(b, el, k); p.remove(); return; }
      const off = parseFloat((img.style.transform.match(/-?[\d.]+/) || [0])[0]) || 0; // where a drag left it
      p.style.transition = 'none'; p.style.transform = `translateX(${dir * w + off}px)`;
      p.getBoundingClientRect(); // start from there
      img.style.transition = p.style.transition = 'transform .25s ease-out';
      img.style.transform = `translateX(${-dir * w}px)`; p.style.transform = 'translateX(0)';
      setTimeout(() => {
        showTile(b, el, k); // the same picture, already loaded, takes the peek's place
        img.style.transition = 'none'; img.style.transform = '';
        const done = () => p.remove();
        if (img.complete) requestAnimationFrame(done); else { img.addEventListener('load', done, { once: true }); setTimeout(done, 800); }
      }, 260);
    }, () => { img.style.transition = 'transform .2s ease-out'; img.style.transform = ''; });
  }
  function showTile(b, el, k) {
    tileShot.set(b.id, k);
    el.querySelector('.open img:not(.peek)').src = b.images[k].thumb;
    const dots = el.querySelector('.dots');
    if (dots) dots.outerHTML = dotsHtml(b.images.length, k);
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
    document.dispatchEvent(new CustomEvent('da:render')); // the map (map.js) follows the same search and filters
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
    const atTable = state.mode === 'books' && !state.q && !state.shelf;
    $('table').hidden = !atTable;
    if (atTable) drawTable();
    $('empty').hidden = list.length > 0;
    const total = items().length, noun = state.mode === 'books' ? 'books' : 'buildings';
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
  const byOf = b => b.arch;
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
  (window.PRITZKER || []).forEach(w => (w.keys || []).forEach(k => { LAUREATE.set(fold(k), w); LAUREATE.set(fold(NAMES.canon(k)), w); }));
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
  // The portrait's credit sits small at the very bottom of the sheet, not under the byline.
  const portraitCredit = p => p ? `Portrait: ${p.credit ? esc(p.credit) + ' · ' : ''}${esc(p.license)}${p.source ? ` · <a href="${esc(p.source)}" target="_blank" rel="noopener">source</a>` : ''}` : '';
  function bylineHtml(b) {
    const who = firstArchitect(b), p = portraitOf(b), n = byArchitect(b).length + 1;
    const face = p ? `<img class="face" src="${esc(p.thumb)}" alt="${esc(p.name)}">` : `<span class="face initials" aria-hidden="true">${esc(initials(who))}</span>`;
    const text = `<span class="by-text"><i>by</i><b${b.by.length > 28 || b.by.split(/[\s-]/).some(w => w.length > 10) ? ' class="long"' : ''}>${esc(b.by)}</b>${n > 1 ? `<span class="see">See all ${n} buildings →</span>` : ''}</span>`;
    const w = laureateOf(p, who);
    const link = n > 1 ? `<button type="button" class="by-link" data-arch="${esc(who)}">${face}${text}</button>` : `<div class="by-link">${face}${text}</div>`;
    return `<div class="by-row">${link}${w ? medalHtml(w, who, n) : ''}</div>`;
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
      `</svg><span class="where-name">${esc(placeName(b))} ↗</span>`;
  }
  const placeName = b => { const city = b.place.split(',')[0], country = countryName(countryOf(b)); return city === country ? city : city + ', ' + country; };
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
    const total = photoCount(b);
    k = (k + total) % total;
    if (!ims[k]) k = 0; // the other photos are still loading
    state.shot = k;
    const im = ims[k];
    // Show the small thumbnail at once, then swap in the full photo (often from Wikimedia) when it arrives.
    const drawing = im.kind === 'Drawing';
    stage.innerHTML = `<img src="${esc(im.thumb)}" alt="${esc(b.name)}: ${esc(drawing ? 'drawing' : im.caption)}">` +
      (drawing ? '<span class="nophoto">Photos unavailable</span>' : '');
    stage.classList.toggle('drawing', drawing);
    if (im.src) { // the wall's own copy has only the thumbnail; the full photo is known once the details have arrived
      const full = new Image();
      full.onload = () => { const img = stage.querySelector('img'); if (img && img.getAttribute('src') === im.thumb) img.src = im.src; };
      full.src = im.src;
    }
    const credit = (im.credit || '').replace(/\.$/, '');
    $('gCap').innerHTML = `<span class="c">${k + 1}/${total}${drawing ? '' : ' · ' + esc(im.caption)}</span>` +
      `<span class="l">${credit ? (im.kind === 'Drawing' ? '' : 'Photo: ') + esc(credit) + ' · ' : ''}${esc(im.license)}${im.source ? ` · <a href="${esc(im.source)}" target="_blank" rel="noopener">source</a>` : ''}</span>`;
    $('strip').querySelectorAll('button').forEach((t, j) => t.setAttribute('aria-current', j === k));
    $('gPrev').hidden = $('gNext').hidden = total < 2;
  }

  // Verified pages found by tools/find_links.py come first; the core sites fall back to their top search result.
  // Go deeper (v14 · A): each site's own icon, cut out and printed in ink so it turns red with its cell.
  // Each site's own logo (images/logos/c): in its colours where they read on white and on black, else in a mid grey,
  // so the logos stay visible when a phone or browser turns the page dark.
  const LOGOS = { ArchDaily: 'archdaily.png', WikiArquitectura: 'wikiarquitectura.svg', Dezeen: 'dezeen.png', Divisare: 'divisare.png', archINFORM: 'archinform.png', Wikipedia: 'wikipedia.png', YouTube: 'youtube.png', 'Wikimedia Commons': 'commons.png', Map: 'openstreetmap.png' };
  const logoOf = n => n === 'Official website' ? '<svg class="lg" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.8 5.8 3.8 9s-1.2 6.2-3.8 9c-2.6-2.8-3.8-5.8-3.8-9S9.4 5.8 12 3z"/></svg>'
    : LOGOS[n] ? `<img class="lg" src="images/logos/c/${LOGOS[n]}" alt="" aria-hidden="true">` : '';
  // Without a verified page on one of these sites, the link opens that site's own search for the building.
  const CORE = [['Projects & drawings', 'ArchDaily', 'https://www.archdaily.com/search/projects?q='], ['Plans & sections', 'WikiArquitectura', 'https://en.wikiarquitectura.com/?s='], ['News & features', 'Dezeen', 'https://www.dezeen.com/?s=']];
  function linksFor(b) {
    const name = b.name, city = b.place.split(',')[0], found = b.links || [];
    const out = found.map((l) => [l.kind, l.site, l.url, true]);
    for (const [k, n, search] of CORE) if (!found.some((l) => l.site === n)) out.push([k, n, search + q(name), false]);
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

  const linksHtml = b => linksFor(b).map(([k, n, u, direct]) =>
    `<a href="${esc(u)}" target="_blank" rel="noopener"${direct ? '' : ' class="guess" title="Searches this site for the building"'}><b class="lt"><span>${esc(k)}</span>${esc(n)} ↗</b>${logoOf(n)}</a>`).join('');
  const stripHtml = b => (b.images || []).map((im, k) =>
    `<button type="button" data-k="${k}" aria-label="Photo ${k + 1}: ${esc(im.caption)}"><img src="${esc(im.thumb)}" alt=""></button>`).join('');
  // The opened building shows at once from what the wall already has; its other photos and its links join in when they arrive.
  function fillDetail(b) {
    if (state.open !== b) return;
    $('strip').innerHTML = stripHtml(b);
    $('links').innerHTML = linksHtml(b);
    showShot(state.shot); // same thumbnail, now with its full photo, credit and licence
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

    $('strip').innerHTML = stripHtml(b);
    showShot(tileShot.get(b.id) || 0);

    const kick = $('bKicker');
    kick.textContent = `${b.type} · ${b.movement}`;
    $('bName').textContent = b.name;
    const city = b.place.split(',')[0], country = countryName(countryOf(b));
    $('byline').innerHTML = bylineHtml(b);
    $('bCredits').innerHTML = portraitCredit(portraitOf(b));
    $('where').innerHTML = mapHtml(b);
    $('where').href = mapUrl(b);
    $('where').setAttribute('aria-label', `Open map: ${city === country ? city : city + ', ' + country}`);
    $('bMeta').textContent = b.year;
    $('bStudy').innerHTML = `<span>Key features</span>${esc(b.study)}`;
    $('pageLink').href = 'buildings/' + b.id + '/';
    $('bChips').innerHTML = (b.concepts || []).map(c => `<button type="button" class="chip" data-g="concepts" data-v="${esc(c)}">${esc(c)} <span class="n">→</span></button>`).join('') +
      `<button type="button" class="chip quiet" data-g="type" data-v="${esc(b.type)}">${esc(b.type)} <span class="n">→</span></button>`;

    $('links').innerHTML = b.full ? linksHtml(b) : '';

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
    if (!b.full) loadDetail(b).then(() => fillDetail(b), () => { if (state.open === b) $('links').innerHTML = linksHtml(b); });
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
    BOOKS.filter(k => (k.architects || []).some(a => names.includes(NAMES.canon(a)))).sort((x, y) => x.y - y.y).forEach(add);
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
    const n = who ? ALL.filter(x => byOf(x).includes(NAMES.canon(who))).length : 0;
    const face = p ? `<img class="face" src="${esc(p.thumb)}" alt="${esc(p.name)}">` : '';
    const text = `<span class="by-text"><i>by</i><b>${esc(k.by)}</b>${n ? `<span class="see">${esc(who)} on the wall: ${n} building${n > 1 ? 's' : ''} →</span>` : ''}</span>`;
    const w = p ? laureateOf(p, who) : null;
    const link = n ? `<button type="button" class="by-link" data-arch="${esc(who)}">${face}${text}</button>` : `<div class="by-link">${face}${text}</div>`;
    return `<div class="by-row">${link}${w ? medalHtml(w, who, n) : ''}</div>`;
  }
  function bookLinks(k) {
    const a = k.by.split(/,| and |\(/)[0].trim(), s = q(k.title + ' ' + a);
    return [ // two ways to get it: one to buy, one to borrow (the owner's choice, Oct 2026)
      ['Buy', 'Amazon', `https://www.${SHOP.amazon}/s?k=${s}&i=stripbooks${SHOP.tag ? '&tag=' + SHOP.tag : ''}`],
      ['Borrow or read', 'Open Library', k.ol ? `https://openlibrary.org/works/${k.ol}` : `https://openlibrary.org/search?q=${s}`]
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
    for (const a of (k.architects || []).map(NAMES.canon)) for (const x of ALL) if (byOf(x).includes(a) && !out.includes(x)) out.push(x);
    return out;
  }
  const sameShelf = k => BOOKS.filter(x => x !== k && x.shelf === k.shelf)
    .sort((x, y) => (y.tags || []).filter(t => (k.tags || []).includes(t)).length - (x.tags || []).filter(t => (k.tags || []).includes(t)).length || x.y - y.y);

  // list: what the previous and next arrows step through (a category or today's five); null for the wall's own order.
  function openBook(id, surprise, fromEl, fromHistory, list) {
    const k = BOOKS.find(x => x.id === id);
    if (!k) return;
    if (list !== undefined) state.stepList = list;
    if (!fromHistory && !(state.open && state.open === k)) remember(keyOf(k), surprise, !sheet.hidden);
    state.open = k; state.seen.add(keyOf(k));
    // stepping through a list on the table: closing returns to that book on the table, not to its tile on the wall
    const onTable = state.stepList && state.stepList.includes(k) && !$('table').hidden ? $('table').querySelector(`button[data-book="${CSS.escape(k.id)}"]`) : null;
    state.lastTile = fromEl || onTable || tiles.get(keyOf(k)) || null;
    card.classList.add('book');
    showCover(k);
    const kick = $('bKicker');
    kick.textContent = [k.shelf, (k.tags || [])[0]].filter(Boolean).join(' · ');
    $('bName').textContent = k.title;
    $('byline').innerHTML = bylineBookHtml(k);
    $('bCredits').innerHTML = portraitCredit((k.architects || [])[0] ? portraitByName(k.architects[0]) : null);
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
  const stepList = () => state.stepList && state.stepList.includes(state.open) ? state.stepList : feedState.list;
  function updateStep() {
    const list = stepList(), i = state.open ? list.indexOf(state.open) : -1;
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
    const f = feedState, list = stepList(), i = state.open ? list.indexOf(state.open) : -1, b = list[i + dir];
    if (i < 0 || !b) return;
    if (list === f.list) while (i + dir >= f.next) addBatch(); // keep the wall in step, so closing lands on this tile
    state.stepped = true;
    openAny(keyOf(b));
  }

  const dropHash = () => { try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ } };
  function hideSheet() {
    sheet.hidden = true;
    document.body.classList.remove('locked');
    state.open = null; state.stepList = null;
    updateDock();
    if (state.lastTile && state.lastTile.isConnected) {
      if (state.stepped) state.lastTile.scrollIntoView({ block: 'center' });
      (state.lastTile.querySelector('.open') || state.lastTile).focus({ preventScroll: true });
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
  // Moving between photos needs the full list, so a very early press waits for it.
  const shotBy = d => { const b = state.open; if (b && b.kind !== 'book' && !b.full) loadDetail(b).then(() => showShot(state.shot + d), () => {}); else showShot(state.shot + d); };
  $('gPrev').addEventListener('click', () => shotBy(-1));
  $('gNext').addEventListener('click', () => shotBy(1));
  $('strip').addEventListener('click', e => { const t = e.target.closest('button[data-k]'); if (t) showShot(+t.dataset.k); });
  // swipe between photos on touch screens
  let swipeX = null;
  $('stage').addEventListener('pointerdown', e => { swipeX = e.clientX; });
  $('stage').addEventListener('pointerup', e => { if (swipeX != null && Math.abs(e.clientX - swipeX) > 40) shotBy(e.clientX < swipeX ? 1 : -1); swipeX = null; });
  const BOOK_STEP = 3 * 84; // three covers (72px wide + 12px gap) per press
  $('relBooksPrev').addEventListener('click', () => $('relBooksRow').scrollBy({ left: -BOOK_STEP, behavior: 'smooth' }));
  $('relBooksNext').addEventListener('click', () => $('relBooksRow').scrollBy({ left: BOOK_STEP, behavior: 'smooth' }));
  $('relBooksRow').addEventListener('scroll', updateBookArrows, { passive: true });
  ['byArchRel', 'sameTypeRel', 'relBooksRow'].forEach(id => $(id).addEventListener('click', e => {
    const t = e.target.closest('button[data-id], button[data-book]'); if (!t) return;
    if (t.dataset.book) openBook(t.dataset.book); else openBuilding(t.dataset.id);
  }));
  // "See all" for an architect chooses them in the Architect filter, so the filter panel can still swap or add architects
  // (a name no building credits falls back to a search); "All" for a typology filters by it.
  function showOnWall(arch, type) {
    // An architect with a page of their own (data/arch_pages.js, tools/architect_pages.py) is shown there, not as a filter.
    const page = arch && !type && window.ARCH_PAGES ? window.ARCH_PAGES[NAMES.canon(arch)] : '';
    if (page) { location.href = 'architects/' + page + '/'; return; }
    setMode('buildings', true);
    GROUPS.forEach(g => state.filters[g.key].clear()); state.decades = null;
    if (type) state.filters.type.add(type);
    if (arch) arch = NAMES.canon(arch);
    const known = arch && ALL.some(b => b.arch.includes(arch));
    if (known) state.filters.arch.add(arch);
    const text = known ? '' : arch || '';
    $('q').value = text; state.q = fold(text);
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
  // Every medal on the page (opened building or book, the filter's architect cards) shares this: the same card,
  // opened by a tap or Enter, and on a computer by pointing at it. A card is kept inside the screen.
  function medalOpen(m, open) {
    const card = m && document.getElementById(m.getAttribute('aria-controls'));
    if (!card) return;
    if (open) document.querySelectorAll('.medal[aria-expanded="true"]').forEach(o => { if (o !== m) medalOpen(o, false); });
    m.setAttribute('aria-expanded', open);
    card.hidden = !open;
    card.style.transform = '';
    if (open) {
      const r = card.getBoundingClientRect(), dx = Math.min(0, innerWidth - 8 - r.right) + Math.max(0, 8 - r.left);
      if (dx) card.style.transform = `translateX(${dx}px)`;
    }
  }
  let medalTimer = 0;
  document.addEventListener('click', e => {
    const m = e.target.closest('.by-row .medal');
    if (m) medalOpen(m, m.getAttribute('aria-expanded') !== 'true');
  });
  document.addEventListener('pointerover', e => {
    const m = e.target.closest('.medal, .medal-card'), row = m && m.closest('.by-row');
    if (!m || !row || e.pointerType !== 'mouse') return;
    clearTimeout(medalTimer);
    medalOpen(row.querySelector('.medal'), true);
  });
  document.addEventListener('pointerout', e => {
    const m = e.target.closest('.medal, .medal-card'), row = m && m.closest('.by-row');
    if (!m || !row || e.pointerType !== 'mouse' || (e.relatedTarget && e.relatedTarget.closest && e.relatedTarget.closest('.medal, .medal-card') && row.contains(e.relatedTarget))) return;
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

  /* ---------- Books: the front table (design v18 · 05 and 06) ---------- */
  // The Books home: five featured books a day, each with a line in its own words (data/book_lines.js), then six
  // categories that open into two rows of covers. A book can sit in more than one category. Searching or choosing a
  // shelf skips the table and shows the wall. A book opened here steps through the list it was opened from.
  const CATEGORIES = [
    { name: 'Start here', blurb: 'The first books most people are handed, in the order to read them.', keep: true,
      has: k => k.shelf === 'Essentials' },
    { name: 'Theory & manifestos', blurb: 'The arguments, and the replies to them.',
      has: (k, t) => k.shelf === 'Theory' || k.shelf === 'Manifestos' || t.has('Theory') || t.has('Criticism') },
    { name: 'Monographs', blurb: 'One architect at a time, with the drawings.', has: k => k.shelf === 'Monographs' },
    { name: 'History & cities', blurb: 'How we got here, and how cities actually work.',
      has: (k, t) => k.shelf === 'History' || k.shelf === 'Cities' || t.has('History') || t.has('Cities') || t.has('Survey') },
    { name: 'Drawing & construction', blurb: 'Books that are mostly drawings, and how things are put together.',
      has: (k, t) => k.shelf === 'Drawing' || k.shelf === 'Construction' || ['Drawing', 'Construction', 'Structure', 'Details'].some(x => t.has(x)) },
    { name: 'Free to read', blurb: 'Out of copyright and online in full.', has: k => k.shelf === 'Free to read' }
  ];
  const table = { built: false, five: [], feat: 0, open: 0, lists: [] };
  function todaysFive() {
    const lines = window.BOOK_LINES || {}, pool = BOOKS.filter(k => lines[k.id]), d = new Date();
    return shuffled(pool, rng(d.getFullYear() * 10000 + (d.getMonth() + 1) * 100 + d.getDate())).slice(0, 5);
  }
  const lineSize = s => s.length <= 18 ? 'l1' : s.length <= 40 ? 'l2' : s.length <= 72 ? 'l3' : 'l4';
  const coverOnly = k => `<span class="cv">${coverHtml(k)}</span>`;
  function drawFeatured() {
    const five = table.five, i = table.feat, k = five[i], el = $('feat');
    if (!k) { el.hidden = true; return; }
    const ln = (window.BOOK_LINES || {})[k.id];
    el.hidden = false;
    el.style.setProperty('--fbg', ln.bg || '#E7DFCF');
    el.classList.toggle('dark', !!ln.dark);
    const arrow = (d, label, path) => `<button type="button" data-feat="${d}" aria-label="${label}"><svg viewBox="0 0 24 24" aria-hidden="true"><path d="${path}"/></svg></button>`;
    el.innerHTML =
      `<div class="feat-top"><span class="k">Today’s featured · ${i + 1} of ${five.length}</span>` +
      `<span class="feat-nav">${arrow(-1, 'Previous featured book', 'M15 5l-7 7 7 7')}${arrow(1, 'Next featured book', 'M9 5l7 7-7 7')}</span></div>` +
      `<div class="feat-body"><button type="button" class="feat-main" data-book="${esc(k.id)}" data-list="feat">` +
      `${coverOnly(k)}<span class="line ${lineSize(ln.line)}">“${esc(ln.line)}”</span>` +
      `<span class="foot"><b>${esc(k.title)}</b><span class="m">${esc([k.by, k.year, k.shelf].join(' · '))}</span>` +
      (k.why ? `<span class="why">${esc(k.why)}</span>` : '') + `<span class="go">Open the book →</span></span></button>` +
      `<div class="also"><span class="k">Also on the table today</span><div class="also-row">` +
      five.map((x, j) => j === i ? '' : `<button type="button" data-pick="${j}" aria-label="${esc(x.title)}, ${esc(x.by)}">${coverOnly(x)}<b>${esc(x.title)}</b></button>`).join('') +
      `</div></div></div>`;
  }
  function drawCats() {
    table.lists = CATEGORIES.map(c => {
      const list = BOOKS.filter(k => c.has(k, new Set(k.tags || [])));
      return c.keep ? list : list.filter(k => k.cover).concat(list.filter(k => !k.cover)); // covers first, so a row opens on pictures
    });
    $('cats').innerHTML = CATEGORIES.map((c, j) => table.lists[j].length ? `<div class="cat">` +
      `<button type="button" class="cat-h" id="catH${j}" aria-expanded="false" aria-controls="catB${j}" data-cat="${j}">` +
      `<span class="cn">${esc(c.name)}</span><span class="cb">${esc(c.blurb)}</span><span class="cc">${table.lists[j].length} books</span>` +
      `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></button>` +
      `<div class="cat-b" id="catB${j}" role="region" aria-labelledby="catH${j}" hidden></div></div>` : '').join('');
    openCat(table.open);
  }
  function openCat(j) {
    document.querySelectorAll('#cats .cat-h').forEach(h => {
      const k = +h.dataset.cat, on = k === j, body = $('catB' + k);
      h.setAttribute('aria-expanded', on);
      body.hidden = !on;
      if (on && !body.firstChild) { // a category's covers are drawn the first time it opens
        body.innerHTML = `<p class="cat-blurb">${esc(CATEGORIES[k].blurb)}</p><div class="cat-row">` +
          table.lists[k].map(x => `<button type="button" data-book="${esc(x.id)}" data-list="${k}">${coverOnly(x)}<b>${esc(x.title)}</b><small>${esc(x.by)}</small></button>`).join('') +
          `</div><button type="button" class="cat-arr prev" data-dir="-1" aria-label="Earlier books" hidden><span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg></span></button>` +
          `<button type="button" class="cat-arr next" data-dir="1" aria-label="More books in ${esc(CATEGORIES[k].name)}" hidden><span><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 5l7 7-7 7"/></svg></span></button>` +
          `<div class="cat-dots" aria-hidden="true"></div>`;
        body.querySelector('.cat-row').addEventListener('scroll', () => catArrows(body), { passive: true });
      }
      if (on) requestAnimationFrame(() => catArrows(body));
    });
    table.open = j;
  }
  function catArrows(body) {
    const row = body.querySelector('.cat-row'); if (!row) return;
    body.querySelector('.prev').hidden = row.scrollLeft <= 2;
    body.querySelector('.next').hidden = row.scrollLeft + row.clientWidth >= row.scrollWidth - 2;
    // Page dots under the row: how far along the shelf you are (at most ten, each a stretch of it); a dot jumps there.
    const max = row.scrollWidth - row.clientWidth, dots = body.querySelector('.cat-dots');
    const n = max > 2 ? Math.min(10, Math.ceil(row.scrollWidth / row.clientWidth)) : 0;
    const at = n > 1 ? Math.round(row.scrollLeft / max * (n - 1)) : 0;
    if (dots.children.length !== n) dots.innerHTML = Array.from({ length: n }, (_, i) => `<button type="button" data-dot="${i}" tabindex="-1"></button>`).join('');
    [...dots.children].forEach((d, i) => d.classList.toggle('on', i === at));
  }
  function drawTable() {
    if (table.built) return;
    table.built = true;
    table.five = todaysFive();
    drawFeatured();
    drawCats();
  }
  $('table').addEventListener('click', e => {
    const t = e.target.closest('button'); if (!t) return;
    if (t.dataset.feat) { const n = table.five.length; table.feat = (table.feat + +t.dataset.feat + n) % n; return drawFeatured(); }
    if (t.dataset.pick) { table.feat = +t.dataset.pick; return drawFeatured(); }
    if (t.dataset.cat) return openCat(t.getAttribute('aria-expanded') === 'true' ? -1 : +t.dataset.cat);
    if (t.dataset.dir) { // eight columns at a time
      const row = t.parentElement.querySelector('.cat-row'), first = row.firstElementChild;
      const col = first ? first.getBoundingClientRect().width + parseFloat(getComputedStyle(row).columnGap || 0) : row.clientWidth / 8;
      return row.scrollBy({ left: +t.dataset.dir * col * 8, behavior: 'smooth' });
    }
    if (t.dataset.dot != null) { // a page dot: jump to that stretch of the shelf
      const row = t.closest('.cat-b').querySelector('.cat-row'), n = t.parentElement.children.length;
      return row.scrollTo({ left: +t.dataset.dot / (n - 1) * (row.scrollWidth - row.clientWidth), behavior: 'smooth' });
    }
    if (t.dataset.book) openBook(t.dataset.book, false, t, false, t.dataset.list === 'feat' ? table.five : table.lists[+t.dataset.list]);
  });
  window.addEventListener('resize', () => { const b = table.open >= 0 && $('catB' + table.open); if (b) catArrows(b); });

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
    $('feed').setAttribute('aria-label', books ? 'Books' : 'Buildings');
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

  // The dock stays on top of everything. On the plain buildings wall it offers Shuffle; anywhere else (the books wall,
  // an opened building, a filtered or searched wall) Shuffle becomes Home, which goes back to the buildings wall.
  // Surprise me works everywhere, even over an opened building.
  const atHome = () => state.mode === 'buildings' && sheet.hidden && !state.q && !state.shelf && !state.decades && GROUPS.every(g => !state.filters[g.key].size);
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
    toggleFilters(false); setMode('buildings', true); clearAll();
  });
  function surprise() {
    const list = visible();
    const pool = list.filter(b => !state.seen.has(keyOf(b)) && b !== state.open);
    const from = pool.length ? pool : list.filter(b => b !== state.open);
    if (from.length) openAny(keyOf(from[Math.floor(Math.random() * from.length)]), true);
  }
  $('surprise').addEventListener('click', surprise);

  /* ---------- start ---------- */
  window.DA = { ALL, get BOOKS() { return BOOKS; }, withBooks, loadDetail, state, GROUPS, matches, esc, fold, countryName, project, world: WORLD,
    coin, medalHtml, laureate: name => laureateOf(null, name), open: id => openAny(id),
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
