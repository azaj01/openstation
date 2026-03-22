---
kind: task
name: 0209-implement-autonomous-chaining-hooks-and
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0204-hook-based-autonomous-task-chaining]]"
created: 2026-03-22
---

# Implement Autonomous Chaining Hooks And Tmux Dispatch

## Requirements

Implement the autonomous chaining system designed in
[[artifacts/specs/hook-based-autonomous-chaining]].

### Deliverables

1. **`bin/os-dispatch`** — shared tmux dispatch helper
   - Spawns a command in a named tmux window with `CLAUDECODE` cleared
   - Falls back to nohup when tmux is unavailable
   - Passes `OS_HOOK_DEPTH` to spawned processes
   - See spec §1 for full script and interface

2. **`bin/hooks/auto-start`** — `*→ready` post-hook
   - Checks `autonomous.enabled` in settings
   - Checks `OS_HOOK_DEPTH` against max
   - Checks task has an assignee
   - Dispatches `openstation run --task $OS_TASK_NAME --attached`
   - See spec §2.1

3. **`bin/hooks/auto-verify`** — `*→review` post-hook
   - Same guards as auto-start (opt-in, depth)
   - Dispatches `openstation run --task $OS_TASK_NAME --verify --attached`
   - See spec §2.2

4. **`bin/hooks/auto-accept`** — `*→verified` post-hook
   - Same guards (opt-in, depth)
   - Runs `openstation status $OS_TASK_NAME done` inline (no tmux needed)
   - See spec §2.3

5. **Update `settings.json`** — add the three hooks and `autonomous` config
   - See spec §6 for full configuration
   - `autonomous.enabled` defaults to `false`

### Testing

- Test `os-dispatch` in both tmux and non-tmux environments
- Test each hook script with the required env vars
- Test opt-in gate: hooks no-op when `autonomous.enabled` is false
- Test depth guard: hooks no-op when depth exceeds max
- Test full chain end-to-end: promote a task to ready → verify it chains through to done

### Reference

- Spec: [[artifacts/specs/hook-based-autonomous-chaining]]
- Research: [[artifacts/research/nested-claude-instance-limitation]]

## Verification

- [x] `bin/os-dispatch` exists, is executable, spawns tmux window or falls back to nohup
- [x] `bin/hooks/auto-start` dispatches on `*→ready` when autonomous is enabled
- [x] `bin/hooks/auto-verify` dispatches on `*→review` when autonomous is enabled
- [x] `bin/hooks/auto-accept` transitions on `*→verified` when autonomous is enabled
- [x] All hooks no-op when `autonomous.enabled` is false
- [x] All hooks no-op when `OS_HOOK_DEPTH` exceeds max
- [x] `auto-start` no-ops when task has no assignee

## Verification Report

*Verified: 2026-03-22*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `bin/os-dispatch` exists, executable, tmux + nohup fallback | PASS | File has `+x`, tmux branch lines 13-17, nohup fallback lines 18-24. 3 tests pass. |
| 2 | `auto-start` dispatches on `*→ready` | PASS | Registered in settings.json, dispatches via `os-dispatch` line 53-54. |
| 3 | `auto-verify` dispatches on `*→review` | PASS | Registered in settings.json, dispatches with `--verify` line 36-37. |
| 4 | `auto-accept` transitions on `*→verified` | PASS | Runs `openstation status $OS_TASK_NAME done` inline, line 36. |
| 5 | All hooks no-op when `autonomous.enabled` is false | PASS | All 3 hooks check and exit 0. All `test_noop_when_autonomous_disabled` pass. |
| 6 | All hooks no-op when depth exceeds max | PASS | All 3 hooks guard on `DEPTH >= MAX_DEPTH`. All tests pass. |
| 7 | `auto-start` no-ops when no assignee | PASS | Assignee guard lines 37-50, `test_noop_when_no_assignee` passes. |

### Summary

7 passed, 0 failed. All verification criteria met.
