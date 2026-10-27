import math
import pytest
from backend.app.analysis import analyze, metrics, normalize


def record(value=100, published='2026-01-15T09:30:00Z', target='2026-01-16T00:00:00Z'):
    return {'generation': value, 'publishTime': published, 'startTime': target, 'fuelType': 'WIND'}


def test_no_lookahead_and_inclusive_cutoff():
    f, _ = normalize([record(100), record(200, '2026-01-15T10:00:00Z'), record(999, '2026-01-15T10:01:00Z')], True)
    a, _ = normalize([record(150, '2026-01-16T01:00:00Z')])
    r = analyze(f, a, '2026-01-15')['rows'][0]
    assert r['forecast'] == 200
    assert r['actual'] == 150
    assert r['error'] == 50


def test_zero_is_valid_and_missing_not_zero():
    f, _ = normalize([record(0)], True)
    a, _ = normalize([record(0)])
    report = analyze(f, a, '2026-01-15')
    assert report['metrics']['matched'] == 1
    assert report['metrics']['mae'] == 0
    assert report['rows'][1]['error'] is None
    assert report['rows'][1]['forecast'] is None


def test_january_boundary():
    report = analyze([], [], '2026-01-31')
    assert report['deliveryDate'] == '2026-02-01'
    assert len(report['rows']) == 48
    assert report['rows'][-1]['startTime'] == '2026-02-01T23:30:00+00:00'
    with pytest.raises(ValueError):
        analyze([], [], '2026-02-01')


def test_metrics_sign_and_denominator():
    rows = [{'error': x, 'forecast': 1, 'actual': 1 if x is not None else None} for x in [-3, 4, None]]
    m = metrics(rows)
    assert m['mae'] == 3.5
    assert m['bias'] == .5
    assert m['rmse'] == math.sqrt(12.5)
    assert m['coverage'] == 66.67


def test_all_missing():
    r = analyze([], [], '2026-01-01')
    assert r['metrics']['mae'] is None
    assert r['metrics']['matched'] == 0


def test_latest_actual_and_duplicate_handling():
    a, rejected = normalize([record(100), record(100), record(120, '2026-01-16T02:00:00Z')])
    assert len(a) == 2 and rejected == 0
    assert analyze([], a, '2026-01-15')['rows'][0]['actual'] == 120
    with pytest.raises(ValueError, match='Conflicting'):
        normalize([record(100), record(200)], True)


@pytest.mark.parametrize('value', [None, float('nan'), float('inf'), -1, True, 'bad'])
def test_invalid_values_rejected(value):
    rows, rejected = normalize([record(value)], True)
    assert rows == [] and rejected == 1


def test_timezone_normalization_and_fuel_filter():
    f, _ = normalize([record(25, '2026-01-15T11:00:00+01:00')], True)
    assert analyze(f, [], '2026-01-15')['rows'][0]['forecast'] == 25
    a, _ = normalize([{**record(), 'fuelType': 'GAS'}])
    assert not a


def test_sparse_hourly_forecast_is_not_filled():
    f, _ = normalize([record(), record(target='2026-01-16T01:00:00Z')], True)
    rows = analyze(f, [], '2026-01-15')['rows']
    assert rows[0]['forecast'] == rows[2]['forecast'] == 100
    assert rows[1]['forecast'] is None
