#!/usr/bin/env python3
"""Find map coordinates (Wikidata P625) for the buildings that have none yet.

  python -u tools/fetch_coords.py              # every building without coords
  python -u tools/fetch_coords.py --limit 80   # a small test run (every k-th building)

Never guesses. A building is matched to a Wikidata item in this order:
  1. qid     the building already carries a Wikidata id.
  2. commons its Commons category (P373 on an item, or the category page's own Wikidata link;
             a category item is followed to its main topic, P301). A category that matches
             several items is used only when exactly one of them passes the checks below.
  3. search  Wikidata search on the name. A candidate is accepted only when its country (P17 -> P297)
             equals the building's, its name shares a distinctive word with the building's, and
             either an architect (P84) shares a surname with `by`, or its inception/opening year is
             within 2 years of `year` AND its place (P131 / description) names the building's city.
Every match is also checked for country (country_ok true / false / null when unknown).

Writes tools/coords_results.json and tools/coords_report.md. It changes nothing under site/;
a reviewer applies the results. Runs on GitHub Actions (run-tool.yml).
"""
import json, re, sys, time, unicodedata, urllib.error, urllib.parse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import fetch, WD, CM, GENERIC, tokens  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'site' / 'data' / 'buildings.js'
OUT = ROOT / 'tools' / 'coords_results.json'
REPORT = ROOT / 'tools' / 'coords_report.md'
SPARQL = 'https://query.wikidata.org/sparql'
EARTH = 'http://www.wikidata.org/entity/Q2'
Q_CATEGORY = 'Q4167836'  # Wikimedia category
# Items in these places carry the parent country in P17.
COUNTRY_ALIASES = {'HK': {'HK', 'CN'}, 'MO': {'MO', 'CN'}, 'PR': {'PR', 'US'}, 'GU': {'GU', 'US'}, 'VI': {'VI', 'US'}}
NOISE = set('architects architect architecture architekten arquitectos partners associates assoc studio atelier office design group '
            'and the of de la le van von der den het inc ltd llp llc sa sl spa gmbh co company'.split())


# ---------- HTTP ----------
def get(url, timeout=60):
    """fetch() retries 429/5xx; this also retries dropped connections and timeouts."""
    for attempt in range(5):
        try:
            return fetch(url, timeout=timeout)
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as e:
            if isinstance(e, urllib.error.HTTPError) or attempt == 4:
                raise
            wait = 5 * (attempt + 1)
            print(f'    {type(e).__name__}, retrying in {wait}s', flush=True)
            time.sleep(wait)


def api(base, **params):
    params.update(format='json', formatversion=2)
    return json.loads(get(base + '?' + urllib.parse.urlencode(params), timeout=40))


def sparql(q):
    url = SPARQL + '?' + urllib.parse.urlencode({'query': q, 'format': 'json'})
    return json.loads(get(url, timeout=120))['results']['bindings']


# ---------- reading the building list ----------
def load_buildings():
    s = DATA.read_text(encoding='utf-8')
    return json.loads(s[s.index('['):s.rindex(']') + 1])


def country_of(b):
    return b['place'].rsplit(', ', 1)[-1].strip().upper() if ', ' in b['place'] else ''


def city_of(b):
    return b['place'].rsplit(', ', 1)[0].strip() if ', ' in b['place'] else b['place']


def commons_name(b):
    c = (b.get('commons') or '').strip()
    c = re.sub(r'^category:', '', c, flags=re.I).replace('_', ' ').strip()
    return c or None


def words(text):
    """Lower-case ASCII words in order (tokens() returns a set)."""
    t = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode().lower()
    return re.findall(r'[a-z0-9]+', t)


def surnames(by):
    """Family-name words of each person or firm in a `by` field: 'Herzog & de Meuron' -> herzog, meuron."""
    out = set()
    for part in re.split(r'\s*(?:,|&|\+|/|;|\band\b|\bund\b|\bet\b|\by\b|\bwith\b)\s*', by or '', flags=re.I):
        ws = [w for w in words(part) if w not in NOISE and len(w) >= 3]
        if ws:
            out.update(ws[1:] or ws)  # drop the given name: 'Alvaro Siza Vieira' -> siza, vieira
    return out


