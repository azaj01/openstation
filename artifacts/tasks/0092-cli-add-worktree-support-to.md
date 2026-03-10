---
kind: task
name: 0092-cli-add-worktree-support-to
type: feature
status: review
assignee: developer
owner: user
created: 2026-03-10
---

# CLI — Add worktree support to find_root()

Resolve `.openstation/` from the main worktree when running inside a git worktree.

## Requirements

1. **Worktree detection** — When `find_root()` fails to locate `.openstation/` by walking up from CWD, detect if the current directory is inside a git worktree (via `git rev-parse --git-common-dir` or similar).

2. **Resolve main worktree root** — If in a worktree, derive the main worktree's root path and check for `.openstation/` there. Return that path as the vault root.

3. **Source repo detection** — The existing source-repo heuristic (`agents/` + `install.sh`) should also work from worktrees — apply the same fallback logic.

4. **No git dependency when unnecessary** — If `.openstation/` is found locally (normal case), skip git subprocess calls entirely. Git is only invoked as a fallback.

5. **Graceful degradation** — If `git` is not installed or the directory isn't a git repo, behave exactly as today (return `None, None`).

6. **No new dependencies** — Use `subprocess.run` to call git; no new packages.

## Verification

- [ ] `find_root()` returns correct vault root when CWD is inside a git worktree that lacks `.openstation/` but the main worktree has it
- [ ] `find_root()` still works as before in a normal (non-worktree) project with `.openstation/`
- [ ] `find_root()` still works for the source repo (`agents/` + `install.sh` detection)
- [ ] No git subprocess is invoked when `.openstation/` is found locally
- [ ] Graceful fallback when `git` is not available (returns `None, None`)
- [ ] Graceful fallback when CWD is not inside a git repo (returns `None, None`)
- [ ] No new package dependencies added
- [ ] Existing CLI tests still pass
