---
kind: task
name: 0034-agent-bash-compound-commands
status: backlog
agent:
owner: manual
created: 2026-03-03
---

# Fix Agent Bash Compound Command Permissions

## Requirements

Claude Code's `allowedTools` patterns are shell-operator-aware —
`Bash(python3 *)` does not match compound commands like
`python3 -m pytest ... && echo done` or `python3 ... 2>&1; echo $?`.
This causes agents to waste turns retrying denied commands.

Decide on a strategy and update all agent specs:

1. **Evaluate options** — narrow patterns (current, lossy) vs
   bare `Bash` (broad, relies on tier 2 budget/turn caps) vs
   a hybrid approach
2. **Update agent specs** — apply the chosen strategy to all
   agents in `artifacts/agents/`
3. **Document the decision** — record the rationale in the agent
   spec conventions or CLAUDE.md so future agents follow the
   same pattern

## Context

- Tier 2 already caps risk via `--max-budget-usd` and `--max-turns`
- Narrow patterns caused 3–16 permission denials per run in
  developer agent testing (tasks 0024, 0033)
- See conversation notes from 2026-03-03 for full analysis

## Verification

- [ ] Agents can run compound bash commands in tier 2 without denials
- [ ] Decision is documented (CLAUDE.md or agent spec conventions)
- [ ] All agent specs in `artifacts/agents/` follow the chosen pattern
