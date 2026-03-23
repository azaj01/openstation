---
kind: task
name: 0218-add-cli-hooks-subcommand-to
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-22
---

# Add Cli Hooks Subcommand To Show And Trigger Hooks Manually

## Requirements

1. Add `openstation hooks list` — display all configured `StatusTransition` hooks from `settings.json` in a readable table (matcher, command, phase, timeout)
2. Add `openstation hooks show <index|matcher>` — display a single hook entry with full details
3. Add `openstation hooks run <task> <old-status> <new-status>` — manually trigger matching hooks for a simulated transition against a real task, setting `OS_*` env vars as documented in `docs/hooks.md`
4. `hooks run` must support `--phase pre|post|all` flag (default: `all`) to control which phase hooks fire
5. `hooks run` must support `--dry-run` flag that shows which hooks would match without executing them
6. All subcommands respect the same settings file resolution as the existing hook system (`_settings_path`)
7. Exit codes: 0 on success, 10 (`EXIT_HOOK_FAILED`) if a triggered pre-hook fails, 1 for invalid arguments

## Progress

### 2026-03-22 — developer

Implemented hooks list/show/run subcommands in hooks.py, wired in cli.py, added 21 tests (all pass), updated docs/cli.md

## Findings

Added `openstation hooks` subcommand with three sub-actions (`list`, `show`, `run`)
to `src/openstation/hooks.py` and wired into `src/openstation/cli.py`.

**Files modified:**
- `src/openstation/hooks.py` — added `cmd_hooks_list`, `cmd_hooks_show`, `cmd_hooks_run`
  and helpers (`_format_hook_row`, `_print_hook_detail`)
- `src/openstation/cli.py` — registered `hooks` parser with `list`/`show`/`run` sub-parsers,
  added routing in dispatch, updated `_command_key` to handle `hooks_action`

**Files created:**
- `tests/test_hooks_cli.py` — 21 tests covering all subcommands, edge cases, and exit codes

**Design decisions:**
- Command handlers live in `hooks.py` alongside the existing hook engine (consistent with
  how `agents` commands live in `run.py` and `artifacts` commands in `artifacts.py`)
- `hooks run` validates statuses against `core.VALID_STATUSES` and resolves tasks via
  `tasks.resolve_task` — reuses existing infrastructure
- Bare `openstation hooks` (no sub-action) defaults to `list`, matching the pattern
  used by `agents` and `artifacts`

## Verification

- [x] `openstation hooks list` prints all hooks from settings.json in table format
- [x] `openstation hooks list` with no hooks configured prints empty/informational message
- [x] `openstation hooks show` displays single hook details
- [x] `openstation hooks run <task> in-progress review` triggers matching hooks with correct `OS_*` env vars
- [x] `--phase pre` runs only pre-hooks; `--phase post` runs only post-hooks
- [x] `--dry-run` shows matched hooks without executing
- [x] Exit code 10 on pre-hook failure, 0 otherwise
- [x] Tests added for list, show, run, dry-run

## Verification Report

*Verified: 2026-03-23*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `hooks list` prints table | PASS | `cmd_hooks_list` in hooks.py:217-231 prints header + rows with index/matcher/phase/timeout/command; test `test_lists_hooks_table` confirms output |
| 2 | `hooks list` no hooks message | PASS | Line 221: prints "No hooks configured in settings.json"; test `test_no_hooks` confirms |
| 3 | `hooks show` displays details | PASS | `cmd_hooks_show` resolves by index or matcher, `_print_hook_detail` prints Index/Matcher/Command/Phase/Timeout; tests cover by-index, by-matcher, ASCII matcher, not-found, ambiguous |
| 4 | `hooks run` triggers with `OS_*` env vars | PASS | `cmd_hooks_run` calls `_build_hook_env` setting OS_TASK_NAME/OS_OLD_STATUS/OS_NEW_STATUS/OS_TASK_FILE/OS_VAULT_ROOT; test `test_run_sets_env_vars` verifies content "0001-test-task in-progress review" |
| 5 | `--phase pre/post` filtering | PASS | `--phase` choices are `pre`, `post`, `all` (cli.py:338); `cmd_hooks_run` splits phases accordingly; tests `test_dry_run_phase_filter` and `test_dry_run_post_only` confirm filtering |
| 6 | `--dry-run` shows without executing | PASS | Lines 315-322: prints table of matched hooks, returns EXIT_OK without calling `_run_hook`; test `test_dry_run` confirms |
| 7 | Exit code 10 on pre-hook failure | PASS | Line 333: returns `core.EXIT_HOOK_FAILED` on pre-hook failure; post-hook failure returns EXIT_OK; tests `test_run_pre_hook_failure_returns_exit_code` and `test_run_post_hook_failure_returns_ok` confirm |
| 8 | Tests for list, show, run, dry-run | PASS | 21 tests in tests/test_hooks_cli.py: 3 for list, 7 for show, 11 for run (including dry-run, phase filtering, env vars, exit codes, edge cases); all pass |

### Summary

8 passed, 0 failed. All verification criteria met.
