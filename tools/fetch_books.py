#!/usr/bin/env python3
"""Find each book in tools/books_seed.json on Open Library, fetch its cover, and write site/data/books.js.

  python3 tools/fetch_books.py            # books that have no cover yet
  python3 tools/fetch_books.py --force    # look every book up again
  python3 tools/fetch_books.py --only thinking-architecture,atmospheres

For each book it searches Open Library by title and author, keeps the best match that has a cover,
downloads the large cover from covers.openlibrary.org and saves a small WebP thumbnail for the wall in
site/images/books/<id>.webp. The opened book loads the full cover straight from Open Library, like
the later buildings' photos load from Wikimedia, so the repository stays small.

Steer a pick in tools/book_choices.json:
  {"thinking-architecture": {"olid": "OL123W"}}       a specific Open Library work
  {"atmospheres": {"isbn": "9783764374952"}}          a specific edition's ISBN
  {"s-m-l-xl": {"cover_id": 8231856}}                 a specific cover
  {"some-book": {"skip": true}}                       no cover, show the typographic stand-in

Writes tools/books_report.md: which books got a cover, which did not, and what to check.
Needs network access to openlibrary.org, so it runs on GitHub Actions (push tools/books_request.txt).
"""
import argparse, io, json, re, sys, time, unicodedata, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SEED = ROOT / 'tools' / 'books_seed.json'
CHOICES = ROOT / 'tools' / 'book_choices.json'
OUT = ROOT / 'site' / 'data' / 'books.js'
IMG = ROOT / 'site' / 'images' / 'books'
REPORT = ROOT / 'tools' / 'books_report.md'
UA = 'DiscoverArchitecture/1.0 (https://akshatpagariya909-svg.github.io/Pagaria/; akshatpagariya909@gmail.com; books shelf)'
SEARCH = 'https://openlibrary.org/search.json'
COVER = 'https://covers.openlibrary.org/b/id/{}-L.jpg?default=false'
THUMB_W = 400


def fetch(url, timeout=60):
    """GET with polite retries. Open Library answers 429 or 503 when it is busy."""
    for attempt in range(6):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': UA})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                data = r.read()
            time.sleep(0.6)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                return None
            if e.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise
            wait = int(e.headers.get('Retry-After') or 0) or min(90, 3 * 2 ** attempt)
            print(f'    {e.code}, retrying in {wait}s')
            time.sleep(wait)
        except (urllib.error.URLError, TimeoutError) as e:
            if attempt == 5:
                raise
            print(f'    {e}, retrying')
            time.sleep(5 * (attempt + 1))


def fold(s):
    return re.sub(r'[^a-z0-9 ]+', ' ', unicodedata.normalize('NFKD', s or '').encode('ascii', 'ignore').decode().lower())


def words(s):
    return {w for w in fold(s).split() if len(w) > 2 and w not in STOP}


STOP = set('the and for von van der del des les une of in on to with its an by other essays'.split())


def search(params):
    q = urllib.parse.urlencode({**params, 'fields': 'key,title,author_name,first_publish_year,cover_i,isbn,edition_count,language', 'limit': 8})
    data = fetch(f'{SEARCH}?{q}', timeout=40)
    return json.loads(data).get('docs', []) if data else []


def score(book, doc):
    """How well a search result matches the book we asked for: title words, an author surname, then popularity."""
    if not doc.get('cover_i'):
        return -1
    want, got = words(book['title']), words(doc.get('title', ''))
    if not want:
        return -1
    overlap = len(want & got) / len(want)
    if overlap < 0.6:
        return -1
    authors = ' '.join(doc.get('author_name') or [])
    surnames = [w for w in fold(book['by']).split() if len(w) > 3 and w not in STOP and w not in ('editor', 'editors', 'edited')]
    author_ok = any(s in fold(authors) for s in surnames) if surnames else True
    s = overlap * 10 + (6 if author_ok else -4) + min(doc.get('edition_count', 0), 30) / 10
    if 'eng' in (doc.get('language') or []):
        s += 1
    return s


