---
kind: content
type: social/twitter
status: draft
---

# Tweet: Agent Context — Rule of Thumb

## Option A (concise)

Where to put agent context — my rule of thumb:

1. **docs/** — source of truth about the world. Facts, schemas, rules go here.
2. **skills/** — reusable instructions shared across agents. Workflows, playbooks.
3. **agent spec** — context only this agent needs. Role, constraints, capabilities.

General → specific. If multiple agents need it, push it up.

## Option B (punchier)

My rule of thumb for where to put AI agent context:

**docs/** — facts about the world (schemas, rules, specs)
**skills/** — instructions any agent can reuse (workflows, playbooks)
**agent spec** — scoped to one agent (role, constraints)

The heuristic: start specific, promote when reuse appears.
