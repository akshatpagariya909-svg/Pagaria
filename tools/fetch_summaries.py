#!/usr/bin/env python3
"""Fetch a short, sourced description for the most looked-up buildings from their Wikipedia article.

  python3 tools/fetch_summaries.py              # top 100 by pageviews + every South Asian building with an article
  python3 tools/fetch_summaries.py --only salk-institute,sangath
  python3 tools/fetch_summaries.py --top 200

Takes the article's introduction and, when present, the first paragraph of its Architecture / Design /
Structure section, trimmed to about 220 words at a sentence end. The text is quoted, not rewritten, so
nothing is invented; each page credits Wikipedia (CC BY-SA 4.0) and links to the article.

Reads tools/pageviews.json (building id -> Wikipedia pageviews over 12 months, from the SEO research).
Writes site/data/summaries.js (window.SUMMARIES). Needs network access to en.wikipedia.org.
"""
import argparse, json, re, sys, time, unicodedata, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / 'site'
OUT = SITE / 'data' / 'summaries.js'
UA = 'DiscoverArchitecture/0.2 (https://github.com/discoverarchitecture/discoverarchitecture.github.io; summaries script)'
API = 'https://en.wikipedia.org/w/api.php'
MAX_WORDS = 220
SECTIONS = ('Architecture', 'Design', 'Structure', 'Building', 'Architecture and design', 'Design and construction',
            'Description', 'Layout')


def load():
    text = (SITE / 'data' / 'buildings.js').read_text()
    items = json.loads(text.split('window.BUILDINGS = ', 1)[1].rstrip().rstrip(';'))
    links = json.loads((SITE / 'data' / 'links.js').read_text().split('window.LINKS = ', 1)[1].rstrip().rstrip(';'))
    return [{**b, **links.get(b['id'], {})} for b in items]


def api(**params):
    params.update(action='query', format='json', formatversion='2')
    url = API + '?' + urllib.parse.urlencode(params)
    for attempt in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': UA}), timeout=60) as r:
                return json.loads(r.read().decode())
        except Exception as err:
            if attempt == 4:
                raise
            time.sleep(5 * (attempt + 1))


def clean(par):
    par = re.sub(r'\[\d+\]|\[[a-z]\]', '', par)        # footnote markers
    par = re.sub(r'\s*\([^()]*\b(pronounced|listen|IPA)\b[^()]*\)', '', par)
    return re.sub(r'\s+', ' ', par).strip()


def trim(words_text, limit=MAX_WORDS):
    """Cut at a sentence end once the limit is reached."""
    words = words_text.split()
    if len(words) <= limit:
        return words_text
    cut = ' '.join(words[:limit])
    m = list(re.finditer(r'[.!?](?=\s|$)', cut))
    return cut[:m[-1].end()] if m else cut + '…'


def extract(title):
    r = api(prop='extracts|info|revisions', explaintext=1, exsectionformat='wiki', titles=title, inprop='url', rvprop='ids')
    page = r['query']['pages'][0]
    if page.get('missing'):
        return None
    text = page.get('extract') or ''
    # split into sections: "== Heading ==" lines
    parts = re.split(r'\n==+ *(.*?) *==+\n', '\n' + text)
    intro, rest = parts[0], dict(zip(parts[1::2], parts[2::2]))
    paras = [clean(p) for p in intro.split('\n') if clean(p)]
    if not paras:
        return None
    words = lambda ps: sum(len(x.split()) for x in ps)
    # The first paragraph says what the subject is. Then prefer the article's own section on the building
    # (an article about a university or a company describes the institution first), then the rest of the intro.
    chosen = [paras[0]]
    design = next((v for name in SECTIONS for k, v in rest.items() if k.lower() == name.lower()), None)
    pool = [clean(p) for p in (design or '').split('\n') if clean(p) and not p.startswith('==')] + paras[1:]
    for p in pool:
        if p in chosen:
            continue
        if p.endswith(':') or len(p.split()) < 8:  # a list follows, or a fragment: stop here
            break
        if p[0].islower():  # a line broken inside a paragraph
            continue
        if words(chosen) + len(p.split()) > MAX_WORDS and words(chosen) >= 120:
            break
        chosen.append(p)
        if words(chosen) >= MAX_WORDS:
            break
    total = ' '.join(chosen)
    if len(total.split()) > MAX_WORDS:
        # trim the last paragraph only
        head = ' '.join(chosen[:-1])
        room = MAX_WORDS - len(head.split())
        chosen[-1] = trim(chosen[-1], max(room, 60))
    return {'paragraphs': chosen, 'title': page['title'], 'url': page['canonicalurl'],
            'revision': page.get('revisions', [{}])[0].get('revid'), '_full': text}


