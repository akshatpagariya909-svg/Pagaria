#!/usr/bin/env python3
"""Download one free image per building (plus its "Through time" works) from Wikimedia.

  python3 tools/fetch_images.py            # fill in buildings that have no image yet
  python3 tools/fetch_images.py --force    # re-pick everything
  python3 tools/fetch_images.py --only eiffel-tower,taj-mahal

How each image is picked:
  * a choice in tools/image_choices.json always wins, e.g. {"eiffel-tower": "File:Georges Seurat 043.jpg"}
    (use "<id>#then0", "<id>#then1" … for the Through-time works);
  * photographs: the lead image of the building's Wikipedia article;
  * paintings, prints, drawings, archive photos: the top Wikimedia Commons search hit for "<title> <artist>".

Only public-domain, CC0, CC BY and CC BY-SA files are accepted. Every pick is written to
tools/review.html so a person can check it before launch: search hits can be wrong.

Needs network access to en.wikipedia.org, commons.wikimedia.org and upload.wikimedia.org,
and Pillow (pip install pillow) for the small thumbnails.
"""
import argparse, html, io, json, re, sys, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'site' / 'data' / 'buildings.js'
IMG = ROOT / 'site' / 'images'
CHOICES = ROOT / 'tools' / 'image_choices.json'
REVIEW = ROOT / 'tools' / 'review.html'
UA = 'DiscoverArchitecture/0.1 (https://github.com/akshatpagariya909-svg/Pagaria; image curation script)'
OK_LICENSE = re.compile(r'(public domain|^pd|cc0|cc[ -]by(?![ -]?nc)(?![ -]?nd))', re.I)
FULL_W, THUMB_W = 1600, 640
NOT_A_PICTURE = re.compile(r'(logo|map|locator|flag|coat of arms|seal|icon|\.svg$)', re.I)


def fetch(url, timeout=60):
    """GET with polite retries: Wikimedia answers 429 when a shared connection is busy."""
    for attempt in range(7):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            time.sleep(0.5)
            return data
        except urllib.error.HTTPError as e:
            if e.code not in (429, 500, 502, 503, 504) or attempt == 6:
                raise
            wait = int(e.headers.get('Retry-After') or 0) or min(60, 2 ** (attempt + 1))
            print(f'    {e.code}, retrying in {wait}s')
            time.sleep(wait)


def api(base, **params):
    params.update(format='json', formatversion=2)
    return json.loads(fetch(base + '?' + urllib.parse.urlencode(params), timeout=30))


def wiki_lead_image(title):
    q = api('https://en.wikipedia.org/w/api.php', action='query', prop='pageimages', piprop='name', titles=title, redirects=1)
    pages = q.get('query', {}).get('pages', [])
    name = pages[0].get('pageimage') if pages else None
    return 'File:' + name if name else None


def commons_search(text):
    q = api('https://commons.wikimedia.org/w/api.php', action='query', list='search', srnamespace=6, srlimit=8, srsearch=text)
    for hit in q.get('query', {}).get('search', []):
        if re.search(r'\.(jpe?g|png|tiff?)$', hit['title'], re.I):
            yield hit['title']


def file_info(file_title):
    q = api('https://commons.wikimedia.org/w/api.php', action='query', titles=file_title, prop='imageinfo',
            iiprop='url|size|mime|extmetadata')
    pages = q.get('query', {}).get('pages', [])
    if not pages or 'imageinfo' not in pages[0]:
        return None
    ii = pages[0]['imageinfo'][0]
    # Originals come from upload.wikimedia.org; resized copies live on thumb.wikimedia.org, which we don't use.
    if ii.get('mime') not in ('image/jpeg', 'image/png') or ii.get('width', 0) < 700 or ii.get('size', 0) > 45_000_000:
        return None
    meta = ii.get('extmetadata', {})
    strip = lambda v: html.unescape(re.sub(r'<[^>]+>', '', (v or {}).get('value', ''))).strip()
    return {
        'file': pages[0]['title'], 'url': ii['url'], 'w': ii['width'], 'h': ii['height'], 'page': ii.get('descriptionurl'),
        'license': strip(meta.get('LicenseShortName')) or strip(meta.get('UsageTerms')),
        'credit': strip(meta.get('Artist'))[:120] or strip(meta.get('Credit'))[:120],
    }


def pick(candidates):
    seen = set()
    for title in candidates:
        if not title or title in seen or NOT_A_PICTURE.search(title):
            continue
        seen.add(title)
        info = file_info(title)
        if info and OK_LICENSE.search(info['license'] or ''):
            return info
        if info:
            print(f'    skip {title}: licence "{info["license"]}"')
    return None


