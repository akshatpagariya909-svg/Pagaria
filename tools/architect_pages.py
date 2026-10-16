"""One static page per architect: findgreatarchitecture.com/architects/<slug>/ (v24, option B, approved 16 Oct 2026).

Left pane: portrait, name, the write-up, links about the whole body of work, books, similar architects.
Right pane: every one of their buildings on the wall, in two columns, with a row of idea keywords above.
Plain HTML and CSS (site/architect.css) plus a small script that sorts and filters the tiles.

Inputs (nothing is typed per architect here):
  tools/architect_bios/results/bios_*.json   write-ups and checked links, made by the Opus writer chat
  site/data/wall data (buildings.js, links.js), names.js (one name per architect), architects.js (portraits), books.js

An architect gets a page when a write-up for them exists and is not skipped. Adding the next batch of write-ups
and running tools/build_pages.py is all it takes. Called from build_pages.main(); `bp` is the build_pages module.
"""
import json
import re
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import names_py

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / 'tools' / 'architect_bios' / 'results'
LOGOS = {'wikipedia': 'wikipedia.png', 'archdaily': 'archdaily.png', 'dezeen': 'dezeen.png', 'divisare': 'divisare.png',
         'wikiarquitectura': 'wikiarquitectura.svg', 'archinform': 'archinform.png'}
OWN_SITE = re.compile(r'foundation|fundação|fondation|fondazione|stiftung|studio|partners|architects|workshop|projects|oma\b|office', re.I)
IDEA_CHIPS = 9


def slugify(name):
    s = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode().lower()
    s = re.sub(r'[^a-z0-9]+', '-', s.replace('&', ' and ')).strip('-')
    return s or 'architect'


def load_bios():
    """name -> write-up record, from every results file; a later file wins."""
    out = {}
    for f in sorted(RESULTS.glob('bios_*.json')) if RESULTS.exists() else []:
        for r in json.loads(f.read_text()):
            if r.get('skip') or not (r.get('bio') or '').strip():
                continue
            out[r['name']] = r
    return out


def sentences(text):
    return re.split(r'(?<=[.!?])\s+(?=[A-Z“"])', text.strip())


def first_sentence(text, limit=120):
    s = sentences(text)[0]
    if len(s) <= limit:
        return s
    cut = s[:limit].rsplit(' ', 1)[0].rstrip(',;:')
    return cut + '…'


def plan(items):
    """Which architects get a page: {name: record with slug and buildings}. Runs before any page is written, so building
    pages and the wall's data can link to them."""
    nm = names_py.Names(items)
    by = defaultdict(list)
    for b in items:
        for n in nm.list(b['by']):
            by[n].append(b)
    out = {}
    for name, rec in load_bios().items():
        key = nm.canon(name)
        if key not in by:
            continue
        out[key] = {**rec, 'name': key, 'slug': slugify(key), 'buildings': sorted(by[key], key=lambda b: (b.get('y') or 0, b['name']))}
    return nm, out


def ratio_of(b):
    im = (b.get('images') or [None])[0]
    return max(2 / 3, min(1.5, im['h'] / im['w'])) if im and im.get('w') else 0.75


def tile(bp, b, up):
    im = (b.get('images') or [None])[0]
    city = b['place'].split(',')[0]
    ideas = '|'.join(b.get('concepts') or [])
    r = ratio_of(b)
    img = (f'<img src="{bp.e(bp.at(up, im["thumb"]))}" width="{im["w"]}" height="{im["h"]}" loading="lazy" decoding="async" alt="{bp.e(b["name"])}, {bp.e(city)}">'
           if im else '<span class="slot">No free photos yet</span>')
    return (f'<a class="t" href="{up}buildings/{b["id"]}/" data-y="{b.get("y") or 0}" data-n="{bp.e(b["name"])}" data-c="{bp.e(city)}" '
            f'data-i="{bp.e(ideas)}" data-r="{r:.3f}" style="aspect-ratio:1/{r:.3f}">{img}'
            f'<span class="cap"><b>{bp.e(b["name"])}</b><span class="r2">{bp.e(b["year"])} · {bp.e(city)}</span></span></a>')


def deal(tiles, ratios, ncols=2):
    heights, cols = [0.0] * ncols, [[] for _ in range(ncols)]
    for t, r in zip(tiles, ratios):
        i = heights.index(min(heights))
        cols[i].append(t)
        heights[i] += r + 0.06
    return ''.join(f'<div class="col">{"".join(c)}</div>' for c in cols)


def portrait_for(rec, people, nm):
    """The best free portrait for this name from architects.js, or None."""
    want = nm.canon(rec['name'])
    best = people.get(rec.get('qid') or '')
    if best and best.get('thumb'):
        return best
    for p in people.values():
        if p.get('thumb') and nm.canon(p.get('name', '')) == want:
            return p
    return None


