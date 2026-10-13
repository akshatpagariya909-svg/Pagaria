"""Find a free portrait for each building's architect and write site/data/architects.js.

Wikidata gives each building's architect (P84) and each architect's image (P18).
Commons gives the licence and author of that image. Only public domain, CC0, CC BY
and CC BY-SA portraits are kept; anything NC, ND or unclear is skipped, and that
architect shows initials instead. An architect is only accepted when their name
appears in the building's "by" line, so a wrong Wikidata match is never shown: either
the whole name, or every word of one of the by line's names ("Mies van der Rohe" matches
Ludwig Mies van der Rohe), and only for people (Wikidata says human), never firms.

When Wikidata names no architect for a building, each name in its by line is looked up
directly, kept only if Wikidata says it is a person who is an architect, engineer or
planner, with that exact name.

Portraits found by hand go in tools/portraits_manual.json ({"name in the by line":
"File:...jpg"}); their licence is checked here like any other. Architects still without a
free portrait are listed in tools/portraits_gaps.md, most buildings first.

A firm (Foster + Partners, OMA, SANAA...) shows its founder's portrait, as the owner chose: the
firms and their founders are in tools/portraits_founders.json. A free photo of a firm's founders
together, found by hand, goes in tools/portraits_manual.json under the firm's name and is shown
before any single founder.

The photos are not copied into the site: the page loads a small thumbnail straight
from upload.wikimedia.org, like the later buildings' photos.

Needs network access to Wikidata and Commons, so it runs on GitHub Actions
(tools/run_request.txt: python -u tools/fetch_portraits.py). Writes a report to
tools/portraits_report.txt.
"""
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / 'site' / 'data' / 'buildings.js'
OUT = ROOT / 'site' / 'data' / 'architects.js'
REPORT = ROOT / 'tools' / 'portraits_report.txt'
MANUAL = ROOT / 'tools' / 'portraits_manual.json'
GAPS = ROOT / 'tools' / 'portraits_gaps.md'
FOUNDERS = ROOT / 'tools' / 'portraits_founders.json'
HUMAN = 'Q5'
# architect, landscape architect, engineer, civil / structural engineer, urban planner, designer, interior designer
TRADES = {'Q42973', 'Q2815948', 'Q81096', 'Q13582652', 'Q2305987', 'Q131062', 'Q5322166', 'Q2133309'}
UA = {'User-Agent': 'DiscoverArchitecture/1.0 (https://findgreatarchitecture.com/; portraits)'}
FREE = re.compile(r'^(public domain|pd\b|cc0|cc[ -]by(-sa)?[ -]?\d|cc[ -]by(-sa)?$|attribution)', re.I)
NOT_FREE = re.compile(r'\b(nc|nd)\b|noncommercial|no ?deriv', re.I)


def get(url, params):
    url = url + '?' + urllib.parse.urlencode({**params, 'format': 'json'})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return json.load(r)
        except Exception as e:  # network hiccup or rate limit: wait and retry
            print('  retry', attempt + 1, e)
            time.sleep(2 ** attempt * 2)
    return {}


def fold(s):
    return unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower()


def entities(ids, props):
    out = {}
    ids = list(dict.fromkeys(ids))
    for i in range(0, len(ids), 50):
        r = get('https://www.wikidata.org/w/api.php', {'action': 'wbgetentities', 'ids': '|'.join(ids[i:i + 50]), 'props': props, 'languages': 'en'})
        out.update(r.get('entities', {}))
        time.sleep(0.3)
    return out


def claim_ids(ent, prop):
    vals = []
    for c in ent.get('claims', {}).get(prop, []):
        v = c.get('mainsnak', {}).get('datavalue', {}).get('value')
        if isinstance(v, dict) and 'id' in v:
            vals.append(v['id'])
        elif isinstance(v, str):
            vals.append(v)
    return vals


def search_building(b):
    """Buildings without a Wikidata id: try a name search and keep the first hit that has an architect."""
    r = get('https://www.wikidata.org/w/api.php', {'action': 'wbsearchentities', 'search': b['name'], 'language': 'en', 'limit': 5, 'type': 'item'})
    ids = [h['id'] for h in r.get('search', [])]
    ents = entities(ids, 'claims') if ids else {}
    for i in ids:
        if claim_ids(ents.get(i, {}), 'P84'):
            return i, ents[i]
    return None, None


def names(by):
    """The separate names in a by line: "Herzog & de Meuron, Rem Koolhaas (OMA)" -> Herzog, de Meuron, Rem Koolhaas."""
    by = re.sub(r'\(.*?\)', '', by or '')
    return [n.strip() for n in re.split(r'\s*(?:,|;|&|/|\+|\band\b|\bwith\b)\s*', by) if n.strip()]


