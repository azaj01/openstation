---
kind: task
name: 0162-resolve-all-cli-artifact-operations
type: research
status: done
assignee: researcher
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-18
---

# Research: Shared Artifacts Across Worktrees

## Problem

When running CLI commands (`list`, `show`, `create`, `status`)
from a worktree, artifact operations read/write the worktree's
own copy of `artifacts/`. Since each worktree checks out its own
branch, newly created or updated tasks in the main repo aren't
visible from worktrees (and vice versa).

**Desired behavior:** All CLI artifact operations (task CRUD,
list, show, status transitions) resolve to the **vault root**
(main repo) regardless of which worktree the user is in. Code
execution stays in the worktree (already fixed in 0154).

## Context

- `find_root()` already resolves to the main repo root from
  worktrees — the path is available.
- Task 0154 established the pattern: vault root for artifact
  ops, original CWD for execution.
- The gap: commands like `list`, `show`, `create`, `status`
  use the `root` from `find_root()` but read files from disk
  in the worktree's checkout, not the main repo's.

## Research Questions

1. **Current resolution paths** — Which CLI commands read/write
   artifacts, and do they all go through `find_root()` → `root`?
   Or do some resolve relative to CWD?
2. **Git-level sharing** — Can `artifacts/` be shared at the git
   level (e.g., sparse-checkout, git worktree add --no-checkout
   with selective checkout)? Pros/cons vs runtime resolution.
3. **Symlink approach** — Would symlinking `<worktree>/artifacts/`
   → `<main>/artifacts/` work? How does git handle symlinked
   directories in worktrees? Risk of git status noise?
4. **Runtime resolution** — If we resolve all artifact paths to
   `<vault_root>/artifacts/` at runtime, what needs to change?
   Audit every call site. Are there edge cases (e.g., relative
   path output, log files)?
5. **Write conflicts** — If two worktrees write to the same
   `artifacts/` (e.g., both create tasks), are there race
   conditions or git conflicts to handle?
6. **Recommendation** — Which approach (git-level, symlink, or
   runtime) best fits the existing architecture?

## Findings

### 1. Current Resolution Paths — Full Audit

**Conclusion:** All CLI commands already resolve through
`find_root()` → `root`, and `root` correctly resolves to the
main repo root from worktrees via `_git_main_worktree_root()`.
The problem statement's claim that commands "read files from disk
in the worktree's checkout" is **incorrect for the current
codebase** — `find_root()` returns the main repo root, not the
worktree root.

**Audit of every artifact read/write call site:**

| Command | Module | Path construction | Resolves to main repo? |
|---------|--------|-------------------|----------------------|
| `list` | tasks.py:discover_tasks | `Path(root) / prefix / "artifacts" / "tasks"` | ✅ Yes — root from find_root() |
| `list` (editor) | tasks.py:cmd_list | `core.tasks_dir_path(root, prefix)` | ✅ Yes |
| `show` | tasks.py:cmd_show | `Path(root) / prefix / "artifacts" / "tasks"` | ✅ Yes |
| `create` | tasks.py:cmd_create | `core.tasks_dir_path(root, prefix)` | ✅ Yes |
| `status` | tasks.py:cmd_status | `core.tasks_dir_path(root, prefix)` | ✅ Yes |
| `status` (hooks) | hooks.py:run_matched | Uses `root` passed from cmd_status | ✅ Yes |
| `status` (parent auto-promote) | tasks.py:auto_promote_parent | Operates on `tasks_dir` from cmd_status | ✅ Yes |
| `agents list` | run.py:discover_agents | `Path(root) / prefix / "artifacts" / "agents"` | ✅ Yes |
| `agents show` | run.py:_find_agent_artifact | `Path(root) / prefix / "artifacts" / "agents"` | ✅ Yes |
| `artifacts list` | artifacts.py:discover_artifacts | `_artifacts_base(root, prefix)` | ✅ Yes |
| `artifacts show` | artifacts.py:resolve_artifact | `_artifacts_base(root, prefix)` | ✅ Yes |
| `run` (task spec read) | run.py:cmd_run | `core.tasks_dir_path(root, prefix)` | ✅ Yes |
| `run` (log dir) | run.py:run_single_task | `root / prefix / "artifacts" / "logs"` | ✅ Yes |
| `run` (agent spec) | run.py:find_agent_spec | `Path(root) / prefix / "agents"` and `Path(root) / "agents"` | ✅ Yes |
| settings.json | hooks.py:_settings_path | `root / prefix / "settings.json"` | ✅ Yes |

