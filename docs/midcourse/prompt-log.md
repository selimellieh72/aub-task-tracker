# Prompt Log

This document records the most significant AI prompts used during the implementation of Feature 1 (Due Dates + Overdue Filter) and Feature 2 (Tags / Labels). For each prompt, it includes the prompt, a summary of the AI response, and my review of what was accepted, edited, or rejected.

I used Claude to plan the work and shape each prompt, and Claude Code in my editor to implement one focused step at a time. After every step I inspected the change, ran the tests, and re-prompted Claude Code when something needed fixing. Each prompt names the files that may change.

---

# Feature 1 – Due Dates + Overdue Filter

## Prompt 1 – Inspect the Existing Project Before Changing It

### Prompt

```text
Do not modify any file yet.

Inspect the Task Tracker project for two upcoming features:
(1) optional due_date on tasks + overdue filter,
(2) tags/labels on tasks + tag filter.

Report with file:line references:
- Repo layout, README sections, any project rules.
- Backend: framework and Pydantic version, Task models and validators,
  storage, every route, how PATCH handles read-only fields and 422s,
  how GET /tasks filters work today, CORS config.
- Tests: framework, fixtures, naming convention, test count,
  the exact command to run them.
- Frontend: how tasks are fetched/rendered, modal form fields,
  how 422 errors are shown, any existing filter controls, CSS tokens.
- Git: current branch, commit message style.
- Run the test suite once and report the baseline result.
- Anything that constrains adding new optional fields.
```

### AI Response Summary

Produced a full map of the project. Four findings changed the plan: `TaskCreate`/`TaskUpdate` use `extra="forbid"` (new fields must be real model fields); one test asserts the exact response key set (`set(body) == RESPONSE_FIELDS`) and will break on any new field; `update_task` uses `exclude_unset=True`, so "omitted" and `null` are already distinguishable; the README claims JSON persistence but storage is pure in-memory. Baseline: 18 tests passing with `venv/bin/python -m pytest`.

### My Review

**Accepted**

- The full map and the baseline result (18 passed).
- Each constraint became an explicit line in later prompts (update `RESPONSE_FIELDS`; reuse `exclude_unset` to clear values).
- The README/storage mismatch was noted in the mini-ADR but deliberately left unchanged (out of scope).

**Edited**

- None.

**Rejected**

- None.

---

## Prompt 2 – Generate Reviewed User Stories and List Assumptions

### Prompt

```text
Generate user stories for both features (Due Dates + Overdue Filter,
Tags / Labels) based on the project inspection above.

Constraints:
- 3-5 stories per feature, user role "team member".
- Every story needs testable acceptance criteria and at least one
  failure case (HTTP 422 / 404).
- Cover backend and frontend behaviour.
- List every assumption you make. For anything that changes
  user-visible behaviour, the data model, or validation limits,
  ask me as a numbered question with your recommended default.
- Wait for my review before writing any code.
```

### AI Response Summary

Generated the user stories with acceptance criteria and eight numbered questions: date-only vs datetime; backend vs UI overdue computation; whether `Done` tasks count as overdue; whether past due dates are allowed; tag normalization; tag limits; single-tag vs multi-tag filter; and whether to keep its planning notes in the repository.

### My Review

**Accepted**

- Defaults for questions 1–7 (date-only; backend-computed `is_overdue`; `Done` never overdue; past dates allowed; trim + lowercase + dedupe; max 10 tags / 30 chars; single `?tag=` filter).

**Edited**

- Kept only the two or three questions that actually changed the design for the reflection; the rest were answered with the defaults.

**Rejected**

- Keeping the planning notes in the repository — only code, tests and the required docs are committed.

---

## Prompt 3 – Add Backend Due Date Support and Tests (weak prompt → strong prompt)

### Weak prompt (first draft, not sent)

```text
Add a due_date field to tasks and an overdue filter. Add tests.
```

This version does not say the date type, whether `Done` counts as overdue, whether past dates are allowed, how clearing works, where overdue is computed, which files may change, how to run the tests, or what the tests must prove.

### Strong prompt (sent)

