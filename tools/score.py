#!/usr/bin/env python3
"""Score every candidate building for quality, so each batch of 1,000 takes the best that is left.

  python tools/score.py        # writes tools/harvest/scored.json and tools/score_report.md

Pool: tools/harvest/candidates.json (Wikidata, architect named, Wikipedia in 6+ languages)
plus tools/pritzker/buildings.json. Extra signals come from tools/harvest/signals.json when
tools/signals.py has run on GitHub Actions; without it the score uses fame, era and type only.

A building must pass the gates (a building, a named architect, a free photo, a year).
Then it scores 0-100:
  fame        up to 30  Wikipedia language editions
  experts     up to 20  listed in archINFORM, Docomomo, #SOSBrutalism, Archnet (Structurae
                        counts little: it lists every tower and stadium);
                        many outside identifiers
  architect   up to 15  a Pritzker winner (15) or an architect students study (10)
  awards      up to 10  architecture awards (8), heritage listing (4), World Heritage (6)
  era/style   up to 20  modern and contemporary work, the movements the site favours
  penalties             generic types (stations, stadiums, hotels, offices, old churches and
                        palaces; halved for studied architects); before 1850; demolished
No network needed.
"""
import json, math, re, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from select_1000 import (STARS, REGION, MODERN_STYLES, TRANSIT, SPORT, COMMERCE, NOT_BUILDING,  # noqa: E402
                         OLD_GENERIC, fold, year)

ROOT = Path(__file__).resolve().parent.parent
H = ROOT / 'tools' / 'harvest'
OUT = H / 'scored.json'
REPORT = ROOT / 'tools' / 'score_report.md'
BATCH = 1000
GOOD = 40  # the floor: nothing under 40 goes on the wall; set properly once signals.json is in

IS_BUILDING = re.compile(r'building|house|museum|church|library|hall|tower|pavilion|school|university|theatre|theater|chapel|villa|centre|center|skyscraper|block', re.I)
ARCH_AWARD = re.compile(r'architect|aga khan|mies van der rohe|stirling|riba|\baia\b|bcs prize|aij prize|public buildings award|kasper salin|good design|european union prize|alvar aalto medal|driehaus|praemium|emporis|ctbuh|wan award', re.I)
EXPERTS = {'archinform': 6, 'structurae': 1, 'docomomo': 5, 'sosbrutalism': 3, 'archnet': 4}
PER_ARCHITECT = 8  # most buildings any one architect gets in a single batch


def key(name):
    return re.sub(r'[^a-z0-9]', '', fold(name or ''))


def load_wall():
    """What is already on the wall, by Wikidata ID, name, English Wikipedia title and Commons category.
    The first hundred have no Wikidata ID, so the other three catch them."""
    def js(name, var):
        s = (ROOT / 'site' / 'data' / name).read_text(encoding='utf-8')
        return json.loads(s[s.index('=', s.index(var)) + 1:].strip().rstrip(';'))
    B, links = js('buildings.js', 'window.BUILDINGS'), js('links.js', 'window.LINKS')
    wiki = {key(v['wiki'].rsplit('/', 1)[-1].replace('_', ' ')) for v in links.values() if v.get('wiki')}
    return ({b['qid'] for b in B if b.get('qid')},
            {key(b['name']) for b in B} | wiki,
            {key(b['commons'].split(':', 1)[-1]) for b in B if b.get('commons')})


def on_wall(r, wall):
    qids, names, cats = wall
    return (r['qid'] in qids or key(r.get('label')) in names or key(r.get('enwiki')) in names
            or any(key(c) in cats for c in r.get('commons', [])))


def pool():
    """Candidates and Pritzker buildings, one record per Wikidata item."""
    recs = {r['qid']: r for r in json.loads((H / 'candidates.json').read_text(encoding='utf-8'))}
    pz = ROOT / 'tools' / 'pritzker' / 'buildings.json'
    pritzker = set()
    if pz.exists():
        for r in json.loads(pz.read_text(encoding='utf-8')):
            pritzker.add(r['qid'])
            recs.setdefault(r['qid'], r)
    return list(recs.values()), pritzker


def gate(r):
    """Why a record can't go on the wall, or None."""
    inst = ' '.join(r.get('instance', []))
    arch = [a for a in r.get('architect', []) if isinstance(a, str)]
    y = year(r)
    if not r.get('label'):
        return 'no name'
    if not (r.get('image') or r.get('commons')):
        return 'no free photo'
    if not arch or arch == ['architectural ensemble']:
        return 'no architect'
    if not y or y > 2026:
        return 'no year'
    if NOT_BUILDING.search(inst) and not IS_BUILDING.search(inst):
        return 'not a building'
    return None


