---
kind: task
name: 0196-task-suspension-backward-transitions-from
type: feature
status: done
assignee:
owner: user
subtasks:
  - "[[0188-research-task-suspension-model-design]]"
  - "[[0189-cli-suspend-subcommand-add-openstation]]"
  - "[[0193-suspend-command-docs-and-skill]]"
created: 2026-03-21
---

# Task Suspension — Backward Transitions From In-Progress With Work Preservation

## Requirements

Add the ability to send tasks backward from `in-progress` to
`ready` or `backlog`, preserving work done so far via git
branches and a `## Suspended` section in the task body.

Spec: `[[artifacts/specs/task-suspension-model]]`

## Subtasks

1. ~~**0188** — Research & spec (done)~~
2. ~~**0189** — CLI transition table + suspend hook (done)~~
3. ~~**0193** — Slash command + docs + skill updates (done)~~

## Verification

- [x] All subtasks are done
- [x] `openstation status <task> ready` works from `in-progress`
- [x] `/openstation.suspend` slash command works end-to-end
- [x] `docs/lifecycle.md` reflects the new transitions
