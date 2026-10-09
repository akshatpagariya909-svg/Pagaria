#!/usr/bin/env python3
"""Find each building's own page on architecture websites, so "Go deeper" opens the article itself.

  python3 tools/find_links.py                       # every building
  python3 tools/find_links.py --only salk-institute

Two sources, both checked against the building's name before a link is kept:
  1. Wikidata identifiers (archINFORM, Structurae, Archnet, Docomomo, ArchDaily …), which are exact.
  2. A web search restricted to each site; the result's address or title must name the building,
     and for one-word names the architect or city too.
Buildings without a verified page on a site fall back, in the browser, to that site's first search
result. Writes `wiki` (Wikipedia article) and `links` into site/data/buildings.js, and a report to
tools/links_report.txt. Needs open internet access, so it runs on GitHub Actions.
"""
import argparse, html, re, sys, time, urllib.parse
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fetch_images import WP, WD, api, fetch, load, save, tokens, distinctive, wiki_article, GENERIC  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
REPORT = ROOT / 'tools' / 'links_report.txt'

# (name, domain, what it is good for); the order is the order on the page.
SITES = [
    ('ArchDaily', 'archdaily.com', 'Projects & drawings'),
    ('WikiArquitectura', 'wikiarquitectura.com', 'Plans & sections'),
    ('Divisare', 'divisare.com', 'Photo essays'),
    ('Arquitectura Viva', 'arquitecturaviva.com', 'Projects'),
    ('Dezeen', 'dezeen.com', 'News & features'),
    ('The Architectural Review', 'architectural-review.com', 'Criticism'),
    ('Domus', 'domusweb.it', 'Features'),
    ('Architectuul', 'architectuul.com', 'Guide'),
    ('archINFORM', 'archinform.net', 'Database'),
    ('Archnet', 'archnet.org', 'Archive'),
    ('Docomomo', 'docomomo', 'Modern heritage'),
    ('Structurae', 'structurae.net', 'Structure'),
]
# Wikidata identifier properties, matched by label, mapped to the sites above.
WD_SITES = {'archinform project': 'archINFORM', 'structurae structure': 'Structurae', 'archnet site': 'Archnet',
            'docomomo': 'Docomomo', 'archdaily': 'ArchDaily', 'architectuul': 'Architectuul',
            'wikiarquitectura': 'WikiArquitectura', 'divisare': 'Divisare'}
SKIP_PATH = re.compile(r'/(search|tag|tags|category|categories|author|authors|page|office|offices|firm|firms|architects?|people|topics?)/|[?&]s=', re.I)
_props = {}


def wikidata_links(qid):
    ent = api(WD, action='wbgetentities', ids=qid, props='claims')['entities'][qid]
    ids = {p: c[0]['mainsnak'].get('datavalue', {}).get('value') for p, c in ent.get('claims', {}).items()
           if c and c[0]['mainsnak'].get('datatype') == 'external-id'}
    todo = [p for p in ids if p not in _props]
    for k in range(0, len(todo), 40):
        q = api(WD, action='wbgetentities', ids='|'.join(todo[k:k + 40]), props='labels|claims', languages='en')
        for p, e in q['entities'].items():
            fmt = [c['mainsnak'].get('datavalue', {}).get('value') for c in e.get('claims', {}).get('P1630', [])]
            _props[p] = ((e.get('labels', {}).get('en', {}).get('value') or '').lower(), fmt[0] if fmt else None)
    out, seen = {}, []
    for p, v in ids.items():
        label, fmt = _props.get(p, ('', None))
        seen.append(f'{label}={v}')
        site = next((s for key, s in WD_SITES.items() if key in label), None)
        if site and fmt and isinstance(v, str) and site not in out:
            out[site] = fmt.replace('$1', urllib.parse.quote(v, safe='/:'))
    return out, seen


def search(query):
    """Result (url, title) pairs: Bing's RSS feed first, DuckDuckGo's HTML page as a fallback."""
    try:
        root = ET.fromstring(fetch('https://www.bing.com/search?format=rss&count=10&q=' + urllib.parse.quote(query), timeout=30))
        hits = [(i.findtext('link') or '', i.findtext('title') or '') for i in root.iter('item')]
        if hits:
            return hits
    except Exception as e:
        print('    bing failed:', e)
    try:
        page = fetch('https://html.duckduckgo.com/html/?q=' + urllib.parse.quote(query), timeout=30).decode('utf-8', 'ignore')
        hits = []
        for href, title in re.findall(r'class="result__a" href="([^"]+)"[^>]*>(.*?)</a>', page):
            u = urllib.parse.parse_qs(urllib.parse.urlparse(html.unescape(href)).query).get('uddg', [html.unescape(href)])[0]
            hits.append((u, re.sub('<[^>]+>', '', html.unescape(title))))
        return hits
    except Exception as e:
        print('    duckduckgo failed:', e)
        return []


def about(b, url, title):
    """True when the page is plausibly this building's own page."""
    d = distinctive(b) or (tokens(b['name']) - GENERIC)
    path = urllib.parse.unquote(urllib.parse.urlparse(url).path)
    text = tokens(path.replace('-', ' ').replace('_', ' ') + ' ' + title)
    need = min(2, len(d))
    if len(d & text) < need:
        return False
    if len(d) == 1:  # a single word like "Pavilion" or "Golconde" needs the architect or city too
        extra = (tokens(b['by']) | tokens(b['place'].split(',')[0])) - GENERIC
        return bool(extra & text)
    return True


def site_link(b, name, domain):
    surname = b['by'].split(',')[0].split()[-1]
    for hit_url, title in search(f'site:{domain} {b["name"]} {surname}'):
        host = urllib.parse.urlparse(hit_url).netloc.lower()
        if domain in host and not SKIP_PATH.search(hit_url) and urllib.parse.urlparse(hit_url).path.strip('/') and about(b, hit_url, title):
            return hit_url
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--only', default='')
    args = ap.parse_args()
    only = set(filter(None, args.only.split(',')))
    head, items = load()
    report = []
    for b in items:
        if only and b['id'] not in only:
            continue
        print(f"{b['n']:>3} {b['name']}")
        found, notes = {}, []
        try:
            page = wiki_article(b)
            if page and 'missing' not in page:
                b['wiki'] = 'https://en.wikipedia.org/wiki/' + urllib.parse.quote(page['title'].replace(' ', '_'))
                qid = page.get('pageprops', {}).get('wikibase_item')
                if qid:
                    found, notes = wikidata_links(qid)
        except Exception as e:
            print('    wikipedia/wikidata failed:', e)
        for name, domain, _ in SITES:
            if name in found or name in ('Structurae', 'Docomomo', 'Archnet'):  # these come from Wikidata only
                continue
            if name == 'archINFORM' and found:
                continue
            u = site_link(b, name, domain)
            if u:
                found[name] = u
            time.sleep(1.2)
        b['links'] = [{'site': n, 'kind': k, 'url': found[n]} for n, _, k in SITES if n in found]
        print('    ' + (', '.join(found) or 'none'))
        report.append(f"{b['n']:03d} {b['name']}\n" + ''.join(f'    {n}: {u}\n' for n, u in found.items())
                      + (f"    wikidata ids: {'; '.join(notes)}\n" if notes else ''))
        save(head, items)
    if not only:
        REPORT.write_text('\n'.join(report))
    print('Done.')


if __name__ == '__main__':
    sys.exit(main())
