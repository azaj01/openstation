---
kind: task
name: 0131-monitor-agents-for-indirect-openstation
type: documentation
status: backlog
assignee: author
owner: user
created: 2026-03-13
---

# Monitor Agents For Indirect Openstation Invocations

## Context

The developer agent was observed using `python -m openstation`
and `PYTHONPATH=src python -m openstation` instead of calling
`openstation` directly. A constraint was added to the developer
agent spec to prevent this. The shared execute skill already
has the general constraint, but it wasn't sufficient for the
developer agent which has `Bash(python *)` in its allowed-tools.

## Requirements

1. Monitor other agents for similar patterns — any agent using
   indirect invocation paths (`python -m openstation`,
   `python3 bin/openstation`, `PYTHONPATH=... openstation`, etc.)
   should get a matching constraint added to its spec.
2. If this pattern recurs across multiple agents, consider
   strengthening the shared constraint in
   `skills/openstation-execute/SKILL.md` instead of patching
   individual agent specs.

## Verification

- [ ] Issue is documented for future reference
- [ ] Developer agent constraint is confirmed in place
- [ ] Clear guidance exists for what to do if other agents exhibit the same behavior
