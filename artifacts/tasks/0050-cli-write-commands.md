---
kind: task
name: 0050-cli-write-commands
status: done
agent: project-manager
owner: user
created: 2026-03-05
subtasks:
  - "[[0051-cli-write-commands-spec]]"
  - "[[0052-cli-write-commands-impl]]"
  - "[[0053-cli-write-commands-prompts]]"
---

# CLI Write Commands

Add write subcommands to the `openstation` CLI: `create` for new
tasks and `status` for changing task status.

## Requirements

1. Add `openstation create <description>` — auto-increment ID,
   generate slug, write `artifacts/tasks/NNNN-slug.md` with
   proper frontmatter. No symlinks.
2. Add `openstation status <task> <new-status>` — update the
   `status` field in frontmatter. Validate transitions per
   `docs/lifecycle.md`.
3. Both commands: zero external dependencies, idempotent,
   consistent with existing CLI patterns.

## Subtasks

- 0051-cli-write-commands-spec — spec the subcommands
- 0052-cli-write-commands-impl — implement in `bin/openstation`
- 0053-cli-write-commands-prompts — update commands and skills

## Verification

- [ ] Sub-task 0051 is done (spec approved)
- [ ] Sub-task 0052 is done (CLI subcommands work)
- [ ] Sub-task 0053 is done (commands/skills updated)
- [ ] `openstation create "test"` creates a valid task file
- [ ] `openstation status <task> ready` updates frontmatter
