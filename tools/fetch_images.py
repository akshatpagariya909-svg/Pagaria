#!/usr/bin/env python3
"""Collect a gallery of 4–8 free photographs per building from Wikimedia Commons.

  python3 tools/fetch_images.py                    # buildings with no gallery yet
  python3 tools/fetch_images.py --only salk-institute,sangath
  python3 tools/fetch_images.py --force            # rebuild every gallery

For each building it finds the building's Commons category (via Wikipedia and Wikidata, or a
Commons search), looks through the photos there and in sub-folders such as "Interior of …",
and picks a spread: exteriors first, then interiors, details and context. Photos Wikimedia
marks as Featured or Quality images score higher; near-duplicates and logos are skipped.
Only public-domain, CC0, CC BY and CC BY-SA files are used. Each photo keeps its credit.

Steer the picks in tools/image_choices.json:
  {"salk-institute": {"category": "Category:Salk Institute",
                      "add": ["File:Some good photo.jpg"],
                      "skip": ["File:A bad pick.jpg"]}}

Writes WebP images to site/images/<id>/ and a review sheet to tools/review.html.
Needs network access to Wikipedia, Wikidata, Wikimedia Commons and upload.wikimedia.org.
"""
import argparse, html, io, json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'site' / 'data' / 'buildings.js'
IMG = ROOT / 'site' / 'images'
CHOICES = ROOT / 'tools' / 'image_choices.json'
REVIEW = ROOT / 'tools' / 'review.html'
PROBE = ROOT / 'tools' / 'category_probe.txt'
UA = 'DiscoverArchitecture/0.2 (https://github.com/akshatpagariya909-svg/Pagaria; image curation script)'
WP = 'https://en.wikipedia.org/w/api.php'
CM = 'https://commons.wikimedia.org/w/api.php'
WD = 'https://www.wikidata.org/w/api.php'

OK_LICENSE = re.compile(r'(public domain|^pd|cc0|cc[ -]by(?![ -]?nc)(?![ -]?nd))', re.I)
NOT_A_PHOTO = re.compile(r'(logo|map\b|locator|flag|coat of arms|seal|icon|\.svg$|\.tiff?$|stamp|banknote|coin|portrait of|poster)', re.I)
KINDS = [
    ('Drawing', re.compile(r'\b(plan|section|elevation|drawing|axonometric|blueprint|sketch|model)\b', re.I)),
    ('Interior', re.compile(r'(interior|inside|innen|intérieur|interno|hall\b|lobby|atrium|foyer|stair|nave|reading room|auditorium|room\b|corridor|kitchen|living)', re.I)),
    ('Detail', re.compile(r'(detail|close[- ]?up|texture|window|door|column|joint|brick|handrail|ceiling|sculpture)', re.I)),
    ('Context', re.compile(r'(aerial|from above|skyline|panorama|view from|seen from|at night|night view|landscape|garden|plaza|street)', re.I)),
]
WANT = {'Exterior': 3, 'Interior': 3, 'Detail': 1, 'Context': 1, 'Drawing': 1}
MAX_PICKS, MIN_PICKS = 8, 4
FULL, THUMB = 1400, 520


# ---------- HTTP ----------
def fetch(url, timeout=60):
    """GET with polite retries: Wikimedia answers 429 when it's busy."""
    for attempt in range(7):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            time.sleep(0.3)
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


# ---------- finding a building's Commons category ----------
GENERIC = set('the of de la le du da des del di and for in at an a house building museum centre center church hall new villa casa'.split())


def tokens(text):
    t = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return {w for w in re.findall(r'[a-z0-9]+', t) if len(w) > 2 or w.isdigit()}


def distinctive(b):
    """Words that name the building itself, not its city or architect."""
    return tokens(b['name']) - GENERIC - tokens(b['place']) - tokens(b['by'])


def fits(b, title):
    d = distinctive(b)
    return bool(d) and bool(d & tokens(title))


def wiki_article(b):
    """The building's English Wikipedia article: its own title first, then a search that must match the name."""
    q = api(WP, action='query', prop='pageprops|pageimages', piprop='name', titles=b['name'], redirects=1)
    page = q['query']['pages'][0]
    if 'missing' not in page and 'disambiguation' not in page.get('pageprops', {}):
        return page
    q = api(WP, action='query', list='search', srsearch=f"{b['name']} {b['by'].split()[-1]}", srlimit=5)
    for hit in q.get('query', {}).get('search', []):
        if fits(b, hit['title']):
            q = api(WP, action='query', prop='pageprops|pageimages', piprop='name', titles=hit['title'], redirects=1)
            return q['query']['pages'][0]
    return None


