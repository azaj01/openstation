---
kind: task
name: 0117-solve-agent-permission-model-for
type: spec
status: backlog
assignee: architect
owner: user
created: 2026-03-12
---

# Solve agent permission model for autonomous execution

## Context

When running `openstation run --task 0017` with the researcher
agent at Tier 2 (autonomous), the agent pauses for Bash command
approval because `allowed-tools` only whitelists narrow patterns
(`openstation *`, `ls *`, `readlink *`). Any other Bash usage
(e.g., `python block_speed.py`) triggers a permission prompt,
breaking autonomous execution.

## Requirements

1. **Document root cause** — why Tier 2 agents still prompt
   for permissions despite being launched autonomously

2. **Design a permission model** that lets agents run
   autonomously at their assigned tier. Consider:
   - Per-agent `allowed-tools` expansion (broader Bash patterns,
     or tier-dependent patterns)
   - `--dangerously-skip-permissions` pass-through from
     `openstation run` to `claude` at Tier 2+
   - Whether `allowed-tools` should vary by tier (Tier 1 =
     restricted, Tier 2 = broader, Tier 3 = all)
   - Security trade-offs of each approach

3. **Spec the solution** — write to `artifacts/specs/`

## Verification

- [ ] Root cause documented (why Tier 2 agents still prompt)
- [ ] Permission model specced with trade-off analysis
- [ ] Solution covers `openstation run` and `agents dispatch` paths
- [ ] Spec written to `artifacts/specs/`
