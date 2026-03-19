---
kind: task
name: 0103-add-devrel-agent-template-for
type: documentation
status: done
assignee: author
owner: user
created: 2026-03-10
---

# Add devrel agent template for openstation init

Add a devrel agent template to `templates/agents/` so `openstation init` can install it in target projects.

## Requirements

1. Create `templates/agents/devrel.md` — a generic version of `artifacts/agents/devrel.md` suitable for any project (not Open Station-specific)
2. Follow the same structure as existing templates (e.g., `templates/agents/author.md`)
3. Template should use `{project}` placeholder if other templates do, or be project-agnostic

## Verification

- [x] `templates/agents/devrel.md` exists
- [x] Template follows the same format as other agent templates
- [x] `openstation init` installs the devrel agent in a target project
