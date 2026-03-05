---
kind: task
name: 0053-cli-write-commands-prompts
status: done
agent: author
owner: user
parent: "[[0050-cli-write-commands]]"
created: 2026-03-05
---

# Update Commands and Skills for CLI Write Commands

Update slash commands and the execute skill to use the new CLI
`create` and `status` subcommands instead of manual file edits.

## Requirements

1. Update `commands/openstation.create.md` — use
   `openstation create` as primary method, keep manual fallback.
2. Update `commands/openstation.ready.md` — use
   `openstation status <task> ready` instead of manual
   frontmatter edit.
3. Update `commands/openstation.done.md` — use
   `openstation status <task> done` instead of manual edit.
4. Update `commands/openstation.reject.md` — use
   `openstation status <task> failed` instead of manual edit.
5. Update `commands/openstation.update.md` — reference CLI
   where applicable.
6. Update `skills/openstation-execute/SKILL.md` — agents should
   use CLI subcommands for status transitions during execution.

**Context to read:**
- `bin/openstation` — after task 0052 is complete
- All files listed above (current versions)

## Verification

- [x] `openstation.create.md` references `openstation create`
- [x] `openstation.ready.md` references `openstation status`
- [x] `openstation.done.md` references `openstation status`
- [x] `openstation.reject.md` references `openstation status`
- [x] Execute skill uses CLI for status transitions
- [x] Manual fallback preserved in all commands