def link_logo(bp, lk, name, up):
    site = (lk.get('site') or '').lower()
    for k, f in LOGOS.items():
        if k in site:
            return f'<img src="{up}images/logos/c/{f}" alt="" width="22" height="22">'
    if OWN_SITE.search(lk.get('site') or '') or name.split()[-1].lower() in site:
        return ('<svg viewBox="0 0 24 24" width="22" height="22" aria-hidden="true"><circle cx="12" cy="12" r="9"/>'
                '<path d="M3 12h18M12 3c2.6 2.8 3.8 5.8 3.8 9s-1.2 6.2-3.8 9c-2.6-2.8-3.8-5.8-3.8-9S9.4 5.8 12 3z"/></svg>')
    letter = (lk.get('site') or '?')[:1].upper()
    return f'<span class="mono" aria-hidden="true">{bp.e(letter)}</span>'


def usable_links(rec):
    """Only links the checker did not reject. (A link with no check recorded yet is kept off the page.)"""
    return [l for l in rec.get('overview_links') or [] if l.get('url') and l.get('ok') is not False and l.get('checked')]


def books_for(bp, key, nm, books):
    mine = [b for b in books if key in {nm.canon(a) for a in b.get('architects') or []}]
    surname = key.split()[-1].lower()
    mine.sort(key=lambda b: (surname not in b['title'].lower(), b.get('y') or 0))  # books named for them first
    return mine[:6]


def title_for(bp, name, drawings):
    what = 'photos, plans & key works' if drawings else 'photos & key works'
    for o in (f'{name} buildings: {what} · {bp.NAME}', f'{name} buildings: {what}', f'{name} buildings and projects', f'{name} buildings', name):
        if len(o) <= bp.TITLE_MAX:
            return o
    return name


def desc_for(bp, rec, n):
    tail = f' {n} buildings with free photos, key features and links.'
    head = first_sentence(rec['bio'], bp.DESC_MAX - len(tail))
    return head + tail


def similar(plans, key, n=4):
    """Architects with pages whose buildings share the most ideas with this one's (cosine on idea counts)."""
    vec = {k: Counter(c for b in p['buildings'] for c in b.get('concepts') or []) for k, p in plans.items()}
    norm = {k: sum(v * v for v in c.values()) ** 0.5 or 1 for k, c in vec.items()}
    a = vec[key]
    scored = [(sum(v * vec[k][c] for c, v in a.items()) / (norm[key] * norm[k]), k) for k in plans if k != key]
    return [k for s, k in sorted(scored, reverse=True) if s > 0][:n]


SCRIPT = """<script>
(function () {
  var cols = [].slice.call(document.querySelectorAll('.wallpane .col')), tiles = [].slice.call(document.querySelectorAll('.wallpane .t'));
  var count = document.getElementById('shown'), st = { sort: 'y', idea: '' };
  var by = { y: function (a, b) { return a.dataset.y - b.dataset.y || a.dataset.n.localeCompare(b.dataset.n); },
             n: function (a, b) { return a.dataset.n.localeCompare(b.dataset.n); },
             c: function (a, b) { return a.dataset.c.localeCompare(b.dataset.c) || a.dataset.y - b.dataset.y; } };
  function deal() {
    var list = tiles.filter(function (t) { return !st.idea || t.dataset.i.split('|').indexOf(st.idea) > -1; }).sort(by[st.sort]);
    var h = cols.map(function () { return 0; });
    cols.forEach(function (c) { while (c.firstChild) c.removeChild(c.firstChild); });
    list.forEach(function (t) { var k = h.indexOf(Math.min.apply(null, h)); cols[k].appendChild(t); h[k] += parseFloat(t.dataset.r) + 0.06; });
    if (count) count.textContent = list.length;
  }
  [].forEach.call(document.querySelectorAll('[data-sort]'), function (b) {
    b.addEventListener('click', function () {
      st.sort = b.dataset.sort;
      [].forEach.call(document.querySelectorAll('[data-sort]'), function (x) { x.setAttribute('aria-pressed', x === b); });
      deal();
    });
  });
  [].forEach.call(document.querySelectorAll('[data-idea]'), function (b) {
    b.addEventListener('click', function () {
      var on = b.getAttribute('aria-pressed') === 'true';
      [].forEach.call(document.querySelectorAll('[data-idea]'), function (x) { x.setAttribute('aria-pressed', 'false'); });
      st.idea = on ? '' : b.dataset.idea;
      if (!on) b.setAttribute('aria-pressed', 'true');
      deal();
    });
  });
})();
</script>"""


