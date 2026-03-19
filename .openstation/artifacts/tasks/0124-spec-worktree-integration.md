---
kind: task
name: 0124-spec-worktree-integration
type: spec
status: done
assignee: architect
owner: user
parent: "[[0122-worktree-integration]]"
artifacts:
  - "[[artifacts/specs/worktree-pass-through]]"
created: 2026-03-13
---

# Spec: Worktree Pass-Through

Scoped to M1 (pass-through) only. No branch field or
branch-scoped task filtering.

## Requirements

1. Define `find_root()` worktree resolution design (`git rev-parse --git-common-dir` fallback when `.openstation/` not found locally)
2. Define `--worktree` pass-through on `openstation run` — forward the flag to `claude` CLI, no custom worktree lifecycle management
3. Define how agents discover the shared vault when running inside a worktree
4. Define milestone boundaries — what ships in M1
5. Track schema changes needed across docs and `CLAUDE.md`
6. Update spec after each milestone based on usability feedback

## Verification

- [ ] Spec artifact exists in `artifacts/specs/`
- [ ] Covers vault resolution from worktrees (`find_root()` fallback)
- [ ] Covers `--worktree` pass-through on `openstation run`
- [ ] Milestone boundaries are defined for M1
- [ ] Schema/doc changes are listed
- [ ] No branch-scoping content included
