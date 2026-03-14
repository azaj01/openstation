---
kind: task
name: 0108-update-agent-skills-and-docs
type: spec
status: backlog
assignee: author
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-10
---

# Update agent skills for worktree workflows

After 0092 (CLI plumbing) and 0094 (branch scoping spec + docs), the project docs are up to date but agents still won't know they're in a worktree or how to behave. This task updates agent-facing specs and skills to close that gap.

## Requirements

1. **Execute skill update** — Add a worktree section to `skills/openstation-execute/` explaining: the vault is shared across worktrees, how branch scoping works, and what to expect when `openstation list` filters by branch.

2. **Agent spec updates** — Review agent specs in `artifacts/agents/` and add worktree-relevant guidance where needed (e.g., developer agent should know about branch-scoped task creation).

3. **Agent-facing guidance** — Cover practical scenarios: "you're dispatched in a worktree, here's what's different." Specifically: vault path resolution, task visibility (branch-scoped vs global), and how to create tasks from a worktree.

## Context

- Depends on: 0092 (worktree CLI support — done), 0094 (branch scoping spec — done)
- Should be the last subtask to land — it updates agent specs based on what the others built and documented

## Verification

- [ ] Execute skill mentions worktrees and branch scoping
- [ ] Agent specs updated with worktree-relevant guidance
- [ ] An agent reading the updated skills would understand how to operate from a worktree
