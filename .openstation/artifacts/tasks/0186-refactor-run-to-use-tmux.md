---
kind: task
name: 0186-refactor-run-to-use-tmux
type: implementation
status: rejected
assignee: developer
owner: user
parent: "[[0183-native-tmux-integration-for-openstation]]"
created: 2026-03-21
---

# Refactor `openstation run` to Use tmux

Wire the tmux module (0185) into `openstation run` and add new
CLI commands. This is the integration task.

Scoped to CLI + run.py changes only — does not build tmux
primitives (that's 0185).

## Requirements

### Modify `openstation run`

1. Default behavior: spawn tmux session + attach immediately
2. `--detached` / `-d` flag: spawn in background (don't attach)
3. `--attached` remains as backward-compat alias (no-op)
4. When tmux is not available, fall back to current subprocess
   mode with a hint to install tmux
5. Log capture continues to work (`.jsonl` files)
6. Duplicate session detection — warn and offer to attach

### New CLI Commands

7. `openstation attach <task-id>` — attach to running session
8. `openstation ps` — list active openstation tmux sessions
9. `openstation stop <task-id>` — kill a running session

### CLI Registration

10. Register new subcommands in `cli.py` argparse
11. Add help text and usage examples

## Context

- Depends on: 0185 (tmux module)
- Current run implementation: `src/openstation/run.py`
- Current CLI: `src/openstation/cli.py`

## Verification

- [ ] `openstation run --task <id>` spawns tmux session and attaches
- [ ] `openstation run --task <id> -d` spawns in background
- [ ] `openstation run <agent>` works with tmux
- [ ] `--attached` flag still works (backward compat)
- [ ] Falls back to subprocess when tmux not installed
- [ ] `openstation attach <id>` works
- [ ] `openstation ps` lists running sessions
- [ ] `openstation stop <id>` kills session
- [ ] `.jsonl` log capture works in tmux mode
- [ ] Duplicate session warns and offers attach
