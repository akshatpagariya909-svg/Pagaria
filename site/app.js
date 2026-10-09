/* Discover Architecture: the wall (equal-width columns, scrolling down), photo galleries, the opened building, search, filters and Surprise me.
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
  const cols = $('cols'), sheet = $('sheet'), card = $('card');
  const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  const fold = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
  const pad = n => String(n).padStart(3, '0');

  const state = {
    q: '', seed: 11, ncols: 0,
    filters: Object.fromEntries(GROUPS.map(g => [g.key, new Set()])),
    open: null, shot: 0, seen: new Set(), lastTile: null
  };
  const tileShot = new Map(); // which photo each tile is showing

  /* ---------- layout: equal-width columns, scrolling down only ---------- */
  const MIN_COL = 240, GAP = 16;

  function rng(seed) {
    let s = seed | 0;
    return () => { s = s + 0x6D2B79F5 | 0; let t = Math.imul(s ^ s >>> 15, 1 | s); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; };
  }
  function shuffled(arr, r) { const a = arr.slice(); for (let k = a.length - 1; k > 0; k--) { const j = Math.floor(r() * (k + 1)); [a[k], a[j]] = [a[j], a[k]]; } return a; }
  // Height per unit of width. Kept between a wide 3:2 crop and a tall 2:3, so no tile turns into a sliver.
  function ratioOf(b) {
    const im = (b.images || [])[0];
    return im && im.w ? Math.max(2 / 3, Math.min(1.5, im.h / im.w)) : 0.75;
  }
  function columnCount() {
    const w = cols.clientWidth;
    return Math.max(2, Math.min(6, Math.floor((w + GAP) / (MIN_COL + GAP))));
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
  function render(toTop) {
    const list = shuffled(visible(), rng(state.seed));
    const C = columnCount();
    state.ncols = C;
    const heights = new Array(C).fill(0);
    const colEls = Array.from({ length: C }, () => { const d = document.createElement('div'); d.className = 'col'; return d; });
    list.forEach(b => {
      const c = heights.indexOf(Math.min(...heights));
      colEls[c].appendChild(tileEl(b));
      heights[c] += ratioOf(b) + 0.06;
    });
    cols.style.setProperty('--n', C);
    cols.replaceChildren(...colEls);
    $('empty').hidden = list.length > 0;
    $('count').textContent = list.length === TOTAL ? `${TOTAL} buildings` : `${list.length} of ${TOTAL}`;
    const nf = GROUPS.reduce((s, g) => s + state.filters[g.key].size, 0);
    $('filterCount').textContent = nf ? '· ' + nf : '';
    renderIdeas();
    if (toTop) window.scrollTo({ top: 0, behavior: 'smooth' });
  }
  let resizeTimer;
  window.addEventListener('resize', () => {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(() => { if (columnCount() !== state.ncols) render(false); }, 120);
  });

  document.addEventListener('keydown', e => {
    if (e.key === 'Escape') { if (!sheet.hidden) closeBuilding(); else toggleFilters(false); return; }
    if (!sheet.hidden) {
      if (e.key === 'ArrowLeft') showShot(state.shot - 1);
      if (e.key === 'ArrowRight') showShot(state.shot + 1);
    }
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

    $('links').innerHTML = linksFor(b).map(([k, n, u, direct]) =>
      `<a href="${esc(u)}" target="_blank" rel="noopener"${direct ? '' : ' class="guess" title="Opens the top search result on this site"'}><span>${esc(k)}</span>${esc(n)} ↗</a>`).join('');

    $('rel').innerHTML = related(b).map(({ x, why }) => `<button type="button" data-id="${esc(x.id)}"><span class="ph">${x.images && x.images[0] ? `<img src="${esc(x.images[0].thumb)}" alt="" loading="lazy">` : ''}</span>${esc(x.name)}<small>${esc(why)}</small></button>`).join('');

    sheet.hidden = false;
    document.body.classList.add('locked');
    card.querySelector('.info').scrollTop = 0;
    card.focus({ preventScroll: true });
    try { history.replaceState(null, '', '#' + b.id); } catch (e) { /* some embedded frames forbid it */ }
  }

  function closeBuilding() {
    sheet.hidden = true;
    document.body.classList.remove('locked');
    state.open = null;
    try { history.replaceState(null, '', location.pathname + location.search); } catch (e) { /* ignore */ }
    if (state.lastTile && state.lastTile.isConnected) state.lastTile.querySelector('.open').focus({ preventScroll: true });
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

  $('shuffle').addEventListener('click', () => { state.seed = Math.floor(Math.random() * 1e6) + 1; render(true); });
  $('surprise').addEventListener('click', () => {
    const list = visible();
    const pool = list.filter(b => !state.seen.has(b.id));
    const from = pool.length ? pool : list;
    if (from.length) openBuilding(from[Math.floor(Math.random() * from.length)].id, true);
  });

  /* ---------- start ---------- */
  buildFilters();
  render(false);
  const openFromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id && (!state.open || state.open.id !== id)) openBuilding(id);
  };
  window.addEventListener('hashchange', openFromHash);
  openFromHash();
})();
