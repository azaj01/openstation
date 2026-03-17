---
kind: task
name: 0153-add-force-flag-to-status
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-17
---

# Add --force Flag to Status Command

## Requirements

1. Add a `--force` / `-f` flag to `openstation status` that
   bypasses transition validation, allowing any status → any
   status move.
2. When `--force` is used, skip the `validate_transition()` check
   but still update frontmatter normally, run hooks, and trigger
   parent auto-promotion.
3. Print a warning when forcing an invalid transition:
   `warning: forced transition <old> → <new> (not a valid lifecycle transition)`.
4. The interactive picker (no `new_status` arg) should show **all**
   statuses when `--force` is set, not just valid transitions.
5. Update `docs/cli.md` with the new flag.

## Findings

Added `--force` / `-f` flag to `openstation status`. Changes:

- **`src/openstation/cli.py`** — added `-f`/`--force` argument to
  the `status` subparser.
- **`src/openstation/tasks.py`** — `cmd_status()` reads the `force`
  flag via `getattr(args, "force", False)`. When force is set and
  the transition is invalid, it prints a warning via `core.warn()`
  instead of returning an error. The `_interactive_status_picker()`
  accepts a `force` keyword; when True it shows all statuses
  (minus current) instead of only valid transitions.
- **`docs/cli.md`** — added Flags table and force examples to the
  `status` section.
- **`tests/test_cli.py`** — 6 new tests in `TestForceFlag` covering
  invalid forced transitions, warning output, valid-with-force (no
  warning), `-f` short form, picker showing all statuses, and hooks
  still firing.

## Progress

- 2026-03-17: Implemented --force flag across CLI, tasks module,
  docs, and tests. All 54 status-related tests pass.

## Verification

- [x] `openstation status <task> backlog --force` works from any status
- [x] Warning is printed when forcing an invalid transition
- [x] Valid transitions with `--force` work normally (no warning)
- [x] Interactive picker shows all statuses when `--force` is set
- [x] Hooks still fire on forced transitions
- [x] `docs/cli.md` documents the flag
