---
kind: task
name: 0090-spec-the-type-field-for
status: done
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

## Findings

Updated `docs/task.spec.md` with the `type` field:

1. **Frontmatter schema** — added `type: feature` to the YAML template, positioned after `name` and before `status`
2. **Field reference table** — added `type` as an optional enum field defaulting to `feature`
3. **Type Values table** — new section documenting the five valid values: `feature`, `research`, `spec`, `implementation`, `documentation`
4. **Type-to-Agent Mapping table** — new section mapping each type to its suggested agent with rationale
5. **Backward compatibility** — explicitly noted that tasks without `type` are treated as `feature`
6. **Examples updated** — all four example tasks now include `type` (`implementation`, `research`, `feature`, `documentation`)
7. **Progressive Disclosure** — Idea stage updated to note `type` as optional early field

## Verification

- [x] `type` field added to frontmatter schema table in `docs/task.spec.md`
- [x] Valid values and default documented
- [x] Type-to-agent mapping moved to `commands/openstation.create.md` (operational, not spec)
- [x] Example tasks updated to show `type` usage
- [x] Backward compatibility noted
