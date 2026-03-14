---
kind: task
name: 0107-add-git-worktree-support
type: feature
status: done
owner: user
created: 2026-03-10
subtasks:
  - "[[0092-cli-add-worktree-support-to]]"
  - "[[0094-spec-branch-based-task-scoping]]"
  - "[[0109-implement-branch-based-task-scoping]]"
  - "[[0108-update-agent-skills-and-docs]]"
---

# Add git worktree support

> **Superseded by [[0122-worktree-integration]].** All subtasks
> re-parented under 0122. This task is closed.

Enable agents to work in git worktrees — the CLI resolves the shared vault, tasks are scoped to branches, and agents understand the worktree workflow.

## Subtasks

1. **0092 — CLI `find_root()` worktree resolution** — Resolve `.openstation/` from the main worktree when running inside a linked worktree. No new dependencies, graceful fallback.

2. **0094 — Spec branch-based task scoping** — Design the `branch` frontmatter field so tasks can be scoped to a branch. Update project docs (task.spec.md, storage-query-layer.md, lifecycle.md, CLAUDE.md).

3. **0109 — Implement branch-based task scoping** — Build the `branch` field, CLI flags, and filtering logic per the 0094 spec.

4. **0108 — Update agent skills for worktree workflows** — Update execute skill and agent specs so agents know how to operate when dispatched from a worktree.

## Verification

- [ ] CLI resolves vault from any worktree (0092)
- [ ] Branch-based task scoping is specced and addresses filtering, CLI, edge cases (0094)
- [ ] Branch scoping is implemented with CLI flags and filtering (0109)
- [ ] Agent skills and docs cover worktree workflows (0108)
- [ ] End-to-end: an agent dispatched in a worktree finds only its branch's tasks and completes work correctly
