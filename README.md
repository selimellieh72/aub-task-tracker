# Task Tracker

A minimal FastAPI learning project: Task Tracker REST API + simple web frontend.

## Architecture
- **Backend:** Python + FastAPI + Pydantic
- **Storage:** in-memory dict (data is lost when the server restarts; the JSON-file persistence planned in ADR-001 was never implemented)
- **Frontend:** static HTML/CSS/JS calling the REST API
- No authentication, no database, no real-time updates, no notifications. Docker is used only to package and run the API (final project) — it is not a deployment target.

## Folder Structure
```
task-tracker/
├── app/
│   ├── main.py          # FastAPI app, routes
│   ├── models.py        # Pydantic models + enums
│   ├── storage.py       # in-memory store
│   ├── business_rules.py # status-transition rules
│   └── requirements.txt
├── tests/
│   ├── conftest.py      # pytest fixtures (TestClient, storage reset)
│   ├── test_tasks.py    # endpoint tests
│   └── verify_a.py      # Part A model verification script
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── .github/workflows/ci.yml   # pytest on push and pull request
├── docs/                # midcourse/ + final project evidence
├── Dockerfile
├── .dockerignore
├── AGENTS.md            # guardrails for AI coding agents
├── .env.example
├── .gitignore
└── README.md
```

## Setup

1. Create and activate a virtual environment (from the project root):
   ```bash
   python -m venv venv
   source venv/bin/activate      # macOS/Linux
   venv\Scripts\activate         # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r app/requirements.txt
   ```

3. (Optional) Copy the example environment file. The app does not currently read `.env` — the port is set on the command line — so this step only matters if you add configuration later:
   ```bash
   cp .env.example .env          # macOS/Linux
   copy .env.example .env        # Windows
   ```

## Run the server

From the project root:
```bash
uvicorn app.main:app --reload --port 8000
```

## Test the health endpoint

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "ok",
  "timestamp": "2026-08-23T12:34:56.789012+00:00"
}
```

## API Docs (Swagger)

Open in your browser:
```
http://localhost:8000/docs
```

## Frontend

Open `frontend/index.html` directly in your browser (`file://` is allowed by CORS) or serve the folder on port 5500. The board talks to `http://localhost:8000`, so start the server first.

## Run the tests

```bash
venv/bin/python -m pytest -v        # or just `pytest` with the venv activated
```

## Mid-course project (branch `mid-course-project`)

Two features were added with an AI-assisted workflow: **due dates + overdue filter** and **tags + tag filter**.

| Step | Command |
|------|---------|
| Backend | `uvicorn app.main:app --reload --port 8000` |
| Frontend | open `frontend/index.html` in a browser |
| Tests | `venv/bin/python -m pytest -v` (43 tests) |

New API surface:

- `due_date` (`YYYY-MM-DD` or `null`) and `tags` (`["bug", "backend"]`) on `POST /tasks` / `PATCH /tasks/{id}`
- `is_overdue` (read-only, computed) on every task response
- `GET /tasks?overdue=true&tag=bug` — both filters combine with `status` / `priority`

Documentation for the project lives in [`docs/midcourse/`](docs/midcourse/): user stories, mini-ADR, prompt log, verification (incl. break tests), and reflection.

## Final Project

Branch reviewed: `final-project`

### What this submission demonstrates
- Existing Task Tracker app still runs inside the intended course scope (no new product features).
- CI runs the pytest suite on push and pull request (`.github/workflows/ci.yml`).
- Docker image builds and runs with `/health` returning 200, as a non-root user.
- AI review, security, and ownership evidence is in `docs/`.

### How to run locally
```bash
python -m venv venv
source venv/bin/activate              # Windows: venv\Scripts\activate
pip install -r app/requirements.txt
uvicorn app.main:app --reload --port 8000
curl http://localhost:8000/health      # {"status":"ok","timestamp":"..."}
```
Then open `frontend/index.html` in a browser (the API allows the `file://` origin).

### How to run tests
```bash
venv/bin/python -m pytest -v           # 43 tests
```

### How to run with Docker
```bash
docker build -t task-tracker:final .
docker run -d --name task-tracker -p 8000:8000 task-tracker:final
curl -i http://localhost:8000/health   # HTTP/1.1 200 OK
docker stop task-tracker && docker rm task-tracker
```
The image contains only `app/` and its dependencies (see `.dockerignore`) and runs as the unprivileged `appuser`. The frontend is not served by the container — open it from disk as above.

### Evidence files
- `docs/release-evidence.md` — baseline, CI, Docker, and documentation claim checks
- `docs/final-ai-review.md` — graded AI code review and security findings, manual check, ownership statement
- `docs/ai-playbook.md` — personal rules for working with AI
- `AGENTS.md` — guardrails for AI coding agents working in this repo

### AI assistance summary
AI helped draft or review: CI workflow, Dockerfile, README claim checks, code review, security review, and the evidence docs.
I verified the work by: running the test suite (43 passed), building and running the image and curling `/health` from the container, checking the container user and file list, and reading every README claim against the repo.
One AI suggestion I rejected or corrected: see `docs/final-ai-review.md` → "One AI output I rejected or corrected".
