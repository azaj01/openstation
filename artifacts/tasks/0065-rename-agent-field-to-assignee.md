---
kind: task
name: 0065-rename-agent-field-to-assignee
status: done
assignee: project-manager
owner: user
created: 2026-03-06
---

# Rename Task `agent` Field to `assignee`

## Requirements

1. Rename the `agent` frontmatter field to `assignee` in the task schema (`docs/task.spec.md`).
2. Update all task files in `artifacts/tasks/` to use `assignee:` instead of `agent:`.
3. Update CLI code (`bin/openstation`) — field parsing, `--assignee` flag for list/create, internal dict keys.
4. Update tests (`tests/test_cli.py`) — fixture helper, CLI flag args, assertions.
5. Update commands (`openstation.list.md`, `openstation.update.md`, `openstation.create.md`).
6. Update execute skill (`openstation-execute/SKILL.md`) — CLI examples, fallback scanning.
7. Update docs (`lifecycle.md`, `storage-query-layer.md`, `CLAUDE.md`) — query examples, CLI usage.
8. Update specs (`cli-feature-spec.md`, `cli-write-commands.md`, `cli-run-spec.md`).
9. Artifact provenance `agent:` field (meaning "which agent created this") stays unchanged.
10. `openstation run <agent>` positional arg and `claude --agent` references stay unchanged.

## Verification

- [ ] `docs/task.spec.md` schema, field reference, and all examples use `assignee`
- [ ] All 62 task files use `assignee:` in frontmatter
- [ ] CLI `--assignee` flag works for list and create
- [ ] All 81 tests pass
- [ ] Commands, skill, docs, and specs updated
- [ ] Artifact provenance `agent:` field unchanged
