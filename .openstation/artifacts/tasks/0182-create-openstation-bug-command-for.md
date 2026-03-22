---
kind: task
name: 0182-create-openstation-bug-command-for
type: feature
status: done
assignee: project-manager
owner: user
created: 2026-03-20
---

# Create openstation.create.bug command

Create a user-invocable command for filing well-structured bug
tasks. Pattern derived from PM's bug-filing workflow on task 0181.

## Requirements

1. Create `commands/openstation.create.bug.md` following existing
   command conventions (frontmatter, Input, Procedure sections).
2. Procedure must enforce: root-cause tracing, scoped numbered
   requirements, preserve boundaries, mechanical verification items.
3. Use draft-approve-create flow consistent with `openstation.create`.

## Verification

- [x] `commands/openstation.create.bug.md` exists
- [x] Command follows create-command conventions (frontmatter with name/description, Input, Procedure)
- [x] Procedure includes root-cause investigation step
- [x] Procedure requires mechanical verification items (with good/bad examples)
- [x] Procedure requires preserve boundaries in requirements

## Progress

- 2026-03-20 — project-manager: Created command directly (had full
  context from 0181 bug-filing session). Marked done retroactively.
