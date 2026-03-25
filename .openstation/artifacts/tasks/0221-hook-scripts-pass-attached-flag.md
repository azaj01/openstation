---
kind: task
name: 0221-hook-scripts-pass-attached-flag
type: bug
status: verified
assignee: developer
owner: user
created: 2026-03-23
subtasks:
  - "[[0227-auto-verify-hook-times-out]]"
---

# Hook scripts pass --attached flag causing dispatched agents to stall on permissions

## Root Cause

`bin/hooks/auto-verify` and `bin/hooks/auto-start` pass `--attached`
to `openstation run`. Since `os-dispatch` sends these to a background
tmux window, the Claude session starts in interactive mode and blocks
waiting for permission grants that nobody is there to approve.

## Affected Files

- `bin/hooks/auto-verify` (line 37): `openstation run --task "$OS_TASK_NAME" --verify --attached`
- `bin/hooks/auto-start` (line 54): `openstation run --task "$OS_TASK_NAME" --attached`

## Not Affected

- `bin/hooks/auto-commit` — uses `claude -p` directly (autonomous)
- `bin/hooks/auto-accept` — no Claude invocation
- `bin/hooks/suspend` — uses `claude -p` directly (autonomous)

## Requirements

1. Remove `--attached` from the `openstation run` invocation in `bin/hooks/auto-verify`
2. Remove `--attached` from the `openstation run` invocation in `bin/hooks/auto-start`
3. Dispatched agents must run in detached (autonomous) mode — `claude -p` with no interactive prompts

## Verification

- [x] `bin/hooks/auto-verify` dispatch command does not include `--attached`
- [x] `bin/hooks/auto-start` dispatch command does not include `--attached`
- [x] Triggering `openstation hooks run <task> in-progress review` dispatches a non-interactive Claude session in tmux
- [x] Triggering `openstation hooks run <task> backlog ready` dispatches a non-interactive Claude session in tmux

## Verification Report

*Verified: 2026-03-23*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `auto-verify` dispatch does not include `--attached` | PASS | Line 37: `openstation run --task "$OS_TASK_NAME" --verify` — no `--attached` flag |
| 2 | `auto-start` dispatch does not include `--attached` | PASS | Line 54: `openstation run --task "$OS_TASK_NAME"` — no `--attached` flag |
| 3 | `in-progress→review` dispatches non-interactive session | PASS | `auto-verify` calls `os-dispatch` → tmux window; without `--attached`, `openstation run` uses detached mode (`claude -p`) |
| 4 | `backlog→ready` dispatches non-interactive session | PASS | `auto-start` calls `os-dispatch --no-attach` → tmux window; without `--attached`, `openstation run` uses detached mode (`claude -p`) |

### Summary

4 passed, 0 failed. All verification criteria met.
