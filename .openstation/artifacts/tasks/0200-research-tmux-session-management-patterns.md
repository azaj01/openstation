---
kind: task
name: 0200-research-tmux-session-management-patterns
type: research
status: backlog
assignee: researcher
owner: user
parent: "[[0199-tmux-integration-for-detached-agent]]"
created: 2026-03-21
---

# Research Tmux Session Management Patterns

## Requirements

1. Investigate tmux session lifecycle management (create, attach, detach, destroy) from a Python subprocess
2. Evaluate alternatives: tmux vs screen vs native PTY — recommend one with rationale
3. Determine how to detect tmux availability at runtime
4. Identify session naming constraints and collision handling (e.g., what if a session with the same name already exists)
5. Research how to keep a session alive after the child process exits (remain-on-exit, hooks)
6. Propose minimal UX for listing/attaching to Open Station sessions
7. Research tmux logging strategies for capturing agent output:
   - `capture-pane -p -S -` — dump full scrollback to file after the fact
   - `pipe-pane 'cat >> file.log'` — stream live output to a log file
   - `tmux-logging` plugin — keybinding-driven logging and screen capture
   - Evaluate which approach works best for `.jsonl` log capture in detached mode

## Verification

- [ ] Research artifact produced in `artifacts/research/`
- [ ] Covers tmux vs alternatives with a clear recommendation
- [ ] Documents tmux session lifecycle API (create/attach/destroy) from Python
- [ ] Addresses session naming collisions and remain-on-exit behavior
- [ ] Proposes a concrete UX for session listing
- [ ] Covers tmux logging approaches (capture-pane, pipe-pane, plugins) with recommendation for agent output capture