```text
You are a senior Python/FastAPI engineer making one focused change.

Touch ONLY app/models.py, app/storage.py, app/main.py, tests/test_tasks.py.
Run tests with venv/bin/python -m pytest -v.

Required behaviour
- TaskCreate and TaskUpdate: add due_date: Optional[date] = None.
  Keep extra="forbid". No custom validator — Pydantic's date parsing
  already rejects "tomorrow" / "2026-13-45" with 422. Past dates are ALLOWED.
- TaskResponse: add due_date and a @computed_field is_overdue: bool =
  due_date is not None and due_date < date.today() and status != Done.
- storage.get_all_tasks gains overdue: Optional[bool]. True → only
  overdue, False → only non-overdue, None → no filter.
- PATCH {"due_date": null} must CLEAR the date via the existing
  exclude_unset path — confirm, do not special-case it.
- GET /tasks gains ?overdue= via Query.

Tests (naming: test_<action>_<condition>_returns_<result>)
- valid due date → 201, due_date echoed, is_overdue False
- "not-a-date" and "2026-13-45" → 422
- no due date → null / False
- past date → is_overdue True; then PATCH to Done through the legal
  transition chain → False
- PATCH new date; PATCH null clears
- three tasks → ?overdue=true, ?overdue=false, omitted: assert exact ids
- ?overdue=banana → 422
Compute "yesterday" with timedelta; never hardcode.
Update RESPONSE_FIELDS. If anything is contradictory, STOP and ask.
```

### AI Response Summary

Implemented the model fields, the computed `is_overdue` property, the storage filter clause, and the query parameter, and added ten new test items. Suite: 28 passed. It split overdue detection into two tests to keep the names honest and used the `ToDo → InProgress → Done` transition chain from `business_rules.py`.

### My Review

**Accepted**

- The full backend diff (read line by line).
- Every new test assertion, including the exact-id filter assertions.

**Edited**

- None.

**Rejected**

- None.

---

## Prompt 4 – Add the Due Date Input, Card Pill, and Overdue Filter

### Prompt

```text
You are a senior frontend engineer making one focused change to a
vanilla-JS Kanban board. Touch ONLY frontend/index.html, frontend/app.js,
frontend/style.css. The backend is already done: every task has
due_date ("YYYY-MM-DD" | null) and is_overdue (boolean);
GET /tasks?overdue=true filters; PATCH {"due_date": null} clears.
Models use extra="forbid" — never send unknown keys.

1. Modal: <input type="date" id="due_date"> after Priority.
   Create: include due_date only when non-empty — never send "".
   Edit: prefill; follow the existing change-only PATCH diff;
   a cleared date sends null.
2. Cards: a .due pill "Due YYYY-MM-DD"; when is_overdue, class
   .overdue and text "Overdue · YYYY-MM-DD". textContent only.
   Copy the .priority pill pattern; overdue uses --error-bg/--error-fg.
3. Filter bar above the board with an "Overdue only" checkbox.
   Keep a filters state object; build the URL with URLSearchParams;
   changing the checkbox refetches; empty columns keep their empty state.
4. Keep drag-and-drop, edit, priority sort and the error banner working.

Run node --check frontend/app.js and the backend suite (must stay 28).
Report the exact payload shapes for create / edit-set / edit-clear.
```

### AI Response Summary

Added the date input, the due/overdue pill, the filter bar and the `filters` → `URLSearchParams` → `fetchTasks()` flow, and reported a payload table verified in node. It also flagged two deviations: the empty-state text becomes "No tasks match the current filters." when a filter is active, and the board refetches after a drag-and-drop while a filter is active so a card moved to Done leaves an overdue-only board.

### My Review

**Accepted**

- The date input, pill, and filter bar.
- Both flagged deviations — the filtered-drag refetch prevented a stale-board bug I had not specified.

**Edited**

- None.

**Rejected**

- None.

---

## Prompt 5 – Review Feature 1 for Bugs

### Prompt