# ---------- reading Wikidata entities ----------
class Wikidata:
    def __init__(self):
        self.ents = {}      # qid -> entity (claims, labels, descriptions)
        self.labels = {}    # qid -> English label
        self.codes = {}     # country qid -> ISO code

    def load(self, qids):
        todo = [q for q in dict.fromkeys(qids) if q and q not in self.ents]
        for k in range(0, len(todo), 50):
            chunk = todo[k:k + 50]
            r = api(WD, action='wbgetentities', ids='|'.join(chunk), props='claims|labels|descriptions', languages='en')
            for q in chunk:
                e = r.get('entities', {}).get(q)
                self.ents[q] = None if (not e or 'missing' in e) else e
            # a redirected id comes back under its target's id
            for q, e in r.get('entities', {}).items():
                if q not in self.ents and e and 'missing' not in e:
                    self.ents[q] = e
        return {q: self.ents.get(q) for q in qids}

    def load_labels(self, qids):
        todo = [q for q in dict.fromkeys(qids) if q and q not in self.labels]
        for k in range(0, len(todo), 50):
            chunk = todo[k:k + 50]
            r = api(WD, action='wbgetentities', ids='|'.join(chunk), props='labels', languages='en')
            for q in chunk:
                e = r.get('entities', {}).get(q) or {}
                self.labels[q] = e.get('labels', {}).get('en', {}).get('value', '')

    def load_codes(self, qids):
        todo = [q for q in dict.fromkeys(qids) if q and q not in self.codes]
        for k in range(0, len(todo), 50):
            chunk = todo[k:k + 50]
            r = api(WD, action='wbgetentities', ids='|'.join(chunk), props='claims', languages='en')
            for q in chunk:
                e = r.get('entities', {}).get(q) or {}
                v = claim_values(e, 'P297')
                self.codes[q] = str(v[0]).upper() if v else ''

    def prepare(self, ents):
        """Load the labels and country codes the checks below need for these entities."""
        arch, places, countries = [], [], []
        for e in ents:
            if not e:
                continue
            arch += [v['id'] for v in claim_values(e, 'P84') if isinstance(v, dict)]
            places += [v['id'] for p in ('P131', 'P276') for v in claim_values(e, p)[:3] if isinstance(v, dict)]
            countries += [v['id'] for v in claim_values(e, 'P17') if isinstance(v, dict)]
        self.load_labels(arch + places)
        self.load_codes(countries)

    # --- facts about one entity ---
    def codes_of(self, e):
        return {self.codes.get(v['id'], '') for v in claim_values(e, 'P17') if isinstance(v, dict)} - {''}

    def architects(self, e):
        return [self.labels.get(v['id'], '') for v in claim_values(e, 'P84') if isinstance(v, dict)]

    def places(self, e):
        names = [self.labels.get(v['id'], '') for p in ('P131', 'P276') for v in claim_values(e, p)[:3] if isinstance(v, dict)]
        return names + [e.get('descriptions', {}).get('en', {}).get('value', ''), e.get('labels', {}).get('en', {}).get('value', '')]


def claim_values(e, prop):
    """Values of a property, preferred rank first, deprecated ones left out."""
    claims = (e or {}).get('claims', {}).get(prop, [])
    claims = [c for c in claims if c.get('rank') != 'deprecated' and c.get('mainsnak', {}).get('snaktype') == 'value']
    claims.sort(key=lambda c: 0 if c.get('rank') == 'preferred' else 1)
    return [c['mainsnak']['datavalue']['value'] for c in claims if 'datavalue' in c['mainsnak']]


def coords_of(e):
    for v in claim_values(e, 'P625'):
        if isinstance(v, dict) and v.get('globe', EARTH) == EARTH and v.get('latitude') is not None:
            lat, lon = round(float(v['latitude']), 5), round(float(v['longitude']), 5)
            if -90 <= lat <= 90 and -180 <= lon <= 180:
                return [lat, lon]
    return None


