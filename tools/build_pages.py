#!/usr/bin/env python3
"""Build one static page per building, a building index, link previews, a sitemap and robots.txt.

  python3 tools/build_pages.py

Run it again whenever site/data/buildings.js or site/data/links.js changes. Pages are plain HTML (no JavaScript),
so search engines and link previews see everything. Output:
  site/buildings/<id>/index.html   one page per building, with its photo gallery
  site/buildings/index.html        A–Z list of all buildings
  site/og.jpg                      preview image for the home page
  site/sitemap.xml, site/robots.txt
  site/index.html                  the "About this wall" block between <!-- about:start --> and <!-- about:end -->

Page titles say what the page has in the words students search for (photos, plans & sections, case study):
"plans & sections" appears only when a verified link leads to drawings. Pages with an entry in
site/data/summaries.js get an "About" section quoted from Wikipedia. tools/pageviews.json ranks the
buildings people look up most (Wikipedia pageviews, Oct 2025 to Sep 2026) for the home page's list.
"""
import html, json, os, random, re, urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
BASE = os.environ.get('SITE_URL', 'https://findgreatarchitecture.com/')
NAME = 'Find Great Architecture'

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
CSS_V = ''  # a short fingerprint of pages.css, so browsers fetch it again when it changes


def at(base, path):
    """Our own files are relative to the site; photos served by Wikimedia are full URLs."""
    return path if path.startswith('http') else base + path


def read_js(name, var):
    """A data file that sets window.<var> = {...}; missing file means {}."""
    path = SITE / 'data' / name
    return json.loads(path.read_text().split(f'window.{var} = ', 1)[1].rstrip().rstrip(';')) if path.exists() else {}


def load():
    text = (SITE / 'data' / 'buildings.js').read_text()
    items = json.loads(text.split('window.BUILDINGS = ', 1)[1].rstrip().rstrip(';'))
    found = read_js('links.js', 'LINKS')  # from tools/find_links.py
    about = read_js('summaries.js', 'SUMMARIES')  # from tools/fetch_summaries.py
    return [{**b, **found.get(b['id'], {}), **({'about': about[b['id']]} if b['id'] in about else {})} for b in items]


def place_full(b):
    parts = [p.strip() for p in b['place'].split(',')]
    if len(parts) == 2 and parts[1] in COUNTRY:
        return f'{parts[0]}, {COUNTRY[parts[1]]}'
    return b['place']


# Sites whose verified links lead to drawings, so a page may say "plans & sections" in its title.
DRAWING_SITES = {'WikiArquitectura', 'ArchDaily'}


def has_drawings(b):
    return any(l['site'] in DRAWING_SITES for l in (b.get('links') or []))


def offer(b):
    """What the page gives a student, in the words they search for: only what it really has."""
    parts = ['photos'] if b.get('images') else []
    if has_drawings(b):
        parts.append('plans & sections')
    return ', '.join(parts)


def anonymous(b):
    return b['by'].lower().startswith('unknown')


def title(b):
    """Villa Savoye — Le Corbusier, 1931: photos, plans & sections for a case study.
    Searches add the architect, "plan", "section", "photos" and "case study" to a building's name."""
    who = b['place'].split(',')[0] if anonymous(b) else b['by']
    what = offer(b)
    return f"{b['name']} — {who}, {b['year']}: " + (f'{what} for a case study' if what else 'notes for a case study')


# How a typology reads in a sentence ("a housing complex in Mumbai"); types not listed read as themselves, lowercased.
NOUN = {'Culture & sport': 'cultural building', 'Office & tower': 'office building', 'Education': 'campus building',
        'Housing': 'housing complex', 'Infrastructure': 'structure', 'Civic': 'civic building', 'Religious': 'religious building',
        'Hospitality': 'hotel or resort', 'Health': 'healthcare building', 'Public space': 'public space', 'Workplace': 'workplace'}


def summary(b):
    who = 'by unknown builders' if anonymous(b) else f"by {b['by']}"
    noun = NOUN.get(b['type'], b['type'].lower())
    a = 'an' if noun[0] in 'aeiou' else 'a'
    verb, tail = ('was', f"; it was {GONE[b['id']]}") if b['id'] in GONE else ('is', '')
    gives = (['free photos with credits'] if b.get('images') else []) + (['links to plans and sections'] if has_drawings(b) else [])
    extra = ' ' + ', '.join(gives + ['notes for a case study']).capitalize() + '.'
    return f"{b['name']} {verb} {a} {noun} in {place_full(b)} {who}, {b['year']}{tail}. Key features: {b['study']}{extra}"


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
<link rel="icon" href="{up}favicon.png" type="image/png" sizes="32x32">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
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
<link href="https://fonts.googleapis.com/css2?family=Big+Shoulders+Display:wght@700..900&family=Barlow:ital,wght@0,400;0,500;0,600;0,700;1,400&family=Barlow+Condensed:wght@500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{up}pages.css?v={css_v}">
<script src="{up}analytics.js"></script>
{extra}
</head>
<body>
<header class="top">
  <a class="mark" href="{up}">Find great<br><span class="accent">Architecture.</span></a>
  <nav><a class="all" href="{up}buildings/" data-tip="A huge, growing collection of buildings">All buildings</a><a class="wall" href="{up}{wallhash}">Back to the wall</a></nav>
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
  <p><a href="{up}">Find Great Architecture</a> · <a href="{up}buildings/">All buildings</a></p>
