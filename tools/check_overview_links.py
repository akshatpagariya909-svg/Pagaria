#!/usr/bin/env python3
"""Check the overview links in the architect write-ups: does each one load, and is it about the architect?

  python -u tools/check_overview_links.py                    # every results/bios_*.json
  python -u tools/check_overview_links.py --files bios_01.json

For every link in overview_links it records the HTTP status, the final address after redirects and the
page title. A link that loads (200) and whose title or page mentions the architect's surname gets
"checked": "<date>"; any other link gets "check_failed": "<reason>" and no "checked". The results files are
updated in place and a summary goes to tools/architect_bios/links_report.json.
Needs the open internet: runs on GitHub Actions (architect-bios.yml).
"""
import argparse, datetime, html, json, re, time, unicodedata, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / 'tools' / 'architect_bios'
UA = ('Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) '
      'Chrome/124.0 Safari/537.36')


def fold(s):
    return unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode().lower()


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA, 'Accept-Language': 'en'})
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            body = r.read(800_000).decode('utf-8', 'ignore')
            return r.status, r.geturl(), body
    except urllib.error.HTTPError as err:
        return err.code, url, ''
    except Exception as err:
        return 0, url, str(err)


def keys(name):
    """Words that should appear on a page about this architect."""
    words = [w for w in re.split(r'[\s&.,]+', fold(name)) if len(w) > 2 and w not in ('and', 'the', 'van', 'der', 'de')]
    return words or [fold(name)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--files')
    args = ap.parse_args()
    files = ([DIR / 'results' / f for f in args.files.split(',')] if args.files
             else sorted((DIR / 'results').glob('bios_*.json')))
    today = datetime.date.today().isoformat()
    report = []
    for path in files:
        data = json.loads(path.read_text())
        for a in data:
            for link in a.get('overview_links', []):
                status, final, body = fetch(link['url'])
                m = re.search(r'<title[^>]*>(.*?)</title>', body, re.S | re.I)
                title = html.unescape(m.group(1)).strip() if m else ''
                page = fold(title + ' ' + body[:400_000])
                about = any(k in page for k in keys(a['name']))
                link.pop('check_failed', None)
                link.pop('checked', None)
                if status == 200 and about:
                    link['checked'] = today
                else:
                    link['check_failed'] = f'status {status}' + ('' if about else ', name not found on page')
                report.append({'architect': a['name'], 'url': link['url'], 'status': status, 'final': final,
                               'title': title[:200], 'about': about})
                print(status, 'ok ' if status == 200 and about else 'BAD', a['name'], '|', link['url'], '|', title[:80])
                time.sleep(1)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1) + '\n')
    (DIR / 'links_report.json').write_text(json.dumps(report, ensure_ascii=False, indent=1) + '\n')


if __name__ == '__main__':
    main()
