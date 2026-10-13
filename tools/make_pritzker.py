#!/usr/bin/env python3
"""Make site/data/pritzker.js, the Pritzker Prize winners the wall marks with a gold medal.

  python tools/make_pritzker.py            write it, and list which names on the wall each winner matched
  python tools/make_pritzker.py --dry-run  just list the matches

Reads tools/pritzker_found.json: one entry per year, {year, laureates[], firm, citation_url, line, note}, collected
from the prize's own site and checked by hand (the line is copied word for word from that year's jury citation).

The site finds a winner by name, so each entry gets `keys`: every way the wall writes that winner. These are the
winner's own names and firm, the names of portraits in site/data/architects.js, and the names in by lines, when
they carry the winner's surname and the first name (or its initial). "B. V. Doshi" matches Balkrishna Doshi, "Álvaro
Siza" Álvaro Siza Vieira; a different Doshi does not. Run it again after the buildings or portraits change.
"""
import argparse, json, re, unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOUND = ROOT / 'tools' / 'pritzker_found.json'
OUT = ROOT / 'site' / 'data' / 'pritzker.js'


def fold(s):
    return unicodedata.normalize('NFD', s or '').encode('ascii', 'ignore').decode().lower()


def words(s):
    return re.findall(r'[a-z]+', fold(s))


def same_person(laureate, name):
    """Does `name`, as the wall writes it, name this laureate? Surname, plus first name or its initial."""
    lw, nw = words(laureate), words(name)
    if not lw or not nw or len(nw) > len(lw) + 2:  # "Richard Rogers Partnership" yes; a long by line no
        return False
    if set(lw) <= set(nw):
        return True
    if len(nw) >= 2 and set(nw) <= set(lw):  # a shorter form: "Álvaro Siza" for Álvaro Siza Vieira, "Francis Kéré"
        return True
    return lw[-1] in nw and nw[0][0] == lw[0][0] and nw[-1] == lw[-1]


def load(path, start, end):
    s = path.read_text(encoding='utf-8')
    return json.loads(s[s.index(start):s.rindex(end) + 1])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    args = ap.parse_args()
    found = json.loads(FOUND.read_text(encoding='utf-8'))
    buildings = load(ROOT / 'site' / 'data' / 'buildings.js', '[', ']')
    people = load(ROOT / 'site' / 'data' / 'architects.js', '{', '}')['people']
    names = {p['name'] for p in people.values() if p.get('name')}
    for b in buildings:
        names |= {n.strip() for n in b['by'].split(',') if n.strip()}
    out = []
    for e in found:
        keys = set(e['laureates']) | ({e['firm']} if e.get('firm') else set())
        for n in names:
            if any(same_person(l, n) for l in e['laureates']) or (e.get('firm') and fold(e['firm']) == fold(n)):
                keys.add(n)
        out.append({'year': e['year'], 'names': e['laureates'], 'line': e.get('line'), 'url': e.get('citation_url'),
                    'keys': sorted(keys, key=fold)})
        print(f"{e['year']} {' & '.join(e['laureates'])}: {', '.join(k for k in sorted(keys) if k not in e['laureates'])}")
    if args.dry_run:
        return
    OUT.write_text('// Pritzker Prize winners, with one line from each jury citation. Made by tools/make_pritzker.py from\n'
                   '// tools/pritzker_found.json; do not edit by hand. The wall puts a gold medal on their portraits.\n'
                   'window.PRITZKER = ' + json.dumps(out, ensure_ascii=False, indent=1) + ';\n', encoding='utf-8')
    print(f'{len(out)} years written to {OUT.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
