---
kind: task
name: 0052-cli-write-commands-impl
status: done
assignee: developer
owner: user
parent: "[[0050-cli-write-commands]]"
created: 2026-03-05
---

# Implement CLI Write Commands

Implement `create` and `status` subcommands in `bin/openstation`
per the spec from task 0051.

## Requirements

1. Implement `openstation create <description>` — scan
   `artifacts/tasks/` for highest ID, increment, generate slug,
   write single `.md` file with frontmatter.
2. Implement `openstation status <task> <new-status>` — read
   task file, validate transition per lifecycle rules, update
   `status` field in frontmatter.
3. Add tests in `tests/test_cli.py` for both subcommands.
4. Zero external dependencies. Follow existing CLI patterns.

**Spec to implement:** `artifacts/specs/cli-write-commands.md`
(from task 0051)

## Verification

- [x] `openstation create "test task"` creates `artifacts/tasks/NNNN-test-task.md`
- [x] Running `create` twice produces unique sequential IDs
- [x] `openstation status <task> ready` updates frontmatter
- [x] Invalid transitions are rejected with error message
- [x] Tests pass for both subcommands
- [x] No external dependencies added
