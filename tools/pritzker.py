#!/usr/bin/env python3
"""Every Pritzker Prize winner and every building Wikidata credits to them or their firm.

  python -u tools/pritzker.py      # writes tools/pritzker/{laureates.json, buildings.json, report.txt}

Winners come from Wikidata ("award received: Pritzker Architecture Prize"), firms from
"founded by" a winner. Buildings are items whose architect (P84) is a winner or one of
those firms. For each building it records the facts the site uses plus the extra facts
we want for filters (height, floors, area, materials, engineer, awards, heritage, state).
Nothing is added to the wall: this only counts and collects, so we can choose.
Needs open internet access, so it runs on GitHub Actions (run-tool.yml).
"""
import json, sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import api, WD  # noqa: E402
from harvest import sparql, value, labels  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tools' / 'pritzker'
WELL_KNOWN = 6  # Wikipedia language editions; the bar the 1,000 list used

PROPS = {'P84': 'architect', 'P571': 'inception', 'P1619': 'opened', 'P17': 'country', 'P131': 'located',
         'P625': 'coords', 'P373': 'commons', 'P18': 'image', 'P31': 'instance', 'P149': 'style',
         'P856': 'website', 'P1435': 'heritage', 'P5816': 'state', 'P576': 'demolished',
         'P2048': 'height', 'P1101': 'floors', 'P2046': 'area', 'P186': 'materials',
         'P631': 'engineer', 'P166': 'awards'}
NAMED = ('architect', 'country', 'located', 'instance', 'style', 'heritage', 'state', 'materials', 'engineer', 'awards')
FACTS = ('height', 'floors', 'area', 'materials', 'engineer', 'awards', 'heritage', 'state', 'coords', 'image', 'commons')


def laureates():
    rows = sparql('''SELECT ?a ?aLabel (MIN(YEAR(?t)) AS ?year) WHERE {
      VALUES ?name { "Pritzker Architecture Prize"@en "Pritzker Prize"@en }
      ?prize rdfs:label ?name .
      ?a p:P166 ?st . ?st ps:P166 ?prize .
      OPTIONAL { ?st pq:P585 ?t }
      SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
    } GROUP BY ?a ?aLabel''')
    out = {}
    for r in rows:
        qid = r['a']['value'].rsplit('/', 1)[1]
        out[qid] = {'qid': qid, 'name': r['aLabel']['value'], 'year': int(r['year']['value']) if 'year' in r else None, 'firms': {}}
    if len(out) < 40:  # 55 winners by 2026; fewer means the prize wasn't matched
        sys.exit(f'Only {len(out)} winners found; check the prize label in laureates()')
    return out


def firms(people):
    values = ' '.join('wd:' + q for q in people)
    rows = sparql(f'''SELECT ?f ?fLabel ?a WHERE {{
      VALUES ?a {{ {values} }}
      ?f wdt:P112 ?a .
      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
    }}''')
    for r in rows:
        f, a = (r[k]['value'].rsplit('/', 1)[1] for k in ('f', 'a'))
        people[a]['firms'][f] = r['fLabel']['value']


def building_ids(people):
    owner = {}
    for a, p in people.items():
        owner.setdefault(a, set()).add(a)
        for f in p['firms']:
            owner.setdefault(f, set()).add(a)
    found = {}
    keys = sorted(owner)
    for k in range(0, len(keys), 40):
        values = ' '.join('wd:' + q for q in keys[k:k + 40])
        rows = sparql(f'''SELECT ?b ?who ?n WHERE {{
          VALUES ?who {{ {values} }}
          ?b wdt:P84 ?who .
          OPTIONAL {{ ?b wikibase:sitelinks ?n }}
        }}''')
        for r in rows:
            b, who = (r[x]['value'].rsplit('/', 1)[1] for x in ('b', 'who'))
            rec = found.setdefault(b, {'laureates': set(), 'sitelinks': 0})
            rec['laureates'].update(owner[who])
            rec['sitelinks'] = max(rec['sitelinks'], int(r.get('n', {}).get('value', 0)))
    return found


def entities(qids):
    out = {}
    for k in range(0, len(qids), 50):
        q = api(WD, action='wbgetentities', ids='|'.join(qids[k:k + 50]), props='labels|claims|sitelinks', languages='en', sitefilter='enwiki')
        for qid, ent in q.get('entities', {}).items():
            rec = {'qid': qid, 'label': ent.get('labels', {}).get('en', {}).get('value'),
                   'enwiki': ent.get('sitelinks', {}).get('enwiki', {}).get('title')}
            for p, name in PROPS.items():
                vals = [value(c['mainsnak']) for c in ent.get('claims', {}).get(p, []) if c['mainsnak'].get('snaktype') == 'value']
                if vals:
                    rec[name] = vals
            out[qid] = rec
        if k % 1000 == 0:
            print(f'  {k}/{len(qids)}', flush=True)
    return out


