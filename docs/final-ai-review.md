# Final AI Review and Ownership Evidence

## AGENTS.md guardrails

- Repo-specific stack and commands included: yes
- Docs-first/read-first guardrail included: yes
- Unexpected app/frontend edits rule included: yes

## AI code review mini-log

Reviewed files: `.github/workflows/ci.yml` and `Dockerfile` (the diff that adds them on `final-project`).

| AI comment | Grade | Reason | Verification or decision |
|---|---|---|---|
| The README "Final Project" section references `docs/final-ai-review.md` and `docs/ai-playbook.md`, which did not exist at review time. | Useful | The section promises evidence files; pointing at missing files would fail the "documentation checked against reality" part. | Both files were written before the docs commit; the README was left unchanged. |
| README line 9 still says "no Docker" while the new section adds a Docker workflow. | Useful | The README contradicted itself inside the same file. | Verified the stale line and reworded it: Docker is used only to package and run the API. |
| Python is pinned only to the minor version (`python:3.13-slim`, `python-version: "3.13"`); pin to `3.13.7` for reproducibility. | Noise | The assignment's shortcut check asks for a specific version rather than `3.x`; `3.13` satisfies that, and pinning the patch version would stop security patches from arriving automatically. The application dependencies are fully pinned in `app/requirements.txt`, which is what matters for reproducible tests. | Kept `3.13`. |
| `actions/checkout@v4` and `actions/setup-python@v5` are pinned to tags, not commit SHAs. | Noise | Correct in principle, but tag pinning is the normal practice for a course repository and the workflow only reads the repo and runs tests. | Kept tag pins; added `permissions: contents: read` instead (see security review). |
| The `.env` / `.env.*` lines in `.dockerignore` are "dead weight" because the Dockerfile only copies `app/`. | Noise | True today, but the exclusion protects against a future `COPY . .`; keeping it costs nothing. The comment did correctly note that `python-dotenv` is listed but never imported. | Kept the exclusions; the unused dependency is handled in the security review. |
| `HEALTHCHECK --start-period=5s` leaves no margin "on a slow CI runner". | Wrong | CI does not run the container; the health check only runs where the image is started. Locally the container reported `healthy` on the first check. | No change. |
| The `pytest` step cannot be silently skipped: no `continue-on-error`, no `|| true`, and `python -m pytest -v` collects 43 tests from the repo root. | Useful | Confirms the shortcut check the assignment asks for, with the collected test count. | Verified with `pytest --collect-only` (43 items). |


## AI security mini-review

| Finding | File evidence | Grade | Reason | Next action |
|---|---|---|---|---|
| CORS allows the literal `null` origin, which any web page can produce with a sandboxed iframe, so a malicious page could call the local API. | `app/main.py` — `FRONTEND_ORIGINS` includes `"null"`; `allow_credentials` is not enabled. | Valid | This is intentional so the frontend can be opened from `frontend/index.html` (`file://`). Without credentials no cookies or sessions are exposed, and the API only listens locally. | Keep for the course project; drop `"null"` and serve the frontend over HTTP if the API is ever exposed beyond localhost. |
| The in-memory store grows without limit and `GET /tasks` returns everything with no pagination or authentication. | `app/storage.py` — module-level `_tasks` dict; `app/main.py` — `list_tasks` returns the full list. | Valid | True, but no persistence and no authentication are stated scope decisions for the course (README ADR-001, `AGENTS.md`). | Do not add pagination or auth; note the limit in the README scope line. |
| The CI workflow has no explicit `permissions:` block, so the job token gets the repository default scope. | `.github/workflows/ci.yml` — no top-level `permissions` key at review time. | Valid | The job only checks out code and runs tests, so it should declare read-only access instead of relying on an organisation default I cannot see from the file. | Added `permissions: contents: read` to the workflow. |
| The `tags` list is iterated by the validator before the 10-item limit is checked, so a very large array costs CPU before it is rejected. | `app/models.py` — `_normalize_tags` loops over every item, then checks `len(normalized) > 10`. | Noise | The loop is linear and no more expensive than parsing the JSON body itself, which already happened; a body-size limit at a reverse proxy is the real control. Adding `max_length=10` on the field would also change the documented rule that duplicates do not count toward the limit. | No change. |
| `/docs`, `/redoc` and `/openapi.json` are enabled and expose the full route schema. | `app/main.py` — no `docs_url=None`. | Noise | Swagger is a documented feature of the project (README "API Docs") and the API is local-only. | No change. |
| The base image tag `python:3.13-slim` is mutable and not pinned to a digest. | `Dockerfile` line 3. | Noise | Digest pinning trades automatic security updates of the base image for bit-for-bit reproducibility; for a course image the tag is the better default. | No change. |
| XSS: all user text in the frontend is inserted with `textContent`; no `innerHTML` anywhere. | `frontend/app.js` — title, description, assignee, due pill and tag chips all use `textContent`. | Valid | Confirms the frontend safety rule in `AGENTS.md`. | Keep as is. |
| Dependency versions could not be checked against a vulnerability database by the AI reviewer ("no network access"). | `app/requirements.txt`. | Valid | An honest gap, not a finding — it told me what it could not verify instead of guessing. | Closed by my manual check below. |


