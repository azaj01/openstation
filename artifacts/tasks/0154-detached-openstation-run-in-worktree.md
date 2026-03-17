---
kind: task
name: 0154-detached-openstation-run-in-worktree
type: bug
status: ready
assignee: developer
owner: user
created: 2026-03-17
---

# Detached `openstation run` in Worktree Executes in Main Repo

## Requirements

1. When `openstation run` (detached, no `--attached`) is invoked
   from a worktree directory, the spawned `claude -p` session runs
   in the main repo root instead of the worktree — because
   `os.chdir(root)` resolves to the main repo.
2. In attached mode (`-a`), Claude's `--worktree` flag correctly
   sets the working directory, so the bug only affects detached
   runs.
3. Fix detached mode to use the worktree directory as `cwd` when
   run from (or targeting) a worktree.
4. Ensure `_stream_and_capture` receives the correct `cwd` for
   worktree sessions.

## Verification

- [ ] `openstation run --task <id>` from a worktree directory runs the session in that worktree
- [ ] `openstation run --task <id> --attached` from a worktree still works correctly
- [ ] `openstation run --task <id>` from the main repo still works correctly (no regression)
