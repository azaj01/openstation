---
kind: task
name: 0126-worktree-pass-through
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-13
---

# Implement --worktree Pass-Through

Implement the `--worktree` flag on `openstation run` per the
spec at `artifacts/specs/worktree-pass-through.md`. Scoped to
M1 CLI plumbing only — no branch field, no worktree lifecycle
management, no parallel orchestration.

## Requirements

1. Add `--worktree` / `-w` argument to the `run` subparser in `cli.py` using `nargs="?"`, `const=True`, `default=None`
2. Add `worktree` parameter to `build_command()` in `run.py` — insert `--worktree <name>` into the claude command
3. Plumb `worktree` through `cmd_run()`, `_exec_or_run()`, and `run_single_task()` in `run.py`
4. Auto-derive worktree name when `--worktree` is given without a value: task name for `--task` mode, agent name for agent mode
5. Works in all modes: attached, detached, dry-run, by-task, by-agent
6. Update `CLAUDE.md` CLI reference with `--worktree` example

## Verification

- [ ] `--worktree my-name` passes `--worktree my-name` to claude CLI
- [ ] `--worktree` (no value) auto-derives name from task or agent
- [ ] Omitting `--worktree` produces no worktree flag in command
- [ ] `--dry-run` output includes `--worktree` when specified
- [ ] Works in both attached and detached modes
- [ ] `CLAUDE.md` CLI reference updated with worktree example
