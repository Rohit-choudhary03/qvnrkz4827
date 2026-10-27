# Validation record

Validated in a Linux workspace on October 27, 2026, with Python 3.12 and Node.js.

## Passed

- Downloaded official Elexon data successfully using 65 daily requests.
- Validated 19,856 forecast records and 1,488 actual records; no invalid records rejected.
- Ran 18 Python unit/API integration tests successfully.
- Built the React production bundle successfully with the checked-in npm lockfile.
- Confirmed full-month analysis uses 744 exact matches over 1,488 expected half-hourly intervals.
- Confirmed January 31 decisions select February 1 delivery.
- Confirmed cutoff selection excludes later forecast publications.
- Checked API CSV contents and input-validation responses.
- Served production HTML and both compiled CSS/JavaScript assets through FastAPI successfully.
- Smoke-tested monthly analysis at 00:00, 10:00, and 23:59 cutoffs.
- npm audit of production dependencies reported zero known vulnerabilities at check time.

## Warnings and limits

- Starlette emitted a deprecation warning for its httpx-based test client; tests still passed.
- Vite emitted an advisory about the main JavaScript chunk exceeding 500 kB uncompressed. This is a performance optimization opportunity, not a failed build.
- The managed browser preview could not start because its isolated runtime could not access the project's Python environment. Browser interaction, screenshots, visual layout, and mobile rendering are therefore **not verified** here.
- Docker is not installed in this workspace. Dockerfile/Compose configuration is supplied, and CI includes a Docker build, but no container build/run was performed here.
- Windows batch startup was not executed on Windows; the underlying Python application was tested on Linux.
- No public GitHub repository, Heroku deployment, YouTube upload, or submission form was created/completed. These require the user's accounts and the steps in `DEPLOYMENT.md`.

Run the local application, Docker build, and incognito checks before submitting. Do not present this record as proof of checks that are listed as unverified.
