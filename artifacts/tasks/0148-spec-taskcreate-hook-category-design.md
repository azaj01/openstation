---
kind: task
name: 0148-spec-taskcreate-hook-category-design
type: spec
status: backlog
assignee: architect
owner: user
parent: "[[0147-hooks-improvements-support-task-creation]]"
created: 2026-03-17
---

# Spec Taskcreate Hook Category Design

## Requirements

1. Design the `TaskCreate` matcher format — what fields to match on (initial status, task type, catch-all `*`, or a combination)
2. Define environment variables for creation hooks (`OS_TASK_NAME`, `OS_TASK_STATUS`, `OS_TASK_TYPE`, `OS_TASK_FILE`, `OS_VAULT_ROOT`, etc.)
3. Decide hook timing: pre-create (can abort) vs post-create (can read the file) with rationale
4. Specify failure behavior — does a failed hook delete the created file? Abort before writing?
5. Update `artifacts/specs/task-lifecycle-hooks.md` with the new `TaskCreate` category
6. Remove `TaskCreate` from the "Scope Exclusions" section of the spec

## Verification

- [ ] Matcher format is defined with examples
- [ ] Environment variables are specified
- [ ] Timing decision (pre/post) is documented with rationale
- [ ] Failure behavior is specified
- [ ] Hooks spec is updated with `TaskCreate` category