## Manual security check

I checked two things myself that the AI review did not cover.

First, I searched the complete git history of every branch for secrets (`git log --all -p` filtered for password, secret, token, API-key and private-key patterns). The only matches were the words "design tokens" in CSS comments and commit messages. `.env` has never been committed, and `.env.example` only contains `PORT=8000` and `APP_ENV=development`.

Second, I ran `pip-audit -r app/requirements.txt` in a throwaway virtual environment to close the dependency gap the AI reviewer reported. It found 11 known advisories in 3 packages: `starlette 0.38.6` (pulled in by `fastapi 0.115.0`; Host/path validation and multipart parsing issues), `python-dotenv 1.0.1` (listed in the requirements but never imported by the app) and `pytest 8.3.3` (a test-only dependency). None of the starlette issues is reachable through this API (it does not use `request.url`, multipart forms or `StaticFiles`), but they are real. I treated this as a security fix allowed by the project rules and bumped the pins in `app/requirements.txt` (`fastapi 0.141.1`, `uvicorn 0.52.4`, `pydantic 2.13.4`, `pytest 9.1.1`, `httpx 0.28.1`) and removed `python-dotenv`. After the bump `pip-audit` reports no known vulnerabilities, the 43 tests still pass, and I rebuilt the Docker image and re-checked `/health`, validation errors and the filters from inside the container. No application code changed.


## One AI output I rejected or corrected

The AI code review recommended pinning Python to the exact patch version (`python:3.13.7-slim` in the Dockerfile and `python-version: "3.13.7"` in CI) so that the image and CI "run the exact interpreter that was locally verified". I did not accept this. The assignment's shortcut check is about avoiding a vague version such as `3.x`; `3.13` already meets that, and a patch-level pin would stop Python security releases from reaching the image automatically while adding nothing the tests need — the application dependencies are already pinned exactly in `app/requirements.txt`. I kept `3.13` and recorded the reasoning here. For the same reason I downgraded the suggestion to SHA-pin the GitHub Actions and instead added an explicit read-only `permissions` block, which closes a real gap at no maintenance cost.


## Three AI Usage Rules

1. **Never paste:** I will never paste real passwords, API keys, tokens, `.env` values, credentials, production logs, or personal/customer data into AI tools, tests, or documentation.

2. **Always verify:** I will read the full diff of any AI-generated change, run the test suite before and after it, and check runtime claims with a real command (`pytest`, `curl /health`, `docker run`) before accepting it.

3. **Record AI contributions by:** I will write down which file AI helped with, what it suggested, how I verified it, and whether I accepted, corrected, downgraded or rejected it — as done in `docs/midcourse/prompt-log.md` and in this file.


## Ownership Statement

I am comfortable submitting this repository as my own work because every change on `final-project` was verified by me with a real command rather than accepted from AI output. I ran the test suite (43 passed), started the API and checked `/health`, built the Docker image and confirmed from inside the running container that it runs as a non-root user with only `app/` copied, and checked eight README claims against the repository, correcting four of them. When the AI review suggested changes I disagreed with, such as patch-pinning Python, I rejected them and wrote down why; when it found real gaps, such as the missing CI permissions block, I applied the fix myself. I can explain every line in the CI workflow, the Dockerfile, `AGENTS.md` and the documentation in `docs/`.
