#!/usr/bin/env python3
"""Build one static page per building, a building index, link previews, a sitemap and robots.txt.

  python3 tools/build_pages.py

Run it again whenever site/data/buildings.js or site/data/links.js changes. Pages are plain HTML (no JavaScript),
so search engines and link previews see everything. Output:
  site/buildings/<id>/index.html   one page per building, with its photo gallery
  site/buildings/index.html        A–Z list of all buildings
  site/og.jpg                      preview image for the home page
  site/sitemap.xml, site/robots.txt
"""
import html, json, os, random, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
BASE = os.environ.get('SITE_URL', 'https://akshatpagariya909-svg.github.io/Pagaria/')
NAME = 'Discover Architecture'

COUNTRY = {
    'US': 'United States', 'BD': 'Bangladesh', 'IN': 'India', 'JP': 'Japan', 'ES': 'Spain', 'DE': 'Germany',
    'CZ': 'Czech Republic', 'AU': 'Australia', 'UK': 'United Kingdom', 'CA': 'Canada', 'BR': 'Brazil',
    'FR': 'France', 'IT': 'Italy', 'CN': 'China', 'NL': 'Netherlands', 'FI': 'Finland', 'MX': 'Mexico',
    'DK': 'Denmark', 'PT': 'Portugal', 'CH': 'Switzerland', 'NO': 'Norway', 'TR': 'Türkiye', 'CL': 'Chile',
    'LK': 'Sri Lanka', 'VN': 'Vietnam', 'EG': 'Egypt', 'BF': 'Burkina Faso', 'ZA': 'South Africa',
    'AE': 'United Arab Emirates', 'AZ': 'Azerbaijan',
}
# Buildings that no longer stand, so their pages say "was".
GONE = {'nakagin-capsule-tower': 'demolished in 2022'}

e = lambda s: html.escape(str(s or ''), quote=True)
q = lambda s: urllib.parse.quote(str(s))

TOTAL = '100'  # set from the data in main()


def at(base, path):
    """Our own files are relative to the site; photos served by Wikimedia are full URLs."""
    return path if path.startswith('http') else base + path


def load():
    text = (SITE / 'data' / 'buildings.js').read_text()
    items = json.loads(text.split('window.BUILDINGS = ', 1)[1].rstrip().rstrip(';'))
    links = SITE / 'data' / 'links.js'  # from tools/find_links.py
    found = json.loads(links.read_text().split('window.LINKS = ', 1)[1].rstrip().rstrip(';')) if links.exists() else {}
    return [{**b, **found.get(b['id'], {})} for b in items]


def place_full(b):
    parts = [p.strip() for p in b['place'].split(',')]
    if len(parts) == 2 and parts[1] in COUNTRY:
        return f'{parts[0]}, {COUNTRY[parts[1]]}'
    return b['place']


def summary(b):
    who = 'by unknown builders' if b['by'].lower().startswith('unknown') else f"by {b['by']}"
    noun = b['type'].lower().replace('culture & sport', 'cultural building').replace('office & tower', 'office building')
    a = 'an' if noun[0] in 'aeiou' else 'a'
    verb, tail = ('was', f"; it was {GONE[b['id']]}") if b['id'] in GONE else ('is', '')
    return f"{b['name']} {verb} {a} {noun} in {place_full(b)} {who}, {b['year']}{tail}. Study it for: {b['study'][0].lower()}{b['study'][1:]}"


def related(b, items, n=6):
    def score(x):
        shared = len(set(x['concepts']) & set(b['concepts']))
        s = shared * 2 + (1 if x['type'] == b['type'] else 0) + (2.5 if x['by'] == b['by'] else 0)
        return s + ((x['n'] * 13 + b['n'] * 7) % 17) / 100
    return sorted((x for x in items if x['id'] != b['id']), key=score, reverse=True)[:n]


CORE = [('Projects & drawings', 'ArchDaily', 'archdaily.com'), ('Plans & sections', 'WikiArquitectura', 'wikiarquitectura.com'),
        ('News & features', 'Dezeen', 'dezeen.com')]


