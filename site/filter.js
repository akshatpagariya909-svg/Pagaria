/* Discover Architecture: the filter panel ("Pattern language").
   Six tabs: Ideas and Type as line drawings, Movement as a timeline, Location as a map, Date as decade bars,
   Architect as an A–Z of faces. One search box finds any filter. Every count is live: it says how many
   buildings you would see with that option added to your other choices.
   Reads and changes the wall's state through window.DA (set up in app.js); drawings come from data/filters.js. */
(() => {
  'use strict';
  const DA = window.DA;
  if (!DA) return;
  const { ALL, state, esc, fold } = DA;
  const ART = window.FILTER_ART || { ideaGroups: [], typeGroups: [], ideaIcons: {}, typeIcons: {} };
  const ARCH = window.ARCHITECTS || { people: {}, buildings: {} };
  const $ = id => document.getElementById(id);
  const root = $('filters'), panel = $('fp');
  const F = state.filters;
  const DOT = 'M12 12h.01';
  const DECADES = ['Before 1880'].concat(Array.from({ length: 15 }, (_, i) => `${1880 + 10 * i}s`));
  const PERIODS = [['Before 1900', 0, 2], ['1900–1949', 3, 7], ['1950–1969', 8, 9], ['1970–1989', 10, 11], ['1990–2009', 12, 13], ['Since 2010', 14, 15]];
  const TABS = [['ideas', 'Ideas'], ['types', 'Type'], ['movs', 'Movement'], ['where', 'Location'], ['when', 'Date'], ['archs', 'Architect']];
  const ui = { tab: 'ideas', q: '', letter: '' };

  const icon = (d, size, cls) => `<svg class="${cls || ''}" width="${size}" height="${size}" viewBox="0 0 24 24" aria-hidden="true"><path d="${d || DOT}"/></svg>`;
  const plural = n => n === 1 ? '1 building' : `${n.toLocaleString('en')} buildings`;
  const countBy = (skip, key) => {
    const c = new Map();
    ALL.forEach(b => { if (DA.matches(b, skip)) [].concat(b[key]).forEach(v => c.set(v, (c.get(v) || 0) + 1)); });
    return c;
  };
  // Ideas or types missing from data/filters.js still appear, in an "Other" group.
  function withOther(groups, all) {
    const known = new Set(groups.flatMap(g => g[2]));
    const rest = [...all].filter(v => !known.has(v)).sort();
    return rest.length ? groups.concat([['Other', 'Not drawn yet.', rest]]) : groups;
  }
  const values = key => new Set(ALL.flatMap(b => [].concat(b[key])));

  /* ---------- tabs ---------- */
  function band(name, desc, items, big, cell) {
    const preview = big ? `<span class="fp-prev">${items.slice(0, 4).map(it => icon(it.d, 26, it.on ? 'on' : '')).join('')}</span>` : '';
    const pips = `<span class="fp-pips">${items.map(it => `<i class="${it.on ? 'on' : ''}"></i>`).join('')}</span>`;
    return `<div class="fp-band${big ? ' big' : ''}"><div class="fp-glabel">${preview}<b>${esc(name)}</b>${pips}<span class="fp-gdesc">${esc(desc)}</span></div>` +
      `<div class="fp-cells">${items.map(cell).join('')}</div></div>`;
  }
  function ideasTab() {
    const pool = ALL.filter(b => DA.matches(b, 'concepts') && [...F.concepts].every(c => b.concepts.includes(c)));
    const n = new Map();
    pool.forEach(b => b.concepts.forEach(c => n.set(c, (n.get(c) || 0) + 1)));
    const q = fold(ui.q);
    return withOther(ART.ideaGroups, values('concepts')).map(([g, desc, names]) => {
      const items = names.filter(v => !q || fold(v).includes(q)).map(v => ({ v, d: ART.ideaIcons[v], on: F.concepts.has(v), n: n.get(v) || 0 }));
      if (!items.length) return '';
      return band(g, desc, items, items.length > 4, it =>
        `<button type="button" class="fp-cell${it.n || it.on ? '' : ' none'}" aria-pressed="${it.on}" data-k="concepts" data-v="${esc(it.v)}">` +
        `${icon(it.d, 30)}<span><b>${esc(it.v)}</b><small>${plural(it.on ? pool.length : it.n)}</small></span></button>`);
    }).join('') || `<p class="fp-note">No idea matches “${esc(ui.q)}”.</p>`;
  }
  function typesTab() {
    const c = countBy('type', 'type'), max = Math.max(1, ...c.values());
    return withOther(ART.typeGroups, values('type')).map(([g, desc, names]) => {
      const items = names.map(v => ({ v, d: ART.typeIcons[v], on: F.type.has(v), n: c.get(v) || 0 }));
      return band(g, desc, items, items.length > 4, it =>
        `<button type="button" class="fp-cell type${it.n || it.on ? '' : ' none'}" aria-pressed="${it.on}" data-k="type" data-v="${esc(it.v)}">` +
        `${icon(it.d, 44)}<span><b>${esc(it.v)}</b><small>${plural(it.n)}</small><i class="fp-bar"><i style="width:${(it.n / max * 100).toFixed(0)}%"></i></i></span></button>`);
    }).join('');
  }
  function movsTab() {
    const c = countBy('movement', 'movement'), X0 = 1800, X1 = 2025;
    const pos = y => Math.max(0, Math.min(100, (y - X0) / (X1 - X0) * 100));
    const rows = [...values('movement')].map(m => {
      const ys = ALL.filter(b => b.movement === m).map(b => b.y).sort((a, b) => a - b);
      const at = q => ys[Math.min(ys.length - 1, Math.floor(q * (ys.length - 1)))];
      return { m, lo: at(0.1), hi: at(0.9), mid: at(0.5), first: ys[0], n: c.get(m) || 0, on: F.movement.has(m) };
    }).sort((a, b) => a.mid - b.mid);
    const axis = [1800, 1850, 1900, 1950, 2000].map(y => `<span style="left:${pos(y)}%">${y}</span>`).join('');
    return `<p class="fp-note">In the order they arrived. Each bar covers the years when most of its buildings were finished; the tick is the middle.</p>` +
      `<div class="fp-tl"><span></span><div class="fp-axis">${axis}</div><span></span>` +
      rows.map(r => {
        const a = pos(r.lo), w = Math.max(1.5, pos(Math.max(r.hi, r.lo + 4)) - a);
        const from = r.first < X0 ? `from ${r.first < 0 ? -r.first + ' BC' : r.first} · ` : '';
        return `<button type="button" class="fp-mrow${r.n || r.on ? '' : ' none'}" aria-pressed="${r.on}" data-k="movement" data-v="${esc(r.m)}" title="${esc(from)}mostly ${r.lo}–${r.hi}">` +
          `<b>${esc(r.m)}</b><span class="fp-track"><i style="left:${a}%;width:${w}%"></i><em style="left:${pos(r.mid)}%"></em></span><small>${r.n}</small></button>`;
      }).join('') + `</div>`;
  }
  let landCache = '';
  function whereTab() {
    const W = DA.world, rc = countBy('region', 'region'), cc = countBy('country', 'country');
    const regions = [...values('region')].sort();
    let map = '';
    if (W) {
      if (!landCache) landCache = Object.values(W.paths).join('');
      const byRegion = {};
      ALL.forEach(b => { (byRegion[b.region] = byRegion[b.region] || new Set()).add(b.country); });
      const max = Math.max(1, ...rc.values());
      const shapes = regions.map(r => {
        const n = rc.get(r) || 0, on = F.region.has(r);
        const fill = on ? 'var(--red)' : !n ? '#ECEAE5' : n / max > 0.5 ? '#A9A69E' : n / max > 0.2 ? '#BDBAB2' : '#D0CDC6';
        const d = [...byRegion[r]].map(c => W.paths[c] || '').join('');
        return `<path class="fp-reg" d="${d}" fill="${fill}" data-k="region" data-v="${esc(r)}"><title>${esc(r)}: ${n}</title></path>`;
      }).join('');
      const dots = ALL.filter(b => b.coords && DA.matches(b)).map(b => { const [x, y] = DA.project(b.coords[0], b.coords[1]); return `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="1.7"><title>${esc(b.name)}, ${esc(b.place.split(',')[0])}</title></circle>`; }).join('');
      map = `<svg class="fp-map" viewBox="0 18 ${W.w} 400" role="img" aria-label="World map by region, with a dot for each matching building"><path class="fp-land" d="${landCache}"/>${shapes}<g class="fp-dots">${dots}</g></svg>`;
    }
    const regionBtns = regions.map(r => `<button type="button" class="fp-opt${rc.get(r) || F.region.has(r) ? '' : ' none'}" aria-pressed="${F.region.has(r)}" data-k="region" data-v="${esc(r)}">${esc(r)} <small>${rc.get(r) || 0}</small></button>`).join('');
    const inRegion = c => !F.region.size || ALL.some(b => b.country === c && F.region.has(b.region));
    const countries = [...cc.keys()].filter(c => F.country.has(c) || inRegion(c)).sort((a, b) => cc.get(b) - cc.get(a)).slice(0, F.region.size ? 40 : 18);
    F.country.forEach(c => { if (!countries.includes(c)) countries.push(c); });
    const countryBtns = countries.map(c => `<button type="button" class="fp-opt" aria-pressed="${F.country.has(c)}" data-k="country" data-v="${esc(c)}">${esc(DA.countryName(c))} <small>${cc.get(c) || 0}</small></button>`).join('');
    return `<p class="fp-note">Tap a region on the map. Darker grey means more buildings; each dot is a building that matches your choices.</p>${map}` +
      `<div class="fp-row"><span class="fp-lab">Regions</span>${regionBtns}</div>` +
      `<div class="fp-row"><span class="fp-lab">${F.region.size ? 'Countries in these regions' : 'Countries with the most buildings'}</span>${countryBtns}</div>`;
  }
  function whenTab() {
    const c = countBy('decades', 'decade'), max = Math.max(1, ...c.values()), d = state.decades;
    const inRange = i => d && i >= d[0] && i <= d[1];
    const bars = DECADES.map((label, i) => `<button type="button" class="fp-dec${inRange(i) ? ' on' : ''}" data-dec="${i}" aria-label="${label}: ${plural(c.get(i) || 0)}">` +
      `<small>${c.get(i) || 0}</small><i style="height:${Math.max(1, Math.round((c.get(i) || 0) / max * 82))}%"></i><span>${i ? '’' + label.slice(2, 4) : 'Pre'}</span></button>`).join('');
    const lo = d ? d[0] : 0, hi = d ? d[1] : 15;
    const periods = PERIODS.map(([label, a, b]) => {
      let n = 0; for (let i = a; i <= b; i++) n += c.get(i) || 0;
      return `<button type="button" class="fp-opt" aria-pressed="${!!d && d[0] === a && d[1] === b}" data-period="${a},${b}">${label} <small>${n}</small></button>`;
    }).join('');
    return `<p class="fp-note">Each bar is a decade; its height is how many buildings were finished then. Drag the two handles, tap a bar, or pick a period.</p>` +
      `<div class="fp-decs">${bars}</div>` +
      `<div class="fp-range"><div class="fp-rtrack"><i style="left:${lo / 15 * 100}%;width:${(hi - lo) / 15 * 100}%" class="${d ? 'on' : ''}"></i>` +
      `<input type="range" min="0" max="15" step="1" value="${lo}" data-end="lo" aria-label="From"><input type="range" min="0" max="15" step="1" value="${hi}" data-end="hi" aria-label="To"></div>` +
      `<b>${d ? rangeLabel(d) : 'All years'}</b></div><div class="fp-row"><span class="fp-lab">Periods</span>${periods}</div>`;
  }
  function rangeLabel(d) {
    const from = d[0] === 0 ? 'Before 1880' : DECADES[d[0]].slice(0, 4);
    const to = d[1] === 0 ? '1879' : String(+DECADES[d[1]].slice(0, 4) + 9);
    return d[0] === d[1] && d[0] > 0 ? DECADES[d[0]] : `${from}–${to}`;
  }
  const surname = n => {
    const w = n.replace(/\s*\(.*?\)/g, '').split(/\s+/);
    return w.length < 2 || /&|\band\b|Architect|Studio|Partners|Office|Associates|Group|builders|Atelier|Design|Lab|\+/i.test(n) || n === n.toUpperCase() ? n : w[w.length - 1] + ' ' + w.slice(0, -1).join(' ');
  };
  const letterOf = n => { const ch = fold(surname(n))[0].toUpperCase(); return ch >= 'A' && ch <= 'Z' ? ch : '#'; };
  const initials = n => { const w = n.split(/\s+/).filter(x => /\p{L}/u.test(x)); return (w.length < 2 ? (w[0] || '?').slice(0, 3) : w[0][0] + w[w.length - 1][0]).toUpperCase(); };
  // A portrait only when the person's name matches the card's name, so a co-author's face never stands in.
  const faces = new Map();
  function faceOf(name) {
    if (faces.has(name)) return faces.get(name);
    const want = fold(name);
    let url = '';
    for (const b of ALL) {
      if (b.arch !== name) continue;
      for (const q of ARCH.buildings[b.id] || []) {
        const p = ARCH.people[q], got = p && fold(p.name);
        if (p && p.thumb && got && (want.includes(got) || got.includes(want))) { url = p.thumb; break; }
      }
      if (url) break;
    }
    faces.set(name, url);
    return url;
  }
  function archsTab() {
    const c = countBy('arch', 'arch');
    const names = [...values('arch')];
    const letters = new Map();
    names.forEach(n => { if (c.get(n)) letters.set(letterOf(n), true); });
    if (!ui.letter || !letters.has(ui.letter)) ui.letter = [...letters.keys()].sort()[0] || 'A';
    const bar = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'.split('').map(L => `<button type="button" class="fp-letter${letters.has(L) ? '' : ' none'}" aria-pressed="${ui.letter === L}" data-letter="${L}">${L}</button>`).join('');
    const list = names.filter(n => letterOf(n) === ui.letter)
      .sort((a, b) => fold(surname(a)).localeCompare(fold(surname(b))));
    const cards = list.map(n => {
      const face = faceOf(n), k = c.get(n) || 0;
      return `<button type="button" class="fp-face${k || F.arch.has(n) ? '' : ' none'}" aria-pressed="${F.arch.has(n)}" data-k="arch" data-v="${esc(n)}">` +
        (face ? `<img src="${esc(face)}" alt="" loading="lazy">` : `<span class="fp-ini">${esc(initials(n))}</span>`) + `<b>${esc(n)}</b><small>${plural(k)}</small></button>`;
    }).join('');
    return `<div class="fp-letters">${bar}</div><p class="fp-note">${list.length} under ${ui.letter}, sorted by surname. Portraits are black and white; initials until a free photo is found.</p><div class="fp-faces">${cards}</div>`;
  }

  /* ---------- search across every filter ---------- */
  function found() {
    const q = fold(ui.q.trim());
    if (!q) return '';
    const out = [];
    const add = (k, v, label, kind, badge, d) => {
      if (out.length >= 24 || !fold(label).includes(q)) return;
      out.push(`<button type="button" class="fp-found" data-k="${k}" data-v="${esc(v)}"><span class="fp-badge">${d ? icon(d, 24) : esc(badge)}</span><span><b>${esc(label)}</b><small>${kind}</small></span></button>`);
    };
    values('concepts').forEach(v => add('concepts', v, v, 'Idea', '', ART.ideaIcons[v] || DOT));
    values('type').forEach(v => add('type', v, v, 'Type', '', ART.typeIcons[v] || DOT));
    values('movement').forEach(v => add('movement', v, v, 'Movement', 'M'));
    PERIODS.forEach(([label, a, b]) => add('period', `${a},${b}`, label, 'Date', '↔'));
    values('region').forEach(v => add('region', v, v, 'Region', '◎'));
    values('country').forEach(v => add('country', v, DA.countryName(v), 'Country', v));
    values('arch').forEach(v => add('arch', v, v, 'Architect', initials(v)));
    return `<div class="fp-results" role="listbox" aria-label="Matching filters">${out.join('') || `<p class="fp-note">No filter matches “${esc(ui.q)}”.</p>`}</div>`;
  }

  /* ---------- footer: what is chosen, what often goes with it ---------- */
  function footer() {
    const chips = [];
    const label = (k, v) => k === 'country' ? DA.countryName(v) : v;
    ['concepts', 'type', 'movement', 'region', 'country', 'arch'].forEach(k => F[k].forEach(v => chips.push(`<button type="button" class="fp-chip" data-rm="${k}" data-v="${esc(v)}" aria-label="Remove ${esc(label(k, v))}">${esc(label(k, v))} ×</button>`)));
    if (state.decades) chips.push(`<button type="button" class="fp-chip" data-rm="decades" aria-label="Remove the date range">${rangeLabel(state.decades)} ×</button>`);
    const hits = ALL.filter(b => DA.matches(b));
    let also = '';
    if (F.concepts.size) {
      const co = new Map();
      hits.forEach(b => b.concepts.forEach(c => { if (!F.concepts.has(c)) co.set(c, (co.get(c) || 0) + 1); }));
      also = [...co.entries()].sort((a, b) => b[1] - a[1]).slice(0, 3)
        .map(([c, n]) => `<button type="button" class="fp-also" data-k="concepts" data-v="${esc(c)}">+ ${esc(c)} <small>${n}</small></button>`).join('');
      if (also) also = `<span class="fp-lab">Often found with</span>${also}`;
    }
    return `<div class="fp-chosen">${chips.length ? `<span class="fp-lab">Chosen</span>${chips.join('')}` : `<span class="fp-lab">Nothing chosen yet</span>`}${also}</div>` +
      `<div class="fp-actions"><button type="button" class="btn ghost" data-clear>Clear all</button>` +
      `<button type="button" class="btn go" data-show>${hits.length ? 'Show ' + plural(hits.length) : 'Nothing matches: remove one'}</button></div>`;
  }

  /* ---------- draw and react ---------- */
  const BODY = { ideas: ideasTab, types: typesTab, movs: movsTab, where: whereTab, when: whenTab, archs: archsTab };
  function refresh(keepSearch) {
    if (root.hidden) return;
    const scroll = panel.querySelector('.fp-body');
    const top = scroll ? scroll.scrollTop : 0;
    const tabs = TABS.map(([k, label]) => {
      const n = k === 'ideas' ? F.concepts.size : k === 'types' ? F.type.size : k === 'movs' ? F.movement.size : k === 'where' ? F.region.size + F.country.size : k === 'when' ? (state.decades ? 1 : 0) : F.arch.size;
      return `<button type="button" class="fp-tab" aria-pressed="${ui.tab === k}" data-tab="${k}">${label}${n ? ` <small>· ${n}</small>` : ''}</button>`;
    }).join('');
    if (!keepSearch) {
      panel.innerHTML = `<div class="fp-head"><div class="fp-tabs">${tabs}</div>` +
        `<label class="fp-search"><svg viewBox="0 0 24 24" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="m20 20-4-4"/></svg><span class="sr">Search all filters</span><input type="search" id="fpQ" placeholder="Search all filters…" autocomplete="off" value="${esc(ui.q)}"></label>` +
        `<button type="button" class="fp-close" data-close aria-label="Close filters"><svg viewBox="0 0 24 24"><path d="M5 5l14 14M19 5 5 19"/></svg></button></div>` +
        `<div class="fp-found-wrap" id="fpFound">${found()}</div><div class="fp-body">${BODY[ui.tab]()}</div><div class="fp-foot">${footer()}</div>`;
    } else {
      panel.querySelector('.fp-tabs').innerHTML = tabs;
      $('fpFound').innerHTML = found();
      panel.querySelector('.fp-body').innerHTML = BODY[ui.tab]();
      panel.querySelector('.fp-foot').innerHTML = footer();
    }
    const body = panel.querySelector('.fp-body');
    if (body) body.scrollTop = top;
  }
  function changed() { DA.apply(); refresh(true); }
  function toggle(k, v) {
    if (k === 'period') { const [a, b] = v.split(',').map(Number); state.decades = state.decades && state.decades[0] === a && state.decades[1] === b ? null : [a, b]; return; }
    const set = F[k];
    set.has(v) ? set.delete(v) : set.add(v);
  }
  function setRange(lo, hi) { state.decades = lo === 0 && hi === 15 ? null : [Math.min(lo, hi), Math.max(lo, hi)]; }

  panel.addEventListener('click', e => {
    const t = e.target.closest('button, path.fp-reg');
    if (!t) return;
    if (t.dataset.close != null) { DA.close(); return; }
    if (t.dataset.show != null) { DA.close(); return; }
    if (t.dataset.clear != null) { Object.values(F).forEach(s => s.clear()); state.decades = null; changed(); return; }
    if (t.dataset.tab) { ui.tab = t.dataset.tab; refresh(true); panel.querySelector('.fp-body').scrollTop = 0; return; }
    if (t.dataset.letter) { ui.letter = t.dataset.letter; refresh(true); return; }
    if (t.dataset.period) { toggle('period', t.dataset.period); changed(); return; }
    if (t.dataset.dec != null) {
      const i = +t.dataset.dec, d = state.decades;
      if (!d) setRange(i, i);
      else if (d[0] === i && d[1] === i) state.decades = null;
      else setRange(i < d[0] ? i : d[0], i > d[1] ? i : i < d[0] ? d[1] : i);
      changed(); return;
    }
    if (t.dataset.rm) { if (t.dataset.rm === 'decades') state.decades = null; else F[t.dataset.rm].delete(t.dataset.v); changed(); return; }
    if (t.dataset.k) {
      const k = t.dataset.k, v = t.dataset.v;
      if (t.classList.contains('fp-found')) {   // from the search list: add it and jump to its tab
        if (k === 'period') { const [a, b] = v.split(',').map(Number); state.decades = [a, b]; }
        else F[k].add(v);
        ui.q = ''; $('fpQ').value = '';
        ui.tab = { concepts: 'ideas', type: 'types', movement: 'movs', region: 'where', country: 'where', period: 'when', arch: 'archs' }[k];
        if (k === 'arch') ui.letter = letterOf(v);
        changed(); return;
      }
      toggle(k, v); changed();
    }
  });
  panel.addEventListener('input', e => {
    if (e.target.id === 'fpQ') { ui.q = e.target.value; refresh(true); return; }
    const end = e.target.dataset.end;
    if (end) {
      const ins = panel.querySelectorAll('.fp-rtrack input');
      let lo = +ins[0].value, hi = +ins[1].value;
      if (end === 'lo' && lo > hi) hi = lo;
      if (end === 'hi' && hi < lo) lo = hi;
      ins[0].value = lo; ins[1].value = hi;
      setRange(lo, hi); DA.apply();
      // while dragging, update the highlight and the footer only; the counts follow when the handle is let go
      const d = state.decades, track = panel.querySelector('.fp-rtrack i');
      track.style.left = `${lo / 15 * 100}%`; track.style.width = `${(hi - lo) / 15 * 100}%`; track.classList.toggle('on', !!d);
      panel.querySelector('.fp-range b').textContent = d ? rangeLabel(d) : 'All years';
      panel.querySelectorAll('.fp-dec').forEach((bar, i) => bar.classList.toggle('on', !!d && i >= d[0] && i <= d[1]));
      panel.querySelector('.fp-foot').innerHTML = footer();
    }
  });
  panel.addEventListener('change', e => { if (e.target.dataset.end) refresh(true); });
  root.addEventListener('click', e => { if (e.target === root) DA.close(); });

  window.DAFilter = { refresh: () => refresh(false) };
})();