def quantity(v, units):
    """Wikidata quantities arrive as {'amount': '+120', 'unit': '.../Q11573'}; keep number and unit name."""
    if not isinstance(v, dict) or 'amount' not in v:
        return v
    unit = v.get('unit', '1').rsplit('/', 1)[-1]
    return [float(v['amount']), units.get(unit, '') if unit != '1' else '']


def on_wall():
    s = (ROOT / 'site' / 'data' / 'buildings.js').read_text(encoding='utf-8')
    B = json.loads(s[s.index('=', s.index('window.BUILDINGS')) + 1:].strip().rstrip(';'))
    return {b['qid'] for b in B if b.get('qid')}, {b['name'].lower() for b in B}


def main():
    people = laureates()
    print(f'{len(people)} Pritzker winners on Wikidata', flush=True)
    firms(people)
    print(f'{sum(len(p["firms"]) for p in people.values())} firms founded by them', flush=True)
    found = building_ids(people)
    print(f'{len(found)} items with a winner or their firm as architect', flush=True)
    recs = entities(sorted(found))

    refs, units = set(), set()
    for r in recs.values():
        for key in NAMED:
            refs.update(v for v in r.get(key, []) if isinstance(v, str) and v.startswith('Q'))
        for key in ('height', 'area'):
            units.update(v['unit'].rsplit('/', 1)[-1] for v in r.get(key, []) if isinstance(v, dict) and v.get('unit', '1') != '1')
    print(f'resolving {len(refs) + len(units)} labels', flush=True)
    names = labels(refs | units)
    wall_q, wall_n = on_wall()
    for qid, r in recs.items():
        for key in NAMED:
            if key in r:
                r[key] = [names.get(v, v) if isinstance(v, str) else v for v in r[key]]
        for key in ('height', 'floors', 'area'):
            if key in r:
                r[key] = [quantity(v, names) for v in r[key]]
        r['laureates'] = sorted(people[a]['name'] for a in found[qid]['laureates'])
        r['sitelinks'] = found[qid]['sitelinks']
        r['on_wall'] = qid in wall_q or (r.get('label') or '').lower() in wall_n

    rows = sorted(recs.values(), key=lambda r: -r['sitelinks'])
    OUT.mkdir(parents=True, exist_ok=True)
    winners = sorted(({**p, 'firms': sorted(p['firms'].values())} for p in people.values()), key=lambda p: (p['year'] or 0, p['name']))
    (OUT / 'laureates.json').write_text(json.dumps(winners, ensure_ascii=False, indent=1))
    (OUT / 'buildings.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')))
    (OUT / 'report.txt').write_text(report(winners, rows), encoding='utf-8')
    print(f'Wrote {len(rows)} buildings to {(OUT / "buildings.json").relative_to(ROOT)}')


def report(winners, rows):
    photo = lambda r: bool(r.get('image') or r.get('commons'))
    known = [r for r in rows if r['sitelinks'] >= WELL_KNOWN]
    lines = ['Pritzker winners and their buildings, from Wikidata. Made by tools/pritzker.py.', '',
             f'Winners: {len(winners)}',
             f'All buildings credited to them or their firms: {len(rows)}',
             f'  with a free photo or Commons folder: {sum(photo(r) for r in rows)}',
             f'  with coordinates: {sum(bool(r.get("coords")) for r in rows)}',
             f'  already on the wall: {sum(r["on_wall"] for r in rows)}',
             f'Well known (Wikipedia in {WELL_KNOWN}+ languages): {len(known)}',
             f'  with a free photo or Commons folder: {sum(photo(r) for r in known)}',
             f'  already on the wall: {sum(r["on_wall"] for r in known)}',
             f'  new, with a photo: {sum(photo(r) and not r["on_wall"] for r in known)}',
             '', 'How many buildings have each fact (all / well known):']
    for f in FACTS:
        lines.append(f'  {f:10} {sum(bool(r.get(f)) for r in rows):5} / {sum(bool(r.get(f)) for r in known)}')
    lines += ['', 'What the items are (top 25):']
    for k, n in Counter(i for r in rows for i in r.get('instance', [])[:1]).most_common(25):
        lines.append(f'  {n:5}  {k}')
    lines += ['', 'Per winner: year | name | all | with photo | well known | already on wall | firms found']
    for p in winners:
        mine = [r for r in rows if p['name'] in r['laureates']]
        lines.append(f'{p["year"]} | {p["name"]} | {len(mine)} | {sum(photo(r) for r in mine)} | '
                     f'{sum(r["sitelinks"] >= WELL_KNOWN for r in mine)} | {sum(r["on_wall"] for r in mine)} | {", ".join(p["firms"]) or "-"}')
    return '\n'.join(lines) + '\n'


if __name__ == '__main__':
    sys.exit(main())
