---
kind: task
name: 0165-rewrite-find-root-to-use
type: feature
status: done
assignee: developer
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-19
---

# Rewrite find_root() — Git Toplevel Instead of Walk-Up

## Context

Current `find_root()` walks up directory-by-directory from CWD
looking for Open Station markers, then compares against the main
worktree root. This is over-complicated. Replace with a simpler
two-step model based on `git rev-parse --show-toplevel`.

## Design

Two-step resolution, no walk-up:

1. `toplevel = git rev-parse --show-toplevel`
2. If toplevel has OS markers (`.openstation/` or `agents/` +
   `install.sh`) → return toplevel (**independent** vault)
3. Else → `main = git rev-parse --git-common-dir` → parent
4. If main has OS markers → return main (**attached** mode —
   worktree uses main repo's vault)
5. Else → not an Open Station project, return `(None, None)`

Non-git projects are no longer supported.

## Requirements

1. Replace `_walk_up()` and current `find_root()` logic in
   `core.py` with the two-step toplevel/main approach above
2. Remove `_walk_up()` helper (no longer needed)
3. Keep `_check_dir()` and `_git_main_worktree_root()` — both
   are still used
4. Add a new helper to get git toplevel (`git rev-parse
   --show-toplevel`)
5. The `run` CWD separation from 0154 still applies — vault ops
   use the resolved root, Claude execution uses original CWD
6. Update existing `find_root` tests to match the new behavior
7. Drop any tests that assume non-git walk-up works

## Progress

### 2026-03-19 — developer
> time: unknown

Implemented two-step git-toplevel find_root(), removed _walk_up(), added _git_toplevel() helper, rewrote tests (11 pass).

## Findings

Replaced `find_root()` with a two-step git-toplevel approach in
`src/openstation/core.py`:

- **Removed** `_walk_up()` entirely — no more directory-by-directory traversal
- **Added** `_git_toplevel()` helper wrapping `git rev-parse --show-toplevel`
- **Kept** `_check_dir()` and `_git_main_worktree_root()` unchanged
- **New logic**: toplevel first (independent vault), then main worktree
  fallback (attached mode), then `(None, None)`

Key behavioral change: worktrees WITH their own `.openstation/` now
return the worktree root (independent mode) instead of always
preferring the main repo. This matches the spec's design.

Tests rewritten in `tests/test_find_root.py` — 11 tests covering
main repo, attached worktree, independent worktree, non-git, and
graceful degradation. Old walk-up and non-git-with-markers tests
replaced with tests asserting `(None, None)`.

## Verification

- [x] `find_root()` from main repo root returns main repo
- [x] `find_root()` from a subdirectory of main repo returns main repo root
- [x] `find_root()` from a worktree WITHOUT `.openstation/` returns main repo root (attached mode)
- [x] `find_root()` from a worktree WITH `.openstation/` returns the worktree root (independent mode)
- [x] `find_root()` from a non-git directory returns `(None, None)`
- [x] `_walk_up()` is removed
- [x] All existing tests pass or are updated
