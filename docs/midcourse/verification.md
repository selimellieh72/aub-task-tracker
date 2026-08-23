# Verification — Mid-course Project

**TL;DR:** Baseline 18 → final **43 pytest tests, all green** (25 new items). Manual checks ran in **headless Chrome** against the live backend, plus a 15-step API contract. **Three break tests**, each restored to green. One "passing" break test was caught as invalid and redone. One bug (filter-change flicker) was found only by manual testing.

Commands (repo root): `venv/bin/python -m pytest -v` · server: `uvicorn app.main:app --reload --port 8000` · frontend: open `frontend/index.html`.

---

## 1. Baseline (before any change)

| | |
|---|---|
| Branch | `mid-course-project` created from `main @ 6258d33` |
| Command | `venv/bin/python -m pytest -q` |
| Result | **18 passed in 0.06s** |
| Server | `uvicorn app.main:app --port 8000` → `GET /tasks` → `[]` |

---

## 2. Backend test results per step

| Step | Commit | Result |
|------|--------|--------|
| Feature 1 backend + tests | `c2e89a0` | 28 passed (18 + 10) |
| Feature 2 backend + tests (incl. `tags: null` guard) | `9db1682` | 42 passed (+14) |
| Fix: reject commas in tags | `bb95a82` | 43 passed (+1) |
| Fix: optimistic overdue pill (frontend only) | `6eacee6` | 43 passed |
| Fix: quiet refetch on filter change (frontend only) | `e7dc5e4` | 43 passed |
| **Final** | | **43 passed in 0.13s** |

New tests (25 items, `tests/test_tasks.py` sections `# --- Due dates` and `# --- Tags`):

- Due dates: valid date · invalid `not-a-date` / `2026-13-45` (parametrized) · no date → null/false · past date → overdue · PATCH to Done → not overdue · PATCH new date · PATCH null clears · `?overdue=true|false|omitted` exact ids · `?overdue=banana` → 422
- Tags: normalize + dedupe · default `[]` · blank → 422 · 11 tags → 422 · 31 chars → 422 · comma → 422 · `"bug"` / `[1,2]` → 422 (parametrized) · PATCH replace · PATCH `[]` clears · PATCH `null` clears · title-only PATCH preserves tags · `?tag=bug` / `?tag=BUG` / `?tag=nothing` · `?tag=` → 422 · `?tag=bug&overdue=true`

---

## 3. Manual browser checks (headless Chrome, `file://frontend/index.html` → `localhost:8000`)

Method: the real page + real `app.js` rendered by Chrome `--headless=new --dump-dom`; interactions scripted by a tiny injected `<script>` that sets a control and dispatches `change`, then the resulting DOM is inspected. State seeded via `curl`.

