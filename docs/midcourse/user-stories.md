# User Stories

User stories for the two selected features. Each story was generated with Claude from a prompt that described the existing project (FastAPI + Pydantic v2, in-memory storage, vanilla-JS Kanban frontend, existing task fields) and then reviewed and corrected by me before implementation. Corrected AI assumptions are marked at the end of each feature.

Status values: `ToDo`, `InProgress`, `Done`. Dates use `YYYY-MM-DD`.

---

# Feature 1 – Due Dates + Overdue Filter

## Story 1 – Create a task with a due date

**Story:**
As a team member, I want to give a task an optional due date when I create it, so that I know when it is expected.

**Acceptance Criteria:**
- The create/edit modal has a **Due date** field (`<input type="date">`) after Priority.
- `POST /tasks` accepts an optional `due_date` in `YYYY-MM-DD` format; when omitted the response contains `due_date: null`.
- An invalid value such as `"tomorrow"` or `"2026-13-45"` returns HTTP 422, and the message is shown in the modal.
- A due date in the past is accepted (a task can already be late when it is logged).

## Story 2 – Update or remove a due date

**Story:**
As a team member, I want to change or clear a task's due date, so that the board reflects the current plan.

**Acceptance Criteria:**
- Opening the edit modal pre-fills the existing due date.
- Saving a new date sends `PATCH /tasks/{id}` with the new `due_date` and the card updates.
- Clearing the field sends `due_date: null` and the card no longer shows a date.
- Editing an unrelated field (e.g. the title) does not change the due date.

## Story 3 – See which tasks are overdue

**Story:**
As a team member, I want overdue tasks to be clearly marked, so that late work is obvious at a glance.

**Acceptance Criteria:**
- Every task response includes a read-only `is_overdue` boolean computed by the backend.
- A task is overdue when `due_date` is before today **and** its status is not `Done`.
- A task without a due date is never overdue; a `Done` task is never overdue even with a past date.
- Cards show `Due YYYY-MM-DD`; overdue cards show a red `Overdue · YYYY-MM-DD` pill instead.
- Sending `is_overdue` in a request body returns HTTP 422 (read-only field).

## Story 4 – Filter the board to overdue tasks

**Story:**
As a team member, I want to show only overdue tasks, so that I can focus on what is late.

**Acceptance Criteria:**
- A filter bar above the board has an **Overdue only** checkbox.
- Checking it requests `GET /tasks?overdue=true` and only overdue tasks are shown; empty columns keep their empty state.
- `GET /tasks?overdue=false` returns only non-overdue tasks; omitting the parameter returns all tasks.
- `GET /tasks?overdue=banana` returns HTTP 422.
- Changing the filter does not flash a loading state or shift the filter bar.

## AI Assumptions (Feature 1)

- `due_date` is a calendar date, not a timestamp. **Kept.**
- "Today" is the server's local date. **Kept**, documented as a risk.
- Overdue is a filter concept only, not a field. **Corrected:** it is also a computed response field so the UI does not re-implement the rule.
- ⚠️ **Corrected AI assumption:** the first frontend implementation assumed that the optimistic drag-and-drop render only needs `status` updated. Because `is_overdue` is derived from status, dragging an overdue card into Done showed a Done card with a red Overdue pill for one round-trip, contradicting Story 3. Fixed by clearing `is_overdue` optimistically on a Done move.

---

# Feature 2 – Tags / Labels

## Story 1 – Add tags to a task

**Story:**
As a team member, I want to add one or more tags to a task, so that I can group related work.

**Acceptance Criteria:**
- The modal has a **Tags** text field that accepts comma-separated values.
- `POST /tasks` accepts `tags` as a JSON list of strings; when omitted the response contains `tags: []`.
- Responses always contain `tags` as a list, never `null`.
- Sending `tags` as a string (`"bug"`) or with non-string items (`[1, 2]`) returns HTTP 422.

## Story 2 – Tags are validated and normalized

**Story:**
As a team member, I want `Bug` and `bug` to be the same tag, so that filtering and chips stay consistent.

**Acceptance Criteria:**
- Each tag is trimmed and lowercased; duplicates are removed keeping the first occurrence (`["Bug", " bug ", "Backend"]` → `["bug", "backend"]`).
- A blank or whitespace-only tag returns HTTP 422 with the message `tags must not contain blank values`.
- A tag longer than 30 characters returns HTTP 422; more than 10 tags (after de-duplication) returns HTTP 422.
- A tag containing a comma returns HTTP 422, because the UI uses commas as the separator.

## Story 3 – See tags on cards

**Story:**
As a team member, I want to see a task's tags on its card, so that I can recognise its category without opening it.

**Acceptance Criteria:**
- Each tag renders as a small chip under the card's meta row; tasks with no tags show no chip list.
- Chips are rendered as text (no HTML injection).
- Chips look correct in light and dark mode.

## Story 4 – Filter the board by tag

**Story:**
As a team member, I want to filter the board by a single tag, optionally combined with the overdue filter.

**Acceptance Criteria:**
- The filter bar has a **Tag** dropdown listing "All tags" plus every known tag, sorted alphabetically.
- Selecting a tag requests `GET /tasks?tag=<name>`; matching is case-insensitive (`?tag=BUG` equals `?tag=bug`).
- The tag filter combines with the overdue checkbox (`?tag=bug&overdue=true`).
- The dropdown does not shrink to the visible tags while a filter is active.
- `GET /tasks?tag=` returns HTTP 422; an unknown tag returns HTTP 200 with `[]` and the board shows "No tasks match the current filters."

## Story 5 – Tags survive unrelated edits

**Story:**
As a team member, I want a task's tags to stay intact when I edit something else.

**Acceptance Criteria:**
- `PATCH /tasks/{id}` with only a title leaves `tags` unchanged.
- The edit modal sends `tags` only when they actually changed.
- `PATCH` with `tags: []` or `tags: null` clears the tags; the response contains `[]`.

## AI Assumptions (Feature 2)

- Tags are free-form strings, not a fixed enum. **Kept.**
- A single-tag filter is enough; no any/all multi-tag query. **Kept.**
- ⚠️ **Corrected AI assumption:** the first draft of the frontend prompt, and Claude Code's first instinct, was to lowercase and de-duplicate tags in JavaScript as well. I removed that: the server is the only place normalization happens, so the board shows exactly what the API stored and there is one set of rules to test.
- ⚠️ **Corrected AI assumption:** the backend implementation assumed `PATCH {"tags": null}` was impossible to send and left it unhandled; it returned `tags: null`. Corrected with a storage guard that treats `null` as "clear".
