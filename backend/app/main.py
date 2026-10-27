"""Read-only API and production React hosting. No upstream calls on page requests."""
import csv
import io
import json
import os
from functools import lru_cache
from pathlib import Path
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from .analysis import analyze, metrics, normalize

ROOT = Path(__file__).resolve().parents[2]
DATA = Path(os.getenv('DATA_DIR', str(ROOT / 'data')))
app = FastAPI(title='Windscope API', version='1.0.0')


@lru_cache(maxsize=1)
def dataset():
    try:
        payload = json.loads((DATA / 'elexon.json').read_text())
        forecasts, bad_f = normalize(payload['forecasts'], forecast=True)
        actuals, bad_a = normalize(payload['actuals'])
        return forecasts, actuals, {**payload['metadata'], 'rejectedForecasts': bad_f, 'rejectedActuals': bad_a,
                                    'forecastRecords': len(forecasts), 'actualRecords': len(actuals)}
    except (OSError, ValueError, KeyError) as exc:
        raise HTTPException(503, 'Dataset unavailable or invalid. Run python scripts/fetch_data.py, then restart the backend.') from exc


def report(day, cutoff):
    forecasts, actuals, metadata = dataset()
    try:
        return {**analyze(forecasts, actuals, day, cutoff), 'source': metadata}
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc


@app.get('/api/health')
def health():
    _, _, source = dataset()
    return {'status': 'ok', 'source': source}


@app.get('/api/day')
def day(decision_date: str = '2026-01-15', cutoff: str = Query('10:00', pattern=r'^([01]\d|2[0-3]):[0-5]\d$')):
    return report(decision_date, cutoff)


@app.get('/api/month')
def month(cutoff: str = Query('10:00', pattern=r'^([01]\d|2[0-3]):[0-5]\d$')):
    reports = [report(f'2026-01-{d:02d}', cutoff) for d in range(1, 32)]
    rows = [r for day in reports for r in day['rows']]
    return {'metrics': metrics(rows), 'days': [
        {'decisionDate': d['decisionDate'], 'deliveryDate': d['deliveryDate'], **d['metrics']}
        for d in reports], 'source': reports[0]['source']}


@app.get('/api/export')
def export(decision_date: str = '2026-01-15', cutoff: str = Query('10:00', pattern=r'^([01]\d|2[0-3]):[0-5]\d$')):
    result = report(decision_date, cutoff)
    output = io.StringIO(newline='')
    fields = ['decisionDate', 'decisionTime', 'deliveryDate', 'startTime', 'forecast', 'actual', 'error',
              'publishTime', 'actualPublishTime', 'forecastAgeHours', 'leadHours']
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in result['rows']:
        writer.writerow({**{k: result[k] for k in fields[:3]}, **row})
    return Response(output.getvalue(), media_type='text/csv', headers={
        'Content-Disposition': f'attachment; filename="windscope-{result["decisionDate"]}-{cutoff.replace(":", "")}.csv"'})


dist = ROOT / 'frontend' / 'dist'
if dist.is_dir():
    app.mount('/', StaticFiles(directory=dist, html=True), name='frontend')
