---
kind: task
name: 0061-generalize-agent-templates-for-any
status: rejected
assignee:
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-06
subtasks:
  - "[[0062-spec-for-project-agnostic-agent]]"
  - "[[0063-rewrite-agent-specs-as-general]]"
---

# Generalize Agent Templates for Any Project

All 5 agent specs (researcher, author, architect, developer, project-manager) currently hardcode "Open Station" in their descriptions and body text. They need to be project-agnostic so they work in any project that installs openstation.

## Requirements

1. Agent specs installed by `openstation init` must not reference "Open Station" as the project name.
2. Agent roles, capabilities, and constraints should be generic — the `openstation-execute` skill already provides OS-specific task protocol context.
3. Project-specific context (vault paths, conventions) comes from the skill and CLAUDE.md, not from agent identity text.

## Subtasks

- [[0062-spec-for-project-agnostic-agent]] — Define what a general agent template looks like
- [[0063-rewrite-agent-specs-as-general]] — Rewrite all 5 agent specs

## Verification

- [ ] No agent spec contains hardcoded "Open Station" in description or body
- [ ] Agent roles remain clear and well-defined without project-specific references
- [ ] Both subtasks completed and verified
