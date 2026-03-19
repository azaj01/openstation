---
kind: task
name: 0168-find-root-in-linked-worktree
type: bug
status: review
assignee: developer
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-19
---

# find_root() in Linked Worktree Returns Local Root Instead of Main Repo

## Problem

`find_root()` (rewritten in 0165) uses a two-step approach:
1. `_git_toplevel()` → check for OS markers → return if found
2. `_git_main_worktree_root()` → check for OS markers → return if found

In linked worktrees, step 1 finds OS markers (inherited from the
same repo) and returns the **worktree root** as an "independent"
vault. Step 2 (attached mode) is never reached. This causes all
CLI artifact operations to read/write to the worktree's local
`artifacts/` instead of the main repo's.

## Requirements

1. When `find_root()` is called from a linked worktree, it must
   return the **main worktree root**, not the linked worktree
   root — even if the linked worktree has OS markers (`agents/`
   + `install.sh` or `.openstation/`).
2. Compare `_git_toplevel()` against `_git_main_worktree_root()`
   — if they differ, we're in a linked worktree → use main root
   (attached mode). If they're the same → use toplevel directly.
3. All CLI artifact operations (`list`, `show`, `create`,
   `status`) from a linked worktree must read/write to the main
   repo's `artifacts/`.
4. The `run` CWD separation (0154) is unaffected — Claude
   execution still uses original CWD.
5. Update `find_root` tests to cover the fix.

## Verification

- [ ] `find_root()` from a linked worktree with OS markers returns main repo root
- [ ] `find_root()` from main repo root still returns main repo root
- [ ] `openstation create` from a linked worktree writes to main repo's `artifacts/tasks/`
- [ ] `openstation list` from a linked worktree shows main repo tasks
- [ ] Existing tests pass or are updated

## Findings

Fixed `find_root()` in `src/openstation/core.py` to compare
`_git_toplevel()` against `_git_main_worktree_root()` **before**
checking for OS markers. When the two differ, we're in a linked
worktree and always use the main root (attached mode).

**What changed:**
- `find_root()` now resolves both toplevel and main worktree root
  upfront, compares them, and if they differ, skips the toplevel
  entirely and uses the main root
- The old `TestWorktreeIndependentMode` test class was renamed to
  `TestWorktreeWithInheritedMarkers` and updated to assert main
  repo root is returned (the correct behavior)
- Added two new tests: inherited source repo markers
  (`agents/` + `install.sh`) and subdirectory within a linked
  worktree with inherited markers

**Files modified:**
- `src/openstation/core.py` — `find_root()` rewritten
- `tests/test_find_root.py` — updated and expanded test class

All 13 find_root tests pass. CLI operations (`list`, `show`,
`create`, `status`) all use `find_root()` for vault discovery,
so they inherit the fix automatically.

## Progress

- 2026-03-19: Fixed `find_root()` to detect linked worktrees by
  comparing toplevel vs main worktree root. Updated tests (13/13
  pass). Moved to review.
