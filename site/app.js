/* Discover Architecture: the wall, the opened building, search, filters and Surprise me.
   Plain JavaScript, no build step. Data comes from data/buildings.js (window.BUILDINGS). */
(() => {
  'use strict';

  const ALL = window.BUILDINGS || [];
  const TOTAL = ALL.length;
  const MEDIA = {
    photo: { label: 'Photographs', kind: 'Photograph' },
    painting: { label: 'Paintings', kind: 'Painting' },
    print: { label: 'Prints', kind: 'Print' },
    drawing: { label: 'Drawings', kind: 'Drawing' },
    archive: { label: 'Archive photos', kind: 'Archive photo' }
  };
  const GROUPS = [
    { key: 'media', title: 'Medium', label: v => MEDIA[v].label },
    { key: 'type', title: 'Type', label: v => v },
    { key: 'region', title: 'Region', label: v => v },
    { key: 'era', title: 'Era', label: v => v }
  ];
  const ERA_ORDER = ['Ancient', 'Medieval', '1400–1800', '1800s', '1900–1970', '1970–today'];

  const $ = id => document.getElementById(id);
  const field = $('field'), world = $('world'), sheet = $('sheet'), card = $('card');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const up = s => String(s).toUpperCase();

  const state = {
    q: '', seed: 11, z: 0.85, px: 40, py: 84,
    filters: { media: new Set(), type: new Set(), region: new Set(), era: new Set() },
    open: null, seen: new Set(), lastTile: null
  };

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
    if (b.w && b.h) { const ratio = b.h / b.w; return ratio > 1.45 ? 't' : ratio > 1.1 ? 'p' : ratio < 0.85 ? 'l' : 's'; }
    return b.aspect || 's';
  }

  function layout(list) {
    const key = state.seed + '|' + list.map(b => b.id).join(',');
    if (layoutCache.key === key) return layoutCache;
    const r = rng(state.seed);
    // Alternate photographs with other media so the wall always reads as a mix.
    const photos = shuffled(list.filter(b => b.media === 'photo'), r);
    const others = shuffled(list.filter(b => b.media !== 'photo'), r);
    const order = [];
    while (photos.length || others.length) { if (others.length) order.push(others.shift()); if (photos.length) order.push(photos.shift()); }
    // Wider than tall, like a whiteboard: about 23 columns for 100 buildings.
    const C = Math.max(4, Math.min(26, Math.round(Math.sqrt(list.length * 5.5))));
    const heights = new Array(C).fill(0);
    const pos = order.map((b, k) => {
      const big = b.media === 'painting' || k % 5 === 0 || r() < 0.18;
      let [w, h] = SIZES[shapeOf(b)][big ? 1 : 0];
      w = Math.min(w, C);
      let best = 0, top = Infinity;
      for (let c = 0; c <= C - w; c++) { let t = 0; for (let q = c; q < c + w; q++) t = Math.max(t, heights[q]); if (t < top) { top = t; best = c; } }
      for (let q = best; q < best + w; q++) heights[q] = top + h;
      return { b, x: best * (U + G), y: top * (U + G), w: w * U + (w - 1) * G, h: h * U + (h - 1) * G, big };
    });
    layoutCache = { key, pos, W: C * (U + G) - G, H: Math.max(0, ...heights) * (U + G) };
    return layoutCache;
  }

  /* ---------- filtering ---------- */
  function matches(b) {
    const f = state.filters;
    for (const g of GROUPS) { const set = f[g.key]; if (set.size && !set.has(b[g.key])) return false; }
    if (!state.q) return true;
    const hay = [b.name, b.by, b.place, b.year, b.type, b.region, b.work && b.work.title, b.work && b.work.by].join(' ').toLowerCase()
      .normalize('NFD').replace(/[̀-ͯ]/g, '');
    return state.q.split(/\s+/).every(w => hay.includes(w));
  }
  const visible = () => ALL.filter(matches);

  /* ---------- tiles ---------- */
  const tiles = new Map();
  function slotHTML(b, big) {
    const m = MEDIA[b.media];
    const isPhoto = b.media === 'photo';
    const head = isPhoto ? b.name : b.work.title;
    const sub = isPhoto ? 'Image pending · Wikimedia Commons' : (b.work.by + (b.work.date && b.work.date !== '—' ? ', ' + b.work.date : ''));
    return `<span class="slot"><span class="k"><span>${esc(m.kind)}</span></span>
      <span><span class="h ${isPhoto ? 'sans' : 'serif'}" style="font-size:${(isPhoto ? 14 : 16) + (big ? 6 : 0)}px">${esc(head)}</span>
      <span class="s" style="display:block">${esc(sub)}</span></span></span>`;
  }
  function tileEl(b) {
    let el = tiles.get(b.id);
    if (el) return el;
    el = document.createElement('button');
    el.type = 'button';
    el.className = 't m-' + b.media;
    el.dataset.id = b.id;
    el.setAttribute('aria-label', `${b.name}, ${b.place}, ${b.year}`);
    const media = b.thumb || b.image
      ? `<img src="${esc(b.thumb || b.image)}" alt="" loading="lazy" decoding="async">`
      : '';
    el.innerHTML = media + `<span class="lab"><small class="k">${esc(String(b.n).padStart(3, '0'))}/${TOTAL} · ${esc(up(MEDIA[b.media].kind))}</small><b>${esc(b.name)}</b><small>${esc(up(b.place))} · ${esc(b.year)}</small></span>`;
    el.addEventListener('click', e => { if (drag.justDragged) { e.preventDefault(); return; } openBuilding(b.id, false, el); });
    world.appendChild(el);
    tiles.set(b.id, el);
    return el;
  }

  function render(refit) {
    const list = visible();
    const L = layout(list);
    const shown = new Set();
    L.pos.forEach(p => {
      const el = tileEl(p.b);
      if (!p.b.thumb && !p.b.image && el.dataset.big !== String(p.big)) {
        el.querySelector('.slot') && el.querySelector('.slot').remove();
        el.insertAdjacentHTML('afterbegin', slotHTML(p.b, p.big));
        el.dataset.big = String(p.big);
      }
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
    const L = layoutCache, vw = innerWidth, vh = innerHeight - 150;
    if (!L.W) return;
    state.z = Math.max(0.2, Math.min(1, vw / (L.W + 80), vh / (L.H + 40)));
    state.px = (vw - L.W * state.z) / 2;
    state.py = 80;
    apply();
  }
  function startView() {
    const L = layoutCache;
    state.z = innerWidth < 820 ? 0.55 : 0.85;
    state.px = L.W * state.z < innerWidth ? (innerWidth - L.W * state.z) / 2 : 24;
    state.py = 84;
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
    if (!sheet.hidden || e.target.closest('input')) return;
    const step = 120;
    if (e.key === 'ArrowLeft') { state.px += step; apply(); }
    else if (e.key === 'ArrowRight') { state.px -= step; apply(); }
    else if (e.key === 'ArrowUp') { state.py += step; apply(); }
    else if (e.key === 'ArrowDown') { state.py -= step; apply(); }
    else if (e.key === '+' || e.key === '=') zoomAt(state.z * 1.25, innerWidth / 2, innerHeight / 2);
    else if (e.key === '-') zoomAt(state.z / 1.25, innerWidth / 2, innerHeight / 2);
  });

  /* ---------- opened building ---------- */
  const wikiUrl = t => 'https://en.wikipedia.org/wiki/' + encodeURIComponent(t.replace(/ /g, '_'));
  function thumbHTML(b) {
    return b.thumb || b.image ? `<img src="${esc(b.thumb || b.image)}" alt="" loading="lazy">` : '';
  }
  function related(b) {
    return ALL.filter(x => x.id !== b.id).map(x => {
      let s = 0;
      if (x.type === b.type) s += 2;
      if (x.era === b.era) s += 1.5;
      if (x.region === b.region) s += 1;
      if (x.by === b.by) s += 3;
      if (x.media !== b.media) s += 0.5;
      return { x, s: s + ((x.n * 13 + b.n * 7) % 17) / 100 };
    }).sort((p, q) => q.s - p.s).slice(0, 4).map(p => p.x);
  }

  function openBuilding(id, surprise, fromEl) {
    const b = ALL.find(x => x.id === id);
    if (!b) return;
    state.open = b; state.seen.add(b.id);
    state.lastTile = fromEl || tiles.get(b.id) || null;
    const m = MEDIA[b.media];
    const isPhoto = b.media === 'photo';

    const hero = $('hero');
    hero.className = 'hero m-' + b.media + (isPhoto ? ' photo' : '');
    hero.innerHTML = b.image
      ? `<img src="${esc(b.image)}" alt="${esc(isPhoto ? b.name : b.work.title + ' by ' + b.work.by)}">`
      : `<div class="slot"><span class="k"><span>${esc(m.kind)}${isPhoto ? '' : ' · ' + esc(b.work.date)}</span><span>Image pending</span></span>
         <span><span class="h ${isPhoto ? 'sans' : 'serif'}">${esc(isPhoto ? b.name : b.work.title)}</span>
         <span class="s" style="display:block">${esc(isPhoto ? 'Best free photograph · Wikimedia Commons' : b.work.by + ' · ' + b.work.holder)}</span></span></div>`;

    const kick = $('bKicker');
    kick.textContent = surprise ? 'You came looking for nothing. You found:' : `${String(b.n).padStart(3, '0')}/${TOTAL} · told through a ${m.kind.toLowerCase()}`;
    kick.classList.toggle('surprise', !!surprise);
    $('bName').textContent = b.name;
    $('pageLink').href = 'buildings/' + b.id + '/';
    $('bMeta').textContent = `${b.by} · ${b.place} · ${b.year}`;

    $('bChips').innerHTML = GROUPS.map(g => `<button type="button" class="chip" data-g="${g.key}" data-v="${esc(b[g.key])}">${esc(g.label(b[g.key]))} <span class="n">→</span></button>`).join('');

    const lic = b.license ? `<span class="lic">${esc(b.license)}${b.credit ? ' · ' + esc(b.credit) : ''}${b.source ? ` · <a href="${esc(b.source)}" target="_blank" rel="noopener">source</a>` : ''}</span>` : '<span class="lic">Licence and credit added when the image is downloaded</span>';
    $('bCredit').innerHTML = isPhoto
      ? `Photograph${b.credit ? ' by ' + esc(b.credit) : ''}${lic}`
      : `<em>${esc(b.work.title)}</em><br>${esc(b.work.by)}${b.work.date && b.work.date !== '—' ? ', ' + esc(b.work.date) : ''} · ${esc(b.work.holder)}${lic}`;

    const then = b.then || [];
    $('thenWrap').hidden = !then.length;
    $('then').innerHTML = then.map(t => `<figure><div class="ph m-${esc(t.media)}">${t.image ? `<img src="${esc(t.image)}" alt="">` : ''}</div>
      <span class="d">${esc(t.date)}</span><b>${esc(t.title)}</b><span>${esc(t.by)}</span></figure>`).join('');

    const q = encodeURIComponent(b.name + ' ' + b.place.split(',')[0]);
    $('links').innerHTML = [
      ['Read', 'Wikipedia', wikiUrl(b.wiki || b.name)],
      ['Projects & articles', 'ArchDaily', 'https://www.archdaily.com/search/all?q=' + encodeURIComponent(b.name)],
      ['More images', 'Wikimedia Commons', 'https://commons.wikimedia.org/w/index.php?search=' + q],
      ['Art & archives', 'Google Arts & Culture', 'https://artsandculture.google.com/search?q=' + q]
    ].map(([k, n, u]) => `<a href="${esc(u)}" target="_blank" rel="noopener"><span>${esc(k)}</span>${esc(n)} ↗</a>`).join('');

    $('rel').innerHTML = related(b).map(x => `<button type="button" data-id="${esc(x.id)}"><span class="ph m-${x.media}">${thumbHTML(x)}</span>${esc(x.name)}<small>${esc(x.year)}</small></button>`).join('');

    sheet.hidden = false;
    card.scrollTop = 0; card.querySelector('.info').scrollTop = 0;
    card.focus({ preventScroll: true });
    try { history.replaceState(null, '', '#' + b.id); } catch (e) { /* some embedded frames forbid it */ }
  }

  function closeBuilding() {
    sheet.hidden = true;
    state.open = null;
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ }
    if (state.lastTile && !state.lastTile.hidden) state.lastTile.focus({ preventScroll: true });
  }

  $('veil').addEventListener('click', closeBuilding);
  $('close').addEventListener('click', closeBuilding);
  $('rel').addEventListener('click', e => { const t = e.target.closest('button[data-id]'); if (t) openBuilding(t.dataset.id); });
  $('bChips').addEventListener('click', e => {
    const t = e.target.closest('.chip'); if (!t) return;
    GROUPS.forEach(g => state.filters[g.key].clear());
    state.filters[t.dataset.g].add(t.dataset.v);
    state.q = ''; $('q').value = '';
    closeBuilding(); buildFilters(); render(true);
  });

  /* ---------- search, filters, dock ---------- */
  let qTimer;
  $('q').addEventListener('input', e => {
    clearTimeout(qTimer);
    qTimer = setTimeout(() => {
      state.q = e.target.value.trim().toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
      render(true);
    }, 160);
  });

  function buildFilters() {
    $('filterGroups').innerHTML = GROUPS.map(g => {
      let vals = [...new Set(ALL.map(b => b[g.key]))];
      if (g.key === 'era') vals = ERA_ORDER.filter(v => vals.includes(v));
      else if (g.key === 'media') vals = Object.keys(MEDIA);
      else vals.sort();
      const chips = vals.map(v => {
        const n = ALL.filter(b => b[g.key] === v).length;
        const sw = g.key === 'media' ? `<span class="sw m-${v}"></span>` : '';
        return `<button type="button" class="chip" aria-pressed="${state.filters[g.key].has(v)}" data-g="${g.key}" data-v="${esc(v)}">${sw}${esc(g.label(v))} <span class="n">${n}</span></button>`;
      }).join('');
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
