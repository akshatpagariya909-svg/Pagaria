#!/usr/bin/env python3
"""Turns what tools/fetch_analytics.py saved (daily.csv, latest.json on the analytics-data branch) into the
small tables the visitor dashboard reads. Plain reshaping, no calculation beyond renaming.

    python3 tools/analytics_dashboard_data.py --src <folder with daily.csv + latest.json> --out <folder>

Writes into --out: daily.csv, breakdowns.json, pages.json, opened.json, status.json
"""
import argparse, csv, json, os

DEVICES = {'phone': 'Phone', 'tablet': 'Tablet', 'desktop': 'Desktop', 'desktophd': 'Large desktop', 'unknown': 'Unknown'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    latest = json.load(open(os.path.join(a.src, 'latest.json')))
    sec = latest['sections']
    until = latest['fetched_at'][:10]  # never show a day later than the day the numbers were fetched
    with open(os.path.join(a.src, 'daily.csv'), newline='') as f, open(os.path.join(a.out, 'daily.csv'), 'w', newline='') as g:
        w = csv.writer(g)
        w.writerow(['day', 'visits'])
        for r in csv.DictReader(f):
            if r['day'] <= until:
                w.writerow([r['day'], r['visits']])

    rows = []
    def add(group, name, visits):
        if int(visits or 0) > 0:
            rows.append({'group': group, 'name': name, 'visits': int(visits)})
    for r in sec['referrers']['stats']:
        # scheme: o = other/direct, g = generated (search engines), h = http link, c = campaign (?ref=...)
        name = r.get('name') or ''
        label = ('Campaign: ' + name) if r.get('ref_scheme') == 'c' else (name or 'Direct or unknown')
        add('Where from', label, r['count'])
    for r in sec['sizes']['stats']:
        add('Device', DEVICES.get(r['id'], r['id']), r['count'])
    for r in sec['systems']['stats']:
        add('System', r.get('name') or r['id'], r['count'])
    for r in sec['browsers']['stats']:
        add('Browser', r.get('name') or r['id'], r['count'])
    for r in sec['locations']['stats']:
        add('Country', r.get('name') or r['id'], r['count'])
    json.dump(rows, open(os.path.join(a.out, 'breakdowns.json'), 'w'), indent=1)

    pages, opened = [], []
    for h in sec['pages'].get('hits') or []:
        if h.get('event'):
            kind, _, key = h['path'].partition('/')
            if kind in ('building', 'book'):
                opened.append({'path': h['path'], 'kind': 'Book' if kind == 'book' else 'Building', 'name': h.get('title') or key, 'opens': int(h['count'])})
        else:
            pages.append({'path': h['path'], 'title': h.get('title') or '', 'visits': int(h['count'])})
    pages.sort(key=lambda r: -r['visits'])
    opened.sort(key=lambda r: -r['opens'])
    json.dump(pages, open(os.path.join(a.out, 'pages.json'), 'w'), indent=1)
    json.dump(opened, open(os.path.join(a.out, 'opened.json'), 'w'), indent=1)
    json.dump([{'fetched_at': latest['fetched_at'], 'visits_30d': latest.get('visits_30d')}], open(os.path.join(a.out, 'status.json'), 'w'), indent=1)
    print(f'{len(rows)} breakdown rows, {len(pages)} pages, {len(opened)} opened buildings/books')


if __name__ == '__main__':
    main()