def commons_category(b):
    """Returns (category, lead file). The category must name the building, not its city or architect."""
    lead, cat = None, None
    try:
        page = wiki_article(b)
        if page:
            lead = 'File:' + page['pageimage'] if page.get('pageimage') else None
            qid = page.get('pageprops', {}).get('wikibase_item')
            if qid:
                c = api(WD, action='wbgetclaims', entity=qid, property='P373')
                claims = c.get('claims', {}).get('P373', [])
                if claims:
                    cat = 'Category:' + claims[0]['mainsnak']['datavalue']['value']
    except Exception as e:  # Wikidata may be unreachable; fall back to a Commons search
        print('    wikipedia/wikidata lookup failed:', e)
    if cat and fits(b, cat):
        return cat, lead
    if cat:
        print('    rejected category', cat)
    for q in (b['name'], f"{b['name']} {b['place'].split(',')[0]}"):
        hits = api(CM, action='query', list='search', srnamespace=14, srlimit=8, srsearch=q).get('query', {}).get('search', [])
        for h in hits:
            if fits(b, h['title']):
                return h['title'], lead
    return None, lead


def probe(b):
    """Prints candidate categories with their file counts, for choosing overrides by hand."""
    cat, lead = commons_category(b)
    seen, out = [], []
    for q in (b['name'], f"{b['name']} {b['by'].split()[-1]}", f"{b['name']} {b['place'].split(',')[0]}"):
        for h in api(CM, action='query', list='search', srnamespace=14, srlimit=6, srsearch=q).get('query', {}).get('search', []):
            if h['title'] not in seen:
                seen.append(h['title'])
    for t in ([cat] if cat else []) + [t for t in seen if t != cat][:10]:
        ci = api(CM, action='query', prop='categoryinfo', titles=t)['query']['pages'][0].get('categoryinfo', {})
        out.append(f"    {'*' if t == cat else ' '} {t}  files={ci.get('files', 0)} subcats={ci.get('subcats', 0)}")
    return f"{b['id']}  lead={lead}\n" + '\n'.join(out)


def members(category, kind):
    out, cont = [], {}
    while len(out) < 300:
        q = api(CM, action='query', list='categorymembers', cmtitle=category, cmtype=kind, cmlimit=200, **cont)
        out += [m['title'] for m in q.get('query', {}).get('categorymembers', [])]
        if 'continue' not in q:
            break
        cont = {'cmcontinue': q['continue']['cmcontinue']}
    return out


def candidate_files(category):
    """Files in the category plus one level of useful sub-folders, tagged with the folder's name."""
    files = [(t, '') for t in members(category, 'file')]
    for sub in members(category, 'subcat')[:25]:
        hint = sub.split(':', 1)[1]
        if re.search(r'(interior|exterior|detail|facade|stair|roof|aerial|night|plan|model|garden|courtyard|views?)', hint, re.I):
            files += [(t, hint) for t in members(sub, 'file')[:80]]
    seen, uniq = set(), []
    for t, h in files:
        if t not in seen and not NOT_A_PHOTO.search(t):
            seen.add(t)
            uniq.append((t, h))
    return uniq[:450]


def infos(titles):
    out = {}
    for k in range(0, len(titles), 50):
        q = api(CM, action='query', titles='|'.join(titles[k:k + 50]), prop='imageinfo', iiprop='url|size|mime|extmetadata', iiurlwidth=1600)
        for p in q.get('query', {}).get('pages', []):
            if 'imageinfo' in p:
                out[p['title']] = p['imageinfo'][0]
    return out


# ---------- choosing ----------
def strip(v):
    v = v.get('value', '') if isinstance(v, dict) else (v or '')
    return html.unescape(re.sub(r'<[^>]+>', ' ', str(v))).strip()


def describe(title, hint, meta):
    text = ' '.join([title, hint, strip(meta.get('ImageDescription'))[:300]])
    for name, rx in KINDS:
        if rx.search(text):
            return name
    return 'Exterior'


