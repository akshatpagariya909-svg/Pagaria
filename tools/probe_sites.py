#!/usr/bin/env python3
"""Try each architecture site's own search for a few known buildings, to see which can be queried directly.
Writes tools/harvest/probe_sites.txt. Run on GitHub Actions (run-tool.yml)."""
import json, sys, urllib.parse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import fetch  # noqa: E402

OUT = Path(__file__).resolve().parent / 'harvest' / 'probe_sites.txt'
TESTS = ['Salk Institute', 'Villa Savoye', 'Sendai Mediatheque']
ENDPOINTS = {
    'wikiarquitectura (wp-json)': 'https://en.wikiarquitectura.com/wp-json/wp/v2/search?per_page=5&search={q}',
    'dezeen (wp-json)': 'https://www.dezeen.com/wp-json/wp/v2/search?per_page=5&search={q}',
    'archdaily (api)': 'https://www.archdaily.com/search/api/v1/us/projects?q={q}',
    'archdaily (html)': 'https://www.archdaily.com/search/all?q={q}',
    'divisare (html)': 'https://divisare.com/search?q={q}',
    'architectuul (html)': 'https://architectuul.com/search?q={q}',
    'arquitecturaviva (html)': 'https://arquitecturaviva.com/search?q={q}',
    'domus (html)': 'https://www.domusweb.it/en/search.html?q={q}',
    'architectural-review (wp-json)': 'https://www.architectural-review.com/wp-json/wp/v2/search?per_page=5&search={q}',
    'bing rss': 'https://www.bing.com/search?format=rss&q={q}+site%3Aarchdaily.com',
    'duckduckgo html': 'https://html.duckduckgo.com/html/?q={q}+site%3Aarchdaily.com',
}
lines = []
for name, url in ENDPOINTS.items():
    for q in TESTS[:2]:
        u = url.format(q=urllib.parse.quote(q))
        try:
            body = fetch(u, timeout=30).decode('utf-8', 'ignore')
            snippet = body[:600].replace('\n', ' ')
            if body.lstrip().startswith('[') or body.lstrip().startswith('{'):
                try:
                    data = json.loads(body)
                    snippet = json.dumps(data)[:600]
                except Exception:
                    pass
            lines.append(f'== {name} | {q} | OK {len(body)} bytes\n{snippet}\n')
        except Exception as e:
            lines.append(f'== {name} | {q} | ERROR {e}\n')
        print(lines[-1][:200], flush=True)
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text('\n'.join(lines))