def download(info, stem):
    data = fetch(info['url'], timeout=120)
    IMG.mkdir(parents=True, exist_ok=True)
    (IMG / 'thumbs').mkdir(exist_ok=True)
    full, thumb = IMG / f'{stem}.jpg', IMG / 'thumbs' / f'{stem}.jpg'
    try:
        from PIL import Image
        im = Image.open(io.BytesIO(data)).convert('RGB')
        im.thumbnail((FULL_W, FULL_W * 2))
        im.save(full, quality=84, optimize=True, progressive=True)
        im.thumbnail((THUMB_W, THUMB_W * 2))
        im.save(thumb, quality=80, optimize=True, progressive=True)
    except ImportError:
        full.write_bytes(data)
        thumb.write_bytes(data)
    return f'images/{stem}.jpg', f'images/thumbs/{stem}.jpg'


def load():
    text = DATA.read_text()
    head, body = text.split('window.BUILDINGS = ', 1)
    return head, json.loads(body.rstrip().rstrip(';'))


def save(head, items):
    DATA.write_text(head + 'window.BUILDINGS = ' + json.dumps(items, ensure_ascii=False, indent=1) + ';\n')


def write_review(items):
    rows = []
    for b in items:
        for label, img, lic, credit, src, file in [(b['name'], b.get('thumb'), b.get('license'), b.get('credit'), b.get('source'), b.get('file'))] + [
                (f"{b['name']} · then: {t['title']}", t.get('image'), t.get('license'), t.get('credit'), t.get('source'), t.get('file')) for t in b.get('then', [])]:
            cell = f'<img src="../site/{html.escape(img)}" loading="lazy">' if img else '<div class="miss">missing</div>'
            rows.append(f'<tr><td>{cell}</td><td><b>{html.escape(label)}</b><br>{html.escape(file or "")}<br>'
                        f'{html.escape(lic or "")} · {html.escape(credit or "")}<br>'
                        f'{f"<a href={chr(34)}{html.escape(src)}{chr(34)}>Commons page</a>" if src else ""}</td></tr>')
    REVIEW.write_text('<!doctype html><meta charset="utf-8"><title>Image review</title><style>body{font:14px system-ui;margin:24px}'
                      'td{border-bottom:1px solid #ddd;padding:8px;vertical-align:top}img{width:220px}.miss{width:220px;height:120px;'
                      'background:#eee;display:grid;place-items:center;color:#a00}</style><h1>Image review</h1>'
                      '<p>Check each pick. To change one, add its file to tools/image_choices.json and run the script with --only.</p>'
                      '<table>' + ''.join(rows) + '</table>')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    only = set(filter(None, args.only.split(',')))
    choices = json.loads(CHOICES.read_text()) if CHOICES.exists() else {}
    head, items = load()
    missing = []
    for b in items:
        if only and b['id'] not in only:
            continue
        if b.get('image') and not args.force and not only:
            continue
        print(f"{b['n']:>3} {b['name']}")
        try:
            if b['media'] == 'photo':
                city = b['place'].split(',')[0]
                cands = [choices.get(b['id']), wiki_lead_image(b['wiki'])] + list(commons_search(f"{b['name']} {city}"))
            else:
                w = b['work']
                cands = [choices.get(b['id'])] + list(commons_search(f"{w['title']} {w['by']}"))
            info = pick(cands)
            if info:
                b['image'], b['thumb'] = download(info, b['id'])
                b.update(w=info['w'], h=info['h'], license=info['license'], credit=info['credit'], source=info['page'], file=info['file'])
            else:
                missing.append(b['name'])
            for k, t in enumerate(b.get('then', [])):
                info = pick([choices.get(f"{b['id']}#then{k}")] + list(commons_search(f"{t['title']} {t['by']}")))
                if info:
                    t['image'] = download(info, f"{b['id']}-then{k}")[1]
                    t.update(license=info['license'], credit=info['credit'], source=info['page'], file=info['file'])
                else:
                    missing.append(f"{b['name']} (then: {t['title']})")
        except Exception as e:  # keep going; one bad request shouldn't stop the batch
            print('    error:', e)
            missing.append(b['name'])
        save(head, items)  # save as we go so an interrupted run keeps its progress
    write_review(items)
    print(f'\nDone. Review the picks in {REVIEW.relative_to(ROOT)}.')
    if missing:
        print(f'{len(missing)} without a usable free image:\n  ' + '\n  '.join(missing))


if __name__ == '__main__':
    sys.exit(main())
