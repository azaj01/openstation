---
kind: task
name: 0029-agent-session-command
status: backlog
agent:
owner: user
created: 2026-03-01
---

# CLI feature: open Claude sessions with project agent

## Requirements

- Add a CLI command (or flag in `openstation-run.sh`) that opens
  an interactive Claude Code session pre-loaded with a project's
  agent — equivalent to `claude --agent <name>` but resolved from
  the Open Station agent registry.
- The command should:
  - Accept an agent name and resolve it via the same discovery
    path used by `openstation-run.sh` (installed `.openstation/agents/`
    then source `agents/`).
  - Default to Tier 1 (interactive, `--permission-mode acceptEdits`)
    if no tier is specified.
  - Optionally accept `--task` to pre-load context about a
    specific task into the session prompt.
- This is essentially Tier 1 of `openstation-run.sh` but
  positioned as the primary "start working" command for
  human-in-the-loop sessions.

## Verification

- [ ] Running the command with an agent name opens an interactive
      Claude session with that agent loaded
- [ ] Agent resolution uses the same discovery path as run.sh
- [ ] `--task` flag pre-loads task context into the session
- [ ] Invalid agent names produce a clear error message
