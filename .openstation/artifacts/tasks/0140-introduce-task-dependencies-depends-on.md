---
kind: task
name: 0140-introduce-task-dependencies-depends-on
type: feature
status: backlog
assignee: 
owner: user
created: 2026-03-15
subtasks:
  - "[[0137-spec-task-dependency-model-depends]]"
  - "[[0141-implement-task-dependencies-in-cli]]"
---

# Introduce Task Dependencies

## Requirements

1. Implement the `depends_on` frontmatter field — a list of
   wikilinks to tasks that must be `done` before this task can
   proceed
2. Enforce dependency-aware transitions in `cmd_status()` —
   block `backlog → ready` when dependencies are unmet (with
   `--force` override)
3. Display dependency status in `openstation show` — list each
   dependency with its current status
4. Indicate blocked tasks in `openstation list` output
5. Support inverse query — show what tasks a given task unblocks
6. Update `docs/task.spec.md` and `docs/lifecycle.md` with
   dependency rules

## Subtasks

1. **0137** — Spec: Task Dependency Model (ready, architect)
2. **0141** — Implement task dependencies in CLI (backlog, developer)

## Verification

- [ ] `depends_on` field accepted in task frontmatter
- [ ] `backlog → ready` blocked when dependencies unmet
- [ ] `--force` overrides dependency check
- [ ] `openstation show` displays dependency status
- [ ] `openstation list` indicates blocked tasks
- [ ] Inverse "unblocks" query works
- [ ] `task.spec.md` and `lifecycle.md` updated
