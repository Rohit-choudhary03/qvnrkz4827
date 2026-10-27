# Demo outline — target 9 minutes

Use this as a speaking outline. Review the code and explain it in your own words. Do not claim the app purchases energy or that you independently authored all its code. The README accurately discloses AI assistance.

## Part 1 — customer presentation, 0:00–4:25

**0:00–0:40 — Problem.** Explain that buyers need wind forecasts available before a day-ahead purchasing decision, and need to understand historical forecast error. Introduce Windscope as a historical pilot using only Elexon national wind data.

**0:40–1:30 — Decision controls.** Show January 15 and the configurable 10:00 UK cutoff. Point out that delivery is January 16. Explain that 10:00 is a documented assumption, not a claimed auction deadline.

**1:30–2:30 — Forecast versus actual.** Point to the forecast markers and actual line. Explain that forecast data in this snapshot is hourly and actuals are half-hourly, so exact-match coverage is 50%. Show a table row and its publication timestamp. Acknowledge that actuals are retrospective.

**2:30–3:20 — Error meaning.** Explain MAE as the average size of a miss and bias as its direction. Positive forecast-minus-actual error means wind was overestimated. Use the numbers currently visible on screen rather than memorizing numbers for another date.

**3:20–4:00 — Monthly review.** Open Monthly accuracy. At 10:00, the included snapshot gives MAE about 1,996 MW and bias about +1,728 MW across 744 matches. Click January 27 to inspect the higher-error delivery day. Do not convert these national values directly to a utility purchase order.

**4:00–4:25 — Auditability.** Export the CSV. Summarize the benefit: a transparent historical decision view, traceable forecast versions, and quantified error with coverage disclosed.

## Part 2 — technical walkthrough, 4:25–9:00

**4:25–5:10 — Architecture.** Show the folder tree. React presents the dashboard; FastAPI serves data and the production frontend. A separate Python downloader creates a versioned, checksum-backed historical snapshot. There is no database because this small fixed dataset fits in memory.

**5:10–6:10 — Ingestion.** Open `scripts/fetch_data.py`. Explain official endpoints, publication-time filters for WINDFOR, settlement-date filters for FUELHH, one-day chunks, retry limits, four workers, cached source responses, and atomic final writes.

**6:10–7:15 — Correctness.** Open `backend/app/analysis.py`. Explain timezone-aware timestamps, greatest publication time at or before cutoff, following-day selection, exact timestamp joins, null handling, latest available actuals, and pooled metric denominators. Show January 31 → February 1.

**7:15–8:00 — Tests.** Run `python -m pytest -q`. Highlight the no-look-ahead, zero-versus-missing, cutoff-boundary, duplicate-conflict, sparse-resolution, and API export checks. Mention the difference between automated checks and deployment verification.

**8:00–8:40 — Packaging.** Show the multi-stage Dockerfile and `heroku.yml`. Explain that the app uses relative API URLs and a single Python process, with `$PORT` provided by Heroku. Show your actual deployed app only once you have verified it.

**8:40–9:00 — Limits.** Acknowledge the hourly/half-hourly comparison, national coverage, missing demand/prices, fixed historical month, and absence of calibrated prediction intervals. Mention the AI disclosure and your own review/adaptations accurately.

## Before recording

- Use a readable browser zoom and close unrelated tabs.
- Start at January 15 and cutoff 10:00.
- Verify data loads and CSV export works.
- Rehearse once; keep each part under five minutes and the total under ten.
- Verify the unlisted video, public repository, and deployed app in incognito mode.
