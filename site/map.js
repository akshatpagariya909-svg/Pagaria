/* Find Great Architecture: the globe map (live for everyone since 15 Oct 2026).
   A Map button sits in the dock; the globe opens over the wall. Tapping a building opens the same building sheet as the
   wall, over the map, and closing it comes back to the map. Surprise me flies to a building and shows a small card.
   Look: v21 D+ (sunset red land, darker red borders at 40%), country names that fade in as you zoom. */
(() => {
  const $ = id => document.getElementById(id);
  const DA = window.DA;
  if (!DA) return;
  const esc = DA.esc;
  const reduce = () => matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- the dock button and the panel ---------- */
  const dock = document.querySelector('.dock');
  dock.insertAdjacentHTML('afterbegin', `<button type="button" id="mapBack" hidden><svg viewBox="0 0 24 24" aria-hidden="true"><path d="M15 5l-7 7 7 7"/></svg>Wall</button>`);
  $('surprise').insertAdjacentHTML('beforebegin', `<button type="button" id="mapBtn" class="mapbtn"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3.5 3 14.5 0 18M12 3c-3 3.5-3 14.5 0 18"/></svg>Map</button>`);
  document.body.insertAdjacentHTML('beforeend', `
<section class="globe" id="globe" aria-label="Map of the buildings" hidden>
  <canvas id="gView"></canvas>
  <div class="g-here" id="gHere" hidden></div>
  <div class="g-none" id="gNone" hidden>No buildings on the map match this search.</div>
  <div class="g-help" id="gHelp">Drag · pinch to zoom · tap a photo</div>
  <div class="g-zoom"><button type="button" id="gIn" aria-label="Zoom in">+</button><button type="button" id="gOut" aria-label="Zoom out">−</button></div>
  <div class="g-tip" id="gTip" hidden><span class="k" id="gtKind"></span><b id="gtName"></b><span class="m" id="gtMeta"></span><p id="gtStudy"></p></div>
  <div class="g-card" id="gCard" hidden>
    <div class="g-ph"><div class="g-strip" id="gcStrip"></div><span class="dots" id="gcDots" aria-hidden="true"></span></div>
    <div class="tx"><span class="k" id="gcKind"></span><b id="gcName"></b><span class="m" id="gcMeta"></span><p id="gcStudy"></p>
      <button type="button" class="open" id="gcOpen">Open the building →</button></div>
    <button type="button" class="x" id="gcX" aria-label="Close">✕</button>
  </div>
</section>`);
  const panel = $('globe'), view = $('gView'), ctx = view.getContext('2d');

  /* ---------- data: buildings with a known position, best known first ---------- */
  let all = [], items = [], LAND = null, DETAIL = null, detailLoading = false, labels = [], ready = null;
  const thumbs = new Map(); // id -> Image, loaded only for photos on screen
  function load() {
    if (ready) return ready;
    const script = new Promise((res, rej) => { const s = document.createElement('script'); s.src = 'vendor/d3-7.9.0.min.js'; s.onload = res; s.onerror = rej; document.head.appendChild(s); });
    const json = f => fetch('data/map/' + f).then(r => r.json());
    ready = Promise.all([script, json('land110.json'), json('labels.json'), json('order.json').catch(() => [])]).then(([, land, lab, order]) => {
      const rank = new Map(order.map((id, i) => [id, i]));
      all = DA.ALL.filter(b => b.coords && b.images && b.images.length).map(b => {
        const la = b.coords[0] * Math.PI / 180, lo = b.coords[1] * Math.PI / 180;
        return { b, lat: b.coords[0], lon: b.coords[1], vx: Math.cos(la) * Math.cos(lo), vy: Math.cos(la) * Math.sin(lo), vz: Math.sin(la), r: rank.has(b.id) ? rank.get(b.id) : 1e9 };
      }).sort((a, c) => a.r - c.r);
      items = all.filter(it => DA.matches(it.b));
      LAND = pieces(land);
      labels = lab.map(l => { const a = l[2] * Math.PI / 180, o = l[1] * Math.PI / 180; return { name: l[0].toUpperCase(), lon: l[1], lat: l[2], size: l[3], vx: Math.cos(a) * Math.cos(o), vy: Math.cos(a) * Math.sin(o), vz: Math.sin(a) }; });
    });
    return ready;
  }
  // Split shapes into pieces with a centre and a reach, so a frame projects only the land on screen.
  function pieces(g) {
    const cut = (geom, poly) => geom.coordinates.map(c => {
      const ring = poly ? c[0] : c, ctr = d3.geoCentroid({ type: 'LineString', coordinates: ring });
      let rad = 0; for (const q of ring) rad = Math.max(rad, d3.geoDistance(ctr, q));
      return { ctr, rad, c };
    });
    if (g.cells) return { land: g.cells.flatMap(c => c.p.map(q => ({ ctr: [c.b[0] + 5, c.b[1] + 5], rad: .124, c: q }))), borders: cut(g.borders, false), cells: true };
    return { land: cut(g.land, true), borders: cut(g.borders, false) };
  }
  function thumb(b) {
    let im = thumbs.get(b.id);
    if (!im) { im = new Image(); im.decoding = 'async'; im.onload = dirty; im.src = b.images[0].thumb; thumbs.set(b.id, im); }
    return im.complete && im.naturalWidth ? im : null;
  }

  /* ---------- drawing ---------- */
  const C = { halo: 'rgba(218,58,38,.10)', sea1: '#FFFFFF', sea2: '#FBEAE6', grat: 'rgba(218,58,38,.12)', equator: 'rgba(218,58,38,.32)', land: '#F3C2BA', border: 'rgba(184,46,29,.4)', rim: '#F3C2BA' };
  const V = { lon: 10, lat: 30, k: 1 };
  let W = 0, H = 0, DPR = 1, raf = 0, selected = null, drawn = { tiles: [], dots: [], T: 26, r: 3 }, stretch = false;
  let globe, gratProj, GRAT;
  const widths = new Map();
  const radius = () => Math.min(W, AH) * .47 * V.k; // fits the clear space between the ideas row and the dock
  let TOP = 0, AH = 0, CY = 0;
  function dirty() { if (!raf && !panel.hidden) raf = requestAnimationFrame(draw); }
  function clampView() {
    V.k = Math.max(stretch ? .55 : 1, Math.min(160, V.k));
    V.lat = Math.max(-85, Math.min(85, V.lat));
    V.lon = ((V.lon + 540) % 360) - 180;
  }
  function resize() {
    DPR = Math.min(window.devicePixelRatio || 1, 2);
    W = view.clientWidth; H = view.clientHeight;
    // the ideas row floats over the top of the map and the dock over the bottom: keep the globe between them
    const ideas = document.querySelector('.ideas'), dk = document.querySelector('.dock'), top = parseFloat(panel.style.top) || 0; // not the rect: the panel may still be sliding in
    TOP = ideas && ideas.offsetParent ? Math.max(0, ideas.getBoundingClientRect().bottom - top) + 8 : 8;
    const bottom = dk ? Math.max(0, top + H - dk.getBoundingClientRect().top) + 8 : 8;
    AH = Math.max(120, H - TOP - bottom); CY = TOP + AH / 2;
    view.width = Math.round(W * DPR); view.height = Math.round(H * DPR);
    dirty();
  }
  function draw() {
    raf = 0;
    if (!W || !LAND) return;
    clampView();
    const R = radius(), p = globe.scale(R).translate([W / 2, CY]).rotate([-V.lon, -V.lat]), path = d3.geoPath(p, ctx);
    ctx.setTransform(DPR, 0, 0, DPR, 0, 0);
    ctx.clearRect(0, 0, W, H);
    // a soft halo, then the sphere with light from the top left, then the globe's own lines
    const halo = ctx.createRadialGradient(W / 2, CY, R * .96, W / 2, CY, R * 1.12);
    halo.addColorStop(0, C.halo); halo.addColorStop(1, 'rgba(218,58,38,0)');
    ctx.fillStyle = halo; ctx.beginPath(); ctx.arc(W / 2, CY, R * 1.12, 0, 6.2832); ctx.fill();
    const shade = ctx.createRadialGradient(W / 2 - R * .35, CY - R * .4, R * .1, W / 2, CY, R);
    shade.addColorStop(0, C.sea1); shade.addColorStop(1, C.sea2);
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.fillStyle = shade; ctx.fill();
    gratProj.scale(R).translate([W / 2, CY]).rotate(p.rotate());
    const gp = d3.geoPath(gratProj, ctx);
    ctx.beginPath(); gp(GRAT); ctx.strokeStyle = C.grat; ctx.lineWidth = 1; ctx.stroke();
    ctx.beginPath(); gp({ type: 'LineString', coordinates: d3.range(-180, 181, 2).map(x => [x, 0]) }); ctx.strokeStyle = C.equator; ctx.stroke();

    // land: the detailed coastline only once a small part of the world fills the screen
    const reach = Math.asin(Math.min(1, Math.hypot(W, H) / 2 / R));
    if (reach < .45 && !DETAIL && !detailLoading) { detailLoading = true; fetch('data/map/land50.json').then(r => r.json()).then(g => { DETAIL = pieces(g); dirty(); }).catch(() => {}); }
    const g = reach < .45 && DETAIL ? DETAIL : LAND, c0 = [V.lon, V.lat];
    const near = list => reach > 1.4 ? list.map(x => x.c) : list.filter(x => d3.geoDistance(c0, x.ctr) - x.rad < reach).map(x => x.c);
    ctx.beginPath(); path({ type: 'MultiPolygon', coordinates: near(g.land) }); ctx.fillStyle = C.land; ctx.fill();
    if (g.cells) ctx.fill(); // a second pass closes the hairline seams between the detailed squares
    ctx.beginPath(); path({ type: 'MultiLineString', coordinates: near(g.borders) }); ctx.strokeStyle = C.border; ctx.lineWidth = .96; ctx.stroke();
    ctx.beginPath(); path({ type: 'Sphere' }); ctx.strokeStyle = C.rim; ctx.lineWidth = 1; ctx.stroke();

    // buildings: the back of the globe left out; photos where they fit, best known first; the rest are dots
    const la = V.lat * Math.PI / 180, lo = V.lon * Math.PI / 180, cx = Math.cos(la) * Math.cos(lo), cy = Math.cos(la) * Math.sin(lo), cz = Math.sin(la);
    const T = Math.round(Math.max(26, Math.min(78, 26 + 9 * Math.log2(V.k)))), cell = T + 4, grid = new Map(), tiles = [], dots = [];
    const free = (x, y) => { const gx = Math.floor(x / cell), gy = Math.floor(y / cell);
      for (let i = -1; i <= 1; i++) for (let j = -1; j <= 1; j++) { const o = grid.get((gx + i) + ',' + (gy + j)); if (o && Math.abs(o[0] - x) < cell && Math.abs(o[1] - y) < cell) return false; } return true; };
    for (const it of items) {
      if (it.vx * cx + it.vy * cy + it.vz * cz < .05) continue;
      const q = p([it.lon, it.lat]);
      if (!q || q[0] < -40 || q[1] < -40 || q[0] > W + 40 || q[1] > H + 40) continue;
      if (tiles.length < 140 && free(q[0], q[1])) { tiles.push([it, q[0], q[1]]); grid.set(Math.floor(q[0] / cell) + ',' + Math.floor(q[1] / cell), q); }
      else dots.push([it, q[0], q[1]]);
    }
    const r = V.k >= 6 ? 4 : 3;
    ctx.fillStyle = '#111110'; ctx.strokeStyle = '#FFFFFF'; ctx.lineWidth = 1.5;
    for (const [, x, y] of dots) { ctx.beginPath(); ctx.arc(x, y, r, 0, 6.2832); ctx.fill(); ctx.stroke(); }
    const photo = (it, x, y, S) => {
      const im = thumb(it.b);
      ctx.fillStyle = '#FFFFFF'; ctx.fillRect(x - S / 2 - 2, y - S / 2 - 2, S + 4, S + 4);
      if (!im) { ctx.fillStyle = '#CFCCC5'; ctx.fillRect(x - S / 2, y - S / 2, S, S); return; }
      const m = Math.min(im.naturalWidth, im.naturalHeight);
      ctx.drawImage(im, (im.naturalWidth - m) / 2, (im.naturalHeight - m) / 2, m, m, x - S / 2, y - S / 2, S, S);
    };
    ctx.shadowColor = 'rgba(17,17,16,.25)'; ctx.shadowBlur = 6; ctx.shadowOffsetY = 2;
    for (const [, x, y] of tiles) { ctx.fillStyle = '#FFFFFF'; ctx.fillRect(x - T / 2 - 2, y - T / 2 - 2, T + 4, T + 4); }
    ctx.shadowColor = 'transparent';
    for (const [it, x, y] of tiles) photo(it, x, y, T);
    if (selected && selected.vx * cx + selected.vy * cy + selected.vz * cz > 0) { // the chosen building always on top, ringed in red
      const q = p([selected.lon, selected.lat]), S = Math.max(T, 40);
      photo(selected, q[0], q[1], S);
      ctx.strokeStyle = '#DA3A26'; ctx.lineWidth = 3; ctx.strokeRect(q[0] - S / 2 - 1.5, q[1] - S / 2 - 1.5, S + 3, S + 3);
      tiles.push([selected, q[0], q[1]]);
    }

    // country names fade in once the country is wide enough to read, never over a photo or another name
    const boxes = tiles.map(t => [t[1] - T / 2 - 3, t[2] - T / 2 - 3, t[1] + T / 2 + 3, t[2] + T / 2 + 3]), shown = new Set();
    ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.lineJoin = 'round';
    for (const l of labels) {
      const px = l.size * R, a = Math.min(1, (px - 60) / 50);
      if (a <= 0 || l.vx * cx + l.vy * cy + l.vz * cz < .2) continue;
      const q = p([l.lon, l.lat]); if (!q || q[0] < 0 || q[1] < 0 || q[0] > W || q[1] > H) continue;
      const fs = Math.round(11 + Math.min(4, px / 200));
      ctx.font = `600 ${fs}px 'Barlow Condensed', 'Arial Narrow', sans-serif`;
      if ('letterSpacing' in ctx) ctx.letterSpacing = '0.16em';
      const key = l.name + fs, tw = widths.get(key) ?? widths.set(key, ctx.measureText(l.name).width).get(key);
      let at = null;
      for (const dy of [0, -(T / 2 + fs), T / 2 + fs]) {
        const y = q[1] + dy, bx = [q[0] - tw / 2 - 4, y - fs / 2 - 3, q[0] + tw / 2 + 4, y + fs / 2 + 3];
        if (!boxes.some(o => bx[0] < o[2] && bx[2] > o[0] && bx[1] < o[3] && bx[3] > o[1])) { at = y; boxes.push(bx); break; }
      }
      if (at == null) continue;
      shown.add(l.name);
      ctx.globalAlpha = a; ctx.strokeStyle = 'rgba(255,255,255,.85)'; ctx.lineWidth = 3; ctx.strokeText(l.name, q[0], at);
      ctx.fillStyle = '#6E5A55'; ctx.fillText(l.name, q[0], at); ctx.globalAlpha = 1;
    }
    if ('letterSpacing' in ctx) ctx.letterSpacing = '0px';
    // zoomed in past a country's own name: it stays pinned, small, at the top
    let here = '', bd = 1.2;
    for (const l of labels) { const d = d3.geoDistance(c0, [l.lon, l.lat]) / l.size; if (d < bd && l.size * R > Math.max(W, H) * .9 && !shown.has(l.name)) { bd = d; here = l.name; } }
    if ($('gHere').textContent !== here) { $('gHere').textContent = here; $('gHere').hidden = !here; }
    drawn = { tiles, dots, T, r };
  }
  function hit(x, y) {
    const { tiles, dots, T, r } = drawn;
    for (let i = tiles.length - 1; i >= 0; i--) { const t = tiles[i]; if (Math.abs(t[1] - x) <= T / 2 + 3 && Math.abs(t[2] - y) <= T / 2 + 3) return t[0]; }
    let best = null, bd = (r + 10) ** 2;
    for (const d of dots) { const dd = (d[1] - x) ** 2 + (d[2] - y) ** 2; if (dd < bd) { bd = dd; best = d[0]; } }
    return best;
  }
  const metaOf = b => [b.by.split(',')[0], [b.year, b.place.split(',')[0]].filter(Boolean).join(' · ')].filter(Boolean).join(' — ');

  /* ---------- the small card (Surprise me) and opening a building ---------- */
  function card(it) {
    selected = it; $('gTip').hidden = true;
    $('gCard').hidden = !it;
    if (it) {
      const b = it.b;
      const ims = b.images.filter(im => !/drawing\.svg$/.test(im.src));
      // every photo, side by side: swipe sideways through them; the dots say which one is showing
      $('gcStrip').innerHTML = ims.map((im, k) => `<img src="${esc(im.thumb)}" alt="${k ? '' : esc(b.name)}" loading="${k ? 'lazy' : 'eager'}" decoding="async">`).join('');
      $('gcStrip').scrollLeft = 0;
      $('gcDots').innerHTML = ims.length > 1 ? ims.slice(0, 6).map((_, k) => `<i${k ? '' : ' class="on"'}></i>`).join('') : '';
      $('gcKind').textContent = `${b.type} · ${b.movement}`;
      $('gcName').textContent = b.name; $('gcMeta').textContent = metaOf(b); $('gcStudy').textContent = b.study || '';
    }
    dirty();
  }
  function open(it) { card(null); selected = it; dirty(); DA.open(it.b.id); }
  $('gcOpen').addEventListener('click', () => { if (selected) open(selected); });
  $('gcX').addEventListener('click', () => card(null));
  $('gcStrip').addEventListener('scroll', () => {
    const st = $('gcStrip'), k = Math.round(st.scrollLeft / st.clientWidth), dots = $('gcDots').children;
    for (let j = 0; j < dots.length; j++) dots[j].classList.toggle('on', j === Math.min(k, dots.length - 1));
  }, { passive: true });
  $('gcStrip').addEventListener('click', () => { if (selected) open(selected); }); // tapping the photo itself opens the building

  /* ---------- moving: drag with a glide, pinch, wheel, double tap, + and −; a bounce at the smallest size ---------- */
  const ptrs = new Map();
  let last = [0, 0, 0], vel = [0, 0], moved = 0, pinch0 = null, glide = 0, flight = 0, lastTap = null, wheelIdle = 0;
  const band = k => k >= 1 ? k : 1 - (1 - k) * .35;
  function panBy(dx, dy) {
    const f = 180 / Math.PI / radius();
    V.lon -= dx * f / Math.max(.2, Math.cos(V.lat * Math.PI / 180)) * .9; V.lat += dy * f;
    clampView(); dirty();
  }
  function zoomAt(f, x, y) {
    const p = globe.scale(radius()).translate([W / 2, CY]).rotate([-V.lon, -V.lat]), before = p.invert([x, y]);
    V.k *= f; clampView();
    const after = globe.scale(radius()).invert([x, y]);
    if (before && after) { V.lon += before[0] - after[0]; V.lat += before[1] - after[1]; }
    clampView(); dirty();
  }
  function stopMotion() { cancelAnimationFrame(glide); glide = 0; cancelAnimationFrame(flight); flight = 0; }
  function fly(it, k1, at) {
    stopMotion();
    const from = [V.lon, V.lat], k0 = V.k;
    let to = it ? [it.lon, it.lat] : from;
    if (!it && at) { const c = globe.scale(radius()).translate([W / 2, CY]).rotate([-V.lon, -V.lat]).invert(at); if (c) to = c; }
    const ip = d3.geoInterpolate(from, to), dist = d3.geoDistance(from, to), mid = Math.min(k0, k1, Math.max(1, 3 / (1 + dist * 3)));
    const dur = it ? 900 + dist * 500 : 260, t0 = performance.now();
    const step = now => {
      const t = reduce() ? 1 : Math.min(1, (now - t0) / dur), e = d3.easeCubicInOut(t), c = ip(e);
      V.lon = c[0]; V.lat = c[1];
      V.k = it ? (t < .5 ? k0 + (mid - k0) * d3.easeCubicOut(t * 2) : mid + (k1 - mid) * d3.easeCubicIn((t - .5) * 2)) : k0 + (k1 - k0) * e;
      clampView(); draw();
      flight = t < 1 ? requestAnimationFrame(step) : 0;
      if (t >= 1 && it && !it.quiet) card(it);
    };
    flight = requestAnimationFrame(step);
  }
  function springBack() {
    if (V.k >= 1) { stretch = false; return; }
    stopMotion(); stretch = true;
    const k0 = V.k, t0 = performance.now(), ease = d3.easeBackOut.overshoot(2.2);
    const step = now => {
      const t = reduce() ? 1 : Math.min(1, (now - t0) / 480);
      V.k = k0 + (1 - k0) * ease(t); draw();
      if (t < 1) flight = requestAnimationFrame(step); else { flight = 0; stretch = false; V.k = Math.max(1, V.k); dirty(); }
    };
    flight = requestAnimationFrame(step);
  }
  const local = e => { const rc = view.getBoundingClientRect(); return [e.clientX - rc.left, e.clientY - rc.top]; };
  view.addEventListener('pointerdown', e => {
    stopMotion(); view.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]);
    last = [e.clientX, e.clientY, performance.now()]; vel = [0, 0]; moved = 0; view.classList.add('drag');
    if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch0 = [Math.hypot(a[0] - b[0], a[1] - b[1]), V.k]; }
    $('gHelp').classList.add('gone');
  });
  view.addEventListener('pointermove', e => {
    if (!ptrs.has(e.pointerId)) { hover(e); return; }
    const prev = ptrs.get(e.pointerId); ptrs.set(e.pointerId, [e.clientX, e.clientY]);
    if (ptrs.size === 2 && pinch0) {
      const [a, b] = [...ptrs.values()], d = Math.hypot(a[0] - b[0], a[1] - b[1]), rc = view.getBoundingClientRect();
      stretch = true; zoomAt(band(pinch0[1] * Math.pow(d / pinch0[0], 2)) / V.k, (a[0] + b[0]) / 2 - rc.left, (a[1] + b[1]) / 2 - rc.top); // pinch zooms twice as fast as the fingers
      panBy((e.clientX - prev[0]) / 2, (e.clientY - prev[1]) / 2); moved += 10; return;
    }
    const dx = e.clientX - prev[0], dy = e.clientY - prev[1], now = performance.now(), dt = Math.max(8, now - last[2]);
    moved += Math.abs(dx) + Math.abs(dy); vel = [dx / dt * 16, dy / dt * 16]; last = [e.clientX, e.clientY, now];
    panBy(dx, dy);
  });
  function up(e) {
    if (!ptrs.has(e.pointerId)) return;
    ptrs.delete(e.pointerId); view.classList.remove('drag');
    if (ptrs.size === 1) { pinch0 = null; springBack(); return; }
    if (ptrs.size) return;
    springBack();
    if (moved < 6 && e.type === 'pointerup') {
      const [x, y] = local(e), it = hit(x, y), now = performance.now();
      if (!it && e.pointerType === 'touch' && lastTap && now - lastTap[0] < 320 && Math.hypot(x - lastTap[1], y - lastTap[2]) < 40) { lastTap = null; fly(null, V.k * 3, [x, y]); return; }
      lastTap = [now, x, y];
      if (!it) card(null);
      else if (e.pointerType === 'mouse') open(it); // a computer goes straight to the building
      else card(it); // a phone first shows a small preview: swipe its photos, then open the building
      return;
    }
    if (performance.now() - last[2] < 80 && Math.hypot(vel[0], vel[1]) > 1) {
      const step = () => { vel = [vel[0] * .92, vel[1] * .92]; panBy(vel[0], vel[1]); glide = Math.hypot(vel[0], vel[1]) > .3 ? requestAnimationFrame(step) : 0; };
      glide = requestAnimationFrame(step);
    }
  }
  view.addEventListener('pointerup', up); view.addEventListener('pointercancel', up);
  view.addEventListener('wheel', e => {
    e.preventDefault(); stopMotion();
    let f = Math.exp(-e.deltaY * (e.ctrlKey ? .03 : .006));
    if (f < 1 && V.k * f < 1) { stretch = true; f = Math.max(.55, V.k - (V.k - V.k * f) * .3) / V.k; }
    const [x, y] = local(e); zoomAt(f, x, y); $('gHelp').classList.add('gone');
    clearTimeout(wheelIdle); wheelIdle = setTimeout(springBack, 140);
  }, { passive: false });
  view.addEventListener('dblclick', e => fly(null, V.k * 3, local(e)));
  $('gIn').addEventListener('click', () => fly(null, V.k * 3, [W / 2, CY]));
  $('gOut').addEventListener('click', () => fly(null, V.k / 3, [W / 2, CY]));

  // hovering a photo with a mouse: a short note beside it
  let hoverRaf = 0, hoverAt = null;
  function hover(e) {
    if (e.pointerType !== 'mouse') return;
    hoverAt = local(e);
    if (hoverRaf) return;
    hoverRaf = requestAnimationFrame(() => {
      hoverRaf = 0; const [x, y] = hoverAt, it = hit(x, y), tip = $('gTip');
      view.style.cursor = it ? 'pointer' : '';
      if (!it || it === selected) { tip.hidden = true; return; }
      const b = it.b;
      $('gtKind').textContent = `${b.type} · ${b.movement}`; $('gtName').textContent = b.name; $('gtMeta').textContent = metaOf(b); $('gtStudy').textContent = b.study || '';
      tip.hidden = false;
      const tw = tip.offsetWidth, th = tip.offsetHeight, gap = drawn.T / 2 + 14;
      let left = x + gap; if (left + tw > W - 12) left = x - gap - tw;
      tip.style.left = Math.max(12, left) + 'px'; tip.style.top = Math.max(70, Math.min(H - th - 100, y - th / 2)) + 'px';
    });
  }
  view.addEventListener('pointerleave', () => { $('gTip').hidden = true; view.style.cursor = ''; });

  /* ---------- open and close ---------- */
  const isOpen = () => !panel.hidden;
  // the map sits under the top bar and the ideas row, so search, filters and ideas stay in reach
  function place() {
    document.body.classList.remove('ideas-away');
    const bar = document.querySelector('.bar');
    const below = bar.getBoundingClientRect().bottom; // the ideas row floats over the top of the map
    panel.style.top = Math.max(0, Math.round(below)) + 'px';
  }
  async function openMap() {
    if (DA.state.mode === 'books') return;
    place();
    panel.hidden = false; document.body.classList.add('mapped');
    requestAnimationFrame(() => panel.classList.add('in'));
    await load();
    if (!globe) {
      globe = d3.geoOrthographic().clipAngle(90).precision(0);
      gratProj = d3.geoOrthographic().clipAngle(90).precision(.3);
      GRAT = d3.geoGraticule().step([15, 15]).extentMinor([[-180, -75], [180, 75]]).precision(1)();
    }
    resize();
    $('gNone').hidden = items.length > 0;
    if (items.length && items.length < all.length) fit();
  }
  function closeMap() {
    panel.classList.remove('in'); document.body.classList.remove('mapped'); card(null); $('gNone').hidden = true;
    setTimeout(() => { if (!document.body.classList.contains('mapped')) panel.hidden = true; }, reduce() ? 0 : 320);
  }
  $('mapBtn').addEventListener('click', openMap);
  $('mapBack').addEventListener('click', closeMap);
  addEventListener('resize', () => { if (isOpen()) { place(); resize(); } });
  // search, filters and ideas change the wall: the map shows the same buildings and moves to fit them
  let lastSet = '';
  document.addEventListener('da:render', () => {
    if (!all.length) return;
    if (DA.state.mode === 'books') { if (isOpen()) closeMap(); return; }
    items = all.filter(it => DA.matches(it.b));
    const key = items.length + ':' + (items[0] ? items[0].b.id : '') + ':' + (items[items.length - 1] ? items[items.length - 1].b.id : '');
    if (key === lastSet) return;
    lastSet = key;
    if (!isOpen()) return;
    if (selected && !items.includes(selected)) card(null);
    $('gNone').hidden = items.length > 0;
    if (items.length && items.length < all.length) fit(); else dirty();
  });
  function fit() { // centre on where most of the buildings shown are, and zoom so most of them fit
    const sample = items.slice(0, 300);
    let seed = sample[0], most = -1;
    for (const a of sample) { let n = 0; for (const o of sample) if (a.vx * o.vx + a.vy * o.vy + a.vz * o.vz > .94) n++; if (n > most) { most = n; seed = a; } }
    let x = 0, y = 0, z = 0;
    for (const o of items) if (seed.vx * o.vx + seed.vy * o.vy + seed.vz * o.vz > .8) { x += o.vx; y += o.vy; z += o.vz; }
    const n = Math.hypot(x, y, z) || 1, c = [Math.atan2(y, x) * 180 / Math.PI, Math.asin(z / n) * 180 / Math.PI];
    const d = items.map(it => d3.geoDistance(c, [it.lon, it.lat])).sort((a, b) => a - b), th = Math.max(.03, d[Math.floor((d.length - 1) * .75)]);
    const k = th > 1.1 ? 1 : Math.min(60, .9 / Math.sin(th));
    fly({ lon: c[0], lat: c[1], quiet: true }, k);
  }
  document.addEventListener('keydown', e => { if (e.key === 'Escape' && isOpen() && $('sheet').hidden) closeMap(); });
  // Surprise me on the map: fly to a well-known building and show the small card (the wall's own Surprise me is untouched)
  document.addEventListener('click', e => {
    if (!e.target.closest('#surprise') || !isOpen() || !$('sheet').hidden || !items.length) return;
    e.stopPropagation();
    const pool = items.slice(0, 400), it = pool[Math.floor(Math.random() * pool.length)];
    card(null); fly(it, 22);
  }, true);
})();
