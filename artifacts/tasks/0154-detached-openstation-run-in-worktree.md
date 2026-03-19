---
kind: task
name: 0154-detached-openstation-run-in-worktree
type: bug
status: failed
assignee: developer
owner: user
created: 2026-03-17
subtasks:
  - "[[0161-update-run-prompts-to-include]]"
---

# `openstation run` in Worktree Executes in Main Repo

## Problem

When `openstation run` is invoked from a worktree directory, the
spawned Claude session runs in the main repo root instead of the
worktree. This affects both attached and detached modes.

**Root cause:** `find_root()` correctly resolves the vault root
(main repo) for artifact/task discovery, but `cmd_run` uses that
same `root` as the `cwd` for Claude execution — via
`os.chdir(root)` and passing `root` to `_stream_and_capture`.
The original CWD (the worktree) is lost.

**Desired behavior:** Two separate concerns:
- **Vault operations** (task discovery, log paths, artifact reads)
  → use `root` from `find_root()` (already correct)
- **Claude execution** (subprocess cwd, `os.execvp` cwd) → use
  the original CWD (the worktree the user is in)

## Requirements

1. Capture the original CWD at the start of `cmd_run`, before
   `find_root()` resolves it away.
2. Use the original CWD as the working directory for all Claude
   execution paths — both `os.chdir` before `os.execvp` (attached)
   and the `cwd` param to `_stream_and_capture` (detached).
3. Continue using `root` for vault operations: task resolution,
   log directory paths, artifact paths.
4. When run from the main repo (not a worktree), behavior is
   unchanged — original CWD and `root` are the same.

### Affected code paths in `run.py`

All six sites that set `cwd` to `root`:
- `_exec_or_run` line 399: `os.chdir(str(root))` — detached by-task
- `_exec_or_run` line 400: `_stream_and_capture(cmd, root, ...)` — detached by-task
- `run_single_task` line 305: `_stream_and_capture(cmd, root, ...)` — subtask dispatch
- `cmd_run` line 616: `os.chdir(str(root))` — verify detached
- `cmd_run` line 617: `_stream_and_capture(cmd, root, ...)` — verify detached
- `cmd_run` line 767: `os.chdir(str(root))` — by-agent attached
- `cmd_run` line 791: `os.chdir(str(root))` — by-agent detached

## Findings

Separated Claude execution CWD from vault root in `run.py` by
capturing `exec_cwd = Path.cwd()` at the top of `cmd_run` and
threading it through to all execution sites.

### Changes

**`src/openstation/run.py`** — All seven sites updated:
- `cmd_run`: Captures `exec_cwd = Path.cwd()` at entry, passes
  it to `_exec_or_run` and `run_single_task` via new `exec_cwd`
  kwarg. Verify-detached and by-agent paths use `exec_cwd`
  directly for `os.chdir()` and `_stream_and_capture()`.
- `_exec_or_run`: New `exec_cwd` param; detached path uses
  `exec_cwd` for both `os.chdir()` and `_stream_and_capture()`.
- `run_single_task`: New `exec_cwd` param; uses it as
  `_stream_and_capture()` cwd (falls back to `root` when None).

Vault operations (log dir creation, task resolution, artifact
paths) remain unchanged — they still use `root`.

**`tests/test_cli.py`** — Added
`test_by_task_detached_uses_original_cwd` in `TestRunClaude`:
creates a subdirectory, runs `openstation run --task` from it,
and verifies the mock claude subprocess received that subdirectory
as its CWD (not the vault root).

## Progress

- 2026-03-18 — Fixed all 7 execution sites in `run.py` to use
  original CWD instead of vault root. Added test. All 418 tests
  pass.

## Verification

- [x] `openstation run --task <id>` (detached) from a worktree directory runs Claude in that worktree
- [x] `openstation run --task <id> --attached` from a worktree runs Claude in that worktree
- [x] `openstation run <agent> --attached` from a worktree runs Claude in that worktree
- [x] `openstation run --task <id> --verify` from a worktree runs Claude in that worktree
- [x] `openstation run --task <id>` from the main repo still works correctly (no regression)
- [x] Vault operations (task discovery, log paths) still resolve to the main repo root
