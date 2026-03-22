---
kind: task
name: 0184-spec-tmux-session-management
type: spec
status: rejected
assignee: architect
owner: user
parent: "[[0183-native-tmux-integration-for-openstation]]"
created: 2026-03-21
---

# Spec: tmux Session Management

Design the tmux integration for `openstation run`. This spec
gates all implementation work.

## Requirements

1. **Session naming convention** — define the `os-<id>` naming
   scheme, collision handling, and character constraints
2. **Session lifecycle** — define spawn, attach, detach, list,
   stop operations and how they map to tmux commands
3. **CLI surface changes** — specify new commands (`attach`,
   `ps`, `stop`) and changes to existing `run` flags
4. **Log capture in tmux mode** — how `.jsonl` logging works
   when Claude runs inside tmux (pipe-tee, tmux pipe-pane, or
   other approach)
5. **Fallback behavior** — define what happens when tmux is not
   installed (graceful degradation to current subprocess mode)
6. **Worktree interaction** — how tmux sessions work with
   `--worktree` flag (session CWD, vault resolution)
7. **Module layout** — propose where tmux code lives in the
   `src/openstation/` package

## Context

- Current run implementation: `src/openstation/run.py`
- Current modes: attached (interactive subprocess) vs detached
  (stream-json subprocess with log capture)
- The spec should unify these into tmux-first with subprocess
  as fallback

## Verification

- [ ] Spec covers session naming and collision handling
- [ ] Spec covers all lifecycle operations (spawn, attach, list, stop)
- [ ] Spec covers CLI surface (new commands + flag changes)
- [ ] Spec covers log capture strategy in tmux mode
- [ ] Spec covers tmux-not-installed fallback
- [ ] Spec covers worktree interaction
- [ ] Spec proposes module layout