def years_of(e):
    out = []
    for p in ('P571', 'P1619', 'P729'):
        for v in claim_values(e, p):
            m = re.match(r'[+-]?(\d{1,4})-', v.get('time', '')) if isinstance(v, dict) else None
            if m:
                out.append(int(m.group(1)))
    return out


def is_category(e):
    return any(isinstance(v, dict) and v.get('id') == Q_CATEGORY for v in claim_values(e, 'P31'))


# ---------- the checks ----------
def country_ok(b, wd, e):
    codes = wd.codes_of(e)
    if not codes:
        return None
    want = COUNTRY_ALIASES.get(country_of(b), {country_of(b)})
    return bool(codes & want)


def architect_ok(b, wd, e):
    s = surnames(b.get('by'))
    have = set()
    for label in wd.architects(e):
        have |= tokens(label)
    return bool(s & have)


def year_ok(b, e):
    y = b.get('y')
    try:
        y = int(y)
    except (TypeError, ValueError):
        return False
    return any(abs(v - y) <= 2 for v in years_of(e))


def city_ok(b, wd, e):
    city = tokens(city_of(b)) - GENERIC
    return bool(city) and bool(city & tokens(' '.join(wd.places(e))))


def name_ok(b, texts):
    want = tokens(b['name']) - GENERIC - tokens(b['place']) - tokens(b['by'])
    if not want:
        want = tokens(b['name']) - GENERIC
    if not want:
        return False
    have = tokens(' '.join(texts))
    return len(want & have) * 2 >= len(want)


def passes(b, wd, e):
    """Evidence for a commons-category candidate: architect or year, plus a country that is not wrong."""
    return country_ok(b, wd, e) is not False and (architect_ok(b, wd, e) or year_ok(b, e))


def same_spot(cs):
    return all(abs(c[0] - cs[0][0]) < 0.01 and abs(c[1] - cs[0][1]) < 0.01 for c in cs)


# ---------- phase 1 and 2: qid and Commons category ----------
def match_commons(todo, wd, found, notes):
    """todo: buildings with a Commons category. Fills `found` and `notes`."""
    names = {b['id']: commons_name(b) for b in todo}
    cand = {}  # category name -> [qid]
    uniq = sorted({n for n in names.values() if n})
    for k in range(0, len(uniq), 40):
        chunk = uniq[k:k + 40]
        vals = ' '.join('"' + n.replace('\\', '\\\\').replace('"', '\\"') + '"' for n in chunk)
        try:
            rows = sparql('SELECT ?item ?cat WHERE { VALUES ?cat { %s } ?item wdt:P373 ?cat . }' % vals)
        except Exception as ex:
            print(f'  SPARQL batch failed ({ex}); those categories use the Commons API instead', flush=True)
            continue
        for r in rows:
            cand.setdefault(r['cat']['value'], []).append(r['item']['value'].rsplit('/', 1)[1])
        print(f'  P373 lookup {min(k + 40, len(uniq))}/{len(uniq)}', flush=True)
    # categories with no item carrying that P373: ask Commons which item the category page links to
    rest = [n for n in uniq if n not in cand]
    for k in range(0, len(rest), 50):
        chunk = rest[k:k + 50]
        r = api(CM, action='query', titles='|'.join('Category:' + n for n in chunk), prop='pageprops', ppprop='wikibase_item', redirects=1)
        q = r.get('query', {})
        back = {}
        for n in chunk:
            t = 'Category:' + n
            for m in q.get('normalized', []):
                if m['from'] == t:
                    t = m['to']
            back[n] = t
        redirect = {m['from']: m['to'] for m in q.get('redirects', [])}
        pages = {p['title']: p for p in q.get('pages', []) if 'missing' not in p}
        for n in chunk:
            t = back[n]
            t = redirect.get(t, t)
            item = pages.get(t, {}).get('pageprops', {}).get('wikibase_item')
            if item:
                cand[n] = [item]
        print(f'  Commons page lookup {min(k + 50, len(rest))}/{len(rest)}', flush=True)
    # fetch every candidate, follow category items to their main topic
    allq = [q for qs in cand.values() for q in qs]
    ents = wd.load(allq)
    topics = []
    for q in allq:
        if ents.get(q) and is_category(ents[q]):
            topics += [v['id'] for v in claim_values(ents[q], 'P301') if isinstance(v, dict)]
    wd.load(topics)
    wd.prepare([wd.ents.get(q) for q in allq + topics])
    for b in todo:
        n = names[b['id']]
        if not n or n not in cand:
            continue
        items = []
        for q in dict.fromkeys(cand[n]):
            e = wd.ents.get(q)
            if not e:
                continue
            if is_category(e):
                tops = [v['id'] for v in claim_values(e, 'P301') if isinstance(v, dict)]
                if len(tops) != 1 or not wd.ents.get(tops[0]):
                    continue
                q, e = tops[0], wd.ents[tops[0]]
            if e.get('id', q) not in [i[1].get('id', i[0]) for i in items]:
                items.append((q, e))
        withxy = [(q, e) for q, e in items if coords_of(e)]
        if len(withxy) == 1 and len(items) == 1:
            pick = withxy[0]
        elif len(items) > 1:
            good = [(q, e) for q, e in withxy if passes(b, wd, e)]
            if len(good) == 1:
                pick = good[0]
            elif len(good) > 1 and same_spot([coords_of(e) for q, e in good]):
                pick = good[0]
            else:
                notes.setdefault('ambiguous', []).append(f'{b["id"]} ({n}: {", ".join(q for q, e in items)})')
                continue
        elif len(items) == 1:
            continue  # the one item has no coordinates
        else:
            continue
        q, e = pick
        found[b['id']] = {'qid': q, 'coords': coords_of(e), 'how': 'commons', 'country_ok': country_ok(b, wd, e),
                          'label': e.get('labels', {}).get('en', {}).get('value', ''),
                          'name_ok': name_ok(b, [e.get('labels', {}).get('en', {}).get('value', '')])}


