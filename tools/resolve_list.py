#!/usr/bin/env python3
"""Find the Wikidata item for each hand-picked building in tools/harvest/extra.json.

Each entry needs name, by and city. The search tries Wikipedia (title, then a search that must
name the building), then Wikidata's own search; an item is accepted only when its architect or
location matches. Adds qid, commons, image and coords, and writes tools/harvest/extra_resolved.json.
Runs on GitHub Actions (run-tool.yml).
"""
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import api, WD, wiki_article, tokens, GENERIC  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
IN = ROOT / 'tools' / 'harvest' / 'extra.json'
OUT = ROOT / 'tools' / 'harvest' / 'extra_resolved.json'


def facts(qid):
    ent = api(WD, action='wbgetentities', ids=qid, props='claims|labels', languages='en')['entities'][qid]
    c = ent.get('claims', {})
    def vals(p):
        return [x['mainsnak'].get('datavalue', {}).get('value') for x in c.get(p, []) if x['mainsnak'].get('snaktype') == 'value']
    arch = [v['id'] for v in vals('P84') if isinstance(v, dict)]
    loc = [v['id'] for v in vals('P131') + vals('P17') if isinstance(v, dict)]
    names = {}
    ids = arch + loc
    if ids:
        q = api(WD, action='wbgetentities', ids='|'.join(ids[:50]), props='labels', languages='en')['entities']
        names = {k: v.get('labels', {}).get('en', {}).get('value', '') for k, v in q.items()}
    xy = vals('P625')
    return {'architects': [names.get(a, '') for a in arch], 'places': [names.get(l, '') for l in loc],
            'commons': (vals('P373') or [None])[0], 'image': (vals('P18') or [None])[0],
            'coords': [xy[0]['latitude'], xy[0]['longitude']] if xy and isinstance(xy[0], dict) else None}


def plausible(e, f):
    by = tokens(e['by']) - GENERIC
    city = tokens(e['city'])
    return bool(by & tokens(' '.join(f['architects']))) or bool(city & tokens(' '.join(f['places'])))


def main():
    items = json.loads(IN.read_text())
    out = []
    for e in items:
        b = {'name': e['name'], 'by': e['by'], 'place': e['city']}
        qid, f = None, None
        try:
            page = wiki_article(b)
            cand = [page.get('pageprops', {}).get('wikibase_item')] if page else []
            q = api(WD, action='wbsearchentities', search=e['name'], language='en', limit=5)
            cand += [s['id'] for s in q.get('search', [])]
            for c in dict.fromkeys(x for x in cand if x):
                f = facts(c)
                if plausible(e, f) and (f['commons'] or f['image']):
                    qid = c
                    break
        except Exception as ex:
            print('  error', e['name'], ex)
        print(('OK ' if qid else '-- ') + e['name'], qid or '', flush=True)
        out.append({**e, 'qid': qid, **({k: f[k] for k in ('commons', 'image', 'coords')} if qid else {})})
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=0))
    print(f"{sum(1 for o in out if o['qid'])}/{len(out)} resolved")


if __name__ == '__main__':
    sys.exit(main())
