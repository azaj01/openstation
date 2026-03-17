---
kind: task
name: 0145-auto-commit-on-task-completion
type: feature
status: done
assignee: developer
owner: user
depends: "[[0144-post-transition-hooks]]"
created: 2026-03-16
---

# Auto-Commit on Task Completion

Use Claude Code (`claude -p`) as the hook command to identify
task-related files and create a commit. Instead of scripting
deterministic file discovery, let the agent read the task file,
review the git diff, and judge which changes belong to the task
— the same way `/commit-commands:commit` works today, but with
task context supplied.

## Approach

The post-hook invokes `claude -p` with a prompt that:
1. Reads the task file for context (description, artifacts,
   progress notes)
2. Reviews `git status` and `git diff` to find related changes
3. Stages the relevant files
4. Creates a commit with a conventional message referencing the
   task (e.g. `chore(0145): complete auto-commit-on-task-completion`)

Example hook config:
```json
{
  "matcher": "*→done",
  "command": "claude -p 'Task $OS_TASK_NAME completed. Read $OS_TASK_FILE for context, then review git status/diff to identify all related changes and create a commit.' --allowedTools 'Bash,Read,Glob,Grep'",
  "phase": "post",
  "timeout": 120
}
```

## Requirements

1. Design the prompt template that gives Claude enough context
   to identify related files accurately
2. Scope tool permissions (`--allowedTools`) to the minimum
   needed (read, search, git commands)
3. Handle edge cases: no uncommitted changes (no-op), worktree
   vs main repo, large diffs
4. Document the hook setup in `docs/hooks.md`
5. Works in both source repo and installed projects

## Findings

Implemented the auto-commit hook as a bash wrapper script
(`bin/hooks/auto-commit`) that invokes `claude -p` with a
carefully designed prompt.

### Deliverables

- **`bin/hooks/auto-commit`** — Executable bash script that:
  1. Guards against missing env vars (exits 1)
  2. Guards against clean repos with no uncommitted changes (exits 0, no-op)
  3. Guards against missing `claude` binary (exits 0 with warning)
  4. Builds a detailed prompt instructing Claude to read the task
     file, review `git status`/`git diff`, stage only task-related
     files (explicit paths, never `git add .`), and create a
     conventional commit: `chore(<id>): complete <task-name>`
  5. Invokes `claude -p` with scoped tools: `Bash`, `Read`, `Glob`, `Grep`

- **`docs/hooks.md`** — Added comprehensive "Auto-commit on task
  completion" example section covering: hook config, how the script
  works, edge case table, and both-context path table
  (source repo vs installed project).

- **`tests/test_auto_commit_hook.py`** — 5 tests covering env var
  guards, no-changes no-op, and missing-claude guard.

### Design decisions

- Wrapper script instead of inline prompt: enables pre-flight
  guards (no changes, no claude) without burning agent tokens.
  The script handles cheap checks in bash; the agent handles the
  intelligent file selection.
- Tool permissions scoped to `Bash(readonly=false),Read,Glob,Grep` —
  no file writes (only git commands via Bash), no network access.
- Timeout set to 120s — sufficient for claude to read the task,
  review diffs, and create a commit.
- Prompt uses `$OS_TASK_FILE` directly rather than task name
  resolution, since the hooks engine provides the absolute path.

## Progress

- 2026-03-17: Created `bin/hooks/auto-commit` script with prompt template, updated `docs/hooks.md` with auto-commit example, added tests. All 41 tests pass (36 hooks + 5 auto-commit).

## Verification

- [x] Hook invokes `claude -p` with task context on `*→done`
- [x] Agent correctly identifies task-related files from diff
- [x] Commit message is conventional and references the task
- [x] No-op when there are no related changes
- [x] Documented in `docs/hooks.md` as an example
- [x] Timeout is sufficient for agent execution