</footer>
<nav class="dock" aria-label="Browse">
  <a href="{up}">Home</a>
  <a class="go" href="{up}#surprise">Surprise me</a>
</nav>
</body>
</html>
"""


def about_block(b):
    """A short description quoted from Wikipedia (tools/fetch_summaries.py), credited and linked. Most pages have none."""
    a = b.get('about')
    if not a:
        return ''
    paras = ''.join(f'<p>{e(p)}</p>' for p in a['paragraphs'])
    return (f'<section class="block about"><h2>About {e(b["name"])}</h2>{paras}'
            f'<p class="src">Shortened from <a href="{e(a["url"])}" rel="noopener">Wikipedia</a>, '
            f'<a href="https://creativecommons.org/licenses/by-sa/4.0/" rel="noopener">CC BY-SA 4.0</a>.</p></section>\n')


def home_block(items):
    """Crawler-readable text for the home page, which is otherwise drawn by JavaScript: what the wall is, and the
    twenty buildings people look up most (tools/pageviews.json). Written between the about:start/end markers."""
    pv = json.loads((ROOT / 'tools' / 'pageviews.json').read_text()) if (ROOT / 'tools' / 'pageviews.json').exists() else {}
    top = sorted((b for b in items if b['id'] in pv), key=lambda b: -pv[b['id']])[:20]
    places = sorted({COUNTRY.get(b['place'].split(', ')[-1], '') for b in items} - {''})
    south = [b for b in sorted((b for b in items if b['id'] in pv), key=lambda b: -pv[b['id']]) if b['region'] == 'South Asia'][:10]
    row = lambda b: f'<li><a href="buildings/{b["id"]}/">{e(b["name"])}</a> <small>{e(b["place"].split(",")[0] if anonymous(b) else b["by"])}</small></li>'
    return (f'<section class="about-wall" id="about">\n'
            f'  <h2>About this wall</h2>\n'
            f'  <p>Find Great Architecture is a huge, growing wall of buildings for architecture students, from the modern masters to '
            f'contemporary and parametric work, brutalism and regionalism, with India and South Asia first. Every building has '
            f'free photos with credits, its key features, and links to plans, sections and articles for a case study. '
            f'Buildings from all over the world; <a href="buildings/">see them all A–Z</a>.</p>\n'
            f'  <h3>Most looked-up buildings</h3>\n  <ol>{"".join(row(b) for b in top)}</ol>\n'
            f'  <h3>Most looked-up in South Asia</h3>\n  <ol>{"".join(row(b) for b in south)}</ol>\n'
            f'</section>')


def building_page(b, items):
    up = '../../'
    url = f"{BASE}buildings/{b['id']}/"
    desc = summary(b)
    ims = b.get('images') or []
    og = at(BASE, ims[0]['src']) if ims else BASE + 'og.jpg'
    ld = {'@context': 'https://schema.org', '@type': 'LandmarksOrHistoricalBuildings', 'name': b['name'], 'description': desc, 'url': url,
          'address': place_full(b),
          'image': [{'@type': 'ImageObject', 'contentUrl': at(BASE, im['src']), 'creditText': im.get('credit') or '', 'license': im.get('license') or '',
                     'acquireLicensePage': im.get('source') or ''} for im in ims],
          'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE}}
    if b.get('wiki'):
        ld['sameAs'] = b['wiki']
    head = HEAD.format(title=e(f"{title(b)} · {NAME}"), desc=e(desc), url=e(url), site=NAME, ogtype='article',
                       ogtitle=e(f"{b['name']} — {b['by']}, {b['year']}"), image=e(og), up=up, wallhash='#' + b['id'],
                       extra='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>', total=TOTAL, css_v=CSS_V)
    if ims:
        figs = ''.join(
            f'<figure id="photo-{k + 1}"><img src="{e(at(up, im["src"]))}" alt="{e(b["name"])}: {e(im["caption"])}" width="{im["w"]}" height="{im["h"]}" loading="{"eager" if k == 0 else "lazy"}">'
            f'{"<span class=" + chr(34) + "nophoto" + chr(34) + ">Photos unavailable</span>" if im.get("kind") == "Drawing" else ""}'
            f'<figcaption><b>{k + 1}/{len(ims)}{"" if im.get("kind") == "Drawing" else " · " + e(im["caption"])}</b><span>{(("" if im.get("kind") == "Drawing" else "Photo: ") + e(im["credit"].rstrip(".")) + " · ") if im.get("credit") else ""}{e(im["license"])}'
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
{about_block(b)}<section class="block"><h2>Go deeper</h2><div class="links">{''.join(f'<a href="{e(u)}" rel="noopener"{"" if d else " class=" + chr(34) + "guess" + chr(34)}><b class="lt"><span>{e(k)}</span>{e(n)} ↗</b>{logo_html(n, up)}</a>' for k, n, u, d in links(b))}</div></section>
<section class="block"><h2>Drift onward</h2><div class="rel">{rel_html}</div></section>
"""
    return head + body + FOOT.format(up=up, total=TOTAL, css_v=CSS_V)


