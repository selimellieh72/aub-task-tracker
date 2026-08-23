# Task Tracker (Module 1)

A minimal FastAPI learning project: Task Tracker REST API + simple web frontend.

## Architecture (ADR-001)
- **Backend:** Python + FastAPI + Pydantic
- **Storage:** in-memory dict backed by a JSON file (`app/tasks.json`, created at runtime, gitignored)
- **Frontend:** static HTML/CSS/JS calling the REST API
- No authentication, no database, no Docker, no real-time updates, no notifications

## Folder Structure
```
task-tracker/
├── app/
│   ├── main.py          # FastAPI app, routes
│   ├── models.py        # Pydantic models + enums
│   ├── storage.py       # in-memory store (JSON persistence later)
│   ├── business_rules.py # status-transition rules
│   ├── tasks.json       # created at runtime, gitignored
│   └── requirements.txt
├── tests/
│   ├── conftest.py      # pytest fixtures (TestClient, storage reset)
│   ├── test_tasks.py    # endpoint tests
│   └── verify_a.py      # Part A model verification script
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
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

3. Copy the example environment file:
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
| Tests | `venv/bin/python -m pytest -v` (42 tests) |

New API surface:

- `due_date` (`YYYY-MM-DD` or `null`) and `tags` (`["bug", "backend"]`) on `POST /tasks` / `PATCH /tasks/{id}`
- `is_overdue` (read-only, computed) on every task response
- `GET /tasks?overdue=true&tag=bug` — both filters combine with `status` / `priority`

Documentation for the project lives in [`docs/midcourse/`](docs/midcourse/): user stories, mini-ADR, prompt log, verification (incl. break tests), and reflection.
