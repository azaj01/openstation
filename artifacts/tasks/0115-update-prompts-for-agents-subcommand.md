---
kind: task
name: 0115-update-prompts-for-agents-subcommand
type: documentation
status: done
assignee: author
owner: user
parent: "[[0111-cli-expand-agents-command-with]]"
created: 2026-03-11
---

# Update prompts for agents subcommand

Update slash commands, skills, and CLAUDE.md to reflect the new `agents` sub-actions after implementation.

## Requirements

1. Update `CLAUDE.md` CLI section to document `agents list`, `agents show`, `agents dispatch`
2. Update any commands or skills that reference `openstation agents` if they need to use new sub-actions
3. Update `/openstation.dispatch` command if it exists, or create one pointing to `agents dispatch`

## Verification

- [ ] `CLAUDE.md` documents the expanded agents subcommand
- [ ] Commands/skills referencing `openstation agents` are updated
- [ ] No stale references to the old single-action `agents` command