def index_page(items):
    up = '../'
    url = BASE + 'buildings/'
    desc = f'Every building on Find Great Architecture, chosen for architecture students: modern masters, brutalism, regionalism, Japan, contemporary and parametric work, plus a few historic precedents.'
    head = HEAD.format(title=f'All buildings A–Z · {NAME}', desc=e(desc), url=url, site=NAME, ogtype='website',
                       ogtitle='All buildings A–Z', image=BASE + 'og.jpg', up=up, wallhash='', extra='', total=TOTAL, css_v=CSS_V)
    rows = ''.join(
        f'<a href="{x["id"]}/"><span class="ph">{f"<img src={chr(34)}{e(at(up, x["images"][0]["thumb"]))}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if x.get("images") else ""}</span>'
        f'<b>{e(x["name"])}</b><small>{e(x["by"])} · {e(x["year"])}</small></a>'
        for x in sorted(items, key=lambda x: x['name'].lower()))
    body = f'<main class="index"><h1>All buildings</h1><p class="lede">{e(desc)}</p><div class="grid">{rows}</div></main>\n'
    return head + body + FOOT.format(up=up, total=TOTAL, css_v=CSS_V)


FONTS = Path(__file__).resolve().parent / 'fonts'
INK, RED = (17, 17, 16), (218, 58, 38)
# Strong exterior photos for the share image; the coolest go under the name.
OG_PICKS = ['saynatsalo-town-hall', 'phillips-exeter-academy-library', 'salk-institute', 'tate-modern', 'ningbo-history-museum', 'kimbell-art-museum']


def redness(im):
    """How red/brick a photo is, so red buildings stay away from the red "Architecture."."""
    r, g, b = [sum(c) / len(c) for c in zip(*im.convert('RGB').resize((24, 16)).getdata())]
    return r - (g + b) / 2


# Go deeper (v14 · A): each site's own icon, cut out in ink (site/images/logos/ink), red with its cell on hover.
LOGOS = {'ArchDaily': 'archdaily.png', 'WikiArquitectura': 'wikiarquitectura.svg', 'Dezeen': 'dezeen.png', 'Divisare': 'divisare.png',
         'archINFORM': 'archinform.png', 'Wikipedia': 'wikipedia.png', 'YouTube': 'youtube.png', 'Wikimedia Commons': 'commons.svg',
         'Map': 'openstreetmap.svg'}
GLOBE = '<svg class="lg" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.8 5.8 3.8 9s-1.2 6.2-3.8 9c-2.6-2.8-3.8-5.8-3.8-9S9.4 5.8 12 3z"/></svg>'


def logo_html(n, up):
    if n == 'Official website':
        return GLOBE
    return f'<i class="lg" aria-hidden="true" style="--m: url({up}images/logos/ink/{LOGOS[n]})"></i>' if n in LOGOS else ''


