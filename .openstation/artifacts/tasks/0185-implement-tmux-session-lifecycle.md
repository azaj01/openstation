---
kind: task
name: 0185-implement-tmux-session-lifecycle
type: implementation
status: rejected
assignee: developer
owner: user
parent: "[[0183-native-tmux-integration-for-openstation]]"
created: 2026-03-21
---

# Implement tmux Session Lifecycle

Build the core tmux primitives as a reusable module. This is the
foundation that `openstation run` will use.

Scoped to the tmux module only — does not modify `run.py` or
CLI commands (that's 0186).

## Requirements

1. Create `src/openstation/tmux.py` (or as specified by 0184 spec)
2. Implement core functions:
   - `spawn(name, command, cwd)` — create a tmux session
   - `attach(name)` — attach to an existing session
   - `list_sessions(prefix)` — list sessions matching prefix
   - `kill_session(name)` — stop a session
   - `session_exists(name)` — check if session is running
   - `is_available()` — check if tmux is installed
3. Session naming follows the convention from 0184 spec
4. All functions handle errors gracefully (tmux not found,
   session doesn't exist, duplicate name)
5. Unit tests for all public functions

## Context

- Depends on: 0184 (spec) — must be done first
- Blocked by: nothing else
- Blocks: 0186 (run refactor)

## Verification

- [ ] `tmux.py` module exists with all required functions
- [ ] `is_available()` correctly detects tmux presence
- [ ] `spawn()` creates a named tmux session
- [ ] `attach()` connects to an existing session
- [ ] `list_sessions()` filters by prefix
- [ ] `kill_session()` terminates a session
- [ ] `session_exists()` returns correct boolean
- [ ] Duplicate session name raises clear error
- [ ] Missing tmux raises clear error
- [ ] Unit tests pass
