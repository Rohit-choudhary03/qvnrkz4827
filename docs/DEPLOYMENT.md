# Public repository and Heroku deployment

The project is prepared for deployment but has not been published. You need your own GitHub and Heroku accounts. Heroku hosting can incur charges; choose an appropriate plan in your account. No account credentials belong in this repository.

## 1. Create the public repository

Create a new **public** GitHub repository with an anonymous name such as `q7m4x9`. Do not initialize it with a README when pushing this folder. Use your actual repository URL below:

```bash
git init
git add .
git commit -m "Build historical wind forecast dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/YOUR_RANDOM_REPO.git
git push -u origin main
```

The `.gitignore` excludes local environments, raw download cache, and generated bundles; the source snapshot and frontend lockfile are included. GitHub Actions tests the backend, builds React, and builds Docker.

## 2. Deploy the complete application to Heroku

Install the Heroku CLI and sign in. Run from this project's root:

```bash
heroku login
heroku create YOUR_UNIQUE_APP_NAME --stack container
git push heroku main
heroku ps:scale web=1
heroku open
```

`heroku.yml` instructs Heroku to build `Dockerfile`. The Docker build compiles React and installs Python. Python serves the frontend and API on Heroku's injected `$PORT`. If a plan or billing selection is requested, complete it in your account before continuing. This configuration targets Heroku's container-stack workflow; consult current Heroku documentation if your account uses a different deployment generation.

For an existing compatible Heroku app:

```bash
heroku git:remote -a YOUR_APP_NAME
heroku stack:set container -a YOUR_APP_NAME
git push heroku main
```

Only change the stack on an app intended for this project. Do not repurpose an unrelated existing deployment.

## 3. Verify the deployed result

- Open the app URL without signing in and test all three tabs.
- Open `/api/health` and confirm status `ok` and `synthetic: false`.
- Set January 31 and confirm February 1 delivery.
- Change the cutoff and export a CSV. Inspect its publication times.
- Confirm forecast points, actual lines, error bars, and the resolution warning render.
- Check a narrow mobile window.
- If needed, use `heroku logs --tail -a YOUR_APP_NAME` to diagnose startup errors.

Update the README with the **actual** deployed URL and public repository URL. Do not replace placeholders with unverified links.

## 4. Record and submit

Record your screen and narration using the outline in `DEMO_GUIDE.md`. Upload it to YouTube with **Unlisted** visibility, keeping the complete video at most 10 minutes. Add its real URL to the README.

Open the GitHub repo, application, and video in incognito mode and verify access. Then submit the required details at:

https://forms.cloud.microsoft/r/FTX6K2bbnU

## References

- https://devcenter.heroku.com/articles/build-docker-images-heroku-yml
- https://devcenter.heroku.com/articles/container-registry-and-runtime

The configuration and commands follow Heroku's container workflow. Account provisioning, paid hosting, live deployment, video recording/upload, and form submission were not performed during project generation.
