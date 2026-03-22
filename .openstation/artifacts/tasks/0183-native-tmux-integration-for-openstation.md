---
kind: task
name: 0183-native-tmux-integration-for-openstation
type: feature
status: rejected
assignee: 
owner: user
created: 2026-03-21
subtasks:
  - "[[0184-spec-tmux-session-management]]"
  - "[[0185-implement-tmux-session-lifecycle]]"
  - "[[0186-refactor-run-to-use-tmux]]"
  - "[[0187-document-tmux-integration]]"
---

# Native tmux Integration for `openstation run`

Replace the current attached/detached dichotomy with native tmux
session management. Every `openstation run` spawns a tmux session
— users choose whether to attach immediately or not.

## Requirements

### Core Behavior

1. `openstation run --task <id>` spawns a tmux session named
   `os-<task-id>` (e.g., `os-0042`) running Claude Code inside it
2. Without `--detached`, attach to the session immediately
3. With `--detached` (or `-d`), spawn in background — user
   attaches later
4. `openstation run <agent>` (no task) spawns `os-<agent>` session

### Session Management Commands

5. `openstation attach <task-id>` — shortcut for
   `tmux attach -t os-<task-id>`
6. `openstation ps` — list running openstation tmux sessions
   (filter `tmux ls` for `os-` prefix)
7. `openstation stop <task-id>` — kill the tmux session

### Backward Compatibility

8. `--attached` flag remains as an alias (no-op since attach is
   now the default)
9. Detached mode (current `--output-format stream-json` subprocess)
   still works as fallback when tmux is not installed
10. Log capture to `.jsonl` continues to work in tmux mode

### Edge Cases

11. If a session named `os-<id>` already exists, warn and offer
    to attach instead of spawning a duplicate
12. Graceful behavior when tmux is not installed — fall back to
    current subprocess mode with a hint to install tmux

## Subtasks

### P0 — Design

1. **Spec tmux session management** — Design the tmux integration:
   session naming, lifecycle, CLI surface changes, fallback
   behavior, log capture strategy.

### P1 — Implementation

2. **Implement tmux session lifecycle** — Core tmux primitives:
   spawn session, attach, list, stop. Reusable module.
3. **Refactor run to use tmux** — Wire tmux session lifecycle
   into `openstation run`, replace current detached subprocess
   mode, add `attach`/`ps`/`stop` CLI commands.

### P2 — Documentation

4. **Document tmux integration** — Update `docs/cli.md`,
   `docs/worktrees.md`, and agent skills with tmux workflows.

## Verification

- [ ] `openstation run --task <id>` opens a tmux session and attaches
- [ ] `openstation run --task <id> -d` spawns in background
- [ ] `openstation attach <id>` connects to running session
- [ ] `openstation ps` lists active agent sessions
- [ ] `openstation stop <id>` kills a session
- [ ] Falls back gracefully when tmux is not installed
- [ ] Duplicate session name is handled (warn + attach)
- [ ] `.jsonl` log capture works in tmux mode
- [ ] `--attached` flag still works (backward compat)
