# Release Evidence

## Baseline
- Branch: final-project
- Date: 2026-08-23
- Local app run command: `uvicorn app.main:app --reload --port 8000`
- /health result: `{"status":"ok","timestamp":"2026-08-23T17:30:10.023514+00:00"}` — API responded with HTTP 200.
- Frontend check: Opened `frontend/index.html` directly in the browser with the API running on port 8000. The Kanban board (To Do / In Progress / Done), the filter bar and the create/edit task dialog are still visible and working.
- Test command: `pytest`
- Test result: `43 passed in 0.13s`


## CI evidence
- Workflow file: `.github/workflows/ci.yml`
- Latest run: https://github.com/selimellieh72/aub-task-tracker/actions/runs/32656507619 — completed successfully on the `final-project` branch (commit `f55df8e`). The log shows `Python 3.13.15, pytest-9.1.1` and `43 passed, 3 warnings in 0.28s`.
- Test command used by CI: `python -m pytest -v`
- Shortcut check: No `continue-on-error`, no `|| true`, pytest is not skipped, Python version is pinned to `3.13`, and dependencies are installed from `app/requirements.txt` before the test step. The workflow also sets `permissions: contents: read` so the job token cannot write to the repository.


## Docker evidence

- Build command: `docker build -t task-tracker:final .`
- Build result: Successful, image created as `task-tracker:final`.
- Run command: `docker run -d --name task-tracker-final -p 8001:8000 task-tracker:final` (port 8001 on the host because the local server was already using 8000)
- /health check: `curl -i http://localhost:8001/health`
- /health result: `HTTP/1.1 200 OK` with `{"status":"ok","timestamp":"2026-08-23T17:32:25.802756+00:00"}`. The container's own `HEALTHCHECK` reported `healthy` and `POST /tasks` through the container returned HTTP 201.
- Non-root check: Dockerfile creates an `appuser` user and runs the container with `USER appuser`. Confirmed at runtime with `docker exec task-tracker-final id` → `uid=1001(appuser)`.
- No-baked-secrets check: `.dockerignore` excludes `.env` and `.env.*`, and the Dockerfile copies only `app/requirements.txt` and `app/`. Listing `/srv` inside the running container showed only the `app` package — no `.env`, `venv/`, `tests/`, `docs/` or `frontend/`.
- Runtime command: `uvicorn app.main:app --host 0.0.0.0 --port 8000`


## Documentation claim-vs-reality log

| Claim checked | Evidence used | Result | Change made, if any |
|---|---|---|---|
| The API starts with `uvicorn app.main:app --reload --port 8000`. | Ran the command locally and confirmed successful startup. | Verified | None |
| The `/health` endpoint returns HTTP 200 with `status` and `timestamp`. | Ran `curl -i http://localhost:8000/health` and received `HTTP/1.1 200 OK` with both keys. | Verified | None |
| The frontend can be opened directly from disk (`file://`). | Read `app/main.py`: the CORS list includes the `"null"` origin. Opened `frontend/index.html` from disk and the board loaded tasks from the API. | Verified | None |
| The Docker image builds and runs with `/health` returning 200. | Ran `docker build`, started the container on port 8001 and received `HTTP/1.1 200 OK`. | Verified | None |
| README (ADR-001) said storage is an "in-memory dict backed by a JSON file (`app/tasks.json`)". | `app/tasks.json` does not exist; `app/storage.py` is a plain in-memory dict and its docstring says persistence was planned for a later step. | Claim was wrong | Corrected the README architecture bullet and folder tree: storage is in-memory only and data is lost on restart. |
| README setup step 3 implied the app reads `.env`. | `grep -rn 'dotenv\|environ\|getenv' app/` found no code that reads environment variables; the port is set on the command line. | Claim was misleading | Marked the step optional and stated that the app does not currently read `.env`. |
| README mid-course section said the suite has 42 tests. | Ran `pytest` and received `43 passed`. | Claim was wrong | Corrected the count to 43. |
| README scope line said "no Docker". | The final project adds a Dockerfile. | Claim was outdated | Reworded the line: Docker is used only to package and run the API. |


## Secret scan

- Searched the full git history of all branches for password, secret, token, API-key and private-key patterns. The only matches were the words "design tokens" in CSS comments and commit messages.
- `.env` has never been committed (`git log --all --diff-filter=A -- .env` returns nothing); `.env.example` contains only `PORT` and `APP_ENV` defaults.
- `.gitignore` excludes `.env`, `venv/` and `.venv/`; `.dockerignore` excludes `.env` and `.env.*`.
