---
kind: task
name: 0122-worktree-integration
type: feature
status: in-progress
assignee:
owner: user
created: 2026-03-13
subtasks:
  - "[[0121-research-worktree-integration-for-parallel]]"
  - "[[0123-research-worktree-integration]]"
  - "[[0124-spec-worktree-integration]]"
  - "[[0126-worktree-pass-through]]"
  - "[[0092-cli-add-worktree-support-to]]"
  - "[[0094-spec-branch-based-task-scoping]]"
  - "[[0109-implement-branch-based-task-scoping]]"
  - "[[0108-update-agent-skills-and-docs]]"
  - "[[0138-research-worktree-merge-back-workflow]]"
---

# Worktree Integration

Enable agents to work in git worktrees with isolated branches.

## Scope

Milestone-based. Each milestone is usability-tested before
the next begins. Implementation subtasks are created
per-milestone after the previous one lands.

### M1 — Pass-through (current)
- Vault resolution from linked worktrees (`find_root()` fallback)
- `--worktree` pass-through on `openstation run`

### M2 — Branch scoping (future)
- Branch-scoped tasks via `branch` frontmatter field
- Branch-scoped task filtering

### M3 — Agent awareness (future)
- Agent skills document worktree workflows
- Parallel agent execution on separate branches

## Subtasks

### M1 — Pass-through (done)

1. **0121 — Research (early)** — Initial worktree research. Findings absorbed into 0123.
2. **0123 — Research** — Consolidated worktree research (claude `--worktree`, worktrunk, workmux). Living document.
3. **0092 — find_root()** — Vault resolution from linked worktrees. Landed independently.
4. **0124 — Spec** — Pass-through design and vault resolution.
5. **0126 — Implement** — `--worktree` CLI plumbing.

### M2 — Branch scoping

6. **0094 — Spec** — Branch-based task scoping design. Spec complete.
7. **0109 — Implement** — `branch` field, CLI flags, filtering logic.

### M3 — Agent awareness

8. **0108 — Agent skills** — Update execute skill and agent specs for worktree workflows.

## Prior Work

- **0107** — Previous worktree parent task (now `done`). Subtasks absorbed into this epic.

## Verification

- [ ] M1: Agents dispatch in worktrees and find the shared vault
- [ ] M1: `openstation run --worktree` creates isolated sessions
- [ ] M2: Branch-scoped tasks filter correctly with `--branch auto`
- [ ] M3: Agent skills document worktree workflows
- [ ] Each milestone is usability-tested before the next begins
