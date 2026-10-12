"""Find a free portrait for each building's architect and write site/data/architects.js.

Wikidata gives each building's architect (P84) and each architect's image (P18).
Commons gives the licence and author of that image. Only public domain, CC0, CC BY
and CC BY-SA portraits are kept; anything NC, ND or unclear is skipped, and that
architect shows initials instead. An architect is only accepted when their name
appears in the building's "by" line, so a wrong Wikidata match is never shown.

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
UA = {'User-Agent': 'DiscoverArchitecture/1.0 (https://discoverarchitecture.github.io/; portraits)'}
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

    # 2. architects' names and portraits
    people = entities([a for ids in arch_of.values() for a in ids], 'labels|claims')
    files = {}
    for q, e in people.items():
        imgs = claim_ids(e, 'P18')
        if imgs:
            files[q] = imgs[0]

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
        for q in arch_of.get(b['id'], []):
            name = people.get(q, {}).get('labels', {}).get('en', {}).get('value', '')
            if not name or fold(name) not in fold(b['by']):
                report.append(f"skip    {b['id']}: {q} {name!r} is not in {b['by']!r}")
                continue
            keep.append(q)
            if q in out_people:
                continue
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
    summary = f'{len(out_buildings)} of {len(buildings)} buildings matched; {len(out_people)} architects, {with_photo} with a free portrait.'
    REPORT.write_text(summary + '\n\n' + '\n'.join(report) + '\n')
    print(summary)


if __name__ == '__main__':
    main()
