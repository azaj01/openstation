---
kind: task
name: 0151-auto-commit-hook-requests-permission
type: bug
status: done
assignee: developer
owner: user
created: 2026-03-17
---

# Auto-Commit Hook Requests Permission Instead Of Running Non-Interactively

## Requirements

1. The `bin/hooks/auto-commit` post-hook spawns `claude -p`, which
   prompts the user to approve `git add` — hooks must run
   non-interactively without requiring user approval.
2. Investigate root cause: the hook's `claude -p` invocation likely
   needs `--dangerously-skip-permissions` or scoped `allowedTools`
   that pre-authorize `Bash(git *)` commands.
3. Fix the hook script so that `git add` and `git commit` execute
   without interactive approval prompts.
4. Ensure the fix doesn't open excessive permissions — scope
   allowed tools to the minimum needed (read + git
   staging/committing).

## Findings

**Root cause:** `bin/hooks/auto-commit` line 109 used
`--allowedTools 'Bash(readonly=false),...'` — `Bash(readonly=false)` is
not a valid `--allowedTools` pattern. Claude Code's `--allowedTools`
expects command-scoped patterns like `Bash(git:*)`. Since the pattern
was invalid, Bash was not pre-authorized, causing interactive permission
prompts even in `-p` (print) mode.

**Fix:** Changed `Bash(readonly=false)` → `Bash(git:*)` in the
`claude -p` invocation. This pre-authorizes all git commands (status,
diff, add, commit, ls-files) while blocking non-git bash commands —
minimal permissions for the hook's purpose.

**Files changed:**
- `bin/hooks/auto-commit` — fixed `--allowedTools` pattern
- `docs/hooks.md` — updated tool scoping description to match
- `tests/test_auto_commit_hook.py` — added regression tests for
  allowed-tools scoping

## Progress

### 2026-03-17 — developer
> time: 16:17

Fixed Bash(readonly=false) → Bash(git:*) in auto-commit hook. Updated docs/hooks.md and added regression tests. All 347 tests pass.

## Verification

- [ ] `openstation status <task> done` with the auto-commit hook triggers a commit without interactive prompts
- [ ] Hook still correctly scopes to task-related files only (no `git add .`)
- [ ] Hook exits cleanly (exit 0) on success
