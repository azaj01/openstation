---
kind: task
name: 0016-agent-templates
status: backlog
assignee:
owner: user
created: 2026-02-28
---

# Agent Templates

## Requirements

- Define a reusable template structure for agent specs so new
  agents can be scaffolded quickly and consistently
- Template should encode all required frontmatter fields (`kind`,
  `name`, `skills`, `description`) and standard markdown sections
- Provide at least one template variant per agent archetype
  (e.g., researcher, author) with pre-filled sections and
  placeholder guidance
- Document how to use the template (manual copy or via a command)
- Ensure templates align with the current agent spec format in
  `docs/` and existing agents in `artifacts/agents/`

## Verification

- [ ] Template file(s) exist in an appropriate location in the vault
- [ ] Templates include all required frontmatter fields per the agent spec format
- [ ] At least two archetype variants are provided (e.g., researcher, author)
- [ ] A new agent can be scaffolded from the template without ambiguity
- [ ] Templates are consistent with existing agent specs in `artifacts/agents/`
