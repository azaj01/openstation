---
kind: task
name: 0091-implement-type-field-in-cli
status: backlog
assignee: developer
owner: user
parent: "[[0089-add-type-field-to-task]]"
created: 2026-03-09
---

# Implement Type Field in CLI

## Requirements

Add `type` support to the `openstation` CLI, following the spec from `[[0090-spec-the-type-field-for]]`:

1. `openstation create` — accept `--type` flag, write to frontmatter, default to `feature`
2. `openstation list` — accept `--type` filter to show tasks of a specific type
3. Backward compatible — tasks without `type` field still work everywhere

## Verification

- [ ] `openstation create "desc" --type research` writes `type: research` to frontmatter
- [ ] `openstation create "desc"` without `--type` writes `type: feature`
- [ ] `openstation list --type research` filters correctly
- [ ] Existing tasks without `type` field don't break `list`, `show`, or `status`