def links(b):
    """(kind, site, url, direct): verified pages from tools/find_links.py, then the core sites' top search result."""
    name, city, found = b['name'], b['place'].split(',')[0], b.get('links') or []
    out = [(l['kind'], l['site'], l['url'], True) for l in found]
    out += [(k, n, 'https://duckduckgo.com/?q=' + q(f"\\ site:{d} {name} {b['by']}"), False)
            for k, n, d in CORE if not any(l['site'] == n for l in found)]
    commons = 'https://commons.wikimedia.org/wiki/' + q(b['commons'].replace(' ', '_')) if b.get('commons') else 'https://commons.wikimedia.org/w/index.php?search=' + q(name)
    return out + [
        ('Read', 'Wikipedia', b.get('wiki') or 'https://en.wikipedia.org/w/index.php?search=' + q(f'{name} {city}'), bool(b.get('wiki'))),
        ('Watch', 'YouTube', 'https://www.youtube.com/results?search_query=' + q(f"{name} {b['by']} architecture"), True),
        ('More photos', 'Wikimedia Commons', commons, True),
    ]


HEAD = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:site_name" content="{site}">
<meta property="og:type" content="{ogtype}">
<meta property="og:title" content="{ogtitle}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{image}">
<meta name="twitter:card" content="summary_large_image">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Archivo:wdth,wght@62..125,100..900&family=IBM+Plex+Mono:wght@400;500&family=Newsreader:ital,opsz,wght@0,6..72,400;1,6..72,400&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}pages.css">
{extra}
</head>
<body>
<header class="top">
  <a class="mark" href="{up}">Discover<br>Architecture</a>
  <nav><a href="{up}buildings/">All {total}</a><a class="wall" href="{up}{wallhash}">Back to the wall</a></nav>
</header>
"""

# Thumbnails scroll the strip sideways rather than jumping the page to the anchor.
GALLERY_JS = """<script>
(function () {
  var g = document.currentScript.previousElementSibling, s = g.querySelector('.slides'), t = [].slice.call(g.querySelectorAll('.thumbs a'));
  function mark() { var k = Math.round(s.scrollLeft / s.clientWidth); t.forEach(function (a, i) { if (i === k) a.setAttribute('aria-current', 'true'); else a.removeAttribute('aria-current'); }); }
  t.forEach(function (a, i) { a.addEventListener('click', function (ev) { ev.preventDefault(); s.scrollTo({ left: i * s.clientWidth }); }); });
  s.addEventListener('scroll', function () { clearTimeout(s._m); s._m = setTimeout(mark, 60); }, { passive: true });
  mark();
})();
</script>"""

FOOT = """<footer class="foot">
  <p>Photos are public domain or Creative Commons, credited under each photo and sourced from Wikimedia Commons.</p>
  <p><a href="{up}">Discover Architecture</a> · <a href="{up}buildings/">All {total} buildings</a></p>
</footer>
</body>
</html>
"""


def building_page(b, items):
    up = '../../'
    url = f"{BASE}buildings/{b['id']}/"
    desc = summary(b)
    ims = b.get('images') or []
    og = at(BASE, ims[0]['src']) if ims else BASE + 'og.jpg'
    ld = {'@context': 'https://schema.org', '@type': 'LandmarksOrHistoricalBuildings', 'name': b['name'], 'description': desc, 'url': url,
          'address': place_full(b),
          'image': [{'@type': 'ImageObject', 'contentUrl': at(BASE, im['src']), 'creditText': im.get('credit') or '', 'license': im.get('license') or '',
                     'acquireLicensePage': im.get('source') or ''} for im in ims]}
    head = HEAD.format(title=e(f"{b['name']}, {b['by']} · {NAME}"), desc=e(desc), url=e(url), site=NAME, ogtype='article',
                       ogtitle=e(f"{b['name']} — {b['by']}, {b['year']}"), image=e(og), up=up, wallhash='#' + b['id'],
                       extra='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>', total=TOTAL)
    if ims:
        figs = ''.join(
            f'<figure id="photo-{k + 1}"><img src="{e(at(up, im["src"]))}" alt="{e(b["name"])}: {e(im["caption"])}" width="{im["w"]}" height="{im["h"]}" loading="{"eager" if k == 0 else "lazy"}">'
            f'<figcaption><b>{k + 1}/{len(ims)} · {e(im["caption"])}</b><span>{("Photo: " + e(im["credit"].rstrip(".")) + " · ") if im.get("credit") else ""}{e(im["license"])}'
            f'{(" · <a href=" + chr(34) + e(im["source"]) + chr(34) + ">source</a>") if im.get("source") else ""}</span></figcaption></figure>'
            for k, im in enumerate(ims))
        thumbs = ''.join(f'<a href="#photo-{k + 1}"><img src="{e(at(up, im["thumb"]))}" alt="Photo {k + 1}: {e(im["caption"])}" loading="lazy"></a>' for k, im in enumerate(ims))
        gallery = f'<div class="gallery"><div class="slides">{figs}</div><div class="thumbs">{thumbs}</div></div>' + GALLERY_JS
    else:
        gallery = '<div class="gallery none"><p>No free photos yet. Use the links to see photos and drawings elsewhere.</p></div>'
    facts = [('Architect', b['by']), ('Place', place_full(b)), ('Year', b['year']), ('Typology', b['type']), ('Movement', b['movement']), ('Region', b['region'])]
    rel_html = ''.join(
        f'<a href="{up}buildings/{x["id"]}/"><span class="ph">{f"<img src={chr(34)}{e(at(up, x["images"][0]["thumb"]))}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if x.get("images") else ""}</span>'
        f'<b>{e(x["name"])}</b><small>{e(x["by"])} · {e(x["year"])}</small></a>' for x in related(b, items))
    body = f"""<main class="page">
  {gallery}
  <article class="info">
    <p class="kicker">{e(b['type'])} · {e(b['movement'])}</p>
    <h1>{e(b['name'])}</h1>
    <p class="by">{e(b['by'])} · {e(place_full(b))} · {e(b['year'])}</p>
    <p class="study"><span>Key features</span>{e(b['study'])}</p>
    <ul class="tags">{''.join(f'<li>{e(c)}</li>' for c in b['concepts'])}</ul>
    <dl class="facts">{''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in facts)}</dl>
    <a class="cta" href="{up}#{b['id']}">See it on the wall</a>
  </article>
