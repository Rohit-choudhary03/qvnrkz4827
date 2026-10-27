"""Download official Elexon streams, retaining all forecast vintages.
Run from the project root. Atomic final write; an interrupted refresh preserves
the previous snapshot. Per-request cache supports resuming a failed download.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from backend.app.analysis import normalize

BASE = 'https://data.elexon.co.uk/bmrs/api/v1/datasets/'


def fetch(kind, day, refresh=False):
    if kind == 'WINDFOR':
        params = {'publishDateTimeFrom': day.isoformat() + 'T00:00:00Z',
                  'publishDateTimeTo': (day + timedelta(days=1)).isoformat() + 'T00:00:00Z'}
    else:
        params = {'settlementDateFrom': day.isoformat(), 'settlementDateTo': day.isoformat(), 'fuelType': 'WIND'}
    url = BASE + kind + '/stream?' + urllib.parse.urlencode(params)
    cache = ROOT / 'data' / 'raw' / f'{kind}-{day}.json'
    if cache.exists() and not refresh:
        return kind, json.loads(cache.read_text()), url
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'Accept': 'application/json', 'User-Agent': 'Windscope/1.0'})
            with urllib.request.urlopen(req, timeout=90) as response:
                payload = json.load(response)
            if isinstance(payload, dict):
                payload = payload.get('data')
            if not isinstance(payload, list):
                raise ValueError('Elexon returned an unexpected payload')
            cache.parent.mkdir(parents=True, exist_ok=True)
            temp = cache.with_suffix('.tmp')
            temp.write_text(json.dumps(payload))
            temp.replace(cache)
            return kind, payload, url
        except (urllib.error.URLError, TimeoutError, ValueError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--refresh', action='store_true', help='Replace cached upstream responses')
    args = parser.parse_args()
    jobs = [('WINDFOR', date(2025, 12, 29) + timedelta(days=n)) for n in range(34)]
    jobs += [('FUELHH', date(2026, 1, 2) + timedelta(days=n)) for n in range(31)]
    records = {'WINDFOR': [], 'FUELHH': []}
    urls = []
    with ThreadPoolExecutor(max_workers=4) as pool:
        futures = [pool.submit(fetch, kind, day, args.refresh) for kind, day in jobs]
        for i, future in enumerate(as_completed(futures), 1):
            kind, rows, url = future.result()
            records[kind].extend(rows)
            urls.append(url)
            print(f'{i}/{len(jobs)} {kind}: {len(rows)} records', flush=True)
    # Keep source records intact except exact duplicates and non-wind actuals.
    forecasts = list({json.dumps(r, sort_keys=True): r for r in records['WINDFOR']}.values())
    actuals = list({json.dumps(r, sort_keys=True): r for r in records['FUELHH'] if r.get('fuelType') == 'WIND'}.values())
    nf, rejected_f = normalize(forecasts, True)
    na, rejected_a = normalize(actuals)
    if not nf or not na or rejected_f or rejected_a:
        raise ValueError(f'Invalid snapshot: forecasts={len(nf)}, actuals={len(na)}, rejected={rejected_f + rejected_a}')
    payload = {'metadata': {
        'provider': 'Elexon Insights', 'synthetic': False,
        'retrievedAt': datetime.now(timezone.utc).isoformat(),
        'decisionRange': ['2026-01-01', '2026-01-31'],
        'deliveryRange': ['2026-01-02', '2026-02-01'],
        'forecastPublicationRange': ['2025-12-29', '2026-02-01'],
        'note': 'Historical snapshot; cached raw responses may originate from earlier retrievals. Actuals are latest available in this snapshot.',
        'requests': sorted(urls),
    }, 'forecasts': forecasts, 'actuals': actuals}
    target = ROOT / 'data' / 'elexon.json'
    temp = target.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, separators=(',', ':')))
    temp.replace(target)
    digest = hashlib.sha256(target.read_bytes()).hexdigest()
    (ROOT / 'data' / 'SHA256SUMS').write_text(f'{digest}  elexon.json\n')
    print(f'Saved {len(forecasts)} forecasts and {len(actuals)} actuals. SHA256 {digest}')


if __name__ == '__main__':
    main()