def words(s):
    return re.findall(r'\w+', fold(s))


def named(name, by):
    """Is this person one of the by line's names? Whole name in the line, or every word of a two-word-plus name in theirs."""
    if fold(name) and fold(name) in fold(by):
        return True
    w = set(words(name))
    return any(len(words(n)) >= 2 and set(words(n)) <= w for n in names(by))


def firms_in(by, founders):
    """(position, firm) for each firm in tools/portraits_founders.json named in this by line. All-capital
    names (OMA, BIG, SOM) must match exactly, as a whole word, so OMA never matches Oman."""
    out = []
    for f in founders:
        m = re.search(r'(?<!\w)' + re.escape(f) + r'(?!\w)', by, 0 if f.isupper() else re.I)
        if m:
            out.append((m.start(), f))
    return out


def is_person(ent):
    return HUMAN in claim_ids(ent, 'P31')


def search_person(name):
    """A person with exactly this name who Wikidata says is an architect, engineer or planner."""
    r = get('https://www.wikidata.org/w/api.php', {'action': 'wbsearchentities', 'search': name, 'language': 'en', 'limit': 7, 'type': 'item'})
    hits = [h for h in r.get('search', []) if fold(h.get('label')) == fold(name) or fold(name) in map(fold, h.get('aliases', []))]
    ents = entities([h['id'] for h in hits], 'labels|claims') if hits else {}
    for h in hits:
        e = ents.get(h['id'], {})
        if is_person(e) and TRADES & set(claim_ids(e, 'P106')):
            return h['id'], e
    return None, None


def strip(s):
    return html.unescape(re.sub(r'<[^>]+>', '', s or '')).strip()


