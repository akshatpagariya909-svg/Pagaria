#!/usr/bin/env python3
"""Look closer at the search endpoints that answered: ArchDaily's JSON API, Bing RSS, Divisare and Architectuul pages.
Writes tools/harvest/probe_sites.txt. Run on GitHub Actions (run-tool.yml)."""
import json, re, sys, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import fetch  # noqa: E402

OUT = Path(__file__).resolve().parent / 'harvest' / 'probe_sites.txt'
lines = []
def log(s):
    lines.append(s); print(s[:300], flush=True)

for q in ['Salk Institute', 'Sendai Mediatheque']:
    d = json.loads(fetch('https://www.archdaily.com/search/api/v1/us/projects?q=' + urllib.parse.quote(q), timeout=60))
    log(f'== archdaily api keys: {list(d.keys())}')
    for k, v in d.items():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            log(f'   list {k} ({len(v)}): keys {list(v[0].keys())[:30]}')
            for it in v[:4]:
                log('     ' + json.dumps({kk: it.get(kk) for kk in ('title', 'name', 'url', 'link', 'slug', 'id', 'year', 'offices')}, ensure_ascii=False)[:400])
        elif isinstance(v, dict):
            log(f'   dict {k}: keys {list(v.keys())[:20]}')
            for kk, vv in v.items():
                if isinstance(vv, list) and vv and isinstance(vv[0], dict):
                    log(f'     list {kk} ({len(vv)}): keys {list(vv[0].keys())[:25]}')
                    for it in vv[:3]:
                        log('       ' + json.dumps({x: it.get(x) for x in ('title', 'name', 'url', 'link', 'slug', 'year')}, ensure_ascii=False)[:400])
    for site in ('archdaily.com', 'dezeen.com', 'divisare.com'):
        rss = fetch('https://www.bing.com/search?format=rss&count=10&q=' + urllib.parse.quote(f'{q} site:{site}'), timeout=30)
        items = [(i.findtext('title'), i.findtext('link')) for i in ET.fromstring(rss).iter('item')]
        log(f'== bing {site} | {q}: {len(items)} items')
        for t, l in items[:5]:
            log(f'     {t} | {l}')
    for name, url in (('divisare', 'https://divisare.com/search?q={q}'), ('architectuul', 'https://architectuul.com/search?q={q}')):
        page = fetch(url.format(q=urllib.parse.quote(q)), timeout=30).decode('utf-8', 'ignore')
        hrefs = sorted(set(re.findall(r'href="(/(?:projects|architecture)/[^"#?]+)"', page)))[:12]
        log(f'== {name} | {q}: {hrefs}')
OUT.write_text('\n'.join(lines) + '\n')
