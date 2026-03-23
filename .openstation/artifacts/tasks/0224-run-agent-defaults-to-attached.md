---
kind: task
name: 0224-run-agent-defaults-to-attached
status: done
type: feature
assignee: developer
owner: user
---

# By-agent run defaults to attached (interactive) mode

## Context

`openstation run <agent_name>` currently has two modes:
- **Attached** (`--attached`): starts an interactive session
  with no prompt — the agent just starts.
- **Detached** (default): injects `"Execute your ready tasks."`
  as a `-p` prompt and auto-executes tasks.

The detached by-agent behavior is unwanted. By-agent mode should
just start the agent interactively — no auto task execution.

## Requirements

- [ ] `os run <agent_name>` defaults to attached (interactive)
  mode — equivalent to today's `--attached` behavior
- [ ] Remove the detached by-agent code path (the
  `prompt = "Execute your ready tasks."` branch at ~line 790
  in `src/openstation/run.py`)
- [ ] `--attached` flag still works on by-agent but is now a
  no-op (already the default) — no error, just redundant
- [ ] Detached-only flags (`--budget`, `--turns`, `--max-tasks`,
  `--quiet`, `--json`) emit a warning or error when used with
  by-agent mode (since there's no detached by-agent anymore)
- [ ] `--dry-run` still works — prints the command that would
  be `execvp`'d
- [ ] By-task mode (`--task`) is unchanged — still supports both
  attached and detached
- [ ] Update CLI docs in `.openstation/docs/cli.md` to reflect
  the new default

## Findings

Removed the detached by-agent code path from `src/openstation/run.py`.
By-agent mode now always uses the attached (interactive) path via
`os.execvp`. Key changes:

- **`run.py`**: Added `is_by_agent` / `effectively_attached` flags so
  incompatibility checks apply to both explicit `--attached` and
  by-agent mode. Replaced the entire by-agent else-branch: removed the
  `prompt = "Execute your ready tasks."` detached path and the
  `if attached:` conditional — the code now unconditionally builds an
  attached command.
- **Tests**: Updated 3 existing tests (`test_by_agent_detached_dry_run`
  → `test_by_agent_dry_run`, `test_by_agent_custom_budget_turns` →
  warns, `test_by_agent_dry_run_json` → errors). Added 2 new tests
  (`test_by_agent_quiet_errors`, `test_by_agent_max_tasks_warns`).
  All 283 tests pass.
- **CLI docs**: Updated modes, incompatibilities table, and examples
  in `docs/cli.md`.

## Progress

- 2026-03-23 — Implemented by-agent attached default. Removed detached
  by-agent code path. Updated tests (283 pass). Updated CLI docs.

## Verification

- [x] `os run researcher` starts an interactive session (no
  task execution prompt)
- [x] `os run researcher --attached` behaves identically
- [x] `os run researcher --dry-run` prints the attached command
- [x] `os run --task 0042` still works in detached mode
- [x] `os run --task 0042 --attached` still works in attached mode
- [x] Existing tests pass; new tests cover the changed default

## Verification Report

*Verified: 2026-03-23*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `os run researcher` starts interactive session | PASS | By-agent else-branch (line 744–787) unconditionally calls `build_command(..., attached=True)` then `os.execvp`. No `-p` prompt, no detached path. `"Execute your ready tasks"` string fully removed from `src/`. |
| 2 | `os run researcher --attached` behaves identically | PASS | `effectively_attached = attached or is_by_agent` (line 635) — both paths converge. Test `test_by_agent_attached_flag_is_noop` confirms identical output. |
| 3 | `os run researcher --dry-run` prints attached command | PASS | Test `test_by_agent_dry_run` asserts `--agent researcher`, `--allowedTools`, and absence of `--max-budget-usd`, `--max-turns`, `--output-format`, `-p`. |
| 4 | `os run --task 0042` still works in detached mode | PASS | By-task path (`_exec_or_run`, line 740) unchanged — `attached=False` default invokes `build_command` without `attached=True`. Test `test_by_task_dry_run` confirms. |
| 5 | `os run --task 0042 --attached` still works in attached mode | PASS | `_exec_or_run` line 356 checks `if attached:` and uses `os.execvp`. Path unchanged from before. |
| 6 | Existing tests pass; new tests cover changed default | PASS | 7 by-agent tests exist: `test_by_agent_dry_run`, `test_by_agent_attached_flag_is_noop`, `test_by_agent_custom_budget_turns_warns`, `test_by_agent_with_quoted_tools`, `test_by_agent_quiet_errors`, `test_by_agent_max_tasks_warns`, `test_by_agent_dry_run_json_errors`. New tests cover `--quiet` error, `--max-tasks` warning, and `--json` error. |

### Summary

6 passed, 0 failed. All verification criteria satisfied.