</main>
<section class="block"><h2>Go deeper</h2><div class="links">{''.join(f'<a href="{e(u)}" rel="noopener"{"" if d else " class=" + chr(34) + "guess" + chr(34)}><span>{e(k)}</span>{e(n)} ↗</a>' for k, n, u, d in links(b))}</div></section>
<section class="block"><h2>Drift onward</h2><div class="rel">{rel_html}</div></section>
"""
    return head + body + FOOT.format(up=up, total=TOTAL)


def index_page(items):
    up = '../'
    url = BASE + 'buildings/'
    desc = f'All {TOTAL} buildings on Discover Architecture, chosen for architecture students: modern masters, brutalism, regionalism, Japan, contemporary and parametric work, plus a few historic precedents.'
    head = HEAD.format(title=f'All {TOTAL} buildings · {NAME}', desc=e(desc), url=url, site=NAME, ogtype='website',
                       ogtitle=f'All {TOTAL} buildings', image=BASE + 'og.jpg', up=up, wallhash='', extra='', total=TOTAL)
    rows = ''.join(
        f'<a href="{x["id"]}/"><span class="ph">{f"<img src={chr(34)}{e(at(up, x["images"][0]["thumb"]))}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if x.get("images") else ""}</span>'
        f'<b>{e(x["name"])}</b><small>{e(x["by"])} · {e(x["year"])}</small></a>'
        for x in sorted(items, key=lambda x: x['name'].lower()))
    body = f'<main class="index"><h1>All {TOTAL} buildings</h1><p class="lede">{e(desc)}</p><div class="grid">{rows}</div></main>\n'
    return head + body + FOOT.format(up=up, total=TOTAL)


def og_image(items):
    from PIL import Image
    W, H = 1200, 630
    canvas = Image.new('RGB', (W, H), (237, 237, 233))
    pics = [x for x in items if x.get('images')]
    random.Random(4).shuffle(pics)
    cols, rows, gap = 6, 3, 6
    cw, ch = (W - gap * (cols + 1)) // cols, (H - gap * (rows + 1)) // rows
    for k, x in enumerate(pics[:cols * rows]):
        im = Image.open(SITE / x['images'][0]['thumb']).convert('RGB')
        r = max(cw / im.width, ch / im.height)
        im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
        left, top = (im.width - cw) // 2, (im.height - ch) // 2
        canvas.paste(im.crop((left, top, left + cw, top + ch)), (gap + (k % cols) * (cw + gap), gap + (k // cols) * (ch + gap)))
    canvas.save(SITE / 'og.jpg', quality=85, optimize=True)


def main():
    global TOTAL
    items = load()
    TOTAL = f'{len(items):,}'
    for b in items:
        out = SITE / 'buildings' / b['id']
        out.mkdir(parents=True, exist_ok=True)
        (out / 'index.html').write_text(building_page(b, items))
    (SITE / 'buildings' / 'index.html').write_text(index_page(items))
    if any(x.get('images') for x in items):
        og_image(items)
    urls = [BASE, BASE + 'buildings/'] + [f"{BASE}buildings/{b['id']}/" for b in items]
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                       + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    (SITE / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n')
    print(f'Built {len(items)} building pages, the index, og.jpg, sitemap.xml and robots.txt.')


if __name__ == '__main__':
    main()
