---
kind: task
name: 0090-spec-the-type-field-for
status: ready
assignee: architect
owner: user
parent: "[[0089-add-type-field-to-task]]"
created: 2026-03-09
---

# Spec the Type Field for Task Frontmatter

## Requirements

Define the `type` field for task frontmatter and update `docs/task.spec.md`:

1. Add `type` to the frontmatter schema table with valid enum values: `feature`, `research`, `spec`, `implementation`, `documentation`
2. Document default value: `feature` when omitted
3. Document the type-to-agent mapping table
4. Add `type` to the example tasks in the spec
5. Ensure the field is optional for backward compatibility — tasks without `type` are treated as `feature`

## Verification

- [ ] `type` field added to frontmatter schema table in `docs/task.spec.md`
- [ ] Valid values and default documented
- [ ] Type-to-agent mapping table included
- [ ] Example tasks updated to show `type` usage
- [ ] Backward compatibility noted
