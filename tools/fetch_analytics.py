#!/usr/bin/env python3
"""Pulls the site's visitor numbers from GoatCounter and saves them into a folder.

Run daily by .github/workflows/analytics.yml (needs the GOATCOUNTER_TOKEN secret).
Writes, into --out:
  daily.csv    day,visits  one row per day, grows over time (old days are kept, recent days refreshed)
  latest.json  the last 30 days: pages, referrers, browsers, systems, locations, screen sizes, languages
Fails loudly (non-zero exit) on any problem, so a broken job is never mistaken for "no visitors".

    GOATCOUNTER_TOKEN=... python3 tools/fetch_analytics.py --out /tmp/analytics
"""
import argparse, csv, datetime as dt, json, os, re, sys, time, urllib.error, urllib.parse, urllib.request

CODE = os.environ.get('GOATCOUNTER_CODE', 'akshatpagaria')
API = os.environ.get('GOATCOUNTER_API') or f'https://{CODE}.goatcounter.com/api/v0'  # the override is for tests
SECTIONS = {  # name in latest.json -> endpoint
    'pages': 'stats/hits', 'referrers': 'stats/toprefs', 'browsers': 'stats/browsers', 'systems': 'stats/systems',
    'locations': 'stats/locations', 'sizes': 'stats/sizes', 'languages': 'stats/languages',
}


def get(path, attempts=5, timeout=40, **params):
    url = f'{API}/{path}?' + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={'Authorization': 'Bearer ' + os.environ['GOATCOUNTER_TOKEN'],
                                               'Accept': 'application/json', 'Content-Type': 'application/json', 'User-Agent': 'discoverarchitecture-analytics'})
    for attempt in range(attempts):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.load(r)
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < attempts - 1:
                time.sleep(min(int(e.headers.get('Retry-After') or 5 * (attempt + 1)), 60))
                continue
            raise SystemExit(f'GoatCounter said {e.code} for {path}: {short(e.read())}')
        except urllib.error.URLError as e:
            if attempt < attempts - 1:
                time.sleep(5 * (attempt + 1))
                continue
            raise SystemExit(f'Could not reach GoatCounter for {path}: {e}')


def short(body):
    """An error body as one short plain line (GoatCounter answers some errors with a whole HTML page)."""
    text = body[:4000].decode('utf8', 'replace')
    title = re.search(r'<title>(.*?)</title>', text, re.S)
    text = re.sub(r'<style.*?</style>|<[^>]+>', ' ', text, flags=re.S)
    return ((title.group(1) + ' | ') if title else '') + ' '.join(text.split())[:200]


def day_visits(entry):
    """One day's visits from a /stats/total entry: its daily figure, or the sum of its hours."""
    if entry.get('daily') is not None:
        return int(entry['daily'])
    return sum(int(h or 0) for h in entry.get('hourly') or [])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    if not os.environ.get('GOATCOUNTER_TOKEN'):
        raise SystemExit('GOATCOUNTER_TOKEN is not set. Create a read-only key in GoatCounter (Settings, API) and add it as a repository secret.')
    os.makedirs(args.out, exist_ok=True)
    now = dt.datetime.now(dt.timezone.utc)
    today = now.date()
    stamp = lambda d: d.strftime('%Y-%m-%dT00:00:00Z')
    until = now.strftime('%Y-%m-%dT%H:%M:%SZ')  # up to this moment: GoatCounter's days follow your own time zone, which can be a day ahead of UTC

    # Daily visits for the last 90 days.
    total = get('stats/total', start=stamp(today - dt.timedelta(days=89)), end=until)
    rows = {e['day'][:10]: day_visits(e) for e in total.get('stats') or [] if e.get('day')}
    if not rows:
        raise SystemExit('GoatCounter returned no days at all; refusing to save an empty result. Raw answer: ' + json.dumps(total)[:300])

    path = os.path.join(args.out, 'daily.csv')
    old = {}
    if os.path.exists(path):
        with open(path, newline='') as f:
            old = {r['day']: int(r['visits']) for r in csv.DictReader(f)}
    old = {d: v for d, v in old.items() if d <= max(rows)}  # drops any day saved ahead of time
    old.update(rows)  # the fetched days win; earlier days stay
    with open(path, 'w', newline='') as f:
        w = csv.writer(f)
        w.writerow(['day', 'visits'])
        for d in sorted(old):
            w.writerow([d, old[d]])

    # The last 30 days, broken down.
    window = {'start': stamp(today - dt.timedelta(days=29)), 'end': until}
    latest = {'fetched_at': dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds'), 'site': f'{CODE}.goatcounter.com',
              'window_days': 30, 'visits_30d': total.get('total'), 'sections': {}}
    prev = {}  # the breakdowns saved last time, kept for any request that fails now
    try:
        with open(os.path.join(args.out, 'latest.json')) as f:
            prev = json.load(f).get('sections', {})
    except (OSError, ValueError):
        pass
    kept = []
    started = time.time()
    for name, endpoint in SECTIONS.items():
        time.sleep(1)  # stay well inside GoatCounter's rate limit
        try:
            if time.time() - started > 300:  # GoatCounter is very slow: stop trying, the daily visits are already saved
                raise SystemExit('out of time')
            data = get(endpoint, attempts=2, timeout=25, limit=100, **window)
        except SystemExit as e:  # the daily visits are saved above, so a failing breakdown must not lose them
            print(f'::warning::{name} could not be fetched ({e}); keeping the numbers saved earlier')
            latest['sections'][name] = prev.get(name) or {'stats': [], 'more': False}
            kept.append(name)
            continue
        for h in data.get('hits') or []:  # the per-hour counts of every page are not needed here
            h.pop('stats', None)
        latest['sections'][name] = data
    latest['kept_from_earlier'] = kept
    with open(os.path.join(args.out, 'latest.json'), 'w') as f:
        json.dump(latest, f, indent=1)

    last = sorted(rows)[-3:]
    print('Saved', len(old), 'days to daily.csv. Latest:', ', '.join(f'{d}={rows[d]}' for d in last))


if __name__ == '__main__':
    main()