**Key insight:** `find_root()` (core.py:108-135) walks up from
CWD looking for OS markers. If the local walk-up fails (which it
will in a worktree that doesn't have `.openstation/` or
`agents/`+`install.sh`), it falls back to
`_git_main_worktree_root()` which uses `git rev-parse
--git-common-dir` to find the main repo. All downstream code uses
this `root` value.

**However**, there is a subtlety: if the worktree **does** check
out `artifacts/` (which it will by default since worktrees check
out the full tree), `find_root()` may find the markers in the
worktree itself and return the **worktree** root, not the main
repo root. This happens when:

1. The worktree is created from a branch that has `.openstation/`
   (installed projects), OR
2. The worktree is the source repo itself (has `agents/` +
   `install.sh`)

**This is the actual bug.** `find_root()` walks up from CWD and
finds markers in the worktree before it gets a chance to fall back
to the main repo. The fallback to `_git_main_worktree_root()` only
fires when the walk-up finds **nothing**.

### 2. Git-Level Sharing

**Approach:** Use sparse-checkout or `--no-checkout` with
selective checkout to prevent worktrees from having their own
copy of `artifacts/`.

**Pros:**
- Clean git status — no untracked or modified files for artifacts
- No runtime code changes needed (find_root would fail local
  walk-up and fall back to main repo correctly)
- Git-native solution

**Cons:**
- **Fragile setup** — every `git worktree add` must use correct
  sparse-checkout configuration; easy to get wrong
- **Breaks other tools** — editors, grep, git log, etc. won't see
  `artifacts/` files in the worktree
- **Claude Code --worktree** — Claude's own `--worktree` flag
  creates worktrees internally; we can't control its
  sparse-checkout config
- **Not composable** — other projects using Open Station can't be
  expected to configure sparse-checkout

**Verdict:** Not recommended. Too fragile and not compatible with
Claude Code's `--worktree` flag.

### 3. Symlink Approach

**Approach:** After creating a worktree, replace
`<worktree>/artifacts/` with a symlink to
`<main>/artifacts/`.

**Pros:**
- All file reads/writes transparently go to main repo
- No runtime code changes needed
- Works with any tool (editors, grep, etc.)

**Cons:**
- **Git tracks symlinks as files** — `git status` in the worktree
  shows `artifacts/` as modified (changed from dir to symlink)
- **Setup burden** — requires a post-worktree-create hook or
  manual step
- **Platform issues** — Windows symlinks require special
  permissions
- **Claude Code --worktree** — again, we can't hook into Claude's
  worktree creation to add the symlink
- **Dirty working tree** — the symlink change shows in `git diff`

**Verdict:** Workable but messy. The git status noise and setup
burden make it a poor fit.

### 4. Runtime Resolution (Recommended)

**Approach:** Modify `find_root()` to always resolve to the main
worktree root when running inside a git worktree, regardless of
whether markers exist in the worktree itself.

**What needs to change:**

1. **`find_root()`** (core.py) — After finding a root via
   walk-up, check whether we're in a worktree. If yes, resolve
   to the main worktree root instead.

   Implementation sketch:
   ```python
   def find_root(start=None):
       d = Path(start or os.getcwd()).resolve()
       # Walk-up as before
       local_root, local_prefix = _walk_up(d)

       # If we found something, check if we're in a worktree
       if local_root is not None:
           main_root = _git_main_worktree_root(d)
           if main_root and main_root.resolve() != local_root.resolve():
               # We're in a worktree — use main repo root
               root, prefix = _check_dir(main_root)
               if root is not None:
                   return root, prefix
           return local_root, local_prefix

       # Fallback (existing behavior)
       main_root = _git_main_worktree_root(...)
       ...
   ```