| # | Check | Observed | ✓ |
|---|-------|----------|---|
| B1 | Card with past due date | `<span class="due overdue">Overdue · 2026-08-20</span>` | ✓ |
| B2 | Card with future due date | `<span class="due">Due 2026-09-10</span>` | ✓ |
| B3 | Card without date | no `.due` element | ✓ |
| B4 | Modal has date + tags inputs | `<input type="date" id="due_date">`, `<input … id="tags">` | ✓ |
| B5 | Tick "Overdue only" | only `data-id="1"` rendered | ✓ |
| B6 | Tag chips | `bug`,`backend` / `frontend` / none / `bug` per card | ✓ |
| B7 | Tag dropdown | `All tags, backend, bug, frontend` (sorted) | ✓ |
| B8 | Select `bug` | cards 1 & 4 only; dropdown **unchanged** (didn't shrink) | ✓ |
| B9 | `bug` + Overdue | only card 1 | ✓ |
| B10 | `frontend` + Overdue (no match) | banner "No tasks match the current filters.", columns still render | ✓ |
| B11 | Drag overdue card → Done (after fix `6eacee6`) | pill text before/during/after: `Overdue · …` → `Due …` → `Due …` | ✓ |
| B12 | Change tag dropdown (after fix `e7dc5e4`) | read synchronously after the change event — old: `state=loading`, banner visible, filter bar shifted 68.8px; new: `state=ready`, banner hidden, shift 0 | ✓ |

Typing in the modal and clicking Save were verified by replaying `readForm()` and the PATCH diff in node (payload tables in `prompt-log.md`) and by the API contract below, then by opening the page and creating/editing a task by hand. The filter flicker (B12) was found during that manual pass, not by any automated check.

---

## 4. Behavior contract (API smoke, run after the final commit)

| # | Request | Expected | Got |
|---|---------|----------|-----|
| C1 | POST past date, tags `["Bug"," bug ","Backend"]` | 201, overdue, `["bug","backend"]` | ✓ |
| C2 | POST future date, `["frontend"]` | 201, not overdue | ✓ |
| C3 | POST bare | `due_date: null`, `is_overdue: false`, `tags: []` | ✓ |
| C4 | POST `due_date: "tomorrow"` | 422 | ✓ |
| C5 | POST `tags: ["a","  "]` | 422 | ✓ |
| C6 | POST `tags: ["a,b"]` | 422 | ✓ |
| C7 | `GET ?overdue=true` | `[1]` | ✓ |
| C8 | `GET ?tag=BUG` | `[1]` | ✓ |
| C9 | `GET ?tag=bug&overdue=false` | `[]` | ✓ |
| C10 | PATCH title only | tags + date preserved | ✓ |
| C11 | PATCH `due_date: null` | null, not overdue | ✓ |
| C12 | PATCH `tags: []` | `[]` | ✓ |
| C13 | PATCH `is_overdue: true` | 422 (read-only, `extra="forbid"`) | ✓ |
| C14 | `?overdue=banana`, `?tag=` | 422, 422 | ✓ |
| C15 | Pre-existing: GET 999 → 404, DELETE → 204, `ToDo→Done` → 422 | unchanged | ✓ |

**Before/after refactor:** the three post-checkpoint fixes (`bb95a82`, `6eacee6`, `e7dc5e4`) were the only changes after the feature commits. The full suite was green before each (42) and after each (43/43); contract C1–C15 above was run after `6eacee6`, and B12 plus a re-run of B5–B10 after `e7dc5e4`. No behavior changed except the three intended ones (commas rejected; optimistic pill; no loading flash on refetch).

---

## 5. Break Tests

Each: mutate one rule → run suite → confirm the *right* test fails for the *right* reason → `git checkout` → green.

### Break 1 — drop the "Done is never overdue" clause
`app/models.py`: comment out `and self.status != TaskStatus.DONE`
```
FAILED tests/test_tasks.py::test_patch_past_due_task_to_done_returns_is_overdue_false - assert True is False
FAILED tests/test_tasks.py::test_list_tasks_filter_by_overdue_returns_only_matches - assert [1, 2] == [1]
2 failed, 40 passed in 0.15s
restored -> 42 passed in 0.12s
```
Two tests caught it from two angles (single task, and the filter leaking a Done task).

### Break 2 — silently drop blank tags instead of rejecting
`app/models.py`: `raise ValueError("tags must not contain blank values")` → `continue`
```
>       assert r.status_code == 422
E       assert 201 == 422
FAILED tests/test_tasks.py::test_create_task_blank_tag_returns_422 - assert 201 == 422
1 failed, 41 passed in 0.15s
restored -> 42 passed in 0.12s
```

### Break 3 — make `?tag=` case-sensitive
First attempt: my `sed` pattern didn't match the real line, nothing changed, suite showed **42 passed** — a "passing" break test that proved nothing. Caught because `git diff --stat` printed no file. Redone against the actual line:

`app/storage.py`: `tag.strip().lower()` → `tag.strip()`
```
FAILED tests/test_tasks.py::test_list_tasks_filter_by_tag_returns_only_matches - assert [] == [1]
1 failed, 41 passed in 0.14s
restored -> 42 passed in 0.12s
```
(`?tag=BUG` returned nothing — the case-insensitivity assertion is load-bearing.)

Lesson: a break test needs evidence the code actually changed, not just a red/green flip.