def caption(kind, meta, b):
    d = re.sub(r'\s+', ' ', strip(meta.get('ImageDescription')))
    d = re.split(r'(?<=[.!?])\s', d)[0] if d else ''
    if not d or len(d) > 110 or re.search(r'[^\x00-ɏ]', d) or d.lower().rstrip('.') == b['name'].lower():
        return kind
    return f'{kind} · {d.rstrip(".")}'


JUNK = re.compile(r'(\bsign(post|board)?\b|plaque|ticket|\bcars?\b|peugeot|bmw|\bbus\b|selfie|concert|festival|protest|crowd|wedding|portrait|meeting|conference|lecture|exhibition poster)', re.I)


def score(info, b=None, title=''):
    meta = info.get('extmetadata', {})
    a = strip(meta.get('Assessments')).lower()
    s = (6 if 'featured' in a or 'poty' in a else 0) + (4 if 'quality' in a else 0) + (3 if 'valued' in a else 0)
    s += min(3, info.get('width', 0) * info.get('height', 0) / 6e6)
    r = info.get('width', 1) / max(1, info.get('height', 1))
    s -= 2 if r > 2.2 or r < 0.5 else 0  # panoramas and slivers crop badly
    if b:
        text = title + ' ' + strip(meta.get('ImageDescription'))[:300]
        s += 2 if distinctive(b) & tokens(text) else 0  # the file names the building
        s -= 6 if JUNK.search(text) else 0
    return s


def eligible(b, files, info, skip=(), boost=()):
    """Free, large-enough photos from the candidates, scored."""
    pool = []
    for t, hint in files:
        i = info.get(t)
        if not i or t in skip:
            continue
        meta = i.get('extmetadata', {})
        lic = strip(meta.get('LicenseShortName')) or strip(meta.get('UsageTerms'))
        if i.get('mime') not in ('image/jpeg', 'image/png') or max(i.get('width', 0), i.get('height', 0)) < 1200:
            continue
        if not OK_LICENSE.search(lic) or i.get('size', 0) > 45_000_000:
            continue
        pool.append({'title': t, 'info': i, 'kind': describe(t, hint, meta), 'score': score(i, b, t) + (100 if t in boost else 0),
                     'credit': strip(meta.get('Artist'))[:100] or strip(meta.get('Credit'))[:100], 'license': lic})
    pool.sort(key=lambda p: -p['score'])
    return pool


def choose(b, files, info, skip, boost=()):
    pool = eligible(b, files, info, skip, boost)
    picks, per_author, stems, kinds = [], {}, {}, {}

    def stem_of(p):
        return re.sub(r'[\d_\-\s()]+', '', p['title'].rsplit('.', 1)[0].lower())[:40]

    def ok(p):
        return p not in picks and per_author.get(p['credit'], 0) < 3 and stems.get(stem_of(p), 0) < 2

    def take(p):
        picks.append(p)
        per_author[p['credit']] = per_author.get(p['credit'], 0) + 1
        stems[stem_of(p)] = stems.get(stem_of(p), 0) + 1
        kinds[p['kind']] = kinds.get(p['kind'], 0) + 1

    # one of each kind first (an exterior leads), then fill by score within each kind's cap
    for want in ['Exterior', 'Interior', 'Detail', 'Context', 'Interior', 'Exterior', 'Drawing']:
        p = next((p for p in pool if p['kind'] == want and kinds.get(want, 0) < WANT[want] and ok(p)), None)
        if p:
            take(p)
    for p in pool:
        if len(picks) >= MAX_PICKS:
            break
        if kinds.get(p['kind'], 0) < WANT[p['kind']] + 1 and ok(p):
            take(p)
    order = {'Exterior': 0, 'Interior': 1, 'Detail': 2, 'Context': 3, 'Drawing': 4}
    return picks[:1] + sorted(picks[1:], key=lambda p: order[p['kind']])


def picked(b, ch):
    """Photos chosen by hand in image_choices.json "pick": "File:…" or ["File:…", "Interior"], in order."""
    want = [(x, None) if isinstance(x, str) else (x[0], x[1]) for x in ch['pick']]
    info = infos([t for t, _ in want])
    pool = {p['title']: p for p in eligible(b, [(t, '') for t, _ in want], info)}
    out = []
    for t, kind in want:
        if t in pool:
            if kind:
                pool[t]['kind'] = kind
            out.append(pool[t])
        else:
            print('    not usable:', t)
    return out


