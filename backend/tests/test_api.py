import csv
import io
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def test_snapshot_health():
    r = client.get('/api/health')
    assert r.status_code == 200
    assert r.json()['source']['synthetic'] is False


def test_day_csv_and_cutoff():
    result = client.get('/api/day?decision_date=2026-01-31&cutoff=10:00')
    assert result.status_code == 200
    data = result.json()
    assert data['deliveryDate'] == '2026-02-01'
    assert len(data['rows']) == 48
    for row in data['rows']:
        if row['publishTime']:
            assert row['publishTime'] <= data['decisionTime']
    csv_result = client.get('/api/export?decision_date=2026-01-31')
    assert csv_result.status_code == 200
    csv_rows = list(csv.DictReader(io.StringIO(csv_result.text)))
    assert len(csv_rows) == 48
    assert csv_rows[0]['decisionDate'] == '2026-01-31'


def test_validation():
    for query in ['decision_date=2026-02-01', 'decision_date=nope', 'cutoff=25:00', 'cutoff=10:99']:
        assert client.get('/api/day?' + query).status_code == 422


def test_month_pools_all_intervals():
    result = client.get('/api/month').json()
    assert len(result['days']) == 31
    assert result['metrics']['expected'] == 1488
    assert result['metrics']['matched'] == sum(d['matched'] for d in result['days'])
    weighted = sum(d['mae'] * d['matched'] for d in result['days'] if d['matched']) / result['metrics']['matched']
    assert abs(result['metrics']['mae'] - weighted) < 1e-8
