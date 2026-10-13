#!/usr/bin/env python3
"""Make the numbers behind the progress dashboard (https://claude.ai/artifact/HSt3top2Y7Pzb36MbrKMWD).

  python tools/make_dashboard_data.py

Writes tools/dashboard/*.json from what is in the repository, so any chat can refresh the dashboard after its
work is merged:
  summary.json   one row: buildings, photos, drawings, links, portraits, Pritzker winners, books
  growth.json    buildings on the wall at the end of each day (by commit date, UTC)
  regions.json   buildings per region
  types.json     buildings per type
  shelves.json   books per shelf
  log.json       every pull request merged to main, newest first, with its workstream; plus the lines in
                 tools/progress_log.json (a chat adds {date, workstream, note} there for work that isn't a merge)

Then upload each changed file to the dashboard and point its source at it (the dashboard's own instructions say
how; ask Claude to "refresh the progress dashboard").
"""
import json, subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / 'tools' / 'dashboard'
STREAMS = {  # branch → workstream, as in CLAUDE.md
    'claude/awesome-clarke-vqongx': 'Data collection', 'claude/building-page': 'Building page', 'claude/game': 'Game',
    'claude/design': 'Design', 'claude/determined-wozniak-162nu7': 'Books', 'claude/seo': 'Search', 'claude/custom-domain': 'Domain',
    'claude/shuffle-surprise-browsing-5fiyin': 'Wall', 'claude/determined-wozniak': 'Books',
}


def git(*args):
    return subprocess.run(['git', *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout


def js(text, start, end):
    return json.loads(text[text.index(start):text.rindex(end) + 1])


def main():
    OUT.mkdir(exist_ok=True)
    read = lambda p: (ROOT / p).read_text(encoding='utf-8')
    buildings = js(read('site/data/buildings.js'), '[', ']')
    links = js(read('site/data/links.js'), '{', '}')
    arch = js(read('site/data/architects.js'), '{', '}')
    books = js(read('site/data/books.js'), '[', ']') if (ROOT / 'site/data/books.js').exists() else []
    pritzker = js(read('site/data/pritzker.js'), '[', ']') if (ROOT / 'site/data/pritzker.js').exists() else []

    face = lambda b: any(arch['people'].get(q, {}).get('thumb') for q in arch['buildings'].get(b['id'], []))
    drawing = lambda b: bool(b.get('images')) and b['images'][0]['src'].endswith('.svg')
    keys = {k.lower() for w in pritzker for k in w.get('keys', [])}
    summary = [{
        'buildings': len(buildings),
        'with_photo': sum(1 for b in buildings if b.get('images') and not drawing(b)),
        'drawing_cover': sum(1 for b in buildings if drawing(b)),
        'with_links': sum(1 for b in buildings if links.get(b['id'], {}).get('links')),
        'links': sum(len(links.get(b['id'], {}).get('links', [])) for b in buildings),
        'portraits': sum(1 for p in arch['people'].values() if p.get('thumb')),
        'with_face': sum(1 for b in buildings if face(b)),
        'pritzker_buildings': sum(1 for b in buildings if b['by'].split(',')[0].strip().lower() in keys or any(
            arch['people'].get(q, {}).get('name', '').lower() in keys for q in arch['buildings'].get(b['id'], []))),
        'books': len(books),
        'updated': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%MZ'),
    }]

    days = {}  # buildings at the end of each day, from every commit that changed the list
    for line in git('log', '--format=%H %cI', '--', 'site/data/buildings.js').splitlines()[::-1]:
        sha, when = line.split()
        day = datetime.fromisoformat(when).astimezone(timezone.utc).strftime('%Y-%m-%d')
        try:
            days[day] = len(js(git('show', f'{sha}:site/data/buildings.js'), '[', ']'))
        except Exception:
            continue
    growth, last = [], 0
    for day in sorted(days):
        growth.append({'day': day, 'total': days[day], 'added': days[day] - last})
        last = days[day]

    log = []
    for block in git('log', '--first-parent', 'main', '--merges', '--format=%cI%x1f%s%x1f%b%x1e').split('\x1e'):
        if not block.strip():
            continue
        when, subject, body = (block.strip().split('\x1f') + ['', ''])[:3]
        if not subject.startswith('Merge pull request'):
            continue
        num, branch = subject.split()[3], subject.split(' from ')[-1].split('/', 1)[-1]
        title = (body.strip().splitlines() or [''])[0]
        log.append({'date': datetime.fromisoformat(when).astimezone(timezone.utc).strftime('%Y-%m-%d'), 'workstream': STREAMS.get(branch, branch), 'what': title, 'pr': num.lstrip('#')})
    extra = ROOT / 'tools' / 'progress_log.json'
    if extra.exists():
        log += [{'date': e['date'], 'workstream': e['workstream'], 'what': e['note'], 'pr': ''} for e in json.loads(extra.read_text())]
    log.sort(key=lambda e: e['date'], reverse=True)

    out = {
        'summary': summary,
        'growth': growth,
        'regions': [{'region': k, 'buildings': v} for k, v in Counter(b['region'] for b in buildings).most_common()],
        'types': [{'type': k, 'buildings': v} for k, v in Counter(b['type'] for b in buildings).most_common()],
        'shelves': [{'shelf': k, 'books': v} for k, v in Counter(b.get('shelf') or 'Other' for b in books).most_common()],
        'log': log,
    }
    for name, rows in out.items():
        (OUT / f'{name}.json').write_text(json.dumps(rows, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
        print(f'{name}.json: {len(rows)} rows')
    print(summary[0])


if __name__ == '__main__':
    main()
