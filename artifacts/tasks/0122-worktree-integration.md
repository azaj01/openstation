---
kind: task
name: 0122-worktree-integration
type: feature
status: in-progress
assignee:
owner: user
created: 2026-03-13
subtasks:
  - "[[0123-research-worktree-integration]]"
  - "[[0124-spec-worktree-integration]]"
  - "[[0126-worktree-pass-through]]"
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

### M1

1. **0123 — Research** — Consolidate worktree research (claude `--worktree`, worktrunk, workmux). Living document.

2. **0124 — Spec** — Pass-through design and vault resolution. M1 scope only.

3. **0126 — Implement** — `--worktree` CLI plumbing. M1 scope only.

### Future
*(Created when the previous milestone lands)*

## Prior Work

- **0107** — Previous worktree parent task (in-progress). Subtasks 0092 (failed), 0094 (spec done), 0109 (backlog), 0108 (backlog) are superseded by this epic.
- **0121** — Worktree research (in review). Findings absorbed into 0123.

## Verification

- [ ] M1: Agents dispatch in worktrees and find the shared vault
- [ ] M1: `openstation run --worktree` creates isolated sessions
- [ ] M2: Branch-scoped tasks filter correctly with `--branch auto`
- [ ] M3: Agent skills document worktree workflows
- [ ] Each milestone is usability-tested before the next begins
