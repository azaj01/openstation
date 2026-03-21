---
kind: task
name: 0189-cli-suspend-subcommand-add-openstation
type: feature
status: done
assignee: developer
owner: user
parent: "[[0196-task-suspension-backward-transitions-from]]"
created: 2026-03-21
---

# Cli Suspend Subcommand — Add Openstation Suspend With Transition Table Update

## Context

Spec: `[[artifacts/specs/task-suspension-model]]` (from task
`[[0188-research-task-suspension-model-design]]`). See §§ 1, 3
for transition table and CLI subcommand details.

## Requirements

Add `in-progress → ready` and `in-progress → backlog` to the
transition table. No new subcommand — `openstation status` handles
the transition, hooks handle suspend-specific behavior.

### 1. Transition Table Update

Add `ready` and `backlog` as valid targets from `in-progress`
in the transition validation table (likely `src/openstation/core.py`):

```python
"in-progress": ["review", "rejected", "ready", "backlog"],
```

### 2. Suspend Hook — `bin/hooks/suspend`

A post-transition hook triggered on `in-progress→ready` and
`in-progress→backlog`. Similar pattern to `bin/hooks/auto-commit`.

Behavior:
1. Prompt user: "Save uncommitted work to a branch? (y/n)"
2. If yes: create `suspend/<task-name>` branch, auto-commit
   related changes via `claude -p` (same tool-scoping as
   `auto-commit`), switch back to original branch
3. Append `## Suspended` section to task body (see format below)
4. Print confirmation

### 3. `## Suspended` Section Format

```markdown
## Suspended

**Date:** YYYY-MM-DD
**Target:** ready|backlog
**Reason:** <reason or "—">
**Branch:** `suspend/<task-name>` (or "—")
```

If `## Suspended` already exists, append a new entry below with
`---` separator.

### 4. Hook Registration

Register the hook in settings for the `in-progress→ready` and
`in-progress→backlog` transitions (see `docs/hooks.md` for
configuration format).

## Progress

### 2026-03-21 — developer

Implemented transition table update, suspend hook, hook registration, and tests. All 23 related tests pass (15 status + 8 suspend hook).

## Findings

Implemented the suspend feature in four parts:

1. **Transition table** (`src/openstation/core.py`): Added
   `("in-progress", "ready")` and `("in-progress", "backlog")`
   to `VALID_TRANSITIONS`. The existing `openstation status`
   command now handles both transitions — no new subcommand needed.

2. **Suspend hook** (`bin/hooks/suspend`): Bash script following
   the `auto-commit` pattern. On `in-progress→ready` or
   `in-progress→backlog`, it prompts for a reason, offers to
   save uncommitted work to a `suspend/<task-name>` branch
   (using `claude -p` for auto-commit), and appends a
   `## Suspended` section to the task body. Handles edge cases:
   no changes, existing branch, non-interactive mode.

3. **Hook registration** (`.openstation/settings.json`): Two new
   post-hook entries for `in-progress→ready` and
   `in-progress→backlog`, both with 120s timeout.

4. **Tests**: Added `test_status_in_progress_to_ready` and
   `test_status_in_progress_to_backlog` to `tests/test_cli.py`.
   Created `tests/test_suspend_hook.py` with 8 tests covering
   section appending, multiple suspensions, backlog target,
   no-changes skip, wrong-status guard, and confirmation output.

## Verification

- [x] Transition table allows `in-progress → ready` and `in-progress → backlog`
- [x] `openstation status <task> ready` works from `in-progress`
- [x] `openstation status <task> backlog` works from `in-progress`
- [x] Suspend hook fires on both transitions
- [x] Hook prompts to save work and creates `suspend/<task-name>` branch when accepted
- [x] `## Suspended` section is appended with correct format (Date, Target, Reason, Branch)
- [x] Multiple suspensions append with `---` separator (not overwrite)
- [x] Hook skips branch creation gracefully when no uncommitted changes

## Verification Report

*Verified: 2026-03-21*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Transition table allows `in-progress → ready` and `in-progress → backlog` | PASS | `VALID_TRANSITIONS` in `src/openstation/core.py` L35-36 contains both tuples |
| 2 | `openstation status <task> ready` works from `in-progress` | PASS | CLI test `test_status_in_progress_to_ready` asserts rc=0 and output contains "in-progress → ready" |
| 3 | `openstation status <task> backlog` works from `in-progress` | PASS | CLI test `test_status_in_progress_to_backlog` asserts rc=0 and output contains "in-progress → backlog" |
| 4 | Suspend hook fires on both transitions | PASS | `settings.json` registers `bin/hooks/suspend` for both `in-progress→ready` and `in-progress→backlog` matchers |
| 5 | Hook prompts to save work and creates `suspend/<task-name>` branch | PASS | Hook L58-65 prompts "Save uncommitted work to a branch? (y/n)", L79 creates branch via `git checkout -b`, L82-124 auto-commits via `claude -p` |
| 6 | `## Suspended` section with correct format | PASS | Hook L140-143 writes Date/Target/Reason/Branch fields; test `test_appends_suspended_section_before_verification` confirms |
| 7 | Multiple suspensions append with `---` separator | PASS | Hook L146-178 detects existing `## Suspended` and inserts with `---` separator; test `test_multiple_suspensions_append_with_separator` confirms |
| 8 | Hook skips branch creation when no changes | PASS | Hook L53-56 detects no changes, L66-68 prints skip message; test `test_no_branch_when_no_uncommitted_changes` confirms `**Branch:** —` |

### Summary

8 passed, 0 failed. All verification criteria met.
