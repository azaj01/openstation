---
kind: task
name: 0146-add-verify-flag-to-openstation
type: feature
status: done
assignee: developer
owner: project-manager
created: 2026-03-17
---

# Add --verify flag to `openstation run`

## Requirements

1. Add `--verify` boolean flag to `openstation run`
2. `--verify` requires `--task` — error if `--task` is not provided
3. Agent resolution order when `--verify` is set:
   - `--agent` flag (explicit override)
   - Task's `owner` frontmatter field
   - Fallback: `project-manager`
4. Launches the resolved agent with `/openstation.verify <task-id>`
   pre-loaded as the command
5. Task must be in `review` status — error early if not
6. Works with `--attached` and `--worktree` flags as usual

## Verification

- [x] `openstation run --task <id> --verify` launches with verify command
- [x] `--verify` without `--task` prints an error
- [x] Agent defaults to task `owner`, overridable with `--agent`
- [x] Falls back to `project-manager` when owner is empty
- [x] Task not in `review` status produces an error
- [x] `--attached` and `--worktree` flags work with `--verify`

## Progress

### 2026-03-17 — developer
> time: 09:26

Implemented --verify flag: CLI arg, run.py verify mode, 8 tests (all 241 pass), docs updated

## Findings

Implemented `--verify` flag for `openstation run` across CLI and run modules.

**Changes:**
- `src/openstation/cli.py` — Added `--verify` flag to run subparser, updated help epilog with verify examples
- `src/openstation/run.py` — Added verify mode in `cmd_run()`: validates `--task` requirement, checks `review` status, resolves agent (agent flag → owner field → `project-manager` fallback), builds `/openstation.verify <task>` prompt. Relaxed agent+task mutual exclusivity when `--verify` is set (needed for `--agent` override)
- `tests/test_cli.py` — 8 new tests in `TestRunVerifyFlag` covering all verification items
- `docs/cli.md` — Documented verify mode, flags, incompatibilities, and examples
- `CLAUDE.md` — Added verify usage to CLI reference and examples

**Design decisions:**
- Verify mode is a separate early-return branch in `cmd_run()`, before the existing by-task/by-agent logic — keeps existing paths untouched
- Agent+task mutual exclusivity check is relaxed only when `--verify` is set, so `openstation run researcher --task 42 --verify` works for explicit agent override
- Both attached and detached modes supported; detached uses `_stream_and_capture` with log file
