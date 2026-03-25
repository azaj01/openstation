---
kind: task
name: 0231-research-agent-compliance-with-inlined
type: feature
status: backlog
assignee: researcher
owner: user
created: 2026-03-25
---

# Research Agent Compliance With Inlined Vs File-Referenced Lifecycle Rules

## Requirements

1. Collect evidence of agent lifecycle violations from completed/rejected tasks — grep for invalid statuses (e.g., `completed`, `closed`), self-verification, missing Findings/Progress sections
2. For each violation, determine whether the broken rule was already inlined in the skill or only in `docs/lifecycle.md`
3. Assess whether inlining more rules into the skill would reduce violations, or if agents ignore inlined rules equally
4. Produce a findings summary with data: violation count, rule source (skill vs lifecycle doc), and a recommendation (inline more, shorten skill, add CLI guardrails, or no change)

## Verification

- [ ] Findings section includes concrete violation examples with task IDs
- [ ] Each violation is categorized as "rule in skill" vs "rule only in lifecycle.md"
- [ ] Recommendation is supported by the evidence collected
