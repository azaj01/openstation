---
kind: task
name: 0139-interactive-status-picker-for-openstation
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-15
---

# Interactive Status Picker

When `openstation status <task>` is run without a target status,
show an interactive radio-button menu of valid transitions from
the task's current status. Must work in both terminal and Claude
agent sessions.

## Requirements

1. Make `new_status` argument optional in `cmd_status()` — when
   omitted, launch interactive picker
2. Query `VALID_TRANSITIONS` in `core.py` to compute valid
   targets from the task's current status
3. Display a radio-button / arrow-key selector in the terminal
   (e.g. `simple-term-menu` or `inquirer`)
4. Highlight or label the current status so the user knows where
   they are
5. Must render correctly inside a Claude Code session (agent
   tools like Bash can display terminal UI)
6. If no valid transitions exist (e.g. status `done`), print a
   message and exit cleanly
7. Non-interactive fallback: if stdin is not a TTY, require the
   positional argument as today (no breaking change)

## Context

- `VALID_TRANSITIONS` and `VALID_STATUSES` are in `core.py`
- `cmd_status()` is in `cli.py` (handles the `status` subcommand)
- Adding a lightweight dependency is fine

## Verification

- [x] `openstation status <task>` (no status arg) shows picker
- [x] Only valid transitions from current status are listed
- [x] Current status is visually indicated
- [x] Selection applies the transition correctly
- [x] Works in a normal terminal session
- [x] ~~Works inside a Claude Code Bash tool session~~ N/A — Bash tool is non-interactive; agents use explicit args
- [x] Non-TTY fallback still requires positional arg
- [x] `done`/terminal statuses show "no transitions" message

## Findings

Implemented the interactive status picker with a two-tier approach:

1. **Primary: `simple-term-menu`** — Arrow-key navigation with cyan
   highlight, status bar showing current status. Added as a project
   dependency in `pyproject.toml`.

2. **Fallback: numbered picker** — If `simple-term-menu` fails (e.g.
   dumb terminal), falls back to a `1) option` numbered list with
   bold current-status label.

3. **Non-TTY guard** — When `sys.stdin.isatty()` is False and no
   `new_status` argument is given, prints an error and exits with
   `EXIT_USAGE`. Explicit status argument always works regardless
   of TTY state.

### Files changed

- `src/openstation/tasks.py` — Split `_interactive_status_picker` into
  `_term_menu_picker` (simple-term-menu) and `_numbered_picker`
  (fallback). Added `sys.stdin.isatty()` check in `cmd_status()`.
- `pyproject.toml` — Added `simple-term-menu>=1.6` dependency.
- `tests/test_cli.py` — Rewrote `TestInteractiveStatusPicker` with
  15 tests covering: picker invocation, transitions, cancellation,
  non-TTY fallback, numbered picker edge cases, and `allowed_from`
  correctness.

## Progress

### 2026-03-15 — developer
> worktree: 0139-interactive-status-picker-for-openstation

Implemented interactive status picker with simple-term-menu,
numbered fallback, non-TTY guard. All 233 tests pass (15 new
picker tests + 218 existing).
