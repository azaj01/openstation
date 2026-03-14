---
kind: task
name: 0137-spec-task-dependency-model-depends
type: spec
status: ready
assignee: architect
owner: user
created: 2026-03-14
---

# Spec: Task Dependency Model

## Requirements

1. Design a `depends_on` frontmatter field for tasks — a list of wikilinks (`"[[0042-some-task]]"`) indicating that the current task is blocked until all listed dependencies reach `done` status.
2. Define how dependencies interact with the lifecycle:
   - A task with unmet dependencies cannot transition from `backlog` → `ready` (or if already `ready`, is flagged as blocked).
   - Specify whether the CLI should enforce this (hard block) or warn (soft advisory).
3. Define how dependencies are displayed: `openstation show` should list dependencies and their current status; `openstation list` should indicate blocked tasks.
4. Specify the inverse relationship: a `blocks` or `dependents` query (derived, not stored) so you can see what a task unblocks.
5. Address interaction with the existing `parent`/`subtasks` hierarchy — are parent-child relationships implicit dependencies, or orthogonal?
6. Update `docs/task.spec.md` with the new field definition and `docs/lifecycle.md` with dependency-aware transition rules.

## Verification

- [ ] Spec defines `depends_on` frontmatter field format with examples
- [ ] Lifecycle interaction rules are documented (blocking behavior on transitions)
- [ ] Display behavior specified for `show` and `list`
- [ ] Inverse query (what does this task unblock?) is addressed
- [ ] Relationship to `parent`/`subtasks` is clarified
- [ ] `task.spec.md` and `lifecycle.md` update plan included