def page(bp, plans, key, ctx):
    rec, up = plans[key], '../../'
    name, bs = rec['name'], rec['buildings']
    url = f'{bp.BASE}architects/{rec["slug"]}/'
    n = len(bs)
    drawings = any(bp.has_drawings(b) for b in bs)
    title, desc = title_for(bp, name, drawings), desc_for(bp, rec, n)
    port = portrait_for(rec, ctx['people'], ctx['nm'])
    paras = [p.strip() for p in re.split(r'\n\s*\n', rec['bio'].strip()) if p.strip()]
    facts = ' · '.join(x for x in (rec.get('born_died') and rec['born_died'][:1].upper() + rec['born_died'][1:],
                                    rec.get('country') and rec['country'][:1].upper() + rec['country'][1:],
                                    f'{n} buildings on the wall') if x)
    # portrait (always black and white, credited, linked to its source)
    fig = ''
    if port:
        big = port['thumb'].replace('/250px-', '/500px-')
        cred = ' · '.join(x for x in (port.get('credit'), port.get('license')) if x)
        src = f' · <a href="{bp.e(port["source"])}" rel="noopener">source</a>' if port.get('source') else ''
        fig = (f'<figure class="portrait"><img src="{bp.e(big)}" alt="{bp.e(name)}" width="500" height="640" '
               f'onerror="this.onerror=null;this.src=this.dataset.fallback" data-fallback="{bp.e(port["thumb"])}">'
               f'<figcaption>{bp.e(cred)}{src}</figcaption></figure>')
    more = (f'<details class="more"><summary><span class="m">Read more</span><span class="l">Show less</span></summary>{"".join(f"<p>{bp.e(p)}</p>" for p in paras[1:])}</details>' if len(paras) > 1 else '')
    rows = ''.join(f'<a href="{bp.e(l["url"])}" rel="noopener">{link_logo(bp, l, name, up)}<span class="lt"><b>{bp.e(l["site"])}</b>'
                   f'<span> · {bp.e(l.get("title") or l.get("why") or "")}</span></span><span class="go" aria-hidden="true">↗</span></a>'
                   for l in usable_links(rec))
    links = f'<section class="blk"><h2>Read about the work</h2><div class="rows">{rows}</div></section>' if rows else ''
    bks = books_for(bp, key, ctx['nm'], ctx['books'])
    bk = ''.join(
        f'<a class="bk" href="{up}#book:{bp.e(b["id"])}"><span class="cv">' +
        (f'<img src="{bp.e(bp.at(up, b["cover"]["thumb"]))}" alt="" loading="lazy" width="78" height="117">' if b.get('cover') and b['cover'].get('thumb')
         else f'<span class="standin">{bp.e(b["title"].split(":")[0])}</span>') +
        f'</span><span class="bt">{bp.e(b["title"])}<small>{bp.e(b["by"])}, {bp.e(b["year"])}</small></span></a>' for b in bks)
    books = f'<section class="blk"><h2>Books to read</h2><div class="books">{bk}</div></section>' if bk else ''
    sim = similar(plans, key) if len(plans) > 1 else []
    simh = (f'<section class="blk"><h2>Similar architects</h2><p class="sim">' +
            ' · '.join(f'<a href="{up}architects/{plans[k]["slug"]}/">{bp.e(k)}</a>' for k in sim) +
            '</p><p class="hint">Picked by the ideas their buildings share.</p></section>') if sim else ''
    ideas = Counter(c for b in bs for c in b.get('concepts') or [])
    chips = ''.join(f'<button type="button" class="chip" data-idea="{bp.e(c)}" aria-pressed="false">{bp.e(c)} <span>{k}</span></button>'
                    for c, k in ideas.most_common(IDEA_CHIPS) if k >= 2)
    kw = f'<div class="ideas" role="group" aria-label="Narrow by idea">{chips}</div>' if chips else ''
    tiles = [tile(bp, b, up) for b in bs]
    grid = deal(tiles, [ratio_of(b) for b in bs])
    sorts = ''.join(f'<button type="button" class="chip" data-sort="{k}" aria-pressed="{str(k == "y").lower()}">{t}</button>' for k, t in (('y', 'Year'), ('n', 'A to Z'), ('c', 'Place')))
    kind = 'Organization' if rec.get('kind') == 'practice' else 'Person'
    ld = [{'@context': 'https://schema.org', '@type': kind, 'name': name, 'url': url, 'description': first_sentence(rec['bio'], 300),
           **({'image': port['thumb']} if port else {}),
           'sameAs': [l['url'] for l in usable_links(rec)],
           'knowsAbout': [c for c, _ in ideas.most_common(5)]},
          {'@context': 'https://schema.org', '@type': 'ItemList', 'name': f'{name} buildings',
           'itemListElement': [{'@type': 'ListItem', 'position': i + 1, 'url': f'{bp.BASE}buildings/{b["id"]}/', 'name': b['name']} for i, b in enumerate(bs)]},
          {'@context': 'https://schema.org', '@type': 'BreadcrumbList', 'itemListElement': [
              {'@type': 'ListItem', 'position': 1, 'name': 'Architects', 'item': bp.BASE + 'architects/'},
              {'@type': 'ListItem', 'position': 2, 'name': name, 'item': url}]}]
    extra = (f'<link rel="stylesheet" href="{up}architect.css?v={bp.fingerprint(bp.SITE / "architect.css")}">\n'
             + '\n'.join(f'<script type="application/ld+json">{json.dumps(x, ensure_ascii=False)}</script>' for x in ld))
    og = bp.at(bp.BASE, bs[0]['images'][0]['thumb']) if bs and bs[0].get('images') else bp.BASE + 'og.jpg'
    head = bp.HEAD.format(title=bp.e(title), desc=bp.e(desc), url=bp.e(url), site=bp.NAME, ogtype='profile', ogtitle=bp.e(f'{name} buildings'),
                          image=bp.e(og), up=up, wallhash='', extra=extra, total=bp.TOTAL, css_v=bp.CSS_V)
    body = (
        f'<main class="arch">\n'
        f'<aside class="rail">{fig}<p class="kicker">{"Practice" if kind == "Organization" else "Architect"}</p>'
        f'<h1>{bp.e(name)}</h1><p class="facts">{bp.e(facts)}</p>'
        f'<div class="bio"><p>{bp.e(paras[0])}</p>{more}</div>'
        f'<a class="cta" href="#buildings">See the {n} buildings ↓</a>'
        f'{links}{books}{simh}</aside>\n'
        f'<section class="wallpane" id="buildings"><div class="whead"><h2>{bp.e(name)} buildings <span><span id="shown">{n}</span></span></h2>'
        f'<div class="sorts"><span>Sort</span>{sorts}</div></div>{kw}'
        f'<div class="cols">{grid}</div>'
        f'<footer class="foot" data-nosnippet><p>Photos are public domain or Creative Commons, credited under each photo and sourced from Wikimedia Commons.</p>'
        f'<p><a href="{up}">Find Great Architecture</a> · <a href="{up}architects/">Architects</a> · <a href="{up}buildings/">All buildings</a></p></footer></section>\n'
        f'</main>\n'
        f'<nav class="dock" data-nosnippet aria-label="Browse"><a href="{up}">Home</a><a class="go" href="{up}#surprise">Surprise me</a></nav>\n'
        f'{SCRIPT}\n</body>\n</html>\n')
    return head + body