```text
Do not modify any file. Review the due-dates commit against the user
stories. Report only REAL defects: bugs, contradictions with the stories,
or a test that does not prove what its name claims. Style is not a
finding. For each: file:line, a concrete failing scenario, severity.

Probe specifically: date.today() edge cases; PATCH null really clears;
the frontend never sends due_date ""; drag-and-drop while the overdue
filter is active; ?overdue=false for tasks with no due date; whether
the exact-key tests are weaker than before.
```

### AI Response Summary

Backend clean (re-ran 18/18 on the base commit and 28/28 on the feature commit). Two frontend findings: (A) with a filter active, if the refetch after a successful drag fails, the whole board is wiped with an error banner; (B) dragging an overdue card into Done shows a Done card with a red "Overdue" pill for one round-trip because the optimistic render only updates `status`.

### My Review

**Accepted**

- Finding B — fixed in four lines (clear `is_overdue` optimistically on a Done move, restore on failure), verified in headless Chrome before/during/after the move.

**Edited**

- None.

**Rejected**

- Finding A — this is the app's pre-existing behaviour for any failed `GET` (initial load, filter change), the move is persisted, and Retry restores the board. Fixing it would mean duplicating filter logic client-side, which I had already decided against.

---

# Feature 2 – Tags / Labels

## Prompt 1 – Add Backend Tag Support with Normalization and Tests

### Prompt

```text
You are a senior Python/FastAPI engineer making one focused change.
Touch ONLY app/models.py, app/storage.py, app/main.py, tests/test_tasks.py.
Run `git show HEAD -- app/ tests/` first and match Feature 1's
conventions (field placement, filter style, test banners, naming).

Required behaviour
- TaskCreate: tags: list[str] = Field(default_factory=list).
  TaskUpdate: tags: Optional[list[str]] = None (None = not provided,
  [] = clear). TaskResponse: tags always a list, never null.
- ONE module-level normalize function used by a @field_validator("tags")
  on BOTH input models (Update returns None unchanged). Rules, in order:
  strip → lowercase → blank → 422 → longer than 30 chars → 422 →
  dedupe keeping first-seen order → more than 10 AFTER dedupe → 422.
- Non-list tags ("bug") and non-string items ([1, 2]) must 422.
- storage.get_all_tasks gains tag: Optional[str]; normalize it the same
  way; keep tasks where tag in task.tags.
- GET /tasks gains ?tag= (Query, min_length=1); combines with ?overdue=.

Tests
- ["Bug", " bug ", "Backend"] → ["bug", "backend"]; body keys == RESPONSE_FIELDS
- no tags → []
- ["bug", "  "] → 422; 11 distinct tags → 422; 31-char tag → 422
- tags: "bug" → 422
- PATCH ["frontend"] replaces; PATCH [] clears
- tags preserved after PATCH {"title": "Renamed"}
- ?tag=bug and ?tag=BUG return the same task; ?tag=nothing → []; ?tag= → 422
- ?tag=bug&overdue=true returns only the overdue tagged task
Add tags to RESPONSE_FIELDS. STOP and ask if anything conflicts.
```

### AI Response Summary

Implemented `_normalize_tags`, the validators, the response field, the storage filter and the query parameter, with thirteen new tests (41 passed). It also reported a hole it chose not to fix because the prompt said "no special-casing": `PATCH {"tags": null}` returns `200` with `tags: null`, because `model_copy(update=…)` skips validation.

### My Review

**Accepted**

- The normalization helper, validators, filter and tests.

**Edited**

- Added a two-line guard in `storage.update_task` (`None → []`, mirroring the existing `description` guard) plus `test_patch_tags_null_clears_tags`. Suite: 42 passed.

**Rejected**

- Rejecting `null` with a 422 from the validator — the leak is in `model_copy`, not the validator, so that would not have closed it.

---

## Prompt 2 – Add the Tags Input, Chips, and Tag Filter

### Prompt

