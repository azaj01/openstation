---
kind: task
name: 0063-rewrite-agent-specs-as-general
status: done
assignee: author
owner: user
parent: "[[0061-generalize-agent-templates-for-any]]"
created: 2026-03-06
---

# Rewrite Agent Specs as General Templates

## Context

**Agents are NOT templates.** The agents in `artifacts/agents/` are the working agents for this repo — they can and should reference "Open Station", vault paths, and specific agent names. Only the **templates** installed by `openstation init` into target projects must be project-agnostic.

References:
- Agent spec format: `docs/agent.spec.md`
- Template guidelines: `artifacts/specs/general-agent-templates.md` (from [[0062-spec-for-project-agnostic-agent]])

## Requirements

1. Create project-agnostic **agent templates** for all 5 agents (researcher, author, architect, developer, project-manager) per `docs/agent.spec.md` template guidelines and the migration checklist in `artifacts/specs/general-agent-templates.md` § 6.
2. Store templates in `templates/agents/` — these are the files `openstation init` installs into target projects.
3. Templates must not reference "Open Station", hardcoded vault paths, or specific agent names. Use the language patterns from `docs/agent.spec.md` § Template Guidelines.
4. Templates must include the two-tier `allowed-tools` comment structure (role-based vs task-system).
5. **Do not modify** the existing agents in `artifacts/agents/` — those are this repo's working agents and remain project-specific.
6. Update `docs/agent.spec.md` to document the `templates/agents/` location and clarify the distinction between agents (project-specific) and templates (project-agnostic).

## Verification

- [ ] `templates/agents/` contains all 5 agent templates
- [ ] No template references "Open Station" in description or body
- [ ] No template hardcodes vault paths or specific agent names
- [ ] Templates follow `docs/agent.spec.md` format (frontmatter schema, body structure)
- [ ] `allowed-tools` uses two-tier comment structure in all templates
- [ ] Existing `artifacts/agents/` specs are unchanged
- [ ] `docs/agent.spec.md` updated to document templates location
