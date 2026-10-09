#!/usr/bin/env python3
"""Build one static page per building, a building index, link previews, a sitemap and robots.txt.

  python3 tools/build_pages.py

Run it again whenever site/data/buildings.js changes. Pages are plain HTML (no JavaScript),
so search engines and link previews see everything. Output:
  site/buildings/<id>/index.html   one page per building
  site/buildings/index.html        A–Z list of all buildings
  site/og.jpg                      preview image for the home page
  site/sitemap.xml, site/robots.txt
"""
import html, json, os, random
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
BASE = os.environ.get('SITE_URL', 'https://akshatpagariya909-svg.github.io/Pagaria/')
NAME = 'Discover Architecture'

COUNTRY = {
    'US': 'United States', 'BD': 'Bangladesh', 'IN': 'India', 'JP': 'Japan', 'ES': 'Spain', 'DE': 'Germany',
    'CZ': 'Czech Republic', 'AU': 'Australia', 'UK': 'United Kingdom', 'CA': 'Canada', 'BR': 'Brazil',
    'YE': 'Yemen', 'ET': 'Ethiopia', 'TN': 'Tunisia', 'FR': 'France', 'IT': 'Italy', 'CN': 'China',
    'MM': 'Myanmar', 'TH': 'Thailand', 'AE': 'United Arab Emirates', 'MY': 'Malaysia', 'ZW': 'Zimbabwe',
    'NO': 'Norway', 'RU': 'Russia', 'GR': 'Greece', 'TR': 'Türkiye', 'JO': 'Jordan', 'EG': 'Egypt',
    'MX': 'Mexico', 'IR': 'Iran', 'KH': 'Cambodia', 'ID': 'Indonesia', 'ML': 'Mali', 'PE': 'Peru',
}
NOUN = {
    'Sacred': 'religious building', 'Culture': 'cultural building', 'Home': 'house', 'Housing': 'housing complex',
    'Civic': 'civic building', 'Tower': 'tower', 'Palace & castle': 'palace', 'Monument': 'monument',
    'Work & learning': 'building', 'Infrastructure': 'structure',
}
# Buildings that no longer stand, so their pages say "was".
GONE = {'crystal-palace': 'destroyed by fire in 1936', 'nakagin-capsule-tower': 'demolished in 2022'}
MEDIA = {'photo': 'Photograph', 'painting': 'Painting', 'print': 'Print', 'drawing': 'Drawing', 'archive': 'Archive photo'}

e = lambda s: html.escape(str(s or ''), quote=True)


def load():
    text = (SITE / 'data' / 'buildings.js').read_text()
    return json.loads(text.split('window.BUILDINGS = ', 1)[1].rstrip().rstrip(';'))


def place_full(b):
    parts = [p.strip() for p in b['place'].split(',')]
    if len(parts) == 2 and parts[1] in COUNTRY:
        return f'{parts[0]}, {COUNTRY[parts[1]]}'
    return b['place']


def summary(b):
    by = b['by']
    who = 'by unknown builders' if by.lower().startswith('unknown') else f'by {by}'
    a = 'an' if NOUN[b['type']][0] in 'aeiou' else 'a'
    if b['id'] in GONE:
        first = f"{b['name']} was {a} {NOUN[b['type']]} in {place_full(b)}, {who}, from {b['year']}; it was {GONE[b['id']]}."
    else:
        first = f"{b['name']} is {a} {NOUN[b['type']]} in {place_full(b)}, {who}, dating from {b['year']}."
    if b['media'] == 'photo':
        credit = (b.get('credit') or '').strip().rstrip('.')
        second = f"Shown here in a photograph{' by ' + credit if credit else ''}."
    else:
        w = b['work']
        date = f", {w['date']}" if w.get('date') and w['date'] != '—' else ''
        second = f"Shown here through {w['title']}, a {MEDIA[b['media']].lower()} by {w['by']}{date}."
    return first + ' ' + second


def related(b, items, n=6):
    def score(x):
        s = (2 if x['type'] == b['type'] else 0) + (1.5 if x['era'] == b['era'] else 0) + (1 if x['region'] == b['region'] else 0)
        s += 3 if x['by'] == b['by'] else 0
        s += 0.5 if x['media'] != b['media'] else 0
        return s + ((x['n'] * 13 + b['n'] * 7) % 17) / 100
    return sorted((x for x in items if x['id'] != b['id']), key=score, reverse=True)[:n]


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
  <nav><a href="{up}buildings/">All 100</a><a class="wall" href="{up}{wallhash}">Back to the wall</a></nav>
