#!/usr/bin/env python3
"""Turns what tools/fetch_analytics.py saved (daily.csv, latest.json on the analytics-data branch) into the
small tables the visitor dashboard reads. Plain reshaping, no calculation beyond renaming.

    python3 tools/analytics_dashboard_data.py --src <folder with daily.csv + latest.json> --out <folder>

Writes into --out: daily.csv, breakdowns.json, pages.json, status.json
(Buildings and books opened are rows of breakdowns.json with group 'Opened': a file with no rows cannot be loaded by the dashboard.)
"""
import argparse, csv, datetime as dt, json, os

# The dashboard is refreshed at these UTC hours, at minute 07, one hour after each GitHub fetch (workflow analytics.yml).
# Keep in step with the "Refresh Visitors dashboard" routine's schedule.
REFRESH_HOURS_UTC = (1, 7, 13, 19)


def next_refresh(now):
    """The next scheduled refresh after `now` (UTC)."""
    for day in (0, 1):
        for h in REFRESH_HOURS_UTC:
            t = (now + dt.timedelta(days=day)).replace(hour=h, minute=7, second=0, microsecond=0)
            if t > now:
                return t


DEVICES = {'phone': 'Phone', 'tablet': 'Tablet', 'desktop': 'Desktop', 'desktophd': 'Large desktop', 'unknown': 'Unknown'}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--src', required=True)
    ap.add_argument('--out', required=True)
    a = ap.parse_args()
    os.makedirs(a.out, exist_ok=True)
    latest = json.load(open(os.path.join(a.src, 'latest.json')))
    sec = latest['sections']
    with open(os.path.join(a.src, 'daily.csv'), newline='') as f, open(os.path.join(a.out, 'daily.csv'), 'w', newline='') as g:
        w = csv.writer(g)
        w.writerow(['day', 'visits'])
        for r in csv.DictReader(f):
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
    pages = []
    for h in sec['pages'].get('hits') or []:
        if h.get('event'):
            kind, _, key = h['path'].partition('/')
            if kind in ('building', 'book'):
                add('Opened', ('Book: ' if kind == 'book' else '') + (h.get('title') or key), h['count'])
        else:
            pages.append({'path': h['path'], 'title': h.get('title') or '', 'visits': int(h['count'])})
    pages.sort(key=lambda r: -r['visits'])
    json.dump(rows, open(os.path.join(a.out, 'breakdowns.json'), 'w'), indent=1)
    json.dump(pages, open(os.path.join(a.out, 'pages.json'), 'w'), indent=1)
    now = dt.datetime.now(dt.timezone.utc)
    json.dump([{'fetched_at': latest['fetched_at'], 'visits_30d': latest.get('visits_30d'),
                'refreshed_at': now.isoformat(timespec='seconds'), 'next_refresh': next_refresh(now).isoformat(timespec='seconds')}],
              open(os.path.join(a.out, 'status.json'), 'w'), indent=1)
    print(f'{len(rows)} breakdown rows ({sum(1 for r in rows if r["group"] == "Opened")} opened buildings/books), {len(pages)} pages')


if __name__ == '__main__':
    main()
