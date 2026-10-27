"""Pure, time-aware forecast selection. All power values are MW."""
from datetime import date, datetime, time, timedelta, timezone
from math import isfinite, sqrt
from zoneinfo import ZoneInfo

UK = ZoneInfo('Europe/London')


def timestamp(value):
    parsed = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if parsed.tzinfo is None:
        raise ValueError('Timezone required')
    return parsed.astimezone(timezone.utc)


def normalize(records, forecast=False):
    """Reject invalid records, deduplicate, fail on conflicting same-version data."""
    result, rejected = {}, 0
    for row in records:
        if not forecast and row.get('fuelType') != 'WIND':
            continue
        try:
            start = timestamp(row['startTime'])
            published = timestamp(row['publishTime'])
            raw = row['generation']
            if raw is None or isinstance(raw, bool):
                raise ValueError('Missing generation')
            value = float(raw)
            if not isfinite(value) or value < 0 or start.second or start.microsecond or start.minute not in (0, 30):
                raise ValueError('Invalid interval or generation')
        except (KeyError, TypeError, ValueError, AttributeError):
            rejected += 1
            continue
        key = (start, published)
        if key in result and result[key]['generation'] != value:
            raise ValueError(f'Conflicting records for {start} at {published}')
        result[key] = {'start': start, 'published': published, 'generation': value}
    return list(result.values()), rejected


def metrics(rows):
    errors = [r['error'] for r in rows if r['error'] is not None]
    n = len(errors)
    return {
        'matched': n, 'expected': len(rows),
        'coverage': round(100 * n / len(rows), 2) if rows else 0,
        'mae': sum(abs(e) for e in errors) / n if n else None,
        'rmse': sqrt(sum(e * e for e in errors) / n) if n else None,
        'bias': sum(errors) / n if n else None,
        'maxAbsoluteError': max(map(abs, errors)) if n else None,
        'forecastIntervals': sum(r['forecast'] is not None for r in rows),
        'actualIntervals': sum(r['actual'] is not None for r in rows),
    }


def analyze(forecasts, actuals, decision_date, cutoff='10:00'):
    day = date.fromisoformat(decision_date)
    if day.year != 2026 or day.month != 1:
        raise ValueError('Decision dates must be in January 2026')
    clock = time.fromisoformat(cutoff)
    if clock.tzinfo is not None or clock.second or clock.microsecond:
        raise ValueError('Cutoff must be HH:MM')
    decision = datetime.combine(day, clock, UK).astimezone(timezone.utc)
    delivery = day + timedelta(days=1)
    start = datetime.combine(delivery, time(), UK).astimezone(timezone.utc)
    end = datetime.combine(delivery + timedelta(days=1), time(), UK).astimezone(timezone.utc)
    selected, observed = {}, {}
    for record in forecasts:
        target = record['start']
        if start <= target < end and record['published'] <= decision:
            if target not in selected or record['published'] > selected[target]['published']:
                selected[target] = record
    for record in actuals:
        target = record['start']
        if start <= target < end:
            if target not in observed or record['published'] > observed[target]['published']:
                observed[target] = record
    rows = []
    target = start
    while target < end:
        f, a = selected.get(target), observed.get(target)
        fv, av = f['generation'] if f else None, a['generation'] if a else None
        rows.append({
            'startTime': target.isoformat(), 'forecast': fv, 'actual': av,
            'error': fv - av if fv is not None and av is not None else None,
            'publishTime': f['published'].isoformat() if f else None,
            'actualPublishTime': a['published'].isoformat() if a else None,
            'forecastAgeHours': (decision - f['published']).total_seconds() / 3600 if f else None,
            'leadHours': (target - f['published']).total_seconds() / 3600 if f else None,
        })
        target += timedelta(minutes=30)
    return {'decisionDate': decision_date, 'decisionTime': decision.isoformat(),
            'deliveryDate': delivery.isoformat(), 'cutoff': cutoff,
            'rows': rows, 'metrics': metrics(rows)}