def score(r, sig, pritzker):
    y = year(r)
    arch = [a for a in r.get('architect', []) if isinstance(a, str)]
    laureate = r['qid'] in pritzker
    star = laureate or any(a.lower() in STARS for a in arch)
    inst = ' '.join(r.get('instance', []))
    styles = ' '.join(r.get('style', []))
    why = []

    fame = 30 * min(1, math.log(max(r.get('sitelinks', 0), 6) / 6) / math.log(60 / 6))
    experts = 0
    for name, pts in EXPERTS.items():
        if name in sig.get('ids', []):
            experts += pts
            why.append(name)
    experts += 6 * min(1, sig.get('n_ids', 0) / 40)
    experts = min(20, experts)
    architect = 15 if laureate else 10 if star else 0
    if laureate:
        why.append('Pritzker winner')
    elif star:
        why.append('studied architect')
    awards = 0
    if any(ARCH_AWARD.search(a) for a in sig.get('awards', [])):
        awards += 8
        why.append('award')
    heritage = ' '.join(r.get('heritage', []))
    if heritage:
        awards += 6 if 'world heritage' in heritage.lower() else 4
    awards = min(10, awards)
    era = 0 if y < 1850 else 4 if y < 1900 else 10 if y < 1945 else 14 if y < 1990 else 16
    if MODERN_STYLES.search(styles):
        era += 4
    era = min(20, era)

    penalty = 0
    generic = TRANSIT.search(inst) or SPORT.search(inst) or re.search(r'racing|circuit|race track', inst, re.I) or COMMERCE.search(inst) or (OLD_GENERIC.search(inst) and y < 1945)
    if generic:
        penalty += 10 if star else 20
        why.append('generic type')
    if y < 1850:
        penalty += 10
    if any('demolish' in s or 'destroyed' in s for s in r.get('state', [])):
        penalty += 15
        why.append('demolished')
    total = max(0, round(fame + experts + architect + awards + era - penalty))
    return total, star, why


def main():
    recs, pritzker = pool()
    sig_file = H / 'signals.json'
    signals = json.loads(sig_file.read_text(encoding='utf-8')) if sig_file.exists() else {}
    wall = load_wall()
    rejected = {c['qid'] for c in json.loads((H / 'curated.json').read_text(encoding='utf-8')) if c.get('keep') == 0}

    out, gates = [], Counter()
    for r in recs:
        g = gate(r)
        if not g and on_wall(r, wall):
            g = 'already on the wall'
        if not g and r['qid'] in rejected:
            g = 'turned down in the first curation'
        if g:
            gates[g] += 1
            continue
        s, star, why = score(r, signals.get(r['qid'], {}), pritzker)
        country = (r.get('country') or ['?'])[0]
        out.append({'qid': r['qid'], 'name': r['label'], 'architect': r['architect'][0], 'year': year(r),
                    'country': country, 'region': REGION.get(country, 'Other'), 'type': (r.get('instance') or ['?'])[0],
                    'sitelinks': r.get('sitelinks', 0), 'score': s, 'star': star, 'why': why})
    out.sort(key=lambda r: -r['score'])

    # next batch: best first, no architect more than PER_ARCHITECT times
    per, batch = Counter(), []
    for r in out:
        if len(batch) >= BATCH or r['score'] < GOOD:
            break
        if per[r['architect']] >= PER_ARCHITECT:
            continue
        per[r['architect']] += 1
        batch.append(r)
    ids = {r['qid'] for r in batch}
    for r in out:
        r['next_batch'] = r['qid'] in ids
    OUT.write_text(json.dumps(out, ensure_ascii=False, separators=(',', ':')))
    REPORT.write_text(report(recs, gates, out, batch, bool(signals)), encoding='utf-8')
    print(f'{len(out)} scored, {sum(r["score"] >= GOOD for r in out)} at {GOOD}+, next batch {len(batch)}')


def report(recs, gates, out, batch, has_signals):
    good = [r for r in out if r['score'] >= GOOD]
    L = ['# Quality score', '',
         f'Made by `tools/score.py`. Expert-database and award signals: {"included" if has_signals else "not yet (run tools/signals.py on Actions)"}.', '',
         f'- Pool: {len(recs):,} Wikidata buildings',
         f'- Ruled out: {sum(gates.values()):,} (' + ', '.join(f'{k} {v:,}' for k, v in gates.most_common()) + ')',
         f'- Scored: {len(out):,}',
         f'- At the quality bar ({GOOD}+): {len(good):,}',
         f'- Next batch: {len(batch):,} (best first, at most {PER_ARCHITECT} per architect), lowest score in it: {batch[-1]["score"] if batch else "-"}',
         '- Buildings at each bar: ' + ', '.join(f'{b}+ {sum(r["score"] >= b for r in out):,}' for b in (30, 40, 50, 60, 70)), '',
         '## How the scores spread', '', '| Score | Buildings |', '|---|---|']
    for lo in range(90, -1, -10):
        L.append(f'| {lo}–{lo + 9} | {sum(lo <= r["score"] < lo + 10 for r in out):,} |')
    for title, key in (('Next batch by region', 'region'), ('Next batch by type (top 15)', 'type')):
        L += ['', f'## {title}', '', '| | Buildings |', '|---|---|']
        L += [f'| {k} | {v} |' for k, v in Counter(r[key] for r in batch).most_common(15)]
    L += ['', '## Next batch by era', '', '| | Buildings |', '|---|---|']
    for lo, hi, name in ((0, 1900, 'Before 1900'), (1900, 1945, '1900–1945'), (1945, 1990, '1945–1990'), (1990, 2100, '1990–today')):
        L.append(f'| {name} | {sum(lo <= r["year"] < hi for r in batch)} |')
    L += ['', '## The next batch, best first', '', '| # | Score | Building | Architect | Year | Country | Type | Why |', '|---|---|---|---|---|---|---|---|']
    L += [f'| {k} | {r["score"]} | {r["name"]} | {r["architect"]} | {r["year"]} | {r["country"]} | {r["type"]} | {", ".join(r["why"])} |'
          for k, r in enumerate(batch, 1)]
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    sys.exit(main())
