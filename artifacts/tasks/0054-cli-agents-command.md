---
kind: task
name: 0054-cli-agents-command
status: done
agent: developer
owner: user
created: 2026-03-05
---

# CLI Agents Command

Add an `openstation agents` subcommand and update the create task
flow and documentation to use it.

## Requirements

1. Add `openstation agents` subcommand — scan
   `artifacts/agents/*.md`, parse frontmatter, display a table
   (name, description/role). Follow existing CLI patterns.
2. Update `/openstation.create` command
   (`commands/openstation.create.md`) — step 5d should run
   `openstation agents` to list available agents before suggesting
   one, instead of relying on a hardcoded list.
3. Update documentation — add the `agents` subcommand to
   `CLAUDE.md`, `docs/storage-query-layer.md` query patterns, and
   `skills/openstation-execute/SKILL.md` where CLI subcommands
   are referenced.

## Verification

- [ ] `openstation agents` lists all agents from `artifacts/agents/`
- [ ] Output includes agent name and description/role
- [ ] `commands/openstation.create.md` step 5d references `openstation agents`
- [ ] `CLAUDE.md` documents the `agents` subcommand
- [ ] Docs/skills updated with the new command
- [ ] No external dependencies added
