"""Fetch each "Go deeper" site's own icon into site/images/logos/.

For every site it reads the home page, collects the icons it declares (apple-touch-icon,
icon, mask-icon), and keeps the largest: an SVG if there is one, otherwise the biggest
PNG or ICO, saved as a 128 px PNG. If the page declares nothing it falls back to
/apple-touch-icon.png and /favicon.ico. The icons are used only to point at each site.

Needs open internet, so it runs on GitHub Actions
(tools/run_request.txt: python -u tools/fetch_logos.py). Writes tools/logos_report.txt.
"""
import io
import re
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'site' / 'images' / 'logos'
REPORT = ROOT / 'tools' / 'logos_report.txt'
UA = {'User-Agent': 'Mozilla/5.0 (DiscoverArchitecture/1.0; https://findgreatarchitecture.com/; logos)'}

SITES = {
    'archdaily': 'https://www.archdaily.com/',
    'wikiarquitectura': 'https://en.wikiarquitectura.com/',
    'dezeen': 'https://www.dezeen.com/',
    'divisare': 'https://divisare.com/',
    'archinform': 'https://www.archinform.net/index.htm',
    'wikipedia': 'https://en.wikipedia.org/',
    'youtube': 'https://www.youtube.com/',
    'commons': 'https://commons.wikimedia.org/',
    'openstreetmap': 'https://www.openstreetmap.org/',
}


class Icons(HTMLParser):
    def __init__(self):
        super().__init__()
        self.found = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        rel = (a.get('rel') or '').lower()
        if tag == 'link' and a.get('href') and ('icon' in rel):
            size = max([int(n) for n in re.findall(r'(\d+)x\d+', a.get('sizes') or '')] or [0])
            self.found.append((a['href'], rel, size, (a.get('type') or '').lower()))


def get(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30) as r:
        return r.read(), r.headers.get('Content-Type', '')


def score(item):
    href, rel, size, typ = item
    svg = href.lower().split('?')[0].endswith('.svg') or 'svg' in typ
    return (2 if svg and 'mask' not in rel else 0, 1 if 'apple' in rel else 0, size)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    report = []
    for key, home in SITES.items():
        try:
            html, _ = get(home)
            p = Icons()
            p.feed(html.decode('utf-8', 'ignore'))
            cands = sorted(p.found, key=score, reverse=True)
            urls = [urllib.parse.urljoin(home, c[0]) for c in cands] + [urllib.parse.urljoin(home, '/apple-touch-icon.png'), urllib.parse.urljoin(home, '/favicon.ico')]
            saved = None
            for u in urls:
                try:
                    data, ctype = get(u)
                except Exception:
                    continue
                if u.lower().split('?')[0].endswith('.svg') or 'svg' in ctype:
                    (OUT / f'{key}.svg').write_bytes(data)
                    saved = f'{key}.svg'
                    break
                try:
                    im = Image.open(io.BytesIO(data))
                    # Pillow opens an .ico at its largest size
                    im = im.convert('RGBA')
                    im.thumbnail((128, 128))
                    im.save(OUT / f'{key}.png')
                    saved = f'{key}.png ({im.width}px)'
                    break
                except Exception:
                    continue
            report.append(f'{key}: {saved or "nothing found"}  ({home})')
        except Exception as e:
            report.append(f'{key}: failed, {e}')
        print(report[-1])
    REPORT.write_text('\n'.join(report) + '\n')


if __name__ == '__main__':
    main()
