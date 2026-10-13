"""Contact sheet of the portraits found by hand, for review by eye.

  python -u tools/portrait_sheet.py

Reads tools/portraits_found.json (see tools/portraits_BRIEF.md), downloads a 300px thumbnail of
each "found" file from Commons and writes tools/portraits_found.jpg, numbered in file order.
Runs on GitHub Actions (tools/run_request.txt), since the sandbox can't reach Wikimedia.
"""
import io
import json
import urllib.parse
import urllib.request
from pathlib import Path
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parent.parent
UA = {'User-Agent': 'DiscoverArchitecture/1.0 (https://discoverarchitecture.github.io/; portrait review)'}


def thumb(title):
    q = urllib.parse.urlencode({'action': 'query', 'titles': title, 'prop': 'imageinfo', 'iiprop': 'url', 'iiurlwidth': 300, 'format': 'json'})
    with urllib.request.urlopen(urllib.request.Request('https://commons.wikimedia.org/w/api.php?' + q, headers=UA), timeout=40) as r:
        page = next(iter(json.load(r)['query']['pages'].values()))
    url = page['imageinfo'][0]['thumburl']
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
        return Image.open(io.BytesIO(r.read())).convert('RGB')


def main():
    found = [x for x in json.loads((ROOT / 'tools' / 'portraits_found.json').read_text(encoding='utf-8')) if x['status'] == 'found']
    W, H, cols = 260, 330, 6
    sheet = Image.new('RGB', (W * cols, H * ((len(found) + cols - 1) // cols)), 'white')
    d = ImageDraw.Draw(sheet)
    for k, x in enumerate(found):
        c, r = k % cols, k // cols
        try:
            im = thumb(x['file'])
            im.thumbnail((W - 10, H - 40))
            sheet.paste(im, (c * W + 5, r * H + 5))
        except Exception as e:
            d.text((c * W + 5, r * H + 20), f'failed: {e}'[:40], fill='red')
        d.text((c * W + 5, r * H + H - 30), f"{k} {x['name']}"[:40], fill='black')
    out = ROOT / 'tools' / 'portraits_found.jpg'  # the workflow commits only site/ and tools/
    out.parent.mkdir(exist_ok=True)
    sheet.save(out, quality=85)
    print(f'{len(found)} portraits on {out}')


if __name__ == '__main__':
    main()
