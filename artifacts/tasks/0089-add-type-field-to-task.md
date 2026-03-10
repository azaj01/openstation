---
kind: task
name: 0089-add-type-field-to-task
status: done
assignee: 
owner: user
created: 2026-03-09
subtasks:
  - "[[0090-spec-the-type-field-for]]"
  - "[[0091-implement-type-field-in-cli]]"
---

# Add Type Field to Task Frontmatter

Add an explicit `type` field to task frontmatter that classifies the nature of the work, enabling deterministic agent assignment and subtask suggestions.

## Requirements

1. Define valid `type` values: `feature`, `research`, `spec`, `implementation`, `documentation`
2. Add `type` to the frontmatter schema in `docs/task.spec.md`
3. Update `openstation create` to accept `--type` flag
4. When `type` is not provided, default to `feature`
5. Use `type` to auto-suggest agent assignment during task creation:
   - `feature` → `developer` (standalone) or none (decomposed)
   - `research` → `researcher`
   - `spec` → `architect`
   - `implementation` → `developer`
   - `documentation` → `author`
6. Use `type` to drive subtask suggestions when creating feature tasks

## Subtasks

### P1

1. **Spec the type field** — define schema, valid values, default, update `docs/task.spec.md`

### P2

2. **Implement type field in CLI** — add `--type` flag to `create`, add `--type` filter to `list`, backward compat

## Verification

- [x] `type` field documented in `docs/task.spec.md` with valid values and default
- [x] `openstation create` accepts `--type` flag and writes it to frontmatter
- [x] When `--type` is omitted, defaults to `feature`
- [x] `openstation list` can filter by `--type`
- [x] Existing tasks without `type` field still work (backward compatible)
