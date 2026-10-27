# Findings from the included Elexon snapshot

At the default 10:00 UK decision cutoff, for decision dates January 1–31, 2026:

| Measure | Result |
| --- | ---: |
| Matched timestamps | 744 |
| Half-hourly delivery intervals | 1,488 |
| Exact-match coverage | 50.0% |
| MAE | 1,995.57 MW |
| RMSE | 2,498.82 MW |
| Bias, forecast minus actual | +1,727.98 MW |
| Largest absolute interval error | 6,857 MW |

These values are calculated from the bundled source data, not example numbers. The dataset contains hourly forecast targets and half-hourly actuals; only coincident timestamps contribute to error scores. No interpolation is used. Consequently, the metrics describe the matched subset and should not be presented as validated half-hourly error estimates across every interval.

The positive bias means forecasts exceeded reported actuals on average in this exact-match sample. It does not establish a causal explanation, a reliable future bias correction, or a purchase requirement. Forecast and actual measurement definitions and national coverage also need consideration before operational use.

The lowest daily MAE is the January 18 decision for January 19 delivery: 750.04 MW. The highest is the January 27 decision for January 28 delivery: 5,328.96 MW. Each uses 24 matched intervals. All 31 daily results can be inspected in the Monthly accuracy view.

## Reproduce

From the project root, in the installed Python environment:

```python
from backend.app.main import month
print(month('10:00')['metrics'])
```

Change the cutoff in the UI to investigate how forecast availability changes. Changing the time does not guarantee lower errors; later information is not necessarily more accurate. Month-wide metrics are retrospective, so using them to claim a prior operational trading strategy would require a separate out-of-sample evaluation.

The provenance, actual API request URLs, and assembly timestamp are embedded in `data/elexon.json`. The checksum is in `data/SHA256SUMS`.
