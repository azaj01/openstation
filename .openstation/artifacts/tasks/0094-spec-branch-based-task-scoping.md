---
kind: task
name: 0094-spec-branch-based-task-scoping
type: spec
status: done
assignee: architect
owner: user
parent: "[[0122-worktree-integration]]"
artifacts:
  - "[[artifacts/specs/branch-based-task-scoping]]"
created: 2026-03-10
---

# Spec branch-based task scoping for worktree-aware execution

With worktree support (0092), all worktrees share one `.openstation/` vault. Design a branch-based scoping mechanism so tasks can be associated with branches and `openstation run` only picks up tasks relevant to the current worktree's branch.

## Requirements

1. **`branch` frontmatter field** — Design an optional `branch` field on tasks. When set, the task is scoped to that branch. When unset, the task is global (available from any worktree).

2. **Auto-detection** — `openstation run` and `openstation list` should auto-detect the current branch (`git branch --show-current`) and filter accordingly. Tasks with matching `branch` + global tasks (no `branch` field) are visible.

3. **CLI support** — `openstation create --branch <name>` to set at creation. `openstation status` or a new command to update it. Consider auto-setting branch from current worktree on create.

4. **Edge cases** — Specify behavior for: detached HEAD, branch rename, task created before branch exists, multiple tasks on same branch.

5. **Concurrency** — Address whether a lock mechanism is also needed to prevent double-pickup when two agents run simultaneously on the same branch, or if `in-progress` status is sufficient.

6. **Schema update** — Define changes needed to `docs/task.spec.md` and `docs/storage-query-layer.md`.

## Context

- Depends on: 0092 (worktree support in `find_root()`)
- Branch approach chosen over worktree-path field (paths are ephemeral) and lock-file-only (doesn't help with scoping)

## Verification

- [ ] Spec covers the `branch` frontmatter field design (optional, scoping semantics)
- [ ] Spec defines filtering logic for `list` and `run` (branch-scoped + global tasks)
- [ ] Spec addresses CLI interface (`--branch` flag on create, update path)
- [ ] Spec covers edge cases (detached HEAD, no branch field, branch rename)
- [ ] Spec addresses concurrency (lock vs status-based)
- [ ] Spec lists schema changes needed in task.spec.md and storage-query-layer.md
