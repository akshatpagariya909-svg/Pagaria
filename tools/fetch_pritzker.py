#!/usr/bin/env python3
"""Save each Pritzker Prize jury citation from pritzkerprize.com, so a line can be chosen from it by hand.

  python -u tools/fetch_pritzker.py

Needs the open internet, so it runs on GitHub Actions (tools/run_request.txt). Reads the winners from
tools/pritzker_found.json, finds the prize's own pages for each year (its sitemap, then its laureates page), and
writes the text of the page that holds the jury citation to tools/pritzker_citations/<year>.txt, with its URL on
the first line. tools/pritzker_citations/report.txt says what was found for each year. The line shown on the site
is then copied from these files by hand into tools/pritzker_found.json (line, citation_url).
"""
import html, json, re, time, unicodedata, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FOUND = ROOT / 'tools' / 'pritzker_found.json'
OUT = ROOT / 'tools' / 'pritzker_citations'
SITE = 'https://www.pritzkerprize.com'
UA = {'User-Agent': 'DiscoverArchitecture/1.0 (https://findgreatarchitecture.com/; jury citations)'}


def get(url):
    for attempt in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=40) as r:
                return r.read().decode('utf-8', 'replace')
        except Exception as e:
            print('  retry', url, e)
            time.sleep(3 * (attempt + 1))
    return ''


def text(page):
    page = re.sub(r'(?is)<(script|style|noscript|svg).*?</\1>', ' ', page)
    page = re.sub(r'(?i)<(br|/p|/h\d|/li|/div)[^>]*>', '\n', page)
    page = html.unescape(re.sub(r'<[^>]+>', ' ', page))
    return re.sub(r'\n\s*\n+', '\n\n', re.sub(r'[ \t\r\f\v]+', ' ', page)).strip()


def slug(s):
    return re.sub(r'[^a-z0-9]+', '-', unicodedata.normalize('NFD', s).encode('ascii', 'ignore').decode().lower()).strip('-')


def main():
    found = json.loads(FOUND.read_text(encoding='utf-8'))
    OUT.mkdir(exist_ok=True)
    urls = set()
    for sm in (SITE + '/sitemap.xml', SITE + '/sitemap_index.xml'):
        xml = get(sm)
        for loc in re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', xml):
            if loc.endswith('.xml'):
                urls |= set(re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', get(loc)))
            else:
                urls.add(loc)
    for page in (SITE + '/laureates', SITE + '/laureates/'):
        urls |= {u if u.startswith('http') else SITE + u for u in re.findall(r'href="([^"#?]*laureate[^"#?]*)"', get(page))}
    urls = sorted(u for u in urls if 'pritzkerprize.com' in u)
    print(len(urls), 'pages on the site')
    report = [f'{len(urls)} pages found on {SITE}', '']
    for e in found:
        year, surnames = str(e['year']), [slug(n).split('-')[-1] for n in e['laureates']]
        cands = [u for u in urls if year in u or any(s and s in u.lower() for s in surnames)]
        cands.sort(key=lambda u: (('citation' not in u.lower() and 'jury' not in u.lower()), len(u)))
        best = None
        for u in cands[:8]:
            t = text(get(u))
            time.sleep(1)
            i = max(t.lower().find('jury citation'), t.lower().find('citation'))
            if i >= 0 and any(s in slug(t).replace('-', ' ') for s in surnames):
                best = (u, t[i:i + 9000])
                if 'jury citation' in t.lower():
                    break
        if best:
            (OUT / f'{year}.txt').write_text(best[0] + '\n\n' + best[1] + '\n', encoding='utf-8')
            report.append(f'{year} {" & ".join(e["laureates"])}: {best[0]}')
        else:
            report.append(f'{year} {" & ".join(e["laureates"])}: no citation found (tried {len(cands)} pages: {", ".join(cands[:4])})')
        print(report[-1])
    (OUT / 'report.txt').write_text('\n'.join(report) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