def match_qid(todo, wd, found):
    ents = wd.load([b['qid'] for b in todo])
    wd.prepare(list(ents.values()))
    for b in todo:
        e = ents.get(b['qid'])
        if e and coords_of(e):
            found[b['id']] = {'qid': b['qid'], 'coords': coords_of(e), 'how': 'qid', 'country_ok': country_ok(b, wd, e),
                              'label': e.get('labels', {}).get('en', {}).get('value', ''),
                              'name_ok': name_ok(b, [e.get('labels', {}).get('en', {}).get('value', '')])}


# ---------- phase 3: search ----------
def variants(name):
    out = [name]
    plain = re.sub(r'\s*\([^)]*\)', '', name).strip()
    out.append(plain)
    if ',' in plain:
        out.append(plain.rsplit(',', 1)[0].strip())
    out += re.findall(r'\(([^)]{4,})\)', name)
    return [v for v in dict.fromkeys(out) if len(v) >= 3]


def search_one(b, wd, notes):
    cc = COUNTRY_ALIASES.get(country_of(b), {country_of(b)})
    for v in variants(b['name']):
        r = api(WD, action='wbsearchentities', search=v, language='en', uselang='en', type='item', limit=8)
        hits = r.get('search', [])
        if not hits:
            continue
        ents = wd.load([h['id'] for h in hits])
        wd.prepare(list(ents.values()))
        good = []
        for h in hits:
            e = ents.get(h['id'])
            if not e or is_category(e) or not coords_of(e):
                continue
            if not (wd.codes_of(e) & cc):
                continue
            texts = [h.get('label', ''), h.get('match', {}).get('text', ''), e.get('labels', {}).get('en', {}).get('value', '')]
            if not name_ok(b, texts):
                continue
            by_arch = architect_ok(b, wd, e)
            by_year = year_ok(b, e) and city_ok(b, wd, e)
            if by_arch or by_year:
                good.append((h['id'], e, 'architect' if by_arch else 'year+city'))
        if len(good) == 1 or (good and same_spot([coords_of(e) for q, e, w in good])):
            q, e, why = good[0]
            return {'qid': q, 'coords': coords_of(e), 'how': 'search', 'country_ok': True,
                    'label': e.get('labels', {}).get('en', {}).get('value', ''), 'name_ok': True, 'why': why}
        if len(good) > 1:
            notes.setdefault('ambiguous', []).append(f'{b["id"]} (search "{v}": {", ".join(q for q, e, w in good)})')
            return None
    return None


