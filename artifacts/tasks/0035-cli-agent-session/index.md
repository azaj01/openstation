---
kind: task
name: 0035-cli-agent-session
status: ready
agent: developer
owner: manual
created: 2026-03-03
---

# CLI Command — Open Agent Session

## Requirements

Add a subcommand to the `openstation` CLI that opens an interactive
Claude Code session with a selected agent. This is a convenience
wrapper around `claude --agent <name>` with short aliases and
optional permission mode flags.

1. **Command syntax:**
   ```
   openstation agent <name-or-alias> [OPTIONS]
   ```
   Shorthand: `openstation -a <name-or-alias> [OPTIONS]`

2. **Agent resolution** — accept full agent names (`project-manager`)
   or short aliases (`pm`, `dev`, `res`, `auth`, `arch`). Map aliases
   to canonical agent names using the specs in `agents/`.

3. **Permission modes** — support flags for Claude Code permission
   modes:
   - `--dangerous` / `-d` — launch with `--dangerously-skip-permissions`
   - `--accept-edits` / `-e` — launch with `--permission-mode acceptEdits`
   - Default (no flag) — standard interactive mode

4. **Agent discovery** — scan `agents/` (source repo) or
   `.openstation/agents/` (installed) for available agent specs.
   Validate the requested agent exists before launching.

5. **Session launch** — construct and exec the `claude --agent`
   invocation. Replace the shell process (exec) for clean signal
   propagation.

6. **List agents** — `openstation agent --list` prints available
   agents with their aliases.

## Verification

- [ ] `openstation agent project-manager` opens a Claude session with the PM agent
- [ ] `openstation -a pm -d` opens a session with dangerously-skip-permissions
- [ ] `openstation -a dev --accept-edits` opens with acceptEdits mode
- [ ] `openstation agent --list` shows available agents and aliases
- [ ] Invalid agent name prints an error with available options
- [ ] Works in both source repo and `.openstation/` installed layouts
- [ ] `artifacts/specs/autonomous-execution.md` C1 section updated with `agent` subcommand