</header>
"""

FOOT = """<footer class="foot">
  <p>Images are public domain or Creative Commons, credited on each page and sourced from Wikimedia Commons.</p>
  <p><a href="{up}">Discover Architecture</a> · <a href="{up}buildings/">All 100 buildings</a></p>
</footer>
</body>
</html>
"""


def building_page(b, items):
    up = '../../'
    url = f"{BASE}buildings/{b['id']}/"
    desc = summary(b)
    img_abs = BASE + b['image'] if b.get('image') else BASE + 'og.jpg'
    is_photo = b['media'] == 'photo'
    alt = f"{b['name']}, {place_full(b)}" + ('' if is_photo else f" — {b['work']['title']} by {b['work']['by']}")
    ld = {
        '@context': 'https://schema.org', '@type': 'LandmarksOrHistoricalBuildings', 'name': b['name'],
        'description': desc, 'url': url,
        'address': place_full(b),
        'image': {'@type': 'ImageObject', 'contentUrl': img_abs, 'creditText': b.get('credit') or '',
                  'license': b.get('license') or '', 'acquireLicensePage': b.get('source') or ''},
    }
    head = HEAD.format(title=e(f"{b['name']}, {b['place'].split(',')[0]} · {NAME}"), desc=e(desc), url=e(url), site=NAME,
                       ogtype='article', ogtitle=e(b['name']), image=e(img_abs), up=up, wallhash='#' + b['id'],
                       extra='<script type="application/ld+json">' + json.dumps(ld, ensure_ascii=False) + '</script>')
    if is_photo:
        credit = (b.get('credit') or '').strip().rstrip('.')
        work = f"Photograph{' by ' + e(credit) if credit else ''}"
    else:
        w = b['work']
        date = f", {e(w['date'])}" if w.get('date') and w['date'] != '—' else ''
        work = f"<em>{e(w['title'])}</em><br>{e(w['by'])}{date}"
    lic = ' · '.join(x for x in [e(b.get('license')), f'<a href="{e(b["source"])}">Wikimedia Commons</a>' if b.get('source') else ''] if x)
    facts = [('Architect / builder', b['by']), ('Place', place_full(b)), ('Date', b['year']), ('Type', b['type']), ('Era', b['era']), ('Region', b['region'])]
    then = b.get('then') or []
    then_html = ''
    if then:
        figs = ''.join(
            f'<figure><div class="ph">{f"<img src={chr(34)}{up}{e(t["image"])}{chr(34)} alt={chr(34)}{e(t["title"])} by {e(t["by"])}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if t.get("image") else ""}</div>'
            f'<figcaption><span class="d">{e(t["date"])}</span><b>{e(t["title"])}</b><span>{e(t["by"])}</span></figcaption></figure>' for t in then)
        then_html = f'<section class="block"><h2>Through time</h2><div class="then">{figs}</div></section>'
    q = b['name'] + ' ' + b['place'].split(',')[0]
    links = [
        ('Read', 'Wikipedia', 'https://en.wikipedia.org/wiki/' + (b.get('wiki') or b['name']).replace(' ', '_')),
        ('Projects & articles', 'ArchDaily', 'https://www.archdaily.com/search/all?q=' + html.escape(b['name'].replace(' ', '+'))),
        ('More images', 'Wikimedia Commons', 'https://commons.wikimedia.org/w/index.php?search=' + html.escape(q.replace(' ', '+'))),
        ('Art & archives', 'Google Arts & Culture', 'https://artsandculture.google.com/search?q=' + html.escape(q.replace(' ', '+'))),
    ]
    rel = related(b, items)
    rel_html = ''.join(
        f'<a href="{up}buildings/{x["id"]}/"><span class="ph">{f"<img src={chr(34)}{up}{e(x["thumb"])}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if x.get("thumb") else ""}</span>'
        f'<b>{e(x["name"])}</b><small>{e(x["place"].split(",")[0])} · {e(x["year"])}</small></a>' for x in rel)
    body = f"""<main class="page">
  <figure class="hero{' photo' if is_photo else ''}">
    <img src="{up}{e(b['image'])}" alt="{e(alt)}" width="{b.get('w', '')}" height="{b.get('h', '')}">
  </figure>
  <article class="info">
    <p class="kicker">{str(b['n']).zfill(3)}/100 · Told through a {MEDIA[b['media']].lower()}</p>
    <h1>{e(b['name'])}</h1>
    <p class="lede">{e(desc)}</p>
    <dl class="facts">{''.join(f'<dt>{e(k)}</dt><dd>{e(v)}</dd>' for k, v in facts)}</dl>
    <p class="credit">{work}<span class="lic">{lic}</span></p>
    <a class="cta" href="{up}#{b['id']}">See it on the wall</a>
  </article>
