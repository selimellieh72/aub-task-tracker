# AGENTS.md — guardrails for AI coding agents in this repo

Read this file before changing anything. It applies to every AI agent or assistant working on the Task Tracker, and to the human using one.

## Stack
- **Backend:** Python 3.13, FastAPI 0.115, Pydantic 2.9 (`app/`). In-memory storage (`app/storage.py`) — nothing persists across restarts.
- **Frontend:** vanilla HTML/CSS/JS in `frontend/`, no build step. Talks to `http://localhost:8000`.
- **Tests:** pytest + httpx `TestClient` in `tests/` (fixtures in `tests/conftest.py`, storage is reset around every test).
- **Release:** `Dockerfile` (non-root, API only), `.github/workflows/ci.yml` (pytest on push/PR).

## Commands
```bash
venv/bin/python -m pytest -v                          # tests (use the venv — system python has no fastapi)
venv/bin/python -m uvicorn app.main:app --reload --port 8000   # API
open frontend/index.html                              # frontend (file:// is allowed by CORS)
docker build -t task-tracker:final . && docker run -p 8000:8000 task-tracker:final
```

## Read first, then act
1. Read `README.md`, then the file(s) you intend to change, then the tests that cover them. Do not propose a change to code you have not read.
2. Check `docs/` before re-deciding something: `docs/midcourse/mini-adr.md` records why overdue is computed server-side, why tags are normalized only on the server, and why the filter bar is backend-driven.
3. Run the test suite before and after every change and report the real numbers.

## Project rules
- **Scope is frozen.** No new product features (comments, auth, databases, notifications, persistence, themes). The course scope is the Task Tracker as it is.
- **`app/` and `frontend/` are protected.** Change them only for a small bug fix, a security fix, or a correction that documentation already supports — and say so explicitly in the PR/commit message and in `docs/final-ai-review.md`.
- **Contracts the tests enforce:** `TaskCreate`/`TaskUpdate` use `extra="forbid"`; responses must contain exactly the keys in `RESPONSE_FIELDS` (`tests/test_tasks.py`); `ToDo → InProgress → Done` transitions are validated in `app/business_rules.py`; `tags` is always a list; `is_overdue` is read-only.
- **One focused change per prompt/commit.** Name the files you may touch. If the task needs more, stop and ask.
- **Never weaken a check to make it pass:** no `continue-on-error`, `|| true`, skipped tests, loosened assertions, or broadened CORS.
- **Frontend safety:** insert user text with `textContent`, never `innerHTML`.

## Secrets and data
- Never paste `.env` values, tokens, credentials, or real personal data into a prompt, a test, a fixture, or a doc. `.env` is gitignored and dockerignored; keep it that way.
- Use obviously fake sample data (`"Fix login"`, `"bug"`, `2030-01-15`).

## When unsure
Ask a numbered question with your recommended default instead of guessing. A blocked question is cheaper than a wrong change.
