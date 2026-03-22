---
kind: task
name: 0199-tmux-integration-for-detached-agent
type: feature
status: backlog
assignee: 
owner: user
created: 2026-03-21
subtasks:
  - "[[0200-research-tmux-session-management-patterns]]"
  - "[[0201-implement-tmux-session-integration-in]]"
  - "[[0202-document-tmux-integration]]"
---

# Tmux Integration For Detached Agent Runs

## Requirements

1. `openstation run` detached mode launches the agent process inside a named tmux session instead of (or in addition to) a raw subprocess
2. Session naming convention: `openstation-<task-name>` (e.g., `openstation-0042-add-login-page`)
3. `openstation run --task <id>` in detached mode creates a tmux session; user can `tmux attach -t <name>` to observe live output
4. If tmux is not installed, fall back to current subprocess behavior with a warning
5. Add a CLI command or flag to list active tmux sessions: e.g., `openstation sessions` or `openstation run --list`
6. When the agent completes, the tmux session remains open (configurable) so the user can review final output before it closes

## Verification

- [ ] Detached `openstation run --task <id>` creates a tmux session named `openstation-<task-name>`
- [ ] User can `tmux attach -t openstation-<task-name>` and see live agent output
- [ ] When tmux is not installed, detached mode falls back to current behavior with a stderr warning
- [ ] `openstation sessions` (or equivalent) lists active Open Station tmux sessions
- [ ] Session persists after agent completion; user can review output
- [ ] Existing `--attached` mode is unaffected

## Subtasks

1. Research tmux session management patterns
2. Implement tmux session integration in `openstation run`
3. Document tmux integration in CLI docs
