"""One name per architect, the same way the wall does it (site/data/names.js), for the generators.

names.js is the rule book: its WHOLE and SAME lists are read from that file at run time, so the two cannot drift apart.
The steps below mirror names.js (parts, tidy, pair, spell); `tools/check_names_parity.js` compares the two on every
building.

    import names_py
    nm = names_py.Names(buildings)       # buildings: dicts with a "by" credit
    nm.list("Zaha Hadid Architects")      # ['Zaha Hadid']
    nm.canon("Foster + Partners")         # 'Norman Foster'
"""
import re
import unicodedata
from pathlib import Path

NAMES_JS = Path(__file__).resolve().parent.parent / 'site' / 'data' / 'names.js'
_STR = re.compile(r"'((?:[^'\\]|\\.)*)'|\"((?:[^\"\\]|\\.)*)\"")


def _strings(block):
    return [(a or b).replace("\\'", "'").replace('\\"', '"') for a, b in _STR.findall(block)]


def _load():
    js = NAMES_JS.read_text()
    whole = _strings(re.search(r'const WHOLE = \[(.*?)\];', js, re.S).group(1))
    flat = _strings(re.search(r'const SAME = \{(.*?)\n  \};', js, re.S).group(1))
    return whole, dict(zip(flat[0::2], flat[1::2]))


WHOLE, SAME = _load()


def fold(s):
    return ''.join(c for c in unicodedata.normalize('NFD', str(s).lower()) if not unicodedata.combining(c))


def marks(s):
    return sum(1 for c in unicodedata.normalize('NFD', s) if unicodedata.combining(c))


def parts(by):
    s = str(by or '')
    for i, w in enumerate(WHOLE):
        s = s.replace(w, f'\x01{i}\x01')
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        if ch == ')':
            depth = max(0, depth - 1)
        if not depth and ch in ',;':
            out.append(cur)
            cur = ''
        else:
            cur += ch
    out.append(cur)
    res = []
    for p in out:
        for q in re.split(r'\s+with\s+', p, flags=re.I):
            q = re.sub(r'\x01(\d+)\x01', lambda m: WHOLE[int(m.group(1))], q).strip()
            q = re.sub(r'^[a-z][^A-Z]*?\bby\s+', '', q)
            if q:
                res.append(q)
    return res


def tidy(name):
    if name in SAME:
        return SAME[name]
    bare = re.sub(r'\s+\(.*?\)', ' ', name)
    bare = re.sub(r'\s+\(.*$', '', bare)
    bare = re.sub(r'\s+', ' ', bare).strip() or name
    return SAME.get(bare, bare)


class Names:
    def __init__(self, buildings):
        self.count = {}
        for b in buildings:
            for p in parts(b['by']):
                t = tidy(p)
                self.count[t] = self.count.get(t, 0) + 1
        self.spelling = {}
        for name, k in self.count.items():
            key = fold(name)
            best = self.spelling.get(key)
            if best is None or marks(name) > marks(best) or (marks(name) == marks(best) and k > self.count[best]):
                self.spelling[key] = name

    def spell(self, t):
        return self.spelling.get(fold(t), t)

    def pair(self, t):
        bits = [tidy(x) for x in re.split(r'\s+(?:and|&)\s+', t)]
        return bits if len(bits) > 1 and all(x in self.count for x in bits) else [t]

    def canon(self, name):
        return self.spell(tidy(str(name).strip()))

    def list(self, by):
        seen, out = set(), []
        for p in parts(by):
            for t in self.pair(tidy(p)):
                s = self.spell(t)
                if s not in seen:
                    seen.add(s)
                    out.append(s)
        return out


if __name__ == '__main__':  # python3 tools/names_py.py > /tmp/names_py.json; node tools/check_names_parity.js /tmp/names_py.json
    import json
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import build_pages
    its = build_pages.load()
    nm_ = Names(its)
    json.dump([nm_.list(b['by']) for b in its], sys.stdout, ensure_ascii=False)