def find(book, choice):
    """Return (work key, cover id, isbn, Open Library first-publish year, note)."""
    if choice.get('cover_id'):
        return choice.get('olid') and f"/works/{choice['olid']}", int(choice['cover_id']), choice.get('isbn'), None, 'cover id from book_choices.json'
    if choice.get('isbn'):
        isbn = re.sub(r'[^0-9Xx]', '', choice['isbn'])
        docs = search({'isbn': isbn})
        docs = [d for d in docs if d.get('cover_i')]
        if docs:
            d = docs[0]
            return d['key'], d['cover_i'], isbn, d.get('first_publish_year'), 'ISBN from book_choices.json'
        return None, None, None, None, f'ISBN {isbn} has no cover on Open Library'
    if choice.get('olid'):
        docs = search({'q': f"key:/works/{choice['olid']}"})
        docs = [d for d in docs if d.get('cover_i')]
        if docs:
            d = docs[0]
            return d['key'], d['cover_i'], (d.get('isbn') or [None])[0], d.get('first_publish_year'), 'work from book_choices.json'
        return None, None, None, None, f"work {choice['olid']} has no cover on Open Library"
    first_author = re.split(r',| and |\(', book['by'])[0].strip()
    tries = [{'title': book['title'], 'author': first_author}, {'title': book['title']}, {'q': f"{book['title']} {first_author}"}]
    best, best_s, seen = None, 0, 0
    for params in tries:
        docs = search(params)
        seen += len(docs)
        for d in docs:
            s = score(book, d)
            if s > best_s:
                best, best_s = d, s
        if best_s >= 14:
            break
    if not best:
        return None, None, None, None, f'no match with a cover among {seen} results'
    note = '' if best_s >= 14 else f'weak match (score {best_s:.0f}): "{best.get("title")}" by {", ".join(best.get("author_name") or [])}'
    return best['key'], best['cover_i'], (best.get('isbn') or [None])[0], best.get('first_publish_year'), note


def save_thumb(data, path):
    from PIL import Image
    im = Image.open(io.BytesIO(data))
    im = im.convert('RGB')
    w, h = im.size
    if w < 120 or h < 150:
        return None
    t = im.copy()
    t.thumbnail((THUMB_W, THUMB_W * 2), Image.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    t.save(path, 'WEBP', quality=82, method=6)
    return w, h


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--force', action='store_true')
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    only = {s.strip() for s in args.only.split(',') if s.strip()}
    seed = json.loads(SEED.read_text())
    choices = json.loads(CHOICES.read_text()) if CHOICES.exists() else {}
    old = {}
    if OUT.exists():
        old = {b['id']: b for b in json.loads(OUT.read_text().split('window.BOOKS = ', 1)[1].rstrip().rstrip(';'))}
    out, rows = [], []
    for book in seed:
        b = {**book}
        prev = old.get(b['id'], {})
        choice = choices.get(b['id'], {})
        keep = prev.get('cover') and not args.force and not (only and b['id'] in only) and not choice
        if only and b['id'] not in only and not prev:
            keep = False
        if keep or (only and b['id'] not in only):
            for k in ('cover', 'ol', 'isbn', 'olYear'):
                if k in prev:
                    b[k] = prev[k]
            out.append(b)
            continue
        print(f"{b['id']}: {b['title']}")
        if choice.get('skip'):
            rows.append((b, 'skipped by book_choices.json'))
            out.append(b)
            continue
        try:
            key, cover_id, isbn, ol_year, note = find(b, choice)
        except Exception as e:
            rows.append((b, f'lookup failed: {e}'))
            out.append(b)
            continue
        if not cover_id:
            print('   ', note)
            rows.append((b, note))
            out.append(b)
            continue
        data = fetch(COVER.format(cover_id))
        size = save_thumb(data, IMG / f"{b['id']}.webp") if data else None
        if not size:
            rows.append((b, f'cover {cover_id} is missing or too small'))
            out.append(b)
            continue
        if key:
            b['ol'] = key.split('/')[-1]
        if isbn:
            b['isbn'] = isbn
        if ol_year:
            b['olYear'] = ol_year
        b['cover'] = {'thumb': f"images/books/{b['id']}.webp", 'src': f'https://covers.openlibrary.org/b/id/{cover_id}-L.jpg', 'id': cover_id, 'w': size[0], 'h': size[1],
                      'source': f'https://openlibrary.org/works/{b["ol"]}' if key else f'https://covers.openlibrary.org/b/id/{cover_id}.json'}
        print(f"    cover {cover_id} ({size[0]}x{size[1]}) {note}")
        rows.append((b, note or 'ok'))
        out.append(b)
    OUT.write_text('// Books for architecture students, curated in tools/books_seed.json; covers found by tools/fetch_books.py on Open Library.\n'
                   'window.BOOKS = ' + json.dumps(out, ensure_ascii=False, indent=1) + ';\n')
    with_cover = sum(1 for b in out if b.get('cover'))
    lines = [f'# Books report', '', f'{with_cover} of {len(out)} books have a cover.', '',
             '| Book | Result |', '|---|---|']
    for b, note in rows:
        lines.append(f"| {b['title']} ({b['by']}) | {note} |")
    missing = [b for b in out if not b.get('cover')]
    if missing:
        lines += ['', '## No cover yet', '', 'Add an ISBN, an Open Library work id or a cover id for these in tools/book_choices.json, then push tools/books_request.txt again.', '']
        lines += [f"- {b['id']}: {b['title']} ({b['by']})" for b in missing]
    REPORT.write_text('\n'.join(lines) + '\n')
    print(f'{with_cover} of {len(out)} books have a cover.')


if __name__ == '__main__':
    main()
