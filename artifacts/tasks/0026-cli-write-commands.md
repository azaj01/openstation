---
kind: task
name: 0026-cli-write-commands
status: failed
reason: Obsolete — references symlink-based storage model replaced by task 0045. Write commands already exist as slash commands (commands/).
assignee:
owner: user
created: 2026-03-01
---

# OpenStation CLI — Write Commands

## Requirements

Extend the `openstation` CLI (built in 0021) with the remaining
write commands that mutate task state:

1. **Commands to implement:**
   - `openstation create <description>` — create a task spec
     (folder + index.md + symlink, auto-increment ID)
   - `openstation ready <task> [--agent <a>]` — promote from
     backlog to ready, move symlink to `tasks/current/`
   - `openstation done <task>` — mark complete, move symlink to
     `tasks/done/`
   - `openstation reject <task> [reason]` — mark failed, append
     rejection reason to spec
   - `openstation update <task> <field:value>...` — update
     frontmatter metadata fields
   - `openstation dispatch <agent>` — show agent details and
     launch instructions for ready tasks

2. **Symlink management** — all status transitions must move
   symlinks between `tasks/backlog/`, `tasks/current/`,
   `tasks/done/` correctly.

3. **ID auto-increment** — `create` scans `artifacts/tasks/` for
   the highest `NNNN-*` prefix and increments.

4. **Validation** — enforce task spec schema (required frontmatter
   fields, valid status values, symlink integrity).

5. **Idempotent operations** — running the same command twice must
   not corrupt state (duplicate symlinks, lost files).

6. **Zero runtime dependencies** — same constraint as 0021.

## Verification

- [ ] `openstation create "test task"` creates folder + index.md + symlink
- [ ] Running `create` twice with same description produces unique IDs
- [ ] `openstation ready <task>` moves symlink from backlog to current
- [ ] `openstation done <task>` moves symlink to done, sets status
- [ ] `openstation reject <task> "reason"` sets status to failed, appends reason
- [ ] `openstation update <task> agent:researcher` updates frontmatter
- [ ] `openstation dispatch <agent>` shows agent info and ready tasks
- [ ] Idempotent: repeated commands don't corrupt state
- [ ] No external dependencies required
