---
kind: task
name: 0136-hooks-implementation-implement-hooks-in
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0134-task-lifecycle-hooks]]"
created: 2026-03-14
---

# Hooks Implementation — Implement Hooks In Cli

## Requirements

1. Implement hook configuration loading from the settings file per the spec from `0135-hooks-spec-design-configuration-schema`
2. Add hook engine: match transitions, execute commands with env vars, enforce timeouts
3. Integrate hook execution into `openstation status` command — fire hooks on successful transition
4. Abort transition and report error if a hook command fails (non-zero exit)
5. Add tests for hook matching, execution, failure handling, and timeout

## Progress

### 2026-03-15 — developer

Implemented hooks per `artifacts/specs/task-lifecycle-hooks.md`.
Created `src/openstation/hooks.py` with `load_hooks`, `match_hooks`,
`run_matched`. Added `EXIT_HOOK_FAILED = 10` to `core.py`. Integrated
pre-transition hook execution into `cmd_status()` in `tasks.py`.
Wrote 26 tests covering loading, matching, execution, env vars,
ordering, failure abort, and timeout. All 324 tests pass.

## Findings

Implemented the hooks engine in three files:

- **`src/openstation/hooks.py`** (new) — Three public functions:
  `load_hooks` reads `StatusTransition` entries from `settings.json`,
  `match_hooks` filters by `old→new` pattern with `*` wildcards,
  `run_matched` orchestrates load→match→execute with env vars and
  timeout enforcement. Uses `subprocess.Popen` with `wait(timeout=)`
  and SIGTERM→SIGKILL escalation.

- **`src/openstation/core.py`** — Added `EXIT_HOOK_FAILED = 10`.

- **`src/openstation/tasks.py`** — Inserted hook call in `cmd_status()`
  between transition validation and `update_frontmatter()`. If any
  hook fails, the transition aborts and the task file is unchanged.

- **`tests/test_hooks.py`** (new) — 26 tests across 4 classes:
  `TestLoadHooks` (8), `TestMatchHooks` (8), `TestRunMatched` (8),
  `TestCLIIntegration` (2).

## Verification

- [x] Hook config is loaded from settings file
- [x] `openstation status` fires matching hooks on transitions
- [x] Env vars (task name, old/new status, path) are passed to hook commands
- [x] Failed hooks abort the transition with clear error output
- [x] Multiple hooks run in declaration order
- [x] Timeout kills long-running hooks
- [x] Tests pass
