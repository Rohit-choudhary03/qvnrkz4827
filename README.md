# Windscope

A React + Python dashboard for reviewing Elexon national wind forecasts available at a historical day-ahead decision cutoff, and measuring their accuracy against actual generation.

**Included:** full source, real Elexon January 2026 snapshot, prebuilt frontend in the download ZIP, Python API, automated tests, Docker configuration, Heroku deployment configuration, and demo guidance. No API key is needed to run the included snapshot.

**Submission status:** the [public repository](https://github.com/Rohit-choudhary03/qvnrkz4827) and [live Vercel app](https://windscope-alpha.vercel.app) are available. The unlisted YouTube demo still needs to be recorded and linked. Verify all submission links in incognito mode before submitting.

## Start on Windows 11

1. Install Python 3.12 or later (tested with 3.12) with the Python launcher enabled.
2. Extract the ZIP. Open the `windscope` folder.
3. Double-click `start-windows.cmd`. First startup downloads Python packages and requires internet.
4. Open **http://localhost:8000**. Keep the terminal open. Press Ctrl+C to stop.

The ZIP includes `frontend/dist`, so Node.js is not required for this quick start. For a Git clone, or to rebuild the frontend, install Node.js 22 first. If the launcher fails, use the manual commands below; the script does not change your PowerShell execution policy.

### Manual Windows startup

Run in PowerShell from the project root:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
# For a Git clone or frontend changes (Node.js 22 required):
cd frontend
npm ci
npm run build
cd ..
.\.venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

### macOS / Linux

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cd frontend
npm ci
npm run build
cd ..
.venv/bin/python -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000
```

## Docker

Install Docker Desktop and start its engine. From the project root:

```bash
docker compose up --build
```

Open http://localhost:8000. Stop with `docker compose down` in another terminal. The multi-stage image builds React, copies the historical data, and serves both the API and static frontend from a non-root Python process. No separate database or API host is required. A local Docker Desktop build and run on Windows succeeded, and the dashboard loaded with daily and monthly metrics. GitHub Actions also includes a Docker image build.

## Local development

Install the backend dependencies as above. Run the backend on port 8000. In a second terminal:

```bash
cd frontend
npm ci
npm run dev
```

Vite serves the frontend at http://localhost:5173 and proxies `/api` to Python. The production frontend uses relative `/api` URLs, avoiding separate-host CORS configuration. Rebuild the frontend and restart Python after changes to the production bundle.

## Features

- Select any January 2026 decision date and a UK-local decision cutoff.
- Inspect the following delivery day's forecasts, actuals, signed errors, forecast ages, and publication timestamps.
- View MAE, RMSE, bias, coverage, and monthly performance; select a monthly row to inspect that day.
- Export a 48-row CSV that retains missing values and publication provenance.
- Inspect methodology, data source, and snapshot information within the app.
- Responsive layout, loading/error states, retry action, accessible labels, and exact-value data tables alongside charts.

## Data and analysis assumptions

1. **Scope:** January 1–31, 2026 are *decision dates*. Their delivery days are January 2–February 1. Including February 1 is intentional.
2. **Cutoff:** default 10:00 Europe/London, configurable. The assignment does not prescribe a market gate closure. This is an analysis assumption, not a claim about a particular auction deadline. January is GMT.
3. **Forecast selection:** for each target interval, choose the greatest `publishTime` satisfying `publishTime <= decisionTime`. Forecasts published later are never used, including in monthly metrics.
4. **Resolution:** the downloaded WINDFOR snapshot has hourly target timestamps, while FUELHH has half-hourly actuals. We compare exact timestamps only. At 10:00 this yields 24 matches per day, 744 total, or 50% of the 1,488 half-hourly intervals. Hourly forecast markers are displayed without manufacturing intermediate values. Other cutoffs can have additional unavailable forecast targets; for example, the 00:00 cutoff has 682 exact matches. At 10:00, this coverage reflects the source-resolution mismatch. It does not imply half the upstream requests failed.
5. **Measurement limitation:** comparing WINDFOR target values to FUELHH half-hourly average MW is the challenge's requested comparison, but does not establish identical underlying measurement definitions or portfolio coverage. Results are descriptive, not a calibrated operational risk model. See the Elexon source documentation below.
6. **Actuals:** latest publication per target in the downloaded snapshot. These are retrospective observations, not information available at the decision cutoff.
7. **Forecast history:** publication windows December 29–January 31 inclusive are downloaded. Forecasts older than this window are not searched; unavailable targets remain missing. No missing values are forward-filled or interpolated; zero is valid.
8. **Quality:** exact duplicates are removed; conflicting values for the same target/publication fail validation; invalid values fail snapshot ingestion. Source data is preserved in the final snapshot and can be re-downloaded using recorded request URLs.
9. **Units:** all values and errors are MW. The application does not treat summed power values as MWh, and does not estimate utility purchase quantities, costs, or savings.

### Error formulas

For matched intervals only, `e = forecast - actual`:

- `MAE = sum(abs(e)) / n`
- `RMSE = sqrt(sum(e²) / n)`
- `Bias = sum(e) / n`; positive means overforecasting.
- `Coverage = 100 × matched / expected half-hourly intervals`.

Monthly metrics pool all matched intervals. They are not unweighted averages of daily scores. When there are no matches, error metrics are null, not zero. Historical monthly results are retrospective evaluation, not evidence available before every January decision.

## Refresh data

The included `data/elexon.json` contains **real Elexon data**, not synthetic fixtures. `data/SHA256SUMS` records its checksum. The snapshot contains 19,856 forecast records and 1,488 actual records.

```bash
python scripts/fetch_data.py
# Force fresh upstream responses instead of reusing the request cache:
python scripts/fetch_data.py --refresh
```

The downloader uses standard-library HTTP requests, four concurrent workers, finite retries/timeouts, one-day windows, and resumable raw-response caching. It writes the final snapshot atomically only after all requests and validation succeed. Restart the backend after refresh because it caches parsed records. Rebuild/redeploy the Docker image to update hosted data. A Heroku dyno's ephemeral filesystem is not a durable store for refreshed snapshots.

Source endpoints and contract:

- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/FUELHH/stream
- https://bmrs.elexon.co.uk/api-documentation/endpoint/datasets/WINDFOR/stream
- https://data.elexon.co.uk/swagger/v1/swagger.json
- https://developer.data.elexon.co.uk/

`FUELHH` requests use `settlementDateFrom`, `settlementDateTo`, and `fuelType=WIND`. `WINDFOR` requests use `publishDateTimeFrom` and `publishDateTimeTo`; those filter publication times, not delivery times. Endpoint parameters were checked against Elexon's OpenAPI contract. National coverage is Great Britain as described by Elexon, not a utility's own portfolio or all UK electricity.

## Architecture and file guide

```text
windscope/
  api/index.py              Vercel ASGI entry point for the FastAPI application
  vercel.json               Vercel build, API routing, and function configuration
  backend/app/analysis.py    Pure normalization, cutoff selection, metrics
  backend/app/main.py        FastAPI routes, CSV export, static frontend hosting
  backend/tests/            Unit and API integration tests
  frontend/src/main.jsx     React dashboard and charts
  frontend/src/style.css    Responsive visual design
  frontend/package-lock.json Locked frontend dependency tree
  frontend/dist/            Prebuilt UI in ZIP; regenerated for Docker/Git
  scripts/fetch_data.py      Reproducible Elexon snapshot ingestion
  data/elexon.json           Real source records and request provenance
  data/SHA256SUMS            Snapshot checksum
  docs/ANALYSIS.md           Findings from the included snapshot
  docs/DEMO_GUIDE.md         Customer and technical demo outline
  docs/DEPLOYMENT.md         Vercel deployment and Heroku alternative
  docs/VALIDATION.md         Checks run and verification limits
  .github/workflows/ci.yml   Tests, frontend build, Docker build
  Dockerfile                Multi-stage production image
  compose.yaml              One-command local container startup
  heroku.yml                Heroku container build declaration
  requirements*.txt         Runtime and test dependencies
  start-windows.cmd         Windows quick start
```

Data flow: Elexon streams → validated file snapshot → pure Python selection/metrics → FastAPI JSON → React. Downloads are separate from page requests, making the historical demo reproducible and independent of upstream latency. This small fixed dataset fits in memory; a database and background queue would add unnecessary complexity for the challenge.

### API

| Route | Purpose |
| --- | --- |
| `GET /api/health` | Dataset readiness and source metadata |
| `GET /api/day?decision_date=2026-01-15&cutoff=10:00` | Selected next-day series and scores |
| `GET /api/month?cutoff=10:00` | All January decision-day scores |
| `GET /api/export?decision_date=2026-01-15&cutoff=10:00` | CSV with cutoff and publication provenance |
| `GET /docs` | Interactive FastAPI API documentation |

Validation errors return 422; absent/invalid data returns 503 with remediation. There are no public write endpoints or user accounts. The API serves only the included historical public dataset.

## Tests

```bash
python -m pip install -r requirements-dev.txt
python -m pytest -q
cd frontend
npm ci
npm run build
```

Tests cover cutoff inclusivity, prevention of look-ahead, zero versus missing data, duplicate handling, invalid records, timezone offsets, January boundaries, sparse forecasts, formulas, input validation, CSV contents, real snapshot loading, and pooled monthly scores. The 18 tests passed during generation. A dependency deprecation warning from Starlette/httpx is documented and does not affect results.

## Deployment and submission links

The app is deployed on [Vercel](https://windscope-alpha.vercel.app), serving React and the Python API under one domain. See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) for Vercel configuration and the Heroku alternative. Docker is available for local execution and CI builds.

- Public anonymous-name GitHub repo: https://github.com/Rohit-choudhary03/qvnrkz4827
- Live Vercel app: https://windscope-alpha.vercel.app
- Unlisted YouTube demo: **NOT RECORDED — add your URL**

The brief requires the demo and starts evaluation with it. Use [docs/DEMO_GUIDE.md](docs/DEMO_GUIDE.md), keep the total under 10 minutes, and verify all URLs in incognito mode before submitting the supplied form. Understand the code and assumptions before presenting it.

## AI assistance disclosure

This project was substantially generated with OpenAI ChatGPT/Codex assistance, including architecture, Python and React implementation, data-ingestion code, tests, styling, and documentation. Automated checks were run during generation. The candidate should review, understand, validate, and adapt the work before submission; this README does not claim independent authorship by the candidate.

## Limitations and next steps

This is a focused historical pilot, not production trading software. It does not include demand, prices, other generation, a forecast model, prediction intervals, live ingestion, or procurement recommendations. The hardcoded decision month is intentional. Future work could validate measurement alignment, add calibrated uncertainty using prior-only history, support broader dates and DST, store versioned snapshots, and introduce monitoring. Local Docker execution on Windows has been verified; the Windows batch launcher and optional Heroku deployment remain unverified.