</main>
{then_html}
<section class="block"><h2>Explore elsewhere</h2><div class="links">{''.join(f'<a href="{e(u)}" rel="noopener"><span>{e(k)}</span>{e(n)} ↗</a>' for k, n, u in links)}</div></section>
<section class="block"><h2>Drift onward</h2><div class="rel">{rel_html}</div></section>
"""
    return head + body + FOOT.format(up=up)


def index_page(items):
    up = '../'
    url = BASE + 'buildings/'
    desc = 'All 100 buildings on Discover Architecture, from the Pyramids of Giza to the Burj Khalifa, each told through one photograph, painting, print, drawing or archive photo.'
    head = HEAD.format(title=f'All 100 buildings · {NAME}', desc=e(desc), url=url, site=NAME, ogtype='website',
                       ogtitle='All 100 buildings', image=BASE + 'og.jpg', up=up, wallhash='', extra='')
    rows = ''.join(
        f'<a href="{x["id"]}/"><span class="ph">{f"<img src={chr(34)}{up}{e(x["thumb"])}{chr(34)} alt={chr(34)}{chr(34)} loading={chr(34)}lazy{chr(34)}>" if x.get("thumb") else ""}</span>'
        f'<b>{e(x["name"])}</b><small>{e(place_full(x))} · {e(x["year"])}</small></a>'
        for x in sorted(items, key=lambda x: x['name'].lower()))
    body = f'<main class="index"><h1>All 100 buildings</h1><p class="lede">{e(desc)}</p><div class="grid">{rows}</div></main>\n'
    return head + body + FOOT.format(up=up)


def og_image(items):
    from PIL import Image
    W, H = 1200, 630
    canvas = Image.new('RGB', (W, H), (237, 237, 233))
    pics = [x for x in items if x.get('thumb')]
    random.Random(4).shuffle(pics)
    cols, rows, gap = 6, 3, 6
    cw, ch = (W - gap * (cols + 1)) // cols, (H - gap * (rows + 1)) // rows
    for k, x in enumerate(pics[:cols * rows]):
        im = Image.open(SITE / x['thumb']).convert('RGB')
        r = max(cw / im.width, ch / im.height)
        im = im.resize((int(im.width * r) + 1, int(im.height * r) + 1))
        left, top = (im.width - cw) // 2, (im.height - ch) // 2
        canvas.paste(im.crop((left, top, left + cw, top + ch)), (gap + (k % cols) * (cw + gap), gap + (k // cols) * (ch + gap)))
    canvas.save(SITE / 'og.jpg', quality=85, optimize=True)


def main():
    items = load()
    for b in items:
        out = SITE / 'buildings' / b['id']
        out.mkdir(parents=True, exist_ok=True)
        (out / 'index.html').write_text(building_page(b, items))
    (SITE / 'buildings' / 'index.html').write_text(index_page(items))
    og_image(items)
    urls = [BASE, BASE + 'buildings/'] + [f"{BASE}buildings/{b['id']}/" for b in items]
    (SITE / 'sitemap.xml').write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                       + ''.join(f'  <url><loc>{u}</loc></url>\n' for u in urls) + '</urlset>\n')
    (SITE / 'robots.txt').write_text(f'User-agent: *\nAllow: /\nSitemap: {BASE}sitemap.xml\n')
    print(f'Built {len(items)} building pages, the index, og.jpg, sitemap.xml and robots.txt.')


if __name__ == '__main__':
    main()