# ---------- candidate sheets for choosing by hand ----------
CAND = ROOT / 'tools' / 'candidates'
CAND_N, TW, TH = 24, 250, 188


def candidates(b, ch):
    auto, lead = commons_category(b)
    cat = ch.get('category') or auto
    files = (candidate_files(cat) if cat else []) + [(t, '') for t in ch.get('add', []) + ([lead] if lead else [])]
    pool = eligible(b, files, infos([t for t, _ in files]), set(ch.get('skip', [])), set(ch.get('add', []) + ([lead] if lead else [])))
    return cat, pool[:CAND_N]


def tile(p, k):
    from PIL import Image, ImageDraw
    url = p['info'].get('thumburl') or p['info']['url']
    url = re.sub(r'/\d+px-', '/330px-', url) if '/thumb/' in url else url
    im = Image.new('RGB', (TW, TH), (40, 40, 40))
    try:
        t = Image.open(io.BytesIO(fetch(url, timeout=120))).convert('RGB')
        t.thumbnail((TW, TH - 18))
        im.paste(t, ((TW - t.width) // 2, 0))
    except Exception as e:
        print('    thumb failed:', e)
    d = ImageDraw.Draw(im)
    d.rectangle([0, TH - 18, TW, TH], fill=(255, 255, 255))
    d.text((4, TH - 15), f"{k}  {p['kind'][:3]}  {p['title'][5:40]}", fill=(0, 0, 0))
    return im


def write_sheets(rows):
    """Two buildings per sheet, 6 x 4 numbered tiles each."""
    from PIL import Image, ImageDraw
    CAND.mkdir(parents=True, exist_ok=True)
    for f in CAND.glob('sheet-*.jpg'):
        f.unlink()
    for s in range(0, len(rows), 2):
        part = rows[s:s + 2]
        sheet = Image.new('RGB', (6 * TW, len(part) * (4 * TH + 30)), (255, 255, 255))
        d = ImageDraw.Draw(sheet)
        for r, (b, cat, tiles) in enumerate(part):
            y = r * (4 * TH + 30)
            d.text((6, y + 8), f"{b['n']:03d} {b['name']} | {b['by']} | {cat}", fill=(0, 0, 0))
            for k, im in enumerate(tiles):
                sheet.paste(im, ((k % 6) * TW, y + 30 + (k // 6) * TH))
        sheet.save(CAND / f"sheet-{part[0][0]['n']:03d}.jpg", quality=78)


# ---------- saving ----------
def save_image(data, folder, k):
    from PIL import Image
    (folder / 'thumbs').mkdir(parents=True, exist_ok=True)
    im = Image.open(io.BytesIO(data)).convert('RGB')
    im.thumbnail((FULL, FULL))
    w, h = im.size
    im.save(folder / f'{k}.webp', 'WEBP', quality=80, method=5)
    im.thumbnail((THUMB, THUMB))
    im.save(folder / 'thumbs' / f'{k}.webp', 'WEBP', quality=72, method=5)
    return w, h


def load():
    text = DATA.read_text()
    head, body = text.split('window.BUILDINGS = ', 1)
    return head, json.loads(body.rstrip().rstrip(';'))


def save(head, items):
    DATA.write_text(head + 'window.BUILDINGS = ' + json.dumps(items, ensure_ascii=False, indent=1) + ';\n')


def write_review(items):
    rows = []
    for b in items:
        cells = ''.join(
            f'<figure><img src="../site/{html.escape(x["thumb"])}" loading="lazy"><figcaption>{k + 1}. {html.escape(x["caption"])}<br>'
            f'<small>{html.escape(x["file"])} · {html.escape(x["license"])}</small></figcaption></figure>'
            for k, x in enumerate(b.get('images', []))) or '<p class="miss">No free photos found</p>'
        rows.append(f'<section><h2>{b["n"]:03d} · {html.escape(b["name"])} <small>({len(b.get("images", []))})</small></h2><div>{cells}</div></section>')
    REVIEW.write_text('<!doctype html><meta charset="utf-8"><title>Gallery review</title><style>body{font:13px system-ui;margin:24px}'
                      'section{border-top:1px solid #ccc;padding:8px 0}div{display:flex;gap:8px;flex-wrap:wrap}figure{margin:0;width:200px}'
                      'img{width:200px;height:150px;object-fit:cover}small{color:#777}.miss{color:#a00}</style>'
                      '<h1>Gallery review</h1><p>To drop a photo, add its file to "skip" for that building in tools/image_choices.json and re-run with --only.</p>'
                      + ''.join(rows))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--only', default='')
    ap.add_argument('--probe', action='store_true', help='list candidate categories instead of downloading')
    ap.add_argument('--candidates', action='store_true', help='render numbered candidate sheets to tools/candidates/')
    args = ap.parse_args()
    only = set(filter(None, args.only.split(',')))
    choices = json.loads(CHOICES.read_text()) if CHOICES.exists() else {}
    head, items = load()
    thin = []
    if args.probe:
        report = []
        for b in items:
            if not only or b['id'] in only:
                try:
                    report.append(probe(b))
                except Exception as e:
                    report.append(f"{b['id']}  error: {e}")
                print(report[-1])
        PROBE.write_text('\n\n'.join(report) + '\n')
        return
    if args.candidates:
        rows, manifest = [], {}
        for b in items:
            if only and b['id'] not in only:
                continue
            print(f"{b['n']:>3} {b['name']}")
            try:
                cat, pool = candidates(b, choices.get(b['id'], {}))
            except Exception as e:
                print('    error:', e)
                cat, pool = None, []
            print(f'    {cat}: {len(pool)} candidates')
            manifest[b['id']] = [[p['title'], p['kind']] for p in pool]
            rows.append((b, cat, [tile(p, k) for k, p in enumerate(pool)]))
        write_sheets(rows)
        (CAND / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=1) + '\n')
        return
    for b in items:
        if only and b['id'] not in only:
            continue
        if b.get('images') and not args.force and not only:
            continue
        ch = choices.get(b['id'], {})
        print(f"{b['n']:>3} {b['name']}")
        try:
            auto, lead = commons_category(b)
            cat = ch.get('category') or auto
            print('    category:', cat, '| lead:', lead)
            add = ch.get('add', []) + ([lead] if lead and lead not in ch.get('skip', []) else [])
            files = (candidate_files(cat) if cat else []) + [(t, '') for t in add]
            if ch.get('pick'):
                picks = picked(b, ch)
            else:
                picks = choose(b, files, infos([t for t, _ in files]), set(ch.get('skip', [])), set(add))
            for t in ([] if ch.get('pick') else reversed(add)):  # files added by hand, then Wikipedia's lead photo, go first
                p = next((p for p in picks if p['title'] == t), None)
                if p:
                    picks.remove(p)
                    picks.insert(0, p)
            folder = IMG / b['id']
            for f in list(folder.glob('*.webp')) + list(folder.glob('thumbs/*.webp')):
                f.unlink()
            images = []
            for k, p in enumerate(picks[:MAX_PICKS]):
                w, h = save_image(fetch(p['info'].get('thumburl') or p['info']['url'], timeout=120), folder, k)
                images.append({'src': f'images/{b["id"]}/{k}.webp', 'thumb': f'images/{b["id"]}/thumbs/{k}.webp', 'w': w, 'h': h,
                               'kind': p['kind'], 'caption': caption(p['kind'], p['info'].get('extmetadata', {}), b),
                               'credit': p['credit'], 'license': p['license'], 'source': p['info'].get('descriptionurl'), 'file': p['title']})
            b['images'] = images
            b['commons'] = cat
            print(f'    {len(images)} photos: ' + ', '.join(i['kind'] for i in images))
            if len(images) < MIN_PICKS:
                thin.append(f"{b['name']} ({len(images)})")
        except Exception as e:  # keep going; one bad building shouldn't stop the batch
            print('    error:', e)
            thin.append(f"{b['name']} (error)")
        save(head, items)
    write_review(items)
    print(f'\nDone. Review the galleries in {REVIEW.relative_to(ROOT)}.')
    if thin:
        print(f'{len(thin)} with fewer than {MIN_PICKS} free photos:\n  ' + '\n  '.join(thin))


if __name__ == '__main__':
    sys.exit(main())
