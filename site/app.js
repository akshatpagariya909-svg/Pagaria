/* Discover Architecture: the wall (equal-width columns, scrolling down), photo galleries, the opened building, search, filters and Surprise me.
   Plain JavaScript, no build step. Data comes from data/buildings.js (window.BUILDINGS). */
(() => {
  'use strict';

  const LINKS = window.LINKS || {};
  const ALL = (window.BUILDINGS || []).map(b => ({ ...b, ...(LINKS[b.id] || {}) }));
  const TOTAL = ALL.length;
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
    q: '', seed: 11, ncols: 0,
    filters: Object.fromEntries(GROUPS.map(g => [g.key, new Set()])), decades: null,
    open: null, shot: 0, seen: new Set(), lastTile: null,
    trail: [] // buildings opened before this one since the sheet opened, for the dock's Back arrow
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
  // skip: leave one group out, so the filter panel can count what each of its options would add
  function matches(b, skip) {
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
  const visible = () => ALL.filter(matches);

  /* ---------- tiles ---------- */
  const tiles = new Map();
  function tileImage(b, k) {
    const im = (b.images || [])[k];
    if (!im) return '';
    const tag = im.kind === 'Drawing' ? '<span class="dtag">Drawing, not a photo</span>' : '';
    return `<img src="${esc(im.thumb)}" alt="" loading="lazy" decoding="async">${tag}`;
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
  // Tiles are added a batch at a time as the reader nears the bottom, so 1,000 buildings stay quick.
  const BATCH = 60;
  const feedState = { list: [], next: 0, heights: [], colEls: [] };
  function addBatch() {
    const f = feedState, end = Math.min(f.list.length, f.next + BATCH);
    for (; f.next < end; f.next++) {
      const b = f.list[f.next];
      const c = f.heights.indexOf(Math.min(...f.heights));
      f.colEls[c].appendChild(tileEl(b));
      f.heights[c] += ratioOf(b) + 0.06;
    }
    $('more').hidden = f.next >= f.list.length;
  }
  function render(toTop) {
    const list = shuffled(visible(), rng(state.seed));
    const C = columnCount();
    state.ncols = C;
    feedState.list = list; feedState.next = 0;
    feedState.heights = new Array(C).fill(0);
    feedState.colEls = Array.from({ length: C }, () => { const d = document.createElement('div'); d.className = 'col'; return d; });
    cols.style.setProperty('--n', C);
    cols.replaceChildren(...feedState.colEls);
    addBatch();
    $('empty').hidden = list.length > 0;
    $('count').textContent = list.length === TOTAL ? `${TOTAL.toLocaleString('en')} buildings` : `${list.length.toLocaleString('en')} of ${TOTAL.toLocaleString('en')}`;
    const nf = GROUPS.reduce((s, g) => s + state.filters[g.key].size, 0) + (state.decades ? 1 : 0);
    $('filterCount').textContent = nf ? '· ' + nf : '';
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
      if (e.key === 'ArrowLeft') showShot(state.shot - 1);
      if (e.key === 'ArrowRight') showShot(state.shot + 1);
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
  function bylineHtml(b) {
    const who = firstArchitect(b), p = portraitOf(b), n = byArchitect(b).length + 1;
    const face = p ? `<img class="face" src="${esc(p.thumb)}" alt="${esc(p.name)}">` : `<span class="face initials" aria-hidden="true">${esc(initials(who))}</span>`;
    const text = `<span class="by-text"><i>by</i><b>${esc(b.by)}</b>${n > 1 ? `<span class="see">See all ${n} buildings →</span>` : ''}</span>`;
    const credit = p ? `<p class="face-credit">Portrait: ${p.credit ? esc(p.credit) + ' · ' : ''}${esc(p.license)}${p.source ? ` · <a href="${esc(p.source)}" target="_blank" rel="noopener">source</a>` : ''}</p>` : '';
    return (n > 1 ? `<button type="button" class="by-link" data-arch="${esc(who)}">${face}${text}</button>` : `<div class="by-link">${face}${text}</div>`) + credit;
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
    // Show the small thumbnail at once, then swap in the full photo (often from Wikimedia) when it arrives.
    stage.innerHTML = `<img src="${esc(im.thumb)}" alt="${esc(b.name)}: ${esc(im.caption)}">`;
    const full = new Image();
    full.onload = () => { const img = stage.querySelector('img'); if (img && img.getAttribute('src') === im.thumb) img.src = im.src; };
    full.src = im.src;
    const credit = (im.credit || '').replace(/\.$/, '');
    $('gCap').innerHTML = `<span class="c">${k + 1}/${ims.length} · ${esc(im.caption)}</span>` +
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

  function openBuilding(id, surprise, fromEl, goingBack) {
    const b = ALL.find(x => x.id === id);
    if (!b) return;
    if (!goingBack && !sheet.hidden && state.open && state.open.id !== b.id) state.trail.push({ id: state.open.id, surprise: state.openSurprise });
    state.open = b; state.openSurprise = !!surprise; state.seen.add(b.id);
    state.lastTile = fromEl || tiles.get(b.id) || null;

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
    try { history.replaceState(null, '', '#' + b.id); } catch (e) { /* some embedded frames forbid it */ }
  }

  function closeBuilding() {
    sheet.hidden = true;
    document.body.classList.remove('locked');
    state.open = null; state.trail = [];
    updateDock();
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
  ['byArchRel', 'sameTypeRel'].forEach(id => $(id).addEventListener('click', e => { const t = e.target.closest('button[data-id]'); if (t) openBuilding(t.dataset.id); }));
  // "See all" for an architect searches the wall for their name; "All" for a typology filters by it.
  function showOnWall(arch, type) {
    GROUPS.forEach(g => state.filters[g.key].clear()); state.decades = null;
    if (type) state.filters.type.add(type);
    $('q').value = arch || ''; state.q = fold(arch || '');
    closeBuilding(); refreshFilters(); render(true);
  }
  $('byline').addEventListener('click', e => { const t = e.target.closest('button[data-arch]'); if (t) showOnWall(t.dataset.arch); });
  $('byArchAll').addEventListener('click', e => showOnWall(e.currentTarget.dataset.arch));
  $('sameTypeAll').addEventListener('click', e => showOnWall('', e.currentTarget.dataset.type));
  $('bChips').addEventListener('click', e => {
    const t = e.target.closest('.chip'); if (!t) return;
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
  function clearAll() {
    GROUPS.forEach(g => state.filters[g.key].clear()); state.decades = null;
    state.q = ''; $('q').value = '';
    refreshFilters(); render(true);
  }
  $('emptyClear').addEventListener('click', clearAll);
  $('home').addEventListener('click', e => { e.preventDefault(); toggleFilters(false); clearAll(); });

  // The dock stays on top of everything. On the plain wall it offers Shuffle; anywhere else (an opened building,
  // a filtered or searched wall) Shuffle becomes Home. Surprise me works everywhere, even over an opened building.
  const atHome = () => sheet.hidden && !state.q && !state.decades && GROUPS.every(g => !state.filters[g.key].size);
  function updateDock() {
    const home = atHome();
    $('shuffle').hidden = !home;
    $('goHome').hidden = home;
    const prev = state.trail.length && !sheet.hidden ? ALL.find(x => x.id === state.trail[state.trail.length - 1].id) : null;
    $('goBack').hidden = !prev;
    if (prev) { $('goBack').title = 'Back to ' + prev.name; $('goBack').setAttribute('aria-label', 'Back to ' + prev.name); }
  }
  $('goBack').addEventListener('click', () => {
    const t = state.trail.pop();
    if (t) openBuilding(t.id, t.surprise, null, true);
  });
  $('shuffle').addEventListener('click', () => { state.seed = Math.floor(Math.random() * 1e6) + 1; render(true); });
  $('goHome').addEventListener('click', () => {
    if (!sheet.hidden) closeBuilding();
    toggleFilters(false); clearAll();
  });
  function surprise() {
    const list = visible();
    const pool = list.filter(b => !state.seen.has(b.id) && (!state.open || b.id !== state.open.id));
    const from = pool.length ? pool : list.filter(b => !state.open || b.id !== state.open.id);
    if (from.length) openBuilding(from[Math.floor(Math.random() * from.length)].id, true);
  }
  $('surprise').addEventListener('click', surprise);

  /* ---------- start ---------- */
  window.DA = { ALL, state, GROUPS, matches, esc, fold, countryName, project, world: WORLD,
    apply: () => render(false), close: () => { toggleFilters(false); window.scrollTo({ top: 0, behavior: 'smooth' }); } };
  render(false);
  const openFromHash = () => {
    const id = decodeURIComponent(location.hash.slice(1));
    if (id === 'surprise') surprise(); // Surprise me on a building page or the A–Z list lands here
    else if (id && (!state.open || state.open.id !== id)) openBuilding(id);
  };
  window.addEventListener('hashchange', openFromHash);
  openFromHash();
})();
