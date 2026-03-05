---
kind: task
name: 0051-cli-write-commands-spec
status: done
agent: architect
owner: user
parent: "[[0050-cli-write-commands]]"
artifacts:
  - "[[artifacts/specs/cli-write-commands]]"
created: 2026-03-05
---

# Spec CLI Write Commands

Write the specification for two new `openstation` CLI subcommands:
`create` and `status`.

## Requirements

1. Spec `openstation create <description>` — define argument
   parsing, ID auto-increment logic, slug generation, file
   format, optional flags (`--agent`, `--owner`, `--status`).
2. Spec `openstation status <task> <new-status>` — define
   argument parsing, valid transitions per `docs/lifecycle.md`,
   error messages for invalid transitions.
3. Propose a robust mechanism for generating the next task ID.
   Must handle concurrent creates without collisions and require
   minimal new components (no external services like Redis).
   Evaluate alternatives to scanning `artifacts/tasks/` and
   recommend the best approach.
4. When `--parent` is used, the CLI must automatically append
   the new task to the parent's `subtasks` frontmatter list.
   Both directions (child `parent` field and parent `subtasks`
   list) must be updated in a single `create` invocation.
   Revise DD-2 accordingly.
5. Document edge cases: duplicate slugs, missing task, already
   at target status.
6. Output spec to `artifacts/specs/cli-write-commands.md`.

**Context to read:**
- `bin/openstation` — existing CLI (patterns for `list`, `show`, `run`)
- `docs/lifecycle.md` — valid status transitions
- `docs/task.spec.md` — task frontmatter schema
- `docs/storage-query-layer.md` — storage model

## Findings

Spec produced at `artifacts/specs/cli-write-commands.md`. Key
decisions:

- **Task ID generation** uses `O_CREAT | O_EXCL` atomic file
  creation with retry (Option B), avoiding counter files or
  UUID-based IDs. See the alternatives analysis in the spec.
- **`--parent` auto-updates** the parent's `subtasks` frontmatter
  list via a new `append_frontmatter_list()` helper. DD-2 was
  revised from "no automatic editing" to "automatic line-by-line
  insertion" — safe because it only inserts lines, never modifies
  existing ones.
- **9 components** defined (C1–C9), all in `bin/openstation`
  with integration tests in `tests/test_cli_write.py`.

## Verification

- [x] Spec covers `create` subcommand with all arguments and flags
- [x] Spec covers `status` subcommand with transition validation
- [x] Task ID generation mechanism specified (robust, no external deps)
- [x] `--parent` auto-updates parent's `subtasks` list (DD-2 revised)
- [x] Edge cases documented (duplicates, missing task, no-op)
- [x] Spec is consistent with existing CLI patterns
- [x] Spec file written to `artifacts/specs/cli-write-commands.md`
