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
import html, json, os, random, re, textwrap, urllib.parse
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


TITLE_MAX = 60   # Google cuts a title at about 580 px, roughly 60 characters
DESC_MAX = 155   # and a description at about 155


def title(b):
    """Villa Savoye — Le Corbusier, 1931: photos, plans & sections   (at most TITLE_MAX characters).
    Searches add the architect, "plan", "section" and "photos" to a building's name, so those come first and nothing
    is left to be cut: a longer, fuller wording is used only when it fits."""
    who = b['place'].split(',')[0] if anonymous(b) else b['by']
    what = offer(b)
    name, year = b['name'], b['year']
    head = f"{name} — {who}, {year}"
    options = ([f"{head}: {what} for a case study · {NAME}", f"{head}: {what} for a case study", f"{head}: {what}"] if what
               else [f"{head}: notes for a case study · {NAME}", f"{head}: notes for a case study"]) + [head]
    for o in options:
        if len(o) <= TITLE_MAX:
            return o
    # A long list of architects: leave the credit out of the title (it is on the page) rather than cut a name in half.
    for o in ([f"{name}, {year}: {what}"] if what else []) + [f"{name}, {year}", name]:
        if len(o) <= TITLE_MAX:
            return o
    return name


# How a typology reads in a sentence ("a housing complex in Mumbai"); types not listed read as themselves, lowercased.
NOUN = {'Culture & sport': 'cultural building', 'Office & tower': 'office building', 'Education': 'campus building',
        'Housing': 'housing complex', 'Infrastructure': 'structure', 'Civic': 'civic building', 'Religious': 'religious building',
        'Hospitality': 'hotel or resort', 'Health': 'healthcare building', 'Public space': 'public space', 'Workplace': 'workplace'}


def summary(b):
    """The page description, at most DESC_MAX characters so Google shows all of it: what the building is, its key
    features (cut at a word if they do not fit), and what the page offers."""
    noun = NOUN.get(b['type'], b['type'].lower())
    a = 'an' if noun[0] in 'aeiou' else 'a'
    verb, tail = ('was', f"; it was {GONE[b['id']]}") if b['id'] in GONE else ('is', '')
    who = 'by unknown builders' if anonymous(b) else f"by {b['by']}"
    first = f"{b['name']} {verb} {a} {noun} in {place_full(b)} {who}, {b['year']}{tail}."
    if len(first) > 110:  # a long credit: the architect is in the title and on the page
        first = f"{b['name']} {verb} {a} {noun} in {place_full(b)}, {b['year']}{tail}."
    gives = (['photos'] if b.get('images') else []) + (['plans and sections'] if has_drawings(b) else [])
    offer_text = f" Free {', '.join(gives)}." if gives else ' Notes for a case study.'
    label = ' Key features: '
    study = ' '.join(b['study'].split()).rstrip('.')
    room = DESC_MAX - len(first) - len(offer_text) - len(label) - 1  # 1 for the full stop after the features
    if room < 25:
        return (first + offer_text)[:DESC_MAX]
    if len(study) > room:
        study = study[:room - 1].rsplit(' ', 1)[0].rstrip(' ,;:-') + '…'
        return f"{first}{label}{study}{offer_text}"
    return f"{first}{label}{study}.{offer_text}"


def related(b, items, n=6):
    def score(x):
        shared = len(set(x['concepts']) & set(b['concepts']))
        s = shared * 2 + (1 if x['type'] == b['type'] else 0) + (2.5 if x['by'] == b['by'] else 0)
        return s + ((x['n'] * 13 + b['n'] * 7) % 17) / 100
    return sorted((x for x in items if x['id'] != b['id']), key=score, reverse=True)[:n]


# Without a verified page on one of these sites, the link opens that site's own search for the building.
CORE = [('Projects & drawings', 'ArchDaily', 'https://www.archdaily.com/search/projects?q='),
        ('Plans & sections', 'WikiArquitectura', 'https://en.wikiarquitectura.com/?s='),
        ('News & features', 'Dezeen', 'https://www.dezeen.com/?s=')]


def links(b):
    """(kind, site, url, direct): verified pages from tools/find_links.py, then the core sites' own search."""
    name, city, found = b['name'], b['place'].split(',')[0], b.get('links') or []
    out = [(l['kind'], l['site'], l['url'], True) for l in found]
    out += [(k, n, search + q(name), False) for k, n, search in CORE if not any(l['site'] == n for l in found)]
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
<header class="top" data-nosnippet>
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