```text
You are a senior frontend engineer making one focused change.
Touch ONLY the three frontend files. Match the due-date patterns exactly
(filters state, filterQuery(), readForm(), change-only PATCH diff).

Backend contract: tags is always a lowercase, trimmed, deduped list;
POST/PATCH accept a JSON list; blank tags → 422; PATCH [] clears;
GET /tasks?tag=bug filters (case-insensitive) and combines with ?overdue=.

1. Modal: <input id="tags" placeholder="bug, backend (comma separated)">.
   readForm(): split on commas, trim, drop empty pieces. Do NOT lowercase
   or dedupe client-side — the server owns normalization.
   Edit: prefill with tags.join(", "). The existing diff compares by
   reference, which would always resend arrays — compare tag arrays by
   value so untouched tags are NOT sent.
2. Cards: <ul class="tags"> with one <li class="tag"> per tag,
   textContent only, existing tokens, dark-mode safe.
3. Filter bar: <select id="filter-tag"> with "All tags" + every known tag,
   sorted. Build the list from an UNFILTERED fetch and only ADD from
   filtered ones so the dropdown never shrinks while filtering.
   Preserve the current selection.

Run node --check; replay readForm + the PATCH diff in node and report
payloads for: create "Bug, bug , Backend"; edit untouched; edit cleared;
edit title-only on a tagged task (must not include tags).
```

### AI Response Summary

Added the input, chips, dropdown and a `knownTags` set with `refreshTagFilter()`. Reported a payload table: untouched tags → `{}` (no request); cleared → `{"tags": []}`; title-only → no `tags` key. Also added a small `.filters select` style so the dropdown matched the bar.

### My Review

**Accepted**

- Everything, after verifying chips, dropdown stability, combined filters and the no-match state in headless Chrome.

**Edited**

- None.

**Rejected**

- None.

---

## Prompt 3 – Review Feature 2 for Bugs

### Prompt

```text
Do not modify any file. Review the tags commit against the user
stories. Only REAL defects.
Probe: None inside the tag list; a tag of exactly 30 chars; tab-only
and NBSP-only tags; ?tag=%20; a spurious PATCH when tags are re-typed
identically; the dropdown never shrinking; XSS in chips; whether the
>10 check happens after dedupe.
```

### AI Response Summary

Found one real bug: a tag containing a comma (legal through the API, e.g. `["a,b", "c"]`) is re-split by the modal into `["a", "b", "c"]` when the task is edited, silently rewriting the tags on an unrelated save. Found one nit: `?tag=%20` returns `200 []` while `?tag=` returns `422`. Everything else checked out with live probes (30 chars inclusive, NBSP rejected, `textContent` everywhere, dedupe before the count).

### My Review

**Accepted**

- The comma bug — fixed on the backend (tags containing commas now return 422, with a test). The UI's delimiter is now part of the contract.

**Edited**

- None.

**Rejected**

- The `?tag=%20` nit — it never returns wrong data, only an empty list; documented instead of changed.
- The suggestion to add a test that duplicates do not count toward the 10-tag limit — noted as a coverage gap, not implemented.

---

## Prompt 4 – Fix the Filter-Change Flicker (found in manual testing)

### Prompt

```text
Bug from manual testing: when I change the tag dropdown the page flickers
and the "Overdue only" label disappears for a moment and comes back.

Investigate before changing anything: read setState() and every CSS rule
keyed on body[data-state]. Report the cause, then make the smallest fix
in frontend/app.js only. The first load and the Retry button must keep
their loading behaviour. Prove the fix in headless Chrome by reading
body.dataset.state, the banner's hidden flag and the filter bar's
vertical position synchronously after dispatching the change event,
against both the old and the new app.js.
```

### AI Response Summary

Cause: every `fetchTasks()` call set the page to the `loading` state, which shows the "Loading tasks…" banner *above* the filter bar (pushing it down ~70px) and dims the board to 50% opacity — correct for the first load, wrong for a filter change when the board already has data. Fix: `fetchTasks({ quiet: true })` skips the loading state; filter changes, post-save refreshes and filtered drag moves use it; initial load and Retry do not. Probe: old code `state=loading, bannerHidden=false, shift=68.8px`; new code `state=ready, bannerHidden=true, shift=0`.

### My Review

**Accepted**

- The quiet refetch and the before/after probe.

**Edited**

- Extended the quiet mode to the post-save refresh as well, since it produced the same flash after closing the modal.

**Rejected**

- Moving the status banner below the filter bar — it would have hidden the symptom without removing the needless loading state.
