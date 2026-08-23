# Personal AI Playbook

## When I Reach for AI First

I use AI first when I need to understand code I did not write recently, when I want a second opinion on a change I already made, or when the task has a well-known shape such as a CI workflow, a Dockerfile, or a test that mirrors an existing one. During this course, the most useful prompts were the ones that asked Claude Code to inspect the project before changing anything — the first prompt of the mid-course project found the exact-key response test and the `exclude_unset` behaviour that shaped both features — and the review prompts, which found the comma-in-tag bug that none of my 43 tests covered. I also use AI to turn a vague idea into user stories with acceptance criteria and numbered questions, but I answer the questions myself.

## When I Do Not Reach for AI First

I do not reach for AI first when I cannot state the expected behaviour, because the prompt would only encode my confusion: the `tags: null` gap in the mid-course project came from a prompt that said "no special-casing" before I had thought about what `null` should do. I also do not start with AI for UI feel and layout problems — the filter-change flicker was obvious in the browser and invisible to every test, so I read `setState()` myself before asking for a fix. Anything touching secrets, CORS or permissions I read first so I understand the blast radius, and when the point of the task is to learn something, such as how Pydantic validators work, I write the first version by hand.

## My Non-Negotiables

- Never give AI passwords, API keys, tokens, `.env` values, credentials, or personal/customer data. Sample data must be obviously fake.
- Every prompt names the files it may change. `app/` and `frontend/` stay frozen unless the change is a bug fix or security fix I can explain.
- Run the tests before and after every change and record the real numbers; "should pass" is not a result.
- Never weaken a check to get green: no `continue-on-error`, `|| true`, skipped tests, loosened assertions, or broadened CORS.
- If I cannot explain a line, it does not ship. Unexplained configuration is the same as unexplained code.

## My Review Rules

I read the whole diff, not the summary, because the summary describes what the agent meant to do and the diff shows what it did. I grade every review finding — Useful, Noise or Wrong for code review; Valid, False Positive or Noise for security — and write the reason next to the grade. Before fixing anything I reproduce it with a failing test, a `curl`, or a headless-browser probe, then fix, then re-run. I also check that a break test actually changed the code (`git diff --stat`) before trusting a red/green flip, because one of mine passed for the wrong reason. Rejecting is a normal outcome: I rejected a "should-fix" about a board wipe on a failed refetch because it was pre-existing behaviour and the fix would have duplicated server logic in the browser, and I rejected patch-pinning Python in the final project for the reasons recorded in `docs/final-ai-review.md`.

## What I Am Still Figuring Out

I am still deciding how much of a prompt log is worth keeping in a real repository; the full log helped the course grade but a short decision record would probably be enough for a team. I also want to learn when a self-reported deviation from an agent ("I also changed the empty-state text") should be accepted as-is and when it should be re-prompted. In a team I would want an agreed `AGENTS.md` plus a clear rule for how AI-assisted changes are labelled in commits and pull requests.

## Decision Card

| Situation | My Rule |
|---|---|
| New feature | Inspect the project first, write user stories and numbered questions, then one focused prompt per layer (model, storage, route, tests, UI), then a review prompt and a break test. |
| Code review | Ask for a handful of comments on one diff, grade each with a reason, and fix only the useful ones. |
| Debugging | Reproduce with a test or `curl`, read the code path myself, then ask for the smallest fix in one named file. |
| Infrastructure | Let AI draft CI and Docker files, then prove them with real commands: build, run, `curl /health`, check the user and the file list inside the container. |
| Never paste | Secrets, tokens, passwords, `.env` values, credentials, production logs, or personal/customer data. |
| One rule | Evidence before claims — a number, a command, or a diff, or it did not happen. |
