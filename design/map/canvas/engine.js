    // The map engine from design/map/map.js, as the body of a component method: `els` holds the map, canvas,
    // label and tile layers and the panel; `ui.set(patch)` updates the chrome (chips, list, counts, the opened
    // building). Tiles and labels are drawn straight into their layers. Returns the api the buttons call.
    'use strict';
    const D = window.MAPDATA, W = D.world;
    const esc = s => String(s == null ? '' : s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    const fold = s => String(s).toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
    const SITE = 'https://akshatpagariya909-svg.github.io/Pagaria/';
    const RAD = Math.PI / 180;
    const reduced = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
    const easeIO = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
    const easeOut = t => 1 - Math.pow(1 - t, 3);

    /* ---------- projections ---------- */
    const [X0, SC, Y0, TOP, BOT] = W.proj;
    function ne(lat, lon) {
      const p = clamp(lat, BOT, TOP) * RAD, l = lon * RAD, p2 = p * p, p4 = p2 * p2;
      const x = l * (0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4)));
      const y = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4)));
      return [(x - X0) * SC, (Y0 - y) * SC];
    }
    function neInv(x, y) {
      const yr = Y0 - y / SC, xr = x / SC + X0;
      let p = yr;
      for (let k = 0; k < 8; k++) {
        const p2 = p * p, p4 = p2 * p2;
        const f = p * (1.007226 + p2 * (0.015085 + p4 * (-0.044475 + 0.028874 * p2 - 0.005916 * p4))) - yr;
        const df = 1.007226 + p2 * (0.045255 + p4 * (-0.311325 + 0.259866 * p2 - 0.065076 * p4));
        p -= f / df;
      }
      const p2 = p * p, p4 = p2 * p2;
      const g = 0.8707 - 0.131979 * p2 + p4 * (-0.013791 + p4 * (0.003971 * p2 - 0.001529 * p4));
      return [p / RAD, xr / g / RAD];
    }

    /* ---------- buildings ---------- */
    const B = D.b.map((r, i) => {
      const o = { i };
      D.fields.forEach((f, k) => { o[f] = r[k]; });
      o.city = o.place.split(',')[0];
      o.country = W.names[o.cc] || o.cc;
      [o.wx, o.wy] = ne(o.lat, o.lon);
      o.slat = Math.sin(o.lat * RAD); o.clat = Math.cos(o.lat * RAD); o.lonr = o.lon * RAD;
      o.hay = fold([o.name, o.by, o.place, o.country, o.year, o.type, o.movement, o.study].join(' '));
      return o;
    });
    const byN = (a, b) => a.n - b.n;
    B.sort(byN);
    const N = B.length;
    const SPR = D.sprite, CARD = D.card;
    const spriteRows = Math.ceil(N / SPR.cols);

    const land = [];
    for (const cc in W.paths) {
      const d = W.paths[cc], path = new Path2D(d);
      const rings = []; let ring = null;
      const re = /([ML])\s*(-?[\d.]+)\s+(-?[\d.]+)|Z/g; let m;
      while ((m = re.exec(d))) {
        if (!m[1]) { if (ring && ring.length > 4) rings.push(new Float64Array(ring)); ring = null; continue; }
        if (m[1] === 'M') { if (ring && ring.length > 4) rings.push(new Float64Array(ring)); ring = []; }
        const [lat, lon] = neInv(+m[2], +m[3]);
        ring.push(lon * RAD, lat * RAD);
      }
      if (ring && ring.length > 4) rings.push(new Float64Array(ring));
      land.push({ cc, path, rings });
    }
    const countryOf = {};
    for (const cc in W.centre) { const [lat, lon] = neInv(W.centre[cc][0], W.centre[cc][1]); countryOf[cc] = { cc, name: W.names[cc] || cc, lat, lon, wx: W.centre[cc][0], wy: W.centre[cc][1], box: W.box[cc] }; }

    /* ---------- state ---------- */
    const map = els.map, cv = els.cv, ctx = cv.getContext('2d'), tilesEl = els.tiles, labelsEl = els.labels, panel = els.panel;
    const V = { mode: 'atlas', z: 0, cx: W.w / 2, cy: W.h / 2, lon: 20, lat: 18, vw: 10, vh: 10, dpr: 1 };
    let TILE = 64, minK = 1, minR = 100, ZMAX = 12;
    let active = B.slice();
    let setVersion = 0, anim = null, raf = 0, settleTimer = 0, hot = null, spread = null;
    const K = z => minK * Math.pow(2, z);
    const R = z => minR * Math.pow(2, z);
    const kEq = () => V.mode === 'atlas' ? K(V.z) : R(V.z) * RAD * 0.36;

    function measure() {
      V.vw = Math.max(10, map.offsetWidth); V.vh = Math.max(10, map.offsetHeight);
      V.dpr = Math.min(2, devicePixelRatio || 1);
      cv.width = Math.round(V.vw * V.dpr); cv.height = Math.round(V.vh * V.dpr);
      TILE = parseFloat(getComputedStyle(map).getPropertyValue('--tile')) || (isPhone ? 54 : 64);
      minK = Math.min(V.vw / W.w, V.vh / W.h) * 0.96;
      minR = Math.min(V.vw, V.vh) / 2 - 18;
      ZMAX = V.mode === 'atlas' ? Math.log2(7000 / minK) : Math.log2(1.1e6 / minR);
      V.z = clamp(V.z, 0, ZMAX);
      clampCentre();
    }

    /* ---------- to the screen and back ---------- */
    function clampCentre() {
      if (V.mode === 'atlas') {
        const k = K(V.z), hw = V.vw / 2 / k, hh = V.vh / 2 / k;
        V.cx = hw * 2 >= W.w ? W.w / 2 : clamp(V.cx, hw, W.w - hw);
        V.cy = hh * 2 >= W.h ? W.h / 2 : clamp(V.cy, hh, W.h - hh);
      } else {
        V.lat = clamp(V.lat, -85, 85);
        V.lon = ((V.lon + 540) % 360) - 180;
      }
    }
    function toScreen(b) {
      if (V.mode === 'atlas') {
        const k = K(V.z);
        return [V.vw / 2 + (b.wx - V.cx) * k, V.vh / 2 + (b.wy - V.cy) * k, true];
      }
      const r = R(V.z), p0 = V.lat * RAD, s0 = Math.sin(p0), c0 = Math.cos(p0), dl = b.lonr - V.lon * RAD;
      const cdl = Math.cos(dl), cosc = s0 * b.slat + c0 * b.clat * cdl;
      return [V.vw / 2 + r * b.clat * Math.sin(dl), V.vh / 2 - r * (c0 * b.slat - s0 * b.clat * cdl), cosc >= 0];
    }
    const geo = (lat, lon) => ({ lat, lon, slat: Math.sin(lat * RAD), clat: Math.cos(lat * RAD), lonr: lon * RAD, wx: 0, wy: 0 });
    function screenToGeo(sx, sy) {
      if (V.mode === 'atlas') {
        const k = K(V.z);
        const [lat, lon] = neInv(V.cx + (sx - V.vw / 2) / k, V.cy + (sy - V.vh / 2) / k);
        return { lat, lon };
      }
      const r = R(V.z), x = sx - V.vw / 2, y = V.vh / 2 - sy, rho = Math.hypot(x, y);
      if (rho > r) return null;
      const c = Math.asin(rho / r), sc = Math.sin(c), cc = Math.cos(c), p0 = V.lat * RAD;
      if (rho < 1e-6) return { lat: V.lat, lon: V.lon };
      const lat = Math.asin(cc * Math.sin(p0) + y * sc * Math.cos(p0) / rho);
      const lon = V.lon * RAD + Math.atan2(x * sc, rho * cc * Math.cos(p0) - y * sc * Math.sin(p0));
      return { lat: lat / RAD, lon: lon / RAD };
    }

    /* ---------- moving the view ---------- */
    function panBy(dx, dy) {
      if (V.mode === 'atlas') { const k = K(V.z); V.cx -= dx / k; V.cy -= dy / k; }
      else { const r = R(V.z); V.lon -= dx / (r * Math.max(0.25, Math.cos(V.lat * RAD))) / RAD; V.lat += dy / r / RAD; }
      clampCentre();
    }
    function zoomAt(sx, sy, f) {
      const z1 = clamp(V.z + Math.log2(f), 0, ZMAX);
      if (z1 === V.z) return;
      spread = null;
      if (V.mode === 'atlas') {
        const k0 = K(V.z), wx = V.cx + (sx - V.vw / 2) / k0, wy = V.cy + (sy - V.vh / 2) / k0;
        V.z = z1; const k1 = K(z1);
        V.cx = wx - (sx - V.vw / 2) / k1; V.cy = wy - (sy - V.vh / 2) / k1;
      } else {
        const g = screenToGeo(sx, sy);
        V.z = z1;
        if (g) {
          const gg = geo(g.lat, g.lon), r = R(z1);
          for (let k = 0; k < 4; k++) {
            const [px, py] = toScreen(gg);
            V.lon -= (sx - px) / (r * Math.max(0.2, Math.cos(V.lat * RAD))) / RAD;
            V.lat += (sy - py) / r / RAD;
            clampCentre();
          }
        }
      }
      clampCentre();
    }
    function centreGeo() { if (V.mode === 'globe') return { lat: V.lat, lon: V.lon }; const [lat, lon] = neInv(V.cx, V.cy); return { lat, lon }; }
    function setCentreGeo(lat, lon) { if (V.mode === 'globe') { V.lat = lat; V.lon = lon; } else [V.cx, V.cy] = ne(lat, lon); clampCentre(); }

    function flyTo(to, ms) {
      spread = null;
      const from = { z: V.z, cx: V.cx, cy: V.cy, lat: V.lat, lon: V.lon };
      to.z = clamp(to.z, 0, ZMAX);
      let dist;
      if (V.mode === 'atlas') dist = Math.hypot(to.cx - from.cx, to.cy - from.cy) * K(from.z);
      else dist = Math.hypot(((to.lon - from.lon + 540) % 360 - 180) * Math.cos(from.lat * RAD), to.lat - from.lat) * RAD * R(from.z);
      const dip = clamp(Math.log2(Math.max(1, dist / (V.vw * 0.4))), 0, 2.5);
      if (reduced) { apply(1); schedule(); return; }
      anim = { kind: 'fly', t0: performance.now(), ms: ms || 650 + Math.min(600, dist / 6) + dip * 160, step: apply };
      schedule();
      function apply(t) {
        const e = easeIO(t);
        V.z = from.z + (to.z - from.z) * e - dip * Math.sin(Math.PI * e);
        if (V.mode === 'atlas') { V.cx = from.cx + (to.cx - from.cx) * e; V.cy = from.cy + (to.cy - from.cy) * e; }
        else { const dl = ((to.lon - from.lon + 540) % 360) - 180; V.lon = from.lon + dl * e; V.lat = from.lat + (to.lat - from.lat) * e; }
        clampCentre();
      }
    }
    function fit(list, zCap) {
      if (!list.length) return;
      if (V.mode === 'atlas') {
        let x0 = 1e9, y0 = 1e9, x1 = -1e9, y1 = -1e9;
        for (const b of list) { x0 = Math.min(x0, b.wx); y0 = Math.min(y0, b.wy); x1 = Math.max(x1, b.wx); y1 = Math.max(y1, b.wy); }
        const pad = 1.6 * TILE;
        const k = Math.min((V.vw - pad * 2) / Math.max(x1 - x0, 1e-3), (V.vh - pad * 2) / Math.max(y1 - y0, 1e-3));
        flyTo({ z: Math.min(zCap == null ? ZMAX - 1.5 : zCap, Math.log2(k / minK)), cx: (x0 + x1) / 2, cy: (y0 + y1) / 2 });
      } else {
        let sx = 0, sy = 0, sz = 0, la0 = 90, la1 = -90;
        for (const b of list) { sx += b.clat * Math.cos(b.lonr); sy += b.clat * Math.sin(b.lonr); sz += b.slat; la0 = Math.min(la0, b.lat); la1 = Math.max(la1, b.lat); }
        const lon = Math.atan2(sy, sx) / RAD, lat = Math.atan2(sz, Math.hypot(sx, sy)) / RAD;
        let lo0 = 180, lo1 = -180;
        for (const b of list) { const d = ((b.lon - lon + 540) % 360) - 180; lo0 = Math.min(lo0, d); lo1 = Math.max(lo1, d); }
        const pad = 1.6 * TILE, c = Math.max(0.2, Math.cos(lat * RAD));
        const r = Math.min((V.vw - pad * 2) / Math.max((lo1 - lo0) * RAD * c, 1e-4), (V.vh - pad * 2) / Math.max((la1 - la0) * RAD, 1e-4));
        flyTo({ z: Math.min(zCap == null ? ZMAX - 1.5 : zCap, Math.log2(r / minR)), lat, lon });
      }
    }
    function world() { flyTo(V.mode === 'atlas' ? { z: 0, cx: W.w / 2, cy: W.h / 2 } : { z: 0, lat: 18, lon: 20 }); }

    /* ---------- clustering ---------- */
    let clusters = [], clKey = '';
    function buildClusters() {
      const zq = Math.round(V.z * 2) / 2, key = V.mode + zq + ':' + setVersion + ':' + TILE;
      if (key === clKey) return;
      clKey = key;
      const cellPx = TILE * 1.3, m = new Map();
      if (V.mode === 'atlas') {
        const cell = cellPx / K(zq);
        for (const b of active) { const k = Math.floor(b.wx / cell) + ',' + Math.floor(b.wy / cell); let c = m.get(k); if (!c) m.set(k, c = []); c.push(b); }
      } else {
        const dlat = cellPx / R(zq) / RAD;
        for (const b of active) {
          const band = Math.floor(b.lat / dlat), dlon = dlat / Math.max(0.15, Math.cos((band + 0.5) * dlat * RAD));
          const k = band + ',' + Math.floor(b.lon / dlon); let c = m.get(k); if (!c) m.set(k, c = []); c.push(b);
        }
      }
      clusters = [];
      for (const members of m.values()) {
        members.sort(byN);
        let wx = 0, wy = 0, sx = 0, sy = 0, sz = 0;
        for (const b of members) { wx += b.wx; wy += b.wy; sx += b.clat * Math.cos(b.lonr); sy += b.clat * Math.sin(b.lonr); sz += b.slat; }
        const n = members.length, lon = Math.atan2(sy, sx) / RAD, lat = Math.atan2(sz, Math.hypot(sx, sy)) / RAD;
        clusters.push({ members, cover: members[0], ...geo(lat, lon), wx: wx / n, wy: wy / n });
      }
    }

    /* ---------- drawing ---------- */
    const posX = new Float64Array(N).fill(NaN), posY = new Float64Array(N).fill(NaN);
    const pool = new Map(), labelPool = new Map();
    let lastDrawn = [];

    function drawLand() {
      const g = ctx; g.setTransform(V.dpr, 0, 0, V.dpr, 0, 0); g.clearRect(0, 0, V.vw, V.vh);
      const fade = clamp((kEq() - 18) / 50, 0, 1), mixc = (a, b) => Math.round(a + (b - a) * fade);
      const landFill = `rgb(${mixc(228, 243)},${mixc(226, 242)},${mixc(220, 238)})`, line = `rgba(255,255,255,${1 - fade})`;
      if (V.mode === 'atlas') {
        const k = K(V.z);
        g.save(); g.translate(V.vw / 2 - V.cx * k, V.vh / 2 - V.cy * k); g.scale(k, k);
        g.fillStyle = landFill; g.strokeStyle = line; g.lineWidth = 0.7 / k;
        for (const c of land) { g.fill(c.path); if (fade < 1) g.stroke(c.path); }
        g.restore();
      } else {
        const r = R(V.z), ox = V.vw / 2, oy = V.vh / 2, p0 = V.lat * RAD, s0 = Math.sin(p0), c0 = Math.cos(p0), l0 = V.lon * RAD;
        g.beginPath(); g.arc(ox, oy, r, 0, Math.PI * 2); g.fillStyle = '#F7F6F3'; g.fill();
        g.save(); g.beginPath(); g.arc(ox, oy, r, 0, Math.PI * 2); g.clip();
        g.strokeStyle = 'rgba(17,17,16,.06)'; g.lineWidth = 1; g.beginPath();
        let off = true;
        const gratPt = (lon, lat, first) => {
          const l = lon * RAD, p = lat * RAD, sl = Math.sin(p), cl = Math.cos(p), dl = l - l0, cdl = Math.cos(dl);
          if (s0 * sl + c0 * cl * cdl < 0) { off = true; return; }
          const x = ox + r * cl * Math.sin(dl), y = oy - r * (c0 * sl - s0 * cl * cdl);
          if (first || off) g.moveTo(x, y); else g.lineTo(x, y);
          off = false;
        };
        for (let lon = -180; lon < 180; lon += 30) for (let lat = -90, first = true; lat <= 90; lat += 3, first = false) gratPt(lon, lat, first);
        for (let lat = -60; lat <= 60; lat += 30) for (let lon = -180, first = true; lon <= 180; lon += 3, first = false) gratPt(lon, lat, first);
        g.stroke();
        g.fillStyle = landFill; g.strokeStyle = line; g.lineWidth = 0.7;
        for (const c of land) for (const ring of c.rings) {
          let any = false;
          g.beginPath();
          for (let i = 0; i < ring.length; i += 2) {
            const lon = ring[i], lat = ring[i + 1], sl = Math.sin(lat), cl = Math.cos(lat), dl = lon - l0, cdl = Math.cos(dl);
            const cosc = s0 * sl + c0 * cl * cdl;
            let x = r * cl * Math.sin(dl), y = r * (c0 * sl - s0 * cl * cdl);
            if (cosc < 0) { const d = Math.hypot(x, y) || 1; x = x / d * r * 1.002; y = y / d * r * 1.002; } else any = true;
            if (i === 0) g.moveTo(ox + x, oy - y); else g.lineTo(ox + x, oy - y);
          }
          if (any) { g.closePath(); g.fill(); if (fade < 1) g.stroke(); }
        }
        g.restore();
        g.beginPath(); g.arc(ox, oy, r, 0, Math.PI * 2); g.strokeStyle = '#E6E4DF'; g.lineWidth = 1; g.stroke();
      }
      g.fillStyle = 'rgba(17,17,16,.5)';
      for (const b of active) { const [x, y, vis] = toScreen(b); if (vis && x > -4 && y > -4 && x < V.vw + 4 && y < V.vh + 4) g.fillRect(x - 1.2, y - 1.2, 2.4, 2.4); }
    }

    function spriteStyle(el, b) { el.style.setProperty('--cx', b.i % SPR.cols); el.style.setProperty('--cy', Math.floor(b.i / SPR.cols)); }
    const bpOf = (b, size) => (-(b.i % SPR.cols) * size) + 'px ' + (-Math.floor(b.i / SPR.cols) * size) + 'px';
    function tipFor(d) {
      const b = d.cover, n = d.count;
      if (n === 1) return `${esc(b.name)}<small>${esc(b.by.split(',')[0])}</small>`;
      const cities = new Set(d.members.map(x => x.city)), cs = new Set(d.members.map(x => x.cc));
      const where = cities.size === 1 ? b.city : cs.size === 1 ? b.country : cs.size + ' countries';
      return `${esc(where)}<small>${n} buildings</small>`;
    }
    function makeTile(d) {
      const el = document.createElement('button');
      el.type = 'button'; el.className = 'pt';
      el.innerHTML = '<i></i><u></u><b></b><span class="tip"></span>';
      el.addEventListener('click', () => onTile(el._d));
      tilesEl.appendChild(el);
      return { el, img: el.firstChild, badge: el.children[2], tip: el.children[3], sig: '', count: 0, from: null, t0: 0, exit: null };
    }

    function frame(now) {
      raf = 0;
      now = now || performance.now();
      let moving = false;
      if (anim) {
        if (anim.kind === 'fly') { const t = clamp((now - anim.t0) / anim.ms, 0, 1); anim.step(t); if (t >= 1) anim = null; else moving = true; }
        else if (anim.kind === 'inertia') {
          const dt = Math.min(40, now - anim.last); anim.last = now;
          const f = Math.pow(0.0025, dt / 1000);
          panBy(anim.vx * dt, anim.vy * dt); anim.vx *= f; anim.vy *= f;
          if (Math.hypot(anim.vx, anim.vy) < 0.02) anim = null; else moving = true;
        }
      }
      buildClusters();
      const T = TILE, half = T / 2, pad = T;
      const seen = [];
      for (const c of clusters) {
        const [sx, sy, vis] = toScreen(c);
        if (!vis || sx < -pad || sy < -pad || sx > V.vw + pad || sy > V.vh + pad) continue;
        seen.push({ sx, sy, cover: c.cover, count: c.members.length, members: c.members, own: true });
      }
      seen.sort((a, b) => b.count - a.count || a.cover.n - b.cover.n);
      let drawn = [];
      const minD = T * 0.92;
      for (const o of seen) {
        let host = null;
        for (const d of drawn) if (Math.abs(d.sx - o.sx) < minD && Math.abs(d.sy - o.sy) < minD) { host = d; break; }
        if (host) { if (host.own) { host.members = host.members.slice(); host.own = false; } host.count += o.count; for (const b of o.members) host.members.push(b); }
        else drawn.push(o);
      }
      if (spread) {
        const i = drawn.findIndex(d => d.cover === spread.cover && d.count > 1);
        if (i < 0) spread = null;
        else {
          const d = drawn[i]; drawn.splice(i, 1);
          const ms = d.members.slice(0, 16), n = ms.length;
          ms.forEach((b, j) => {
            const ring = j < 8 ? 0 : 1, m = ring ? Math.min(8, n - 8) : Math.min(8, n), idx = ring ? j - 8 : j;
            const a = -Math.PI / 2 + idx / m * Math.PI * 2 + (ring ? Math.PI / m : 0), rad = T * (ring ? 2.1 : 1.15) * (n === 1 ? 0 : 1);
            drawn.push({ sx: d.sx + Math.cos(a) * rad, sy: d.sy + Math.sin(a) * rad, cover: b, count: 1, members: [b] });
          });
          if (d.members.length > 16) drawn.push({ sx: d.sx, sy: d.sy, cover: d.members[16], count: d.members.length - 16, members: d.members.slice(16) });
        }
      }
      const nx = new Float64Array(N).fill(NaN), ny = new Float64Array(N).fill(NaN);
      for (const d of drawn) for (const b of d.members) { nx[b.i] = d.sx; ny[b.i] = d.sy; }
      const keep = new Set();
      for (const d of drawn) {
        let t = pool.get(d.cover.i);
        if (!t) {
          t = makeTile(d); pool.set(d.cover.i, t);
          const px = posX[d.cover.i];
          t.from = isNaN(px) ? null : [px, posY[d.cover.i]]; t.t0 = now;
          spriteStyle(t.img, d.cover);
        }
        if (t.exit) { t.exit = null; t.t0 = now; t.from = [t.x, t.y]; t.el.style.pointerEvents = ''; }
        keep.add(d.cover.i);
        t.el._d = d;
        const sig = d.count + ':' + (d.count > 1 ? d.members.length : '');
        if (sig !== t.sig || t.count !== d.count) {
          t.sig = sig; t.count = d.count;
          t.badge.textContent = d.count > 99 ? '99+' : d.count;
          t.el.classList.toggle('c', d.count > 1);
          t.tip.innerHTML = tipFor(d);
          t.el.setAttribute('aria-label', d.count === 1 ? `${d.cover.name}, ${d.cover.by}` : `${d.count} buildings, open the stack`);
        }
        let x = d.sx, y = d.sy, s = 1, a = 1;
        const p = reduced ? 1 : clamp((now - t.t0) / 240, 0, 1);
        if (p < 1) { moving = true; const e = easeOut(p); if (t.from) { x = t.from[0] + (x - t.from[0]) * e; y = t.from[1] + (y - t.from[1]) * e; } s = 0.55 + 0.45 * e; a = 0.2 + 0.8 * e; }
        t.x = x; t.y = y;
        t.el.style.transform = `translate3d(${(x - half).toFixed(1)}px,${(y - half).toFixed(1)}px,0) scale(${s.toFixed(3)})`;
        t.el.style.opacity = a;
        t.el.classList.toggle('hot', hot != null && d.members.some(b => b.i === hot));
      }
      for (const [i, t] of pool) {
        if (keep.has(i)) continue;
        if (!t.exit) { t.exit = { t0: now, x0: t.x, y0: t.y, tx: isNaN(nx[i]) ? t.x : nx[i], ty: isNaN(ny[i]) ? t.y : ny[i] }; }
        const p = reduced ? 1 : clamp((now - t.exit.t0) / 200, 0, 1);
        if (p >= 1) { t.el.remove(); pool.delete(i); continue; }
        moving = true;
        const e = easeOut(p), x = t.exit.x0 + (t.exit.tx - t.exit.x0) * e, y = t.exit.y0 + (t.exit.ty - t.exit.y0) * e;
        t.el.style.transform = `translate3d(${(x - half).toFixed(1)}px,${(y - half).toFixed(1)}px,0) scale(${(1 - 0.45 * e).toFixed(3)})`;
        t.el.style.opacity = 1 - e; t.el.style.pointerEvents = 'none';
      }
      posX.set(nx); posY.set(ny);
      lastDrawn = drawn;
      drawLand();
      drawLabels(drawn);
      if (moving) schedule(); else settleSoon();
    }
    function schedule() { if (!raf) raf = requestAnimationFrame(frame); }
    function settleSoon() { clearTimeout(settleTimer); settleTimer = setTimeout(settle, 140); }

    /* ---------- place names ---------- */
    const cityIndex = new Map();
    function rebuildCities() {
      cityIndex.clear();
      for (const b of active) { let c = cityIndex.get(b.place); if (!c) cityIndex.set(b.place, c = { name: b.city, cc: b.cc, members: [] }); c.members.push(b); }
      for (const c of cityIndex.values()) {
        c.members.sort(byN);
        let sx = 0, sy = 0, sz = 0, wx = 0, wy = 0;
        for (const b of c.members) { sx += b.clat * Math.cos(b.lonr); sy += b.clat * Math.sin(b.lonr); sz += b.slat; wx += b.wx; wy += b.wy; }
        Object.assign(c, geo(Math.atan2(sz, Math.hypot(sx, sy)) / RAD, Math.atan2(sy, sx) / RAD), { wx: wx / c.members.length, wy: wy / c.members.length });
      }
    }
    const countryCount = new Map();
    function rebuildCountries() { countryCount.clear(); for (const b of active) countryCount.set(b.cc, (countryCount.get(b.cc) || 0) + 1); }

    function drawLabels(drawn) {
      const k = kEq(), T = TILE, boxes = drawn.map(d => [d.sx - T / 2 - 2, d.sy - T / 2 - 2, d.sx + T / 2 + 2, d.sy + T / 2 + 10]);
      const want = [];
      for (const [cc, n] of countryCount) {
        const c = countryOf[cc]; if (!c) continue;
        const bw = c.box ? (c.box[2] - c.box[0]) * k : 0;
        if (bw < 70 || bw > V.vw * 1.8) continue;
        want.push({ key: 'c' + cc, text: c.name, n, kind: 'country', pt: c, w: c.name.length * 7.4 + (String(n).length + 1) * 7 + 10, pri: n * 3 });
      }
      if (k >= 9) for (const c of cityIndex.values()) {
        if (c.members.length < 2 && k < 90) continue;
        want.push({ key: 'y' + c.name + c.cc, text: c.name, n: c.members.length, kind: 'city', pt: c, w: c.name.length * 7.2 + (c.members.length > 1 ? (String(c.members.length).length + 1) * 7 : 0) + 10, pri: c.members.length });
      }
      want.sort((a, b) => b.pri - a.pri);
      const placed = [], keep = new Set();
      const cand = [[0, T * 0.5 + 14], [0, -(T * 0.5 + 12)], [T * 0.6, 0], [-T * 0.6, 0], [T * 0.7, T * 0.6], [-T * 0.7, T * 0.6], [0, T + 22], [0, 0]];
      for (const l of want) {
        const [sx, sy, vis] = toScreen(l.pt);
        if (!vis || sx < -40 || sy < -20 || sx > V.vw + 40 || sy > V.vh + 20) continue;
        let ok = null;
        for (const [dx, dy] of cand) {
          const x = sx + dx, y = sy + dy, r = [x - l.w / 2, y - 10, x + l.w / 2, y + 10];
          if (r[0] < 2 || r[1] < 2 || r[2] > V.vw - 2 || r[3] > V.vh - 2) continue;
          if (boxes.some(b => r[0] < b[2] && r[2] > b[0] && r[1] < b[3] && r[3] > b[1])) continue;
          if (placed.some(b => r[0] < b[2] && r[2] > b[0] && r[1] < b[3] && r[3] > b[1])) continue;
          ok = [x, y, r]; break;
        }
        if (!ok) continue;
        placed.push(ok[2]); keep.add(l.key);
        let el = labelPool.get(l.key);
        if (!el) {
          el = document.createElement('button'); el.type = 'button'; el.className = 'lb ' + l.kind;
          el.innerHTML = `${esc(l.text)}<small>${l.n}</small>`;
          el.addEventListener('click', () => fit(l.kind === 'country' ? active.filter(b => b.cc === l.pt.cc) : l.pt.members));
          labelsEl.appendChild(el); labelPool.set(l.key, el);
        } else if (el._n !== l.n) el.innerHTML = `${esc(l.text)}<small>${l.n}</small>`;
        el._n = l.n;
        el.style.transform = `translate(${ok[0].toFixed(1)}px,${ok[1].toFixed(1)}px) translate(-50%,-50%)`;
      }
      for (const [key, el] of labelPool) if (!keep.has(key)) { el.remove(); labelPool.delete(key); }
    }

    /* ---------- what is in view ---------- */
    function settle() {
      const inView = [];
      for (const b of active) { const [x, y, vis] = toScreen(b); if (vis && x >= 0 && y >= 0 && x <= V.vw && y <= V.vh) inView.push(b); }
      inView.sort(byN);
      const cs = new Map(); for (const b of inView) cs.set(b.cc, (cs.get(b.cc) || 0) + 1);
      const top = [...cs.entries()].sort((a, b) => b[1] - a[1])[0];
      let where;
      if (!inView.length) where = 'Nothing here yet';
      else if (V.z < 0.8) where = '';
      else if (cs.size === 1) where = `${top[1] === 1 ? inView[0].city + ', ' : ''}${W.names[top[0]] || top[0]} · ${top[1]}`;
      else where = `${cs.size} countries · mostly ${W.names[top[0]] || top[0]}`;
      const size = isPhone ? 88 : 44;
      ui.set({
        where,
        inview: inView.length ? `${inView.length} building${inView.length === 1 ? '' : 's'}` : '',
        rows: inView.slice(0, 300).map(b => ({ name: b.name, meta: `${b.by.split(',')[0]} · ${b.city} · ${b.year}`, bp: bpOf(b, size), open: () => openCard(b), hover: () => setHot(b.i) })),
      });
    }
    function setHot(i) { if (i !== hot) { hot = i; schedule(); } }

    /* ---------- clicks ---------- */
    function onTile(d) {
      hideHint();
      if (d.count === 1) { openCard(d.cover); return; }
      if (V.z >= ZMAX - 1.2 || sameSpot(d.members)) { spread = { cover: d.cover }; schedule(); return; }
      fit(d.members);
    }
    const sameSpot = ms => ms.every(b => Math.abs(b.lat - ms[0].lat) < 0.0015 && Math.abs(b.lon - ms[0].lon) < 0.0015);

    /* ---------- the opened building, handed to the chrome ---------- */
    function openCard(b) {
      const k = Math.floor(b.i / CARD.per), j = b.i % CARD.per;
      const city = cityIndex.get(b.place), inCountry = active.filter(x => x.cc === b.cc);
      let nearLabel = '', nearList = null;
      if (city && city.members.length > 1) { nearLabel = `More in ${b.city} · ${city.members.length}`; nearList = city.members; }
      else if (inCountry.length > 1) { nearLabel = `More in ${b.country} · ${inCountry.length}`; nearList = inCountry; }
      ui.card({
        sheet: 'm' + k, bp: `${(j % 16) / 15 * 100}% ${Math.floor(j / 16) / 9 * 100}%`, alt: 'Photo of ' + b.name,
        kicker: `${b.type} · ${b.movement}`, name: b.name, by: b.by,
        meta: `${b.city === b.country ? b.city : b.city + ', ' + b.country} · ${b.year}${b.approx ? ' · pin shows the city' : ''}`,
        study: b.study,
        credit: `${b.nimg} photo${b.nimg === 1 ? '' : 's'} on the site · ${b.credit ? 'Photo: ' + b.credit + ' · ' : ''}${b.license}`,
        source: b.source || '#', url: SITE + 'buildings/' + b.id + '/',
        nearLabel, nearClass: nearList ? '' : 'none', near: () => { ui.card(null); if (nearList) fit(nearList); },
      });
    }

    /* ---------- pointer, wheel, keys ---------- */
    const ptrs = new Map();
    let drag = null, rect = null, scale = [1, 1], suppressClick = false;
    const grab = () => { rect = map.getBoundingClientRect(); scale = [map.offsetWidth / (rect.width || 1), map.offsetHeight / (rect.height || 1)]; };
    const pt = e => [(e.clientX - rect.left) * scale[0], (e.clientY - rect.top) * scale[1]];
    map.addEventListener('pointerdown', e => {
      if (e.button) return;
      grab();
      map.setPointerCapture(e.pointerId);
      const [x, y] = pt(e);
      ptrs.set(e.pointerId, { x, y });
      anim = null;
      if (ptrs.size === 1) drag = { x, y, lx: x, ly: y, lt: performance.now(), vx: 0, vy: 0, moved: false };
      else if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; drag = { pinch: true, d: Math.hypot(a.x - b.x, a.y - b.y), mx: (a.x + b.x) / 2, my: (a.y + b.y) / 2, moved: true }; }
    });
    map.addEventListener('pointermove', e => {
      const p = ptrs.get(e.pointerId); if (!p || !drag) return;
      const [x, y] = pt(e); p.x = x; p.y = y;
      if (drag.pinch) {
        if (ptrs.size < 2) return;
        const [a, b] = [...ptrs.values()], d = Math.hypot(a.x - b.x, a.y - b.y), mx = (a.x + b.x) / 2, my = (a.y + b.y) / 2;
        if (d > 0 && drag.d > 0) zoomAt(mx, my, d / drag.d);
        panBy(mx - drag.mx, my - drag.my);
        drag.d = d; drag.mx = mx; drag.my = my;
      } else {
        if (!drag.moved && Math.hypot(x - drag.x, y - drag.y) < 4) return;
        if (!drag.moved) { drag.moved = true; map.classList.add('dragging'); spread = null; hideHint(); }
        const now = performance.now(), dt = Math.max(1, now - drag.lt);
        panBy(x - drag.lx, y - drag.ly);
        const a = Math.min(1, dt / 50);
        drag.vx = drag.vx * (1 - a) + ((x - drag.lx) / dt) * a; drag.vy = drag.vy * (1 - a) + ((y - drag.ly) / dt) * a;
        drag.lx = x; drag.ly = y; drag.lt = now;
      }
      schedule();
    });
    function endPointer(e) {
      if (!ptrs.has(e.pointerId)) return;
      ptrs.delete(e.pointerId);
      if (ptrs.size) { if (drag && drag.pinch && ptrs.size === 1) { const p = [...ptrs.values()][0]; drag = { x: p.x, y: p.y, lx: p.x, ly: p.y, lt: performance.now(), vx: 0, vy: 0, moved: true }; } return; }
      map.classList.remove('dragging');
      if (drag && drag.moved) {
        suppressClick = true; setTimeout(() => { suppressClick = false; }, 0);
        const stale = performance.now() - drag.lt > 80;
        if (!drag.pinch && !stale && !reduced && Math.hypot(drag.vx, drag.vy) > 0.05) { anim = { kind: 'inertia', vx: drag.vx, vy: drag.vy, last: performance.now() }; schedule(); }
        else settleSoon();
      }
      drag = null;
    }
    map.addEventListener('pointerup', endPointer);
    map.addEventListener('pointercancel', endPointer);
    map.addEventListener('click', e => { if (suppressClick) { e.stopPropagation(); e.preventDefault(); } }, true);
    map.addEventListener('wheel', e => {
      e.preventDefault(); hideHint();
      grab();
      const [x, y] = pt(e);
      const f = Math.exp(-e.deltaY * (e.ctrlKey ? 0.012 : 0.0019) * (e.deltaMode === 1 ? 18 : e.deltaMode === 2 ? 300 : 1));
      anim = null; zoomAt(x, y, f); schedule();
    }, { passive: false });
    map.addEventListener('dblclick', e => {
      grab();
      const [x, y] = pt(e), g = screenToGeo(x, y);
      if (!g) return;
      if (V.mode === 'atlas') { const k0 = K(V.z), wx = V.cx + (x - V.vw / 2) / k0, wy = V.cy + (y - V.vh / 2) / k0, k1 = K(Math.min(ZMAX, V.z + 1.5)); flyTo({ z: V.z + 1.5, cx: wx - (x - V.vw / 2) / k1, cy: wy - (y - V.vh / 2) / k1 }, 420); }
      else flyTo({ z: V.z + 1.5, lat: g.lat, lon: g.lon }, 420);
    });
    panel.addEventListener('keydown', e => {
      if (e.target.tagName === 'INPUT') return;
      const step = 90; let used = true;
      if (e.key === 'ArrowLeft') panBy(step, 0); else if (e.key === 'ArrowRight') panBy(-step, 0);
      else if (e.key === 'ArrowUp') panBy(0, step); else if (e.key === 'ArrowDown') panBy(0, -step);
      else if (e.key === '+' || e.key === '=') zoomAt(V.vw / 2, V.vh / 2, 1.7); else if (e.key === '-' || e.key === '_') zoomAt(V.vw / 2, V.vh / 2, 1 / 1.7);
      else if (e.key === '0') world(); else used = false;
      if (used) { e.preventDefault(); hideHint(); schedule(); }
    });
    let hintShown = true;
    function hideHint() { if (hintShown) { hintShown = false; ui.set({ hint: false }); } }

    /* ---------- chips and "show only" ---------- */
    function renderChips() {
      const c = new Map(); for (const b of active) c.set(b.cc, (c.get(b.cc) || 0) + 1);
      const top = [...c.entries()].sort((a, b) => b[1] - a[1]).slice(0, 9);
      ui.set({ chips: [{ label: 'World', n: '', go: () => { hideHint(); world(); } }].concat(top.map(([cc, n]) => ({ label: W.names[cc] || cc, n, go: () => { hideHint(); fit(active.filter(b => b.cc === cc)); } }))) });
    }
    let qTimer;
    function find(q) { clearTimeout(qTimer); qTimer = setTimeout(() => setQuery(q), 180); }
    function setQuery(q) {
      const words = fold(q.trim()).split(/\s+/).filter(Boolean);
      active = words.length ? B.filter(b => words.every(w => b.hay.includes(w))) : B.slice();
      setVersion++; spread = null;
      rebuildCities(); rebuildCountries(); renderChips();
      ui.set({ count: active.length === N ? `${N.toLocaleString('en')} buildings` : active.length ? `${active.length.toLocaleString('en')} of ${N.toLocaleString('en')} · ${q.trim()}` : `nothing matches “${q.trim()}”` });
      if (words.length && active.length && active.length <= 400) fit(active, ZMAX - 2); else schedule();
    }

    function setMode(mode) {
      if (mode === V.mode) return;
      const c = centreGeo(), z = V.z;
      V.mode = mode; measure(); setCentreGeo(c.lat, c.lon); V.z = clamp(z, 0, ZMAX);
      map.style.background = mode === 'globe' ? '#fff' : '';
      schedule();
    }
    function relayout() { measure(); schedule(); }
    new ResizeObserver(() => { if (map.offsetWidth) relayout(); }).observe(map);

    let seed = 3;
    function drawWall() {
      const first = B.filter(b => b.i < CARD.per);
      let s = seed; const r = () => { s = (s * 9301 + 49297) % 233280; return s / 233280; };
      const pick = first.slice().sort(() => r() - 0.5).slice(0, 20);
      ui.set({ wall: pick.map(b => ({ name: b.name, by: b.by.split(',')[0], bp: `${(b.i % 16) / 15 * 100}% ${Math.floor(b.i / 16) / 9 * 100}%` })) });
    }

    /* ---------- start ---------- */
    rebuildCities(); rebuildCountries(); renderChips(); drawWall();
    ui.set({ count: `${N.toLocaleString('en')} buildings`, total: `${N.toLocaleString('en')} buildings` });
    measure();
    if (isPhone) { setCentreGeo(28, 30); V.z = 1; }
    schedule();
    return {
      setMode, relayout, world, find,
      zoomIn: () => { zoomAt(V.vw / 2, V.vh / 2, 1.8); schedule(); },
      zoomOut: () => { zoomAt(V.vw / 2, V.vh / 2, 1 / 1.8); schedule(); },
      hot: setHot,
      shuffle: () => { seed = Math.floor(Math.random() * 1e6) + 1; drawWall(); },
      surprise: () => openCard(B[Math.floor(Math.random() * N)]),
      fit: list => fit(list), B, V,
      get drawn() { return lastDrawn; },
    };