FOOT = """<footer class="foot" data-nosnippet>
  <p>Photos are public domain or Creative Commons, credited under each photo and sourced from Wikimedia Commons.</p>
  <p><a href="{up}">Find Great Architecture</a> · <a href="{up}buildings/">All buildings</a></p>
</footer>
<nav class="dock" data-nosnippet aria-label="Browse">
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
    row = lambda b: f'<li><a href="buildings/{b["id"]}/">{e(b["name"])}</a> <small>{e(b["place"].split(",")[0] if anonymous(b) else b["by"])}</small></li>'
    return (f'<section class="about-wall" id="about">\n'
            f'  <h2>About this wall</h2>\n'
            f'  <p>Find Great Architecture is a huge, growing wall of buildings for architecture students, from the modern masters to '
            f'contemporary and parametric work, brutalism and regionalism. Every building has '
            f'free photos with credits, its key features, and links to plans, sections and articles for a case study. '
            f'Buildings from all over the world; <a href="buildings/">see them all A–Z</a>. '
            f'Short building videos on <a href="https://www.youtube.com/@findgreatarchitecture" rel="noopener">YouTube</a>.</p>\n'
            f'  <h3>Most looked-up buildings</h3>\n  <ol>{"".join(row(b) for b in top)}</ol>\n'
            f'</section>')


def license_url(name):
    """Link to the licence text. Google's licensable-image markup wants a link, not the licence's name."""
    n = (name or '').strip()
    if n == 'CC0':
        return 'https://creativecommons.org/publicdomain/zero/1.0/'
    if n == 'Public domain':
        return 'https://creativecommons.org/publicdomain/mark/1.0/'
    m = re.match(r'^CC (BY|BY-SA) (\d\.\d)(?: ([a-z]+))?$', n)
    if not m:
        return ''
    return f'https://creativecommons.org/licenses/{m.group(1).lower()}/{m.group(2)}/' + (f'{m.group(3)}/' if m.group(3) else '')


# Commons descriptions that crept into captions: template boilerplate, file names, truncated scraps.
BOILERPLATE = re.compile(r"^this (is a |photo|picture|image)|identified (by|as) |\(Q\d+\)|uploaded via|wikimedia|file:|\.jpe?g|\.png|^img[_ ]?\d|^dsc"
                         r"|digital camera|^title:|more information|plus d.infos|immovable heritage|heritage monument|^[a-z]+-\d{4}$", re.I)
PHRASE = {'Exterior': 'exterior', 'Interior': 'interior', 'Context': 'seen in its setting', 'Detail': 'detail', 'Model': 'model',
          'Plan': 'plan', 'Elevation': 'elevation', 'Drawing': 'drawing'}


def photo_kind(im):
    return (im.get('caption') or '').split(' · ')[0].strip() or 'Photo'


def photo_note(im):
    """The useful part of a caption after its kind ('Exterior · The terrace of ...'), or '' when it is boilerplate."""
    note = ' '.join((im.get('caption') or '').partition(' · ')[2].split())
    return '' if len(note) < 4 or len(note) > 140 or BOILERPLATE.search(note) else note


def photo_caption(im):
    note = photo_note(im)
    return photo_kind(im) + (f' · {note}' if note else '')


def photo_alt(b, im):
    """Alt text for a photo: the building, its city, what the photo shows, and its own description when it has a good one."""
    alt = f"{b['name']}, {b['place'].split(',')[0]}: {PHRASE.get(photo_kind(im), photo_kind(im).lower())}"
    note = photo_note(im)
    return textwrap.shorten(alt + (f'. {note}' if note else ''), 125, placeholder='…')


def ld_image(b, im):
    """schema.org ImageObject with licence markup, so Google Images can show the photo as licensable."""
    credit, lic = (im.get('credit') or '').rstrip('.'), im.get('license') or ''
    credit = credit or 'Wikimedia Commons contributor'  # Google's licensable-image markup wants a creator on every photo
    d = {'@type': 'ImageObject', 'contentUrl': at(BASE, im['src']), 'name': f"{b['name']}: {photo_kind(im)}", 'caption': photo_alt(b, im),
         'width': im['w'], 'height': im['h'], 'creator': {'@type': 'Person', 'name': credit}, 'creditText': credit,
         'copyrightNotice': f'{credit}, {lic}' if lic else credit}
    if license_url(lic):
        d['license'] = license_url(lic)
    if im.get('source'):
        d['acquireLicensePage'] = im['source']
    return d


ARCH = {}  # canonical architect name -> page slug, filled in by main() before any page is written (tools/architect_pages.py)
NM = None  # names_py.Names, the same one-name-per-architect rule as the wall


def architect_html(b, up):
    """The building's credit as text, with the architect's own page linked when they have one."""
    text = e(b['by'])
    for n in (NM.list(b['by']) if NM else []):
        if n in ARCH:
            link = f'<a href="{up}architects/{ARCH[n]}/">{e(n)}</a>'
            return text.replace(e(n), link, 1) if e(n) in text else f'{text}<br>{link}: all buildings'
    return text


# The facts table: a small drawing to the left of each fact, on the same 24 x 24 grid as the filter's drawings;
# the architect's row shows their portrait (black and white) when there is a free one.
FACT_ART = {
    'Architect': '<circle cx="12" cy="8" r="4"/><path d="M4 21c1-4.5 4.5-7 8-7s7 2.5 8 7"/>',
    'Place': '<path d="M12 21s-7-6.5-7-12a7 7 0 0 1 14 0c0 5.5-7 12-7 12z"/><circle cx="12" cy="9" r="2.5"/>',
    'Year': '<rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    'Typology': '<path d="M3 21h18M5 21V9l7-5 7 5v12M9 21v-6h6v6"/>',
    'Movement': '<path d="M3 12h4l3-7 4 14 3-7h4"/>',
    'Region': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.8 5.8 3.8 9s-1.2 6.2-3.8 9c-2.6-2.8-3.8-5.8-3.8-9S9.4 5.8 12 3z"/>',
}
PEOPLE = {}  # architects.js, read once by fact_icon
FILTER_ART = read_js('filters.js', 'FILTER_ART')  # the filter's drawings, for the building type


def fact_icon(k, b):
    if k == 'Architect':
        if not PEOPLE:
            PEOPLE.update(read_js('architects.js', 'ARCHITECTS') or {'people': {}, 'buildings': {}})
        for qid in PEOPLE.get('buildings', {}).get(b['id'], []):
            p = PEOPLE['people'].get(qid)
            if p and p.get('thumb'):
                return f'<img class="fi face" src="{e(p["thumb"])}" alt="" loading="lazy">'
    if k == 'Typology':
        d = (FILTER_ART.get('typeIcons') or {}).get(b['type'])
        if d:
            return f'<svg class="fi" viewBox="0 0 24 24" aria-hidden="true"><path d="{e(d)}"/></svg>'
    return f'<svg class="fi" viewBox="0 0 24 24" aria-hidden="true">{FACT_ART[k]}</svg>'


def facts_html(b, up):
    facts = [('Architect', b['by']), ('Place', place_full(b)), ('Year', b['year']), ('Typology', b['type']), ('Movement', b['movement']), ('Region', b['region'])]
    return '<dl class="facts">' + ''.join(
        f'<div>{fact_icon(k, b)}<dt>{e(k)}</dt><dd>{architect_html(b, up) if k == "Architect" else e(v)}</dd></div>' for k, v in facts) + '</dl>'


def building_page(b, items):
    up = '../../'
    url = f"{BASE}buildings/{b['id']}/"
    desc = summary(b)
    ims = b.get('images') or []
    og = at(BASE, ims[0]['src']) if ims else BASE + 'og.jpg'
    ld = {'@context': 'https://schema.org', '@type': 'LandmarksOrHistoricalBuildings', 'name': b['name'], 'description': desc, 'url': url,
          'address': place_full(b),
          'isPartOf': {'@type': 'WebSite', 'name': NAME, 'url': BASE}}
    photos = [ld_image(b, im) for im in ims if not im['src'].endswith('drawing.svg')]  # not our own placeholder drawing
    if photos:
        ld['image'] = photos
    if b.get('wiki'):
        ld['sameAs'] = b['wiki']
    head = HEAD.format(title=e(title(b)), desc=e(desc), url=e(url), site=NAME, ogtype='article',
                       ogtitle=e(f"{b['name']} — {b['by']}, {b['year']}"), image=e(og), up=up, wallhash='#' + b['id'],
                       extra='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>', total=TOTAL, css_v=CSS_V)
    if ims:
        figs = ''.join(
            f'<figure id="photo-{k + 1}"><img src="{e(at(up, im["src"]))}" alt="{e(photo_alt(b, im))}" width="{im["w"]}" height="{im["h"]}" loading="{"eager" if k == 0 else "lazy"}">'
            f'{"<span class=" + chr(34) + "nophoto" + chr(34) + ">Photos unavailable</span>" if im.get("kind") == "Drawing" else ""}'
            f'<figcaption><b>{k + 1}/{len(ims)}{"" if im.get("kind") == "Drawing" else " · " + e(photo_caption(im))}</b><span>{(("" if im.get("kind") == "Drawing" else "Photo: ") + e(im["credit"].rstrip(".")) + " · ") if im.get("credit") else ""}{e(im["license"])}'
            f'{(" · <a href=" + chr(34) + e(im["source"]) + chr(34) + ">source</a>") if im.get("source") else ""}</span></figcaption></figure>'
            for k, im in enumerate(ims))
        thumbs = ''.join(f'<a href="#photo-{k + 1}"><img src="{e(at(up, im["thumb"]))}" alt="Photo {k + 1}: {e(photo_kind(im))}" loading="lazy"></a>' for k, im in enumerate(ims))
        gallery = f'<div class="gallery"><div class="slides">{figs}</div><div class="thumbs">{thumbs}</div></div>' + GALLERY_JS
    else:
        gallery = '<div class="gallery none"><p>No free photos yet. Use the links to see photos and drawings elsewhere.</p></div>'
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
    {facts_html(b, up)}
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


# Go deeper: each site's own logo (site/images/logos/c), in its colours where they read on white and on black, else in a
# mid grey, so the logos stay visible when a phone or browser turns the page dark.
LOGOS = {'ArchDaily': 'archdaily.png', 'WikiArquitectura': 'wikiarquitectura.svg', 'Dezeen': 'dezeen.png', 'Divisare': 'divisare.png',
         'archINFORM': 'archinform.png', 'Wikipedia': 'wikipedia.png', 'YouTube': 'youtube.png', 'Wikimedia Commons': 'commons.png',
         'Map': 'openstreetmap.png'}
GLOBE = '<svg class="lg" viewBox="0 0 24 24" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c2.6 2.8 3.8 5.8 3.8 9s-1.2 6.2-3.8 9c-2.6-2.8-3.8-5.8-3.8-9S9.4 5.8 12 3z"/></svg>'


def logo_html(n, up):
    if n == 'Official website':
        return GLOBE
    return f'<img class="lg" src="{up}images/logos/c/{LOGOS[n]}" alt="" aria-hidden="true">' if n in LOGOS else ''


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
    # Google shows a site's icon in results only if it is a multiple of 48 px (48, 96, 144, 192...), so those sizes and an .ico too.
    for size, name in [(32, 'favicon.png'), (48, 'favicon-48.png'), (96, 'favicon-96.png'), (180, 'apple-touch-icon.png'), (192, 'favicon-192.png'), (512, 'icon-512.png')]:
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
    Image.open(SITE / 'icon-512.png').save(SITE / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])


def fingerprint(path):
    import hashlib
    return hashlib.md5(path.read_bytes()).hexdigest()[:8]


def stamp_wall():
    """Add ?v=<fingerprint> to the wall's scripts and stylesheet, so a new version reaches browsers at once
    instead of waiting for their cached copy to expire."""
    page = SITE / 'index.html'
    html = page.read_text()
    for name in ('styles.css', 'data/wall.js', 'data/names.js', 'data/architects.js', 'data/pritzker.js', 'data/filters.js', 'data/world.js', 'data/books.js', 'data/book_lines.js', 'data/swipe.js', 'data/arch_pages.js', 'app.js', 'filter.js', 'map.js'):
        html = re.sub(r'(["\'])' + re.escape(name) + r'(\?v=[0-9a-f]*)?\1', lambda m: f'{m.group(1)}{name}?v={fingerprint(SITE / name)}{m.group(1)}', html)
    page.write_text(html)
    play = SITE / 'play' / 'index.html'  # the game page: its own script and styles, and the buildings it asks about
    if play.exists():
        html = play.read_text()
        for name, path in (('play.css', SITE / 'play' / 'play.css'), ('play.js', SITE / 'play' / 'play.js'), ('../data/buildings.js', SITE / 'data' / 'buildings.js'), ('../data/links.js', SITE / 'data' / 'links.js'), ('../data/architects.js', SITE / 'data' / 'architects.js'), ('../data/names.js', SITE / 'data' / 'names.js')):
            html = re.sub(r'(["\'])' + re.escape(name) + r'(\?v=[0-9a-f]*)?\1', lambda m: f'{m.group(1)}{name}?v={fingerprint(path)}{m.group(1)}', html)
        play.write_text(html)


def write_swipe():
    """site/data/swipe.js: the buildings whose tiles get photo dots ("Worth the swipe", tools/worth_swipe.py)."""
    import worth_swipe
    ids = worth_swipe.chosen()
    (SITE / 'data' / 'swipe.js').write_text('// Buildings worth swiping through: photo dots under their tiles. Made by tools/build_pages.py from\n'
                                            '// tools/worth_swipe.py (the rule) and tools/worth_swipe.txt (decisions by eye); edit those, not this file.\n'
                                            'window.SWIPE = ' + json.dumps(ids) + ';\n')
    return len(ids)


# What the wall needs for every building up front. The rest of each building (all its photos, its links) is one small file
# in site/data/detail/, which the opened building fetches. The first photo is kept in the wall: it is the tile.
WALL_FIELDS = ('id', 'n', 'name', 'by', 'place', 'year', 'y', 'type', 'movement', 'region', 'era', 'concepts', 'study', 'coords')
DETAIL_FIELDS = ('images', 'commons', 'links', 'wiki')


def write_wall(items=None):
    """site/data/wall.js (window.BUILDINGS, the slim list the wall loads) and site/data/detail/<id>.json (one per building),
    both made from buildings.js and links.js. buildings.js stays the full source; the game still reads it."""
    import hashlib
    items = load() if items is None else items
    out = SITE / 'data' / 'detail'
    out.mkdir(parents=True, exist_ok=True)
    dump = lambda o: json.dumps(o, ensure_ascii=False, separators=(',', ':'))
    rows, digest, ids = [], hashlib.md5(), set()
    for b in items:
        ids.add(b['id'])
        ims = b.get('images') or []
        row = {k: b[k] for k in WALL_FIELDS if b.get(k) is not None}
        row['images'] = [{k: ims[0][k] for k in ('thumb', 'w', 'h') if k in ims[0]}] if ims else []
        row['ni'] = len(ims)
        rows.append(dump(row))
        detail = dump({k: b[k] for k in DETAIL_FIELDS if b.get(k)})
        digest.update(detail.encode())
        path = out / (b['id'] + '.json')
        if not path.exists() or path.read_text() != detail:
            path.write_text(detail)
    for old in out.glob('*.json'):  # a building that left the list leaves its file too
        if old.stem not in ids:
            old.unlink()
    version = hashlib.md5((digest.hexdigest() + ''.join(rows)).encode()).hexdigest()[:8]
    (SITE / 'data' / 'wall.js').write_text('// The wall\'s buildings, one per line, first photo only; the rest of each is in data/detail/<id>.json.\n'
                                           '// Made by tools/build_pages.py from data/buildings.js and data/links.js; edit those, not this file.\n'
                                           f'window.WALL_V = "{version}";\nwindow.BUILDINGS = [\n' + ',\n'.join(rows) + '\n];\n')
    return len(rows)


def main():
    import sys
    if '--stamp' in sys.argv:  # used by the deploy workflow: refresh the wall's data and the fingerprints only
        write_wall()
        stamp_wall()
        return
    global TOTAL, CSS_V
    items = load()
    TOTAL = f'{len(items):,}'
    CSS_V = fingerprint(SITE / 'pages.css')
    page = SITE / 'index.html'
    page.write_text(re.sub(r'<!-- about:start -->.*?<!-- about:end -->', lambda m: '<!-- about:start -->\n' + home_block(items) + '\n<!-- about:end -->',
                           page.read_text(), flags=re.S))
    write_swipe()
    write_wall(items)
    global NM
    import architect_pages
    NM, plans = architect_pages.build(sys.modules[__name__], items)
    ARCH.clear()
    ARCH.update({k: p['slug'] for k, p in plans.items()})
    (SITE / 'data' / 'arch_pages.js').write_text('// Architects who have their own page (site/architects/<slug>/). Made by tools/build_pages.py.\n'
                                                 'window.ARCH_PAGES = ' + json.dumps(ARCH, ensure_ascii=False, sort_keys=True) + ';\n')
    stamp_wall()
    for b in items:
        out = SITE / 'buildings' / b['id']
        out.mkdir(parents=True, exist_ok=True)
        (out / 'index.html').write_text(building_page(b, items))
    (SITE / 'buildings' / 'index.html').write_text(index_page(items))
    if any(x.get('images') for x in items):
        og_image(items)
    urls = [BASE, BASE + 'play/', BASE + 'buildings/'] + ([BASE + 'architects/'] + [f"{BASE}architects/{v}/" for v in sorted(ARCH.values())] if ARCH else []) + [f"{BASE}buildings/{b['id']}/" for b in items]
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                       + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    (SITE / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n')
    icons()
    print(f'Built {len(items)} building pages, the index, og.jpg, sitemap.xml and robots.txt.')


if __name__ == '__main__':
    main()