def index_page(bp, plans):
    up = '../'
    url = bp.BASE + 'architects/'
    desc = 'Architects whose buildings are on Find Great Architecture: a short write-up, links, books and every building of theirs with free photos.'
    head = bp.HEAD.format(title=f'Architects A–Z · {bp.NAME}', desc=bp.e(desc), url=url, site=bp.NAME, ogtype='website', ogtitle='Architects A–Z',
                          image=bp.BASE + 'og.jpg', up=up, wallhash='', extra='', total=bp.TOTAL, css_v=bp.CSS_V)
    rows = ''.join(f'<a href="{p["slug"]}/"><b>{bp.e(k)}</b><small>{len(p["buildings"])} buildings</small></a>' for k, p in sorted(plans.items(), key=lambda kv: names_py.fold(kv[0])))
    body = f'<main class="index"><h1>Architects</h1><p class="lede">{bp.e(desc)}</p><div class="names">{rows}</div></main>\n'
    return head + body + bp.FOOT.format(up=up, total=bp.TOTAL, css_v=bp.CSS_V)


def build(bp, items):
    """Write site/architects/ and return {name: slug}. Pages left over from earlier runs are removed."""
    nm, plans = plan(items)
    out = bp.SITE / 'architects'
    out.mkdir(exist_ok=True)
    if not plans:
        return nm, plans
    ctx = {'nm': nm, 'books': bp.read_js('books.js', 'BOOKS') or [],
           'people': (bp.read_js('architects.js', 'ARCHITECTS') or {}).get('people', {})}
    keep = set()
    for key, p in plans.items():
        d = out / p['slug']
        d.mkdir(exist_ok=True)
        (d / 'index.html').write_text(page(bp, plans, key, ctx))
        keep.add(p['slug'])
    (out / 'index.html').write_text(index_page(bp, plans))
    for d in out.iterdir():
        if d.is_dir() and d.name not in keep:
            for f in d.iterdir():
                f.unlink()
            d.rmdir()
    return nm, plans