# Typologies whose Wikipedia article is usually about the institution (the school, the company, the hotel chain)
# rather than the building, so the chosen text itself must name the architect.
INSTITUTIONS = {'Education', 'Workplace', 'Health', 'Hospitality'}


def about_the_building(s, b):
    """Articles about a university, a company or a chain describe the institution, not Kahn's campus or Baker's
    cafe. Keep a summary only if the article names the architect (or the builders are unknown) and the text
    talks about the building."""
    fold = lambda t: unicodedata.normalize('NFKD', t).encode('ascii', 'ignore').decode().lower()
    text, full = fold(' '.join(s['paragraphs'])), fold(s.get('_full', ''))
    generic = {'and', 'the', 'partners', 'architects', 'associates', 'studio', 'group', 'builders', 'office', 'design', 'with'}
    names = [w for w in re.findall(r'[a-z]+', fold(b['by'])) if len(w) >= 3 and w not in generic]
    where = text if b['type'] in INSTITUTIONS else full
    named = b['by'].lower().startswith('unknown') or b['by'].lower().endswith('builders') or \
        any(re.search(r'\b' + re.escape(n) + r'\b', where) for n in names)
    built = any(w in text for w in ('design', 'architect', 'built', 'building', 'construct', 'structure', 'concrete', 'brick', 'stone'))
    return named and built


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    ap.add_argument('--top', type=int, default=100)
    args = ap.parse_args()
    items = load()
    only = set(filter(None, args.only.split(',')))
    pv = json.loads((ROOT / 'tools' / 'pageviews.json').read_text())
    ranked = sorted((b for b in items if b['id'] in pv), key=lambda b: -pv[b['id']])
    wanted = [b for b in ranked[:args.top]] + [b for b in items if b['region'] == 'South Asia']
    if only:
        wanted = [b for b in items if b['id'] in only]
    out = {}
    if OUT.exists():
        out = json.loads(OUT.read_text().split('window.SUMMARIES = ', 1)[1].rstrip().rstrip(';'))
    seen = set()
    for b in wanted:
        if b['id'] in seen or not b.get('wiki'):
            continue
        seen.add(b['id'])
        if b['id'] in out and not only:
            continue
        title = urllib.parse.unquote(b['wiki'].rsplit('/wiki/', 1)[1]).replace('_', ' ')
        try:
            s = extract(title)
        except Exception as err:
            print(f"  {b['id']}: error {err}", file=sys.stderr)
            continue
        if s and about_the_building(s, b):
            s.pop('_full')
            s['fetched'] = time.strftime('%Y-%m-%d')
            out[b['id']] = s
            print(f"{b['id']}: {sum(len(p.split()) for p in s['paragraphs'])} words")
        else:
            out.pop(b['id'], None)
            print(f"{b['id']}: skipped ({'not about the building' if s else 'no text'})")
        time.sleep(0.5)
    OUT.write_text('// Short descriptions quoted from each building\'s Wikipedia article (CC BY-SA 4.0). Generated by tools/fetch_summaries.py.\n'
                   'window.SUMMARIES = ' + json.dumps(out, ensure_ascii=False, indent=1) + ';\n')
    print(f'{len(out)} summaries in {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