def og_image(items):
    """The share image: six buildings, with the name and address over a dark fade at the bottom.
    The coolest (least red) photos go along the bottom row, under the name."""
    from PIL import Image, ImageDraw, ImageFont
    W, H = 1200, 630
    canvas = Image.new('RGB', (W, H), INK)
    by_id = {x['id']: x for x in items}
    pics = [by_id[i] for i in OG_PICKS if i in by_id and by_id[i].get('images')]
    if len(pics) < 6:  # fall back to any photos, never drawings
        more = [x for x in items if x.get('images') and not x['images'][0]['thumb'].endswith('.svg') and x not in pics]
        random.Random(4).shuffle(more)
        pics += more[:6 - len(pics)]
    ims = [Image.open(SITE / x['images'][0]['thumb']).convert('RGB') for x in pics[:6]]
    if len([i for i in OG_PICKS if i in by_id]) < 6:  # fallback photos: warm on top, cool below
        ims = sorted(ims, key=redness, reverse=True)[:3] + sorted(ims, key=redness)[:3]
    cols, rows, gap = 3, 2, 6
    cw, ch = (W - gap * (cols - 1)) // cols, (H - gap * (rows - 1)) // rows
    for k, im in enumerate(ims):
        r = max(cw / im.width, ch / im.height)
        im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
        left, top = (im.width - cw) // 2, (im.height - ch) // 2
        canvas.paste(im.crop((left, top, left + cw, top + ch)), ((k % cols) * (cw + gap), (k // cols) * (ch + gap)))
    fade = Image.new('L', (1, H))
    for y in range(H):
        t = max(0.0, (y - H * 0.36) / (H * 0.5))
        fade.putpixel((0, y), int(255 * min(0.88, t * 1.1)))
    canvas = Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), canvas, fade.resize((W, H)))
    d = ImageDraw.Draw(canvas)
    big = ImageFont.truetype(str(FONTS / 'BigShouldersDisplay-Black.ttf'), 104)
    small = ImageFont.truetype(str(FONTS / 'BarlowCondensed-SemiBold.ttf'), 30)
    x0, base = 44, H - 40
    d.text((x0, base - 92), 'ARCHITECTURE.', font=big, fill=RED, anchor='ls')
    d.text((x0, base - 184), 'FIND GREAT', font=big, fill=(255, 255, 255), anchor='ls')
    d.text((W - 44, base - 96), 'FINDGREATARCHITECTURE.COM', font=small, fill=(255, 255, 255), anchor='rs')
    canvas.save(SITE / 'og.jpg', quality=85, optimize=True)


def icons():
    """The tab and home-screen icon: a black A (for Architecture) with the red full stop, on white (v19)."""
    from PIL import Image, ImageDraw, ImageFont
    for size, name in [(32, 'favicon.png'), (180, 'apple-touch-icon.png'), (512, 'icon-512.png')]:
        S = size * 4
        im = Image.new('RGB', (S, S), (255, 255, 255))
        d = ImageDraw.Draw(im)
        f = ImageFont.truetype(str(FONTS / 'BigShouldersDisplay-Black.ttf'), int(S * 0.86))
        fw = d.textlength('A', font=f)
        dw = d.textlength('.', font=f)
        x = (S - fw - dw) / 2
        y = S * 0.5 + f.getbbox('A')[3] * 0.5 - f.getbbox('A')[1] * 0.5
        d.text((x, y), 'A', font=f, fill=INK, anchor='ls')
        d.text((x + fw, y), '.', font=f, fill=RED, anchor='ls')
        im.resize((size, size), Image.LANCZOS).save(SITE / name)


def fingerprint(path):
    import hashlib
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def stamp_wall():
    """Add ?v=<fingerprint> to the wall's scripts and stylesheet, so a new version reaches browsers at once
    instead of waiting for their cached copy to expire."""
    page = SITE / 'index.html'
    html = page.read_text()
    for name in ('styles.css', 'data/buildings.js', 'data/names.js', 'data/links.js', 'data/architects.js', 'data/pritzker.js', 'data/filters.js', 'data/world.js', 'data/books.js', 'app.js', 'filter.js'):
        html = re.sub(r'(["\'])' + re.escape(name) + r'(\?v=[0-9a-f]*)?\1', lambda m: f'{m.group(1)}{name}?v={fingerprint(SITE / name)}{m.group(1)}', html)
    page.write_text(html)
    play = SITE / 'play' / 'index.html'  # the game page: its own script and styles, and the buildings it asks about
    if play.exists():
        html = play.read_text()
        for name, path in (('play.css', SITE / 'play' / 'play.css'), ('play.js', SITE / 'play' / 'play.js'), ('../data/buildings.js', SITE / 'data' / 'buildings.js'), ('../data/names.js', SITE / 'data' / 'names.js')):
            html = re.sub(r'(["\'])' + re.escape(name) + r'(\?v=[0-9a-f]*)?\1', lambda m: f'{m.group(1)}{name}?v={fingerprint(path)}{m.group(1)}', html)
        play.write_text(html)


def main():
    import sys
    if '--stamp' in sys.argv:  # used by the deploy workflow: refresh the fingerprints only
        stamp_wall()
        return
    global TOTAL, CSS_V
    items = load()
    TOTAL = f'{len(items):,}'
    CSS_V = fingerprint(SITE / 'pages.css')
    page = SITE / 'index.html'
    page.write_text(re.sub(r'<!-- about:start -->.*?<!-- about:end -->', lambda m: '<!-- about:start -->\n' + home_block(items) + '\n<!-- about:end -->',
                           page.read_text(), flags=re.S))
    stamp_wall()
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
    icons()
    print(f'Built {len(items)} building pages, the index, og.jpg, sitemap.xml and robots.txt.')


if __name__ == '__main__':
    main()
