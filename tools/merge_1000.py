#!/usr/bin/env python3
"""Add the curated buildings to site/data/buildings.js, growing the first 100 towards 1,000.

Sources (all in tools/harvest/):
  curated.json         the 1,400 Wikidata shortlist, each rated keep 0-3 with name, type, movement, concepts, features
  selected.json        Wikidata facts for that shortlist (Commons category, lead photo, coordinates, score)
  extra_resolved.json  hand-picked additions matched to Wikidata by resolve_list.py

  python tools/merge_1000.py           add new buildings (a few more than needed, since some will have no free photos)
  python tools/merge_1000.py --trim    after fetching photos: drop new buildings without photos, keep the best up to 1,000
"""
import argparse, json, re, sys, unicodedata
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import load, save  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
H = ROOT / 'tools' / 'harvest'
TARGET = 1000
OVERSHOOT = 60
# No country should crowd the wall; the first hundred count towards these.
COUNTRY_CAP = {'US': 75, 'JP': 70, 'GB': 50, 'FR': 45, 'DE': 45, 'CN': 40, 'IT': 35, 'ES': 35, 'IN': 40}
DEFAULT_CAP = 30

REGIONS = {
    'Europe': 'AD AT BA BE BG BY CH CZ DE DK EE ES FI FR GB GR HR HU IE IS IT LI LT LU LV MK MT NL NO PL PT RS RU SE SI SK UA VA XK',
    'Americas': 'AR BR CA CL CO CU DO EC GT MX NI PA PE PR PY SV US UY VE',
    'East Asia': 'CN HK JP KR MO TW',
    'Southeast Asia': 'ID KH MY PH SG TH VN',
    'South Asia': 'BD IN LK NP PK',
    'Middle East': 'AE AM AZ BH EG GE IL IQ IR JO KW KZ LB OM PS QA SA TR UZ YE',
    'Africa': 'AO BF CI DZ ER ET GH GN KE MA ML MZ NE NG RW SD SN TZ UG ZA ZW',
    'Oceania': 'AU NC NZ',
}
REGION = {cc: r for r, ccs in REGIONS.items() for cc in ccs.split()}


def fold(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', fold(s)).strip('-')[:60]


def era(y):
    return ('Before 1900' if y < 1900 else '1900–1945' if y < 1945 else '1945–1970' if y < 1970
            else '1970–1990' if y < 1990 else '1990–2005' if y < 2005 else '2005–today')


def candidates():
    """Every rated building with a Wikidata item, best first."""
    sel = {s['qid']: s for s in json.loads((H / 'selected.json').read_text())}
    out = []
    for c in json.loads((H / 'curated.json').read_text()):
        s = sel.get(c['qid'], {})
        if c['keep'] < 1:
            continue
        label = s.get('label') or ''
        name = label if fold(label) == fold(c['name']) else c['name']  # Wikidata keeps the accents
        out.append({**c, 'name': name, 'commons': (s.get('commons') or [None])[0], 'lead': (s.get('image') or [None])[0],
                    'coords': (s.get('coords') or [None])[0], 'rank': (c['keep'], s.get('score', 0))})
    extra = H / 'extra_resolved.json'
    for c in json.loads(extra.read_text()) if extra.exists() else []:
        if c.get('qid'):
            out.append({**c, 'rank': (c['keep'], 1.0)})
    out.sort(key=lambda c: c['rank'], reverse=True)
    return out


def entry(c, n, ids):
    y = int(re.search(r'\d{3,4}', str(c['year'])).group())
    base = slug(c['name'])
    i = base if base not in ids else f"{base}-{slug(c['city'])}"
    return {
        'id': i, 'n': n, 'name': c['name'], 'by': c['by'], 'place': f"{c['city']}, {c['cc']}", 'year': str(c['year']), 'y': y,
        'type': c['type'], 'movement': c['movement'], 'region': REGION.get(c['cc'], 'Europe'), 'era': era(y),
        'concepts': c['concepts'], 'study': c['features'], 'qid': c['qid'],
        'commons': 'Category:' + c['commons'] if c.get('commons') else None,
        'lead': 'File:' + c['lead'] if c.get('lead') else None,
        'coords': c.get('coords'), 'hotlink': True,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--trim', action='store_true')
    args = ap.parse_args()
    head, items = load()
    if args.trim:
        rank = {c['qid']: c['rank'] for c in candidates()}
        old = [b for b in items if not b.get('qid')]
        new = [b for b in items if b.get('qid') and b.get('images')]
        new.sort(key=lambda b: rank.get(b['qid'], (0, 0)), reverse=True)
        keep = old + new[:TARGET - len(old)]
        print(f'{len(items) - len(keep)} dropped ({sum(1 for b in items if b.get("qid") and not b.get("images"))} without photos)')
        for n, b in enumerate(keep, 1):
            b['n'] = n
        save(head, keep)
        return
    have = {b.get('qid') for b in items} | {fold(b['name']) for b in items}
    ids = {b['id'] for b in items}
    per_cc = {}
    for b in items:
        cc = b['place'].rsplit(', ', 1)[-1]
        per_cc[cc] = per_cc.get(cc, 0) + 1
    added = 0
    for c in candidates():
        if len(items) >= TARGET + OVERSHOOT:
            break
        if c['qid'] in have or fold(c['name']) in have or per_cc.get(c['cc'], 0) >= COUNTRY_CAP.get(c['cc'], DEFAULT_CAP):
            continue
        if not (c.get('commons') or c.get('lead')):
            continue
        b = entry(c, len(items) + 1, ids)
        items.append(b)
        ids.add(b['id'])
        have |= {c['qid'], fold(c['name'])}
        per_cc[c['cc']] = per_cc.get(c['cc'], 0) + 1
        added += 1
    save(head, items)
    print(f'{added} added, {len(items)} in all')


if __name__ == '__main__':
    sys.exit(main())