2. **No other call sites need changes** — all commands already
   use `root` from `find_root()`. The fix is centralized.

3. **Edge case: `run` CWD** — `run.py` correctly captures
   `exec_cwd = Path.cwd()` before resolving root, and passes it
   as the working directory for agent execution. This is already
   correct — code execution stays in the worktree, artifact ops
   use vault root.

4. **Edge case: log files** — Log files are written to
   `root/artifacts/logs/`, which would be the main repo. This is
   correct — logs should be shared.

5. **Edge case: relative path output** — `run.py:307` calls
   `log_file.relative_to(root)` which still works since both are
   in the main repo tree.

**Pros:**
- Single fix in one function
- No setup burden (no symlinks, no sparse-checkout)
- Works with Claude Code `--worktree` automatically
- Works with `worktrunk` and `workmux`
- No git status noise
- Fully transparent to all downstream commands

**Cons:**
- Behavioral change: if someone intentionally wants worktree-local
  artifacts, this prevents it. (This is not a current use case.)

### 5. Write Conflict Assessment

When two worktrees both write to the same `artifacts/` directory
(via runtime resolution to the main repo):

**Task creation (`create`):** Already race-safe. `create_task_file()`
uses `os.O_CREAT | os.O_EXCL` (atomic exclusive create) with
retry. Two concurrent creates will get different IDs.

**Status transitions (`status`):** Uses string replacement
(`update_frontmatter()`). Two concurrent transitions on the
**same** task could corrupt the file if they interleave. However,
this is a pre-existing risk even without worktrees (two terminals
in the main repo). The risk is low — tasks are typically assigned
to one agent.

**Frontmatter list append (`append_frontmatter_list`):** Not
atomic — read-modify-write cycle. Same pre-existing risk.

**Log files:** Each task writes to its own `<task-name>.jsonl`.
No cross-task conflict. Two agents on the same task would
interleave, but that's prevented by the lifecycle (only one agent
at a time).

**Summary:** No new race conditions are introduced by runtime
resolution. The existing non-atomic read-modify-write patterns
could be improved with file locking in the future, but this is
orthogonal to the worktree question.

### 6. Recommendation

**Runtime resolution in `find_root()`** is the clear winner.

- **Scope:** 1 function change (~10 lines) in `core.py`
- **Risk:** Low — centralizes the fix, no downstream changes
- **Compatibility:** Works with all worktree tools (Claude Code,
  worktrunk, workmux, raw git)
- **Testing:** Can be verified by running `openstation list` from
  a worktree and confirming it shows the same tasks as the main
  repo

**Implementation steps:**

1. Extract the walk-up loop into a helper `_walk_up(start)`
2. In `find_root()`, after walk-up succeeds, compare against
   `_git_main_worktree_root()`
3. If they differ, prefer the main root (with fallback to local
   if main root has no OS markers)
4. Add test: create worktree, run `openstation list` from it,
   verify output matches main repo

## Downstream

- **Implementation task needed** — Modify `find_root()` per the
  runtime resolution approach above. ~10 lines of code.
- **Test coverage** — Add integration test that creates a worktree
  and verifies artifact resolution from within it.
- **Documentation** — `docs/cli.md` should note that all artifact
  operations resolve to the vault root regardless of worktree.

## Progress

- 2026-03-18: Audited all CLI commands (list, show, create, status,
  agents, artifacts, run) for artifact path resolution. Evaluated
  3 approaches (git-level sharing, symlinks, runtime resolution).
  Recommended runtime resolution in find_root(). Write conflict
  analysis shows no new risks.

## Verification

- [x] All CLI commands that read/write artifacts are audited
- [x] At least 2 sharing approaches are evaluated with pros/cons
- [x] A recommended approach is documented with implementation sketch
- [x] Write conflict risks are assessed