# ---------- main ----------
def write_outputs(all_b, todo, found, notes, done_all):
    OUT.write_text(json.dumps(found, ensure_ascii=False, indent=1, sort_keys=True), encoding='utf-8')
    by_id = {b['id']: b for b in todo}
    how = {h: sum(1 for f in found.values() if f['how'] == h) for h in ('qid', 'commons', 'search')}
    missing = [b for b in todo if b['id'] not in found]
    bad = [(i, f) for i, f in found.items() if f['country_ok'] is False]
    unknown = sum(1 for f in found.values() if f['country_ok'] is None)
    lines = ['# Coordinates from Wikidata (P625)', '',
             'Made by `tools/fetch_coords.py`. Nothing under `site/` was changed.' + ('' if done_all else ' **Run stopped early; results are partial.**'), '',
             f'- Buildings in the list: {len(all_b)}',
             f'- Without coords at the start: {len(todo)}',
             f'- Found by qid: {how["qid"]}',
             f'- Found by Commons category: {how["commons"]}',
             f'- Found by name search: {how["search"]}',
             f'- Found in all: {len(found)}',
             f'- Still missing: {len(missing)}',
             f'- Country mismatches (Wikidata country differs from the building\'s): {len(bad)}',
             f'- Country unknown on Wikidata (country_ok null): {unknown}',
             f'- Label shares no distinctive word with the building name (name_ok false; check these by eye): {sum(1 for f in found.values() if f.get("name_ok") is False)}',
             f'- Skipped as ambiguous: {len(notes.get("ambiguous", []))}', '']
    lines += ['## Country mismatches', '']
    lines += [f'- `{i}` {by_id[i]["name"]} ({by_id[i]["place"]}) -> {f["qid"]} "{f["label"]}" {f["coords"]} via {f["how"]}' for i, f in sorted(bad)] or ['None.']
    lines += ['', '## Ambiguous (left out)', '']
    lines += [f'- {a}' for a in notes.get('ambiguous', [])] or ['None.']
    lines += ['', '## Still missing', '']
    lines += [f'- `{b["id"]}` {b["name"]} ({b["place"]})' for b in sorted(missing, key=lambda b: b.get('n', 0))] or ['None.']
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')


def main():
    limit = int(sys.argv[sys.argv.index('--limit') + 1]) if '--limit' in sys.argv else 0
    all_b = load_buildings()
    todo = [b for b in all_b if not b.get('coords')]
    print(f'{len(all_b)} buildings, {len(todo)} without coords', flush=True)
    if limit:
        step = max(1, len(todo) // limit)
        todo = todo[::step][:limit]
        print(f'test run on {len(todo)} buildings', flush=True)
    wd, found, notes = Wikidata(), {}, {}
    done = False
    try:
        print('Phase 1: qid', flush=True)
        match_qid([b for b in todo if b.get('qid')], wd, found)
        print(f'  {len(found)} found', flush=True)
        print('Phase 2: Commons category', flush=True)
        match_commons([b for b in todo if b['id'] not in found and commons_name(b)], wd, found, notes)
        print(f'  {len(found)} found so far', flush=True)
        print('Phase 3: search', flush=True)
        rest = [b for b in todo if b['id'] not in found]
        for i, b in enumerate(rest, 1):
            try:
                m = search_one(b, wd, notes)
            except Exception as ex:
                print(f'  {b["id"]}: {type(ex).__name__} {ex}', flush=True)
                continue
            if m:
                found[b['id']] = m
            if i % 50 == 0:
                print(f'  searched {i}/{len(rest)}, {len(found)} found so far', flush=True)
                write_outputs(all_b, todo, found, notes, False)
        done = True
    finally:
        write_outputs(all_b, todo, found, notes, done)
    print(f'Done: {len(found)} of {len(todo)} found', flush=True)


if __name__ == '__main__':
    main()