def main():
    text = DATA.read_text()
    buildings = json.loads(text[text.index('['):text.rindex(']') + 1])
    report = []

    # 1. each building's architects
    with_qid = [b for b in buildings if b.get('qid')]
    ents = entities([b['qid'] for b in with_qid], 'claims')
    arch_of = {}
    for b in with_qid:
        arch_of[b['id']] = claim_ids(ents.get(b['qid'], {}), 'P84')
    for b in buildings:
        if b.get('qid'):
            continue
        qid, ent = search_building(b)
        arch_of[b['id']] = claim_ids(ent, 'P84') if ent else []
        report.append(f"search  {b['id']}: {qid or 'no match'}")

    # 2. architects' names; buildings whose Wikidata architects don't match their by line get their names looked up
    people = entities([a for ids in arch_of.values() for a in ids], 'labels|claims')
    def label(q):
        return people.get(q, {}).get('labels', {}).get('en', {}).get('value', '')
    founders = {k: v for k, v in json.loads(FOUNDERS.read_text(encoding='utf-8')).items() if not k.startswith('_')} if FOUNDERS.exists() else {}
    manual = json.loads(MANUAL.read_text(encoding='utf-8')) if MANUAL.exists() else {}
    found, founder_at = {}, {}  # founder_at[building][qid]: where in the by line their firm is named
    for b in buildings:
        for at, f in firms_in(b['by'], founders):
            if f in manual:  # a photo of the founders together, found by hand: it comes before any single founder
                founder_at.setdefault(b['id'], {}).setdefault('manual:' + f, at - 0.5)
            for k, n in enumerate(founders[f]):
                if n in manual:
                    q = 'manual:' + n
                else:
                    if n not in found:
                        found[n] = search_person(n)
                        report.append(f"founder {n} ({f}): {found[n][0] or 'no architect of that name'}")
                    q, e = found[n]
                    if not q:
                        continue
                    people.setdefault(q, e)
                    arch_of.setdefault(b['id'], []).append(q)
                founder_at.setdefault(b['id'], {}).setdefault(q, at + k / 100)
        hit = {n for q in arch_of.get(b['id'], []) if is_person(people.get(q, {})) for n in names(b['by']) if named(label(q), n)}
        for n in names(b['by']):
            if n in hit or len(words(n)) < 2:
                continue
            if n not in found:
                found[n] = search_person(n)
                report.append(f"name    {n}: {found[n][0] or 'no architect of that name'}")
            q, e = found[n]
            if q:
                people.setdefault(q, e)
                arch_of.setdefault(b['id'], []).append(q)
    files = {}
    for q, e in people.items():
        imgs = claim_ids(e, 'P18')
        if imgs:
            files[q] = imgs[0]
    for n, f in manual.items():  # found by hand: keyed by the name as the by line writes it
        files['manual:' + n] = f.replace('File:', '').replace('_', ' ')

    # 3. licence and author of each portrait
    meta = {}
    titles = ['File:' + f for f in dict.fromkeys(files.values())]
    for i in range(0, len(titles), 50):
        r = get('https://commons.wikimedia.org/w/api.php', {'action': 'query', 'titles': '|'.join(titles[i:i + 50]), 'prop': 'imageinfo',
                                                            'iiprop': 'url|extmetadata', 'iiurlwidth': 240})
        for p in r.get('query', {}).get('pages', {}).values():
            ii = (p.get('imageinfo') or [{}])[0]
            em = ii.get('extmetadata', {})
            meta[p.get('title', '')[5:].replace('_', ' ')] = {
                'thumb': ii.get('thumburl'),
                'source': ii.get('descriptionurl'),
                'license': strip(em.get('LicenseShortName', {}).get('value')),
                'credit': strip(em.get('Artist', {}).get('value'))[:80],
            }
        time.sleep(0.3)

    # 4. keep only free portraits of architects named in the building's "by" line
    out_people, out_buildings = {}, {}
    for b in buildings:
        keep = []
        for q in dict.fromkeys(arch_of.get(b['id'], [])):
            name = label(q)
            if q in founder_at.get(b['id'], {}):
                keep.append(q)  # the founder of a firm in the by line
                continue
            if not name or not named(name, b['by']):
                report.append(f"skip    {b['id']}: {q} {name!r} is not in {b['by']!r}")
                continue
            if not is_person(people.get(q, {})):
                report.append(f"skip    {b['id']}: {q} {name!r} is a firm, not a person")
                continue
            keep.append(q)
        for n in names(b['by']) + [m[len('manual:'):] for m in founder_at.get(b['id'], {}) if m.startswith('manual:')]:
            if n in manual and 'manual:' + n not in keep:
                people['manual:' + n] = {'labels': {'en': {'value': n}}}
                keep.append('manual:' + n)
        by = b['by']  # the by line's order, so the first architect's face comes first

        def at(q):
            if q in founder_at.get(b['id'], {}):
                return founder_at[b['id']][q]
            return min([by.find(n) for n in names(by) if named(label(q), n)] or [len(by)])
        keep.sort(key=at)
        for q in keep:
            if q in out_people:
                continue
            name = label(q)
            person = {'name': name}
            m = meta.get(files.get(q, '').replace('_', ' '))
            if m and m['thumb'] and FREE.search(m['license']) and not NOT_FREE.search(m['license']):
                person.update(m)
            elif m:
                report.append(f"licence {name}: {m['license'] or 'unknown'}, not used")
            out_people[q] = person
        if keep:
            out_buildings[b['id']] = keep

    OUT.write_text(
        '// Architects and their free portraits, by building. Generated by tools/fetch_portraits.py; do not edit by hand.\n'
        '// Portraits load from upload.wikimedia.org and are shown in black and white with their credit.\n'
        'window.ARCHITECTS = ' + json.dumps({'people': out_people, 'buildings': out_buildings}, ensure_ascii=False, indent=1) + ';\n')
    with_photo = sum(1 for p in out_people.values() if p.get('thumb'))
    count = {}
    for b in buildings:  # names on the wall still without a free portrait, most buildings first
        faces = [out_people[q]['name'] for q in out_buildings.get(b['id'], []) if out_people[q].get('thumb')]
        firm_faces = any(out_people[q].get('thumb') for q in out_buildings.get(b['id'], []) if q in founder_at.get(b['id'], {}))
        firm_text = fold(' '.join(f for _, f in firms_in(b['by'], founders)))
        for n in names(b['by']):
            if firm_faces and fold(n) in firm_text:
                continue  # the firm shows its founder
            if not any(named(f, n) for f in faces):
                count.setdefault(n, []).append(b['name'])
    G = ['# Architects without a free portrait yet', '', 'Made by `tools/fetch_portraits.py`. Names from the by lines, most buildings first; '
         'firms are listed too, since the wall has no face for them either. Portraits found by hand go in `tools/portraits_manual.json`.', '',
         '| Name | Buildings | For example |', '|---|---|---|']
    G += [f'| {n} | {len(v)} | {v[0]} |' for n, v in sorted(count.items(), key=lambda kv: (-len(kv[1]), kv[0]))]
    GAPS.write_text('\n'.join(G) + '\n', encoding='utf-8')
    summary = f'{len(out_buildings)} of {len(buildings)} buildings matched; {len(out_people)} architects, {with_photo} with a free portrait.'
    REPORT.write_text(summary + '\n\n' + '\n'.join(report) + '\n')
    print(summary)


if __name__ == '__main__':
    main()
