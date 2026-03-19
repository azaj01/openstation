---
kind: task
name: 0120-remove-agents-dispatch-subcommand-replace
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-12
---

# Remove `agents dispatch` subcommand

## Context

With `--attached` mode on `openstation run` (see 0119 research),
`agents dispatch` becomes redundant. `openstation run <agent>`
already covers agent-based interactive launches.

## Requirements

1. Remove `agents dispatch` subcommand from CLI parser (`cli.py`)
   and handler (`cmd_agents_dispatch` in `run.py`)
2. Ensure `openstation run <agent>` covers the dispatch use case —
   it already launches interactively via `os.execvp` for agent-only runs
3. Remove or redirect `commands/openstation.dispatch.md` slash command
4. Update references in `CLAUDE.md`, `docs/cli.md`, and agent specs
   that mention `agents dispatch`
5. Keep `agents list` and `agents show` untouched

## Verification

- [x] `openstation agents dispatch` is no longer a valid subcommand
- [x] `openstation run <agent>` still works as the replacement
- [x] No dangling references to `agents dispatch` in docs/commands
- [x] Tests updated (remove dispatch tests, if any)

## Implementation Notes

Implemented as part of the attached-mode-run spec. Changes:

- Removed `cmd_agents_dispatch` from `run.py`
- Removed `dispatch` subparser from `cli.py`
- Removed `commands/openstation.dispatch.md`
- Removed `dispatch.md` from `INIT_COMMANDS` in `init.py`
- Updated `CLAUDE.md`, `docs/cli.md` — no remaining dispatch references
- Removed all dispatch tests from `test_cli.py` and `test_agents_subcommand.py`
- All 219 tests pass
