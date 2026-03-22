---
kind: task
name: 0201-implement-tmux-session-integration-in
type: implementation
status: backlog
assignee: developer
owner: user
parent: "[[0199-tmux-integration-for-detached-agent]]"
created: 2026-03-21
---

# Implement Tmux Session Integration In Openstation Run

## Requirements

1. Detached `openstation run` wraps agent execution in a named tmux session (`openstation-<task-name>`)
2. Graceful fallback: if tmux is not installed, use current subprocess behavior and emit a stderr warning
3. Handle session name collisions (error or append suffix)
4. Configure remain-on-exit so session persists after agent completion
5. Add `openstation sessions` (or equivalent) to list active Open Station tmux sessions
6. `--attached` mode unchanged — no tmux involvement

## Verification

- [ ] Detached run creates tmux session named `openstation-<task-name>`
- [ ] `tmux attach -t openstation-<task-name>` shows live agent output
- [ ] Missing tmux falls back to subprocess with stderr warning
- [ ] Session name collision is handled gracefully
- [ ] Session persists after agent exit
- [ ] `openstation sessions` lists active sessions
- [ ] `--attached` mode is unaffected
- [ ] Tests pass for new and existing detached-mode behavior
