/* Discover Architecture: the wall, photo galleries, the opened building, search, filters and Surprise me.
   Plain JavaScript, no build step. Data comes from data/buildings.js (window.BUILDINGS). */
(() => {
  'use strict';

  const ALL = window.BUILDINGS || [];
  const TOTAL = ALL.length;
  const GROUPS = [
    { key: 'concepts', title: 'Idea', multi: true },
    { key: 'type', title: 'Typology' },
    { key: 'movement', title: 'Movement' },
    { key: 'region', title: 'Region' },
    { key: 'era', title: 'Era' }
  ];
  const ERA_ORDER = ['Before 1900', '1900–1945', '1945–1970', '1970–1990', '1990–2005', '2005–today'];

  const $ = id => document.getElementById(id);
  const field = $('field'), world = $('world'), sheet = $('sheet'), card = $('card');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fold = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const pad = n => String(n).padStart(3, '0');

  const state = {
    q: '', seed: 11, z: 0.85, px: 40, py: 120,
    filters: Object.fromEntries(GROUPS.map(g => [g.key, new Set()])),
    open: null, shot: 0, seen: new Set(), lastTile: null
  };
  const tileShot = new Map(); // which photo each tile is showing

  /* ---------- layout ---------- */
  const U = 150, G = 10;
  const SIZES = { l: [[2, 1], [3, 2]], p: [[1, 2], [2, 3]], s: [[1, 1], [2, 2]], t: [[1, 2], [1, 3]] };
  let layoutCache = { key: '', pos: [], W: 0, H: 0 };

  function rng(seed) {
    let s = seed | 0;
    return () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  function shuffled(arr, r) { const a = arr.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(r() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }
  function shapeOf(b) {
    const im = (b.images || [])[0];
    if (!im || !im.w) return 's';
    const ratio = im.h / im.w;
    return ratio > 1.45 ? 't' : ratio > 1.1 ? 'p' : ratio < 0.85 ? 'l' : 's';
  }

  function layout(list) {
    const key = state.seed + '|' + list.map(b => b.id).join(',');
    if (layoutCache.key === key) return layoutCache;
    const r = rng(state.seed);
    const order = shuffled(list, r);
    const C = Math.max(4, Math.min(26, Math.round(Math.sqrt(list.length * 5.5))));
    const heights = new Array(C).fill(0);
    const pos = order.map((b, k) => {
      const big = k % 4 === 0 || r() < 0.2;
      let [w, h] = SIZES[shapeOf(b)][big ? 1 : 0];
      w = Math.min(w, C);
      let best = 0, top = Infinity;
      for (let c = 0; c <= C - w; c++) { let t = 0; for (let q = c; q < c + w; q++) t = Math.max(t, heights[q]); if (t < top) { top = t; best = c; } }
      for (let q = best; q < best + w; q++) heights[q] = top + h;
      return { b, x: best * (U + G), y: top * (U + G), w: w * U + (w - 1) * G, h: h * U + (h - 1) * G };
    });
    layoutCache = { key, pos, W: C * (U + G) - G, H: Math.max(0, ...heights) * (U + G) };
    return layoutCache;
  }

  /* ---------- filtering ---------- */
  const values = (b, key) => (Array.isArray(b[key]) ? b[key] : [b[key]]);
  function matches(b) {
    for (const g of GROUPS) {
      const set = state.filters[g.key];
      if (set.size && !values(b, g.key).some(v => set.has(v))) return false;
    }
    if (!state.q) return true;
    const hay = fold([b.name, b.by, b.place, b.year, b.type, b.movement, b.region, b.study, (b.concepts || []).join(' ')].join(' '));
    return state.q.split(/\s+/).every(w => hay.includes(w));
  }
  const visible = () => ALL.filter(matches);

  /* ---------- tiles ---------- */
  const tiles = new Map();
  function tileImage(b, k) {
    const im = (b.images || [])[k];
    return im ? `<img src="${esc(im.thumb)}" alt="" loading="lazy" decoding="async">` : '';
  }
  function tileEl(b) {
    let el = tiles.get(b.id);
    if (el) return el;
    const n = (b.images || []).length;
    el = document.createElement('div');
    el.className = 't' + (n ? '' : ' empty-tile');
    el.dataset.id = b.id;
    el.innerHTML =
      `<button type="button" class="open" aria-label="${esc(b.name)}, ${esc(b.by)}, ${esc(b.year)}">${tileImage(b, 0)}` +
      (n ? '' : `<span class="slot"><span class="k">No free photos yet</span><span class="h">${esc(b.name)}</span></span>`) + `</button>` +
      (n > 1 ? `<button type="button" class="flip prev" aria-label="Previous photo of ${esc(b.name)}"><svg viewBox="0 0 24 24"><path d="M15 5l-7 7 7 7"/></svg></button>` +
               `<button type="button" class="flip next" aria-label="Next photo of ${esc(b.name)}"><svg viewBox="0 0 24 24"><path d="M9 5l7 7-7 7"/></svg></button>` +
               `<span class="dots">${Array.from({ length: n }, (_, k) => `<i class="${k ? '' : 'on'}"></i>`).join('')}</span>` : '') +
      `<span class="lab"><small class="k">${pad(b.n)}/${TOTAL} · ${esc(b.type)}</small><b>${esc(b.name)}</b><small>${esc(b.by)} · ${esc(b.year)}</small></span>`;
    el.querySelector('.open').addEventListener('click', e => { if (drag.justDragged) { e.preventDefault(); return; } openBuilding(b.id, false, el); });
    el.querySelectorAll('.flip').forEach(btn => btn.addEventListener('click', e => {
      e.stopPropagation();
      if (drag.justDragged) return;
      flipTile(b, el, btn.classList.contains('next') ? 1 : -1);
    }));
    world.appendChild(el);
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

  function render(refit) {
    const list = visible();
    const L = layout(list);
    const shown = new Set();
    L.pos.forEach(p => {
      const el = tileEl(p.b);
      el.style.left = p.x + 'px'; el.style.top = p.y + 'px'; el.style.width = p.w + 'px'; el.style.height = p.h + 'px';
      el.hidden = false;
      shown.add(p.b.id);
    });
    tiles.forEach((el, id) => { if (!shown.has(id)) el.hidden = true; });
    world.style.width = L.W + 'px'; world.style.height = L.H + 'px';
    $('empty').hidden = list.length > 0;
    $('count').textContent = list.length === TOTAL ? `${TOTAL} buildings` : `${list.length} of ${TOTAL}`;
    const nf = GROUPS.reduce((s, g) => s + state.filters[g.key].size, 0);
    $('filterCount').textContent = nf ? '· ' + nf : '';
    renderIdeas();
    if (refit) fit();
  }

  /* ---------- pan & zoom ---------- */
  function apply() {
    world.style.transform = `translate(${state.px}px, ${state.py}px) scale(${state.z})`;
    $('zoomPct').textContent = Math.round(state.z * 100) + '%';
  }
  function zoomAt(nz, mx, my) {
    nz = Math.max(0.2, Math.min(2.5, nz));
    state.px = mx - (mx - state.px) * nz / state.z;
    state.py = my - (my - state.py) * nz / state.z;
    state.z = nz;
    apply();
  }
  function fit() {
    const L = layoutCache, vw = innerWidth, vh = innerHeight - 190;
    if (!L.W) return;
    state.z = Math.max(0.2, Math.min(1, vw / (L.W + 80), vh / (L.H + 40)));
    state.px = (vw - L.W * state.z) / 2;
    state.py = 116;
    apply();
  }
  function startView() {
    const L = layoutCache;
    state.z = innerWidth < 820 ? 0.55 : 0.85;
    state.px = L.W * state.z < innerWidth ? (innerWidth - L.W * state.z) / 2 : 24;
    state.py = 120;
    apply();
  }

  field.addEventListener('wheel', e => {
    e.preventDefault();
    if (e.ctrlKey || e.metaKey) {
      // Trackpad pinch sends small deltas; a Ctrl + mouse-wheel notch sends ~100. Clamp so both feel the same.
      const d = Math.max(-25, Math.min(25, e.deltaY));
      zoomAt(state.z * Math.exp(-d * 0.012), e.clientX, e.clientY);
    } else {
      const sx = e.shiftKey && !e.deltaX;
      state.px -= sx ? e.deltaY : e.deltaX;
      state.py -= sx ? 0 : e.deltaY;
      apply();
    }
  }, { passive: false });

  // Drag to pan with mouse or one finger; pinch with two fingers.
  const drag = { pts: new Map(), moved: false, justDragged: false, start: null, pinch: null };
  field.addEventListener('pointerdown', e => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    drag.pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (drag.pts.size === 1) { drag.start = { x: e.clientX, y: e.clientY, px: state.px, py: state.py }; drag.moved = false; }
    if (drag.pts.size === 2) {
      const [a, b] = [...drag.pts.values()];
      drag.pinch = { d: Math.hypot(a.x - b.x, a.y - b.y), z: state.z };
    }
  });
  window.addEventListener('pointermove', e => {
    if (!drag.pts.has(e.pointerId)) return;
    drag.pts.set(e.pointerId, { x: e.clientX, y: e.clientY });
    if (drag.pts.size === 2 && drag.pinch) {
      const [a, b] = [...drag.pts.values()];
      zoomAt(drag.pinch.z * Math.hypot(a.x - b.x, a.y - b.y) / drag.pinch.d, (a.x + b.x) / 2, (a.y + b.y) / 2);
      drag.moved = true;
      return;
    }
    const s = drag.start; if (!s) return;
    const dx = e.clientX - s.x, dy = e.clientY - s.y;
    if (!drag.moved && Math.abs(dx) + Math.abs(dy) > 5) { drag.moved = true; field.classList.add('dragging'); }
    if (drag.moved) { state.px = s.px + dx; state.py = s.py + dy; apply(); }
  });
  function endPointer(e) {
    if (!drag.pts.has(e.pointerId)) return;
    drag.pts.delete(e.pointerId);
    if (drag.pts.size < 2) drag.pinch = null;
    if (drag.pts.size === 0) {
      if (drag.moved) { drag.justDragged = true; setTimeout(() => { drag.justDragged = false; }, 0); }
      drag.start = null; drag.moved = false;
      field.classList.remove('dragging');
    }
  }
  window.addEventListener('pointerup', endPointer);
  window.addEventListener('pointercancel', endPointer);

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { if (!sheet.hidden) closeBuilding(); else toggleFilters(false); return; }
    if (!sheet.hidden) {
      if (e.key === 'ArrowLeft') showShot(state.shot - 1);
      if (e.key === 'ArrowRight') showShot(state.shot + 1);
      return;
    }
    if (e.target.closest('input')) return;
    const step = 120;
    if (e.key === 'ArrowLeft') { state.px += step; apply(); }
    else if (e.key === 'ArrowRight') { state.px -= step; apply(); }
    else if (e.key === 'ArrowUp') { state.py += step; apply(); }
    else if (e.key === 'ArrowDown') { state.py -= step; apply(); }
    else if (e.key === '+' || e.key === '=') zoomAt(state.z * 1.25, innerWidth / 2, innerHeight / 2);
    else if (e.key === '-') zoomAt(state.z / 1.25, innerWidth / 2, innerHeight / 2);
  });

  /* ---------- opened building ---------- */
  const q = s => encodeURIComponent(s);
  function related(b) {
    return ALL.filter(x => x.id !== b.id).map(x => {
      const shared = (x.concepts || []).filter(c => (b.concepts || []).includes(c));
      let s = shared.length * 2;
      if (x.type === b.type) s += 1;
      if (x.by === b.by) s += 2.5;
      if (x.movement === b.movement) s += 0.5;
      return { x, s: s + ((x.n * 13 + b.n * 7) % 17) / 100, why: shared[0] || (x.by === b.by ? 'Same architect' : x.type) };
    }).sort((p, r) => r.s - p.s).slice(0, 4);
  }

  function showShot(k) {
    const b = state.open; if (!b) return;
    const ims = b.images || [];
    const stage = $('stage');
    if (!ims.length) {
      stage.innerHTML = `<div class="slot"><span class="k">No free photos yet</span><span class="h">${esc(b.name)}</span><span class="s">See photos and drawings through the links →</span></div>`;
      $('gCap').innerHTML = ''; $('strip').innerHTML = '';
      $('gPrev').hidden = $('gNext').hidden = true;
      return;
    }
    k = (k + ims.length) % ims.length;
    state.shot = k;
    const im = ims[k];
    stage.innerHTML = `<img src="${esc(im.src)}" alt="${esc(b.name)}: ${esc(im.caption)}">`;
    const credit = (im.credit || '').replace(/\.$/, '');
    $('gCap').innerHTML = `<span class="c">${k + 1}/${ims.length} · ${esc(im.caption)}</span>` +
      `<span class="l">${credit ? 'Photo: ' + esc(credit) + ' · ' : ''}${esc(im.license)}${im.source ? ` · <a href="${esc(im.source)}" target="_blank" rel="noopener">source</a>` : ''}</span>`;
    $('strip').querySelectorAll('button').forEach((t, j) => t.setAttribute('aria-current', j === k));
    $('gPrev').hidden = $('gNext').hidden = ims.length < 2;
  }

  function openBuilding(id, surprise, fromEl) {
    const b = ALL.find(x => x.id === id);
    if (!b) return;
    state.open = b; state.seen.add(b.id);
    state.lastTile = fromEl || tiles.get(b.id) || null;

    $('strip').innerHTML = (b.images || []).map((im, k) =>
      `<button type="button" data-k="${k}" aria-label="Photo ${k + 1}: ${esc(im.caption)}"><img src="${esc(im.thumb)}" alt=""></button>`).join('');
    showShot(tileShot.get(b.id) || 0);

    const kick = $('bKicker');
    kick.textContent = surprise ? 'You came looking for nothing. You found:' : `${pad(b.n)}/${TOTAL} · ${b.type} · ${b.movement}`;
    kick.classList.toggle('surprise', !!surprise);
    $('bName').textContent = b.name;
    $('bMeta').textContent = `${b.by} · ${b.place} · ${b.year}`;
    $('bStudy').innerHTML = `<span>Study it for</span>${esc(b.study)}`;
    $('pageLink').href = 'buildings/' + b.id + '/';
    $('bChips').innerHTML = (b.concepts || []).map(c => `<button type="button" class="chip" data-g="concepts" data-v="${esc(c)}">${esc(c)} <span class="n">→</span></button>`).join('') +
      `<button type="button" class="chip quiet" data-g="type" data-v="${esc(b.type)}">${esc(b.type)} <span class="n">→</span></button>`;

    const name = b.name, city = b.place.split(',')[0];
    $('links').innerHTML = [
      ['Plans & sections', 'WikiArquitectura', 'https://en.wikiarquitectura.com/?s=' + q(name)],
      ['Projects & drawings', 'ArchDaily', 'https://www.archdaily.com/search/all?q=' + q(name)],
      ['Read', 'Wikipedia', 'https://en.wikipedia.org/w/index.php?search=' + q(name + ' ' + city)],
      ['News & features', 'Dezeen', 'https://www.dezeen.com/?s=' + q(name)],
      ['Watch', 'YouTube', 'https://www.youtube.com/results?search_query=' + q(name + ' ' + b.by + ' architecture')],
      ['More photos', 'Wikimedia Commons', b.commons ? 'https://commons.wikimedia.org/wiki/' + q(b.commons.replace(/ /g, '_')) : 'https://commons.wikimedia.org/w/index.php?search=' + q(name)]
    ].map(([k, n, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener"><span>${esc(k)}</span>${esc(n)} ↗</a>`).join('');

    $('rel').innerHTML = related(b).map(({ x, why }) => `<button type="button" data-id="${esc(x.id)}"><span class="ph">${x.images && x.images[0] ? `<img src="${esc(x.images[0].thumb)}" alt="" loading="lazy">` : ''}</span>${esc(x.name)}<small>${esc(why)}</small></button>`).join('');

    sheet.hidden = false;
    card.querySelector('.info').scrollTop = 0;
    card.focus({ preventScroll: true });
    try { history.replaceState(null, '', '#' + b.id); } catch (e) { /* some embedded frames forbid it */ }
  }

  function closeBuilding() {
    sheet.hidden = true;
    state.open = null;
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ }
    if (state.lastTile && !state.lastTile.hidden) state.lastTile.querySelector('.open').focus({ preventScroll: true });
  }

  $('veil').addEventListener('click', closeBuilding);
  $('close').addEventListener('click', closeBuilding);
  $('gPrev').addEventListener('click', () => showShot(state.shot - 1));
  $('gNext').addEventListener('click', () => showShot(state.shot + 1));
  $('strip').addEventListener('click', e => { const t = e.target.closest('button[data-k]'); if (t) showShot(+t.dataset.k); });
  // swipe between photos on touch screens
  let swipeX = null;
  $('stage').addEventListener('pointerdown', e => { swipeX = e.clientX; });
  $('stage').addEventListener('pointerup', e => { if (swipeX != null && Math.abs(e.clientX - swipeX) > 40) showShot(state.shot + (e.clientX < swipeX ? 1 : -1)); swipeX = null; });
  $('rel').addEventListener('click', e => { const t = e.target.closest('button[data-id]'); if (t) openBuilding(t.dataset.id); });
  $('bChips').addEventListener('click', e => {
    const t = e.target.closest('.chip'); if (!t) return;
    GROUPS.forEach(g => state.filters[g.key].clear());
    state.filters[t.dataset.g].add(t.dataset.v);
    state.q = ''; $('q').value = '';
    closeBuilding(); buildFilters(); render(true);
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
    const c = counts('concepts');
    const top = [...c.entries()].filter(([, n]) => n >= 3).sort((a, b) => b[1] - a[1]).map(([v]) => v);
    const on = state.filters.concepts;
    $('ideas').innerHTML = `<span class="lead">Browse by idea</span>` + top.map(v =>
      `<button type="button" class="idea" aria-pressed="${on.has(v)}" data-v="${esc(v)}">${esc(v)}</button>`).join('');
  }
  $('ideas').addEventListener('click', e => {
    const t = e.target.closest('.idea'); if (!t) return;
    const set = state.filters.concepts, v = t.dataset.v;
    const only = set.size === 1 && set.has(v);
    set.clear();
    if (!only) set.add(v);
    buildFilters(); render(true);
  });

  function buildFilters() {
    $('filterGroups').innerHTML = GROUPS.map(g => {
      const c = counts(g.key);
      let vals = [...c.keys()];
      if (g.key === 'era') vals = ERA_ORDER.filter(v => vals.includes(v));
      else if (g.key === 'concepts') vals.sort((a, b) => c.get(b) - c.get(a) || a.localeCompare(b));
      else vals.sort();
      const chips = vals.map(v => `<button type="button" class="chip" aria-pressed="${state.filters[g.key].has(v)}" data-g="${g.key}" data-v="${esc(v)}">${esc(v)} <span class="n">${c.get(v)}</span></button>`).join('');
      return `<div class="fgroup"><h3>${g.title}</h3><div class="fchips">${chips}</div></div>`;
    }).join('');
  }
  $('filterGroups').addEventListener('click', e => {
    const t = e.target.closest('.chip'); if (!t) return;
    const set = state.filters[t.dataset.g];
    set.has(t.dataset.v) ? set.delete(t.dataset.v) : set.add(t.dataset.v);
    t.setAttribute('aria-pressed', set.has(t.dataset.v));
    render(true);
  });
  function toggleFilters(force) {
    const open = force == null ? $('filters').hidden : force;
    $('filters').hidden = !open;
    $('filterBtn').setAttribute('aria-expanded', open);
  }
  $('filterBtn').addEventListener('click', () => toggleFilters());
  function clearAll() {
    GROUPS.forEach(g => state.filters[g.key].clear());
    state.q = ''; $('q').value = '';
    buildFilters(); render(true);
  }
  $('clearFilters').addEventListener('click', clearAll);
  $('emptyClear').addEventListener('click', clearAll);
  $('home').addEventListener('click', e => { e.preventDefault(); toggleFilters(false); clearAll(); });

  $('shuffle').addEventListener('click', () => { state.seed = Math.floor(Math.random() * 1e6) + 1; render(false); });
  $('surprise').addEventListener('click', () => {
    const list = visible();
    const pool = list.filter(b => !state.seen.has(b.id));
    const from = pool.length ? pool : list;
    if (from.length) openBuilding(from[Math.floor(Math.random() * from.length)].id, true);
  });
  $('fit').addEventListener('click', fit);
  $('zoomIn').addEventListener('click', () => zoomAt(state.z * 1.25, innerWidth / 2, innerHeight / 2));
  $('zoomOut').addEventListener('click', () => zoomAt(state.z / 1.25, innerWidth / 2, innerHeight / 2));

  /* ---------- start ---------- */
  buildFilters();
  render(false);
  startView();
  const openFromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && (!state.open || state.open.id !== id)) openBuilding(id);
  };
  window.addEventListener('hashchange', openFromHash);
  openFromHash();
})();
