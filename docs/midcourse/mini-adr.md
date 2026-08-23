# Mini-ADR — Due dates + Tags

**Status:** Accepted · **Date:** 2026-08-23 · **Branch:** `mid-course-project`

**TL;DR:** Both features are thin extensions of the existing model → storage → route → test → UI chain. Overdue is a **backend-computed boolean**; tags are a **server-normalized list of strings**; both are filtered **server-side** via `GET /tasks` query params that a new filter bar drives. No persistence, no new dependencies, no multi-tag queries.

## Context
- Module 1–3 Task Tracker: FastAPI + Pydantic 2, in-memory dict store, vanilla-JS Kanban with a create/edit modal, 18 passing tests.
- `TaskCreate`/`TaskUpdate` use `extra="forbid"`; `update_task` applies only explicitly-set fields (`exclude_unset=True`).
- A test asserts the exact response key set, so every new field is a deliberate contract change.
- README's ADR-001 says storage is "backed by a JSON file" — it isn't (pure in-memory). Not changed here; noted so nobody expects due dates/tags to survive a restart.

## Decisions

| # | Decision | Why |
|---|----------|-----|
| D1 | `due_date` is **date-only** (`YYYY-MM-DD`), nullable | Kanban granularity is "by Friday"; maps 1:1 to `<input type="date">`; no timezone format wrangling. |
| D2 | **Backend computes `is_overdue`** (`@computed_field`: `due_date < today and status != Done`) and exposes `?overdue=true\|false` | One source of truth, testable in pytest, UI reads a boolean. `Done` tasks are never overdue. |
| D3 | Past due dates are **allowed** | You often log work that's already late; rejecting it is a surprise with no upside. |
| D4 | Clearing a date = `PATCH {"due_date": null}` | Zero new mechanism: `exclude_unset=True` already distinguishes "omitted" from "null". |
| D5 | `tags: list[str]`, **server-normalized** (trim → lowercase → blank/len>30 → 422 → dedupe first-wins → >10 → 422) via one `_normalize_tags` helper shared by both validators | `Bug`/`bug` must be the same tag; the rules live in one place; the UI shows exactly what was stored. |
| D6 | Tags are **always a list** in responses; `PATCH {"tags": null}` is coerced to `[]` in storage | `model_copy(update=…)` skips validation, so `null` would otherwise leak through — same hole the existing `description` guard plugs. |
| D7 | `?tag=<name>` is a **single, case-insensitive, exact-match** filter | Matches the single-value `status`/`priority` precedent; combines with `?overdue`. |
| D8 | **Filter bar is backend-driven**: state object → `URLSearchParams` → refetch | Consistent with D2/D7; no second filtering implementation in JS. |
| D9 | Tag dropdown is built from **all tags ever seen in an unfiltered fetch**; filtered responses only add | Otherwise selecting `bug` shrinks the dropdown to just `bug` and you can't switch. |
| D10 | Refetches triggered by a filter change, a save, or a filtered drag are **quiet** (no loading state); only the first load and Retry show it | The loading banner sits above the filter bar and shifted it on every change — a visible flicker for a sub-100 ms request. |

## Alternatives Claude suggested — and what I rejected

| Suggested | Verdict | Reason |
|-----------|---------|--------|
| `due_date` as `datetime` with timezone | Rejected | Overbuild for a board; the date picker is date-only anyway. |
| Compute overdue in the UI from `due_date` | Rejected | Untestable in pytest; two clocks (browser vs server) would disagree on edge days. |
| Reject past due dates on create | Rejected | D3 — real tasks are often already late. |
| Client-side lowercase/dedupe of tags in `readForm()` | Rejected | Duplicates the rule set; the server must validate anyway. |
| Multi-tag filter (`?tag=a&tag=b`, any/all semantics) | Rejected (scope) | Brief asks for "filter by tag"; any/all semantics is a design decision with no user driving it. |
| Tag colors / tag management panel | Rejected (scope) | Frontend polish; doesn't exercise backend/testing. |
| Persist tasks to JSON so tags/dates survive restarts | Rejected (scope) | Not part of either feature; would widen the diff into storage redesign. |
| Always refetch after drag-and-drop | Rejected | Accepted only in the filtered case — keeps the default path optimistic and request-free. |
| Reject `PATCH {"tags": null}` with 422 | Rejected | The leak is in `model_copy`, not the validator; coercing to `[]` matches the `description` precedent (D6). |
| Allow commas inside tags | Rejected | The modal joins/splits on commas, so `"a,b"` would be silently rewritten on edit; commas now return 422 (found in review). |
| Move the status banner below the filter bar to hide the flicker | Rejected | Hides the symptom; the real issue was a needless loading state on every refetch (D10). |

## Consequences
- `RESPONSE_FIELDS` in tests grew by 3 keys (`due_date`, `is_overdue`, `tags`) — intentional contract change.
- "Today" is the **server's local date**; overdue flips at server midnight. Fine for a local app, documented here.
- `knownTags` never shrinks within a page session if a tag is removed from every task — acceptable; a reload rebuilds it.
- Test count: 18 → 43 (25 new items).
