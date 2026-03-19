---
kind: task
name: 0144-post-transition-hooks
type: feature
status: done
assignee: developer
owner: user
parent: "[[0134-task-lifecycle-hooks]]"
created: 2026-03-16
---

# Post-Transition Hooks

Add a `post` phase to the hooks engine so commands can run
**after** `update_frontmatter()` succeeds. Currently all hooks
are pre-transition — they fire before the status is written.
Post-hooks enable workflows like auto-commit, notifications,
and archival that need the task file to reflect the new status.

## Requirements

1. Extend `settings.json` schema to support a `phase` field on
   hook entries: `"pre"` (default, current behavior) or `"post"`
2. Post-hooks run after `update_frontmatter()` and
   `auto_promote_parent()` succeed
3. Post-hook failure does **not** roll back the transition — the
   status change is already persisted
4. Post-hook failure is reported as a warning (non-zero exit
   from `openstation status` is acceptable but not required)
5. Environment variables are the same as pre-hooks
6. Declaration order is preserved within each phase
7. Update `docs/hooks.md` with the new phase option

## Findings

Added `phase` field support to the hooks engine. Changes:

- **`src/openstation/hooks.py`** — `match_hooks()` now accepts a
  `phase` keyword (`"pre"` or `"post"`, default `"pre"`).
  `run_matched()` accepts the same keyword; post-hook failures
  emit warnings but always return `None`. Extracted
  `_build_hook_env()` helper to avoid duplication.
- **`src/openstation/tasks.py`** — `cmd_status()` now makes two
  `run_matched()` calls: `phase="pre"` before `update_frontmatter()`
  (existing behavior) and `phase="post"` after
  `auto_promote_parent()`.
- **`docs/hooks.md`** — Added `phase` field to schema table,
  updated timing diagram to show both phases, added post-hook
  failure semantics, updated examples (notify-on-completion now
  uses `phase: "post"`), updated architecture section.
- **`tests/test_hooks.py`** — Added `TestPhaseFiltering` (5 tests)
  and `TestPostHooks` (5 tests) covering phase filtering,
  post-hook execution, failure semantics, env vars, and backward
  compatibility. All 36 tests pass.

Design decisions:
- Post-hook failures continue running remaining post-hooks (unlike
  pre-hooks which abort on first failure). This matches the
  "best-effort" semantics for post-hooks.
- Invalid `phase` values default to `"pre"` for safety.

## Verification

- [x] `phase: "post"` hooks run after the status is written
- [x] `phase: "pre"` (or omitted) hooks behave as before
- [x] Post-hook failure does not revert the transition
- [x] Env vars are correct in post-hooks (new status matches file)
- [x] Docs updated with phase field and examples
- [x] Tests cover both phases
