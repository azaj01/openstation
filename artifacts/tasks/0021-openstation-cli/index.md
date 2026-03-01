---
kind: task
name: 0021-openstation-cli
status: backlog
agent: researcher
owner: manual
created: 2026-02-28
---

# Create OpenStation CLI

## Requirements

Build a CLI tool (`openstation`) that replaces prompt-driven task
and artifact management with deterministic, scriptable commands.

1. **Core commands** — mirror existing slash commands with a proper
   CLI interface:
   - `openstation create <description>` — create a task spec
   - `openstation list [--status <s>] [--agent <a>]` — list tasks
   - `openstation show <task>` — display task details
   - `openstation ready <task> [--agent <a>]` — promote to ready
   - `openstation done <task>` — mark complete, move to done
   - `openstation reject <task> [reason]` — mark failed
   - `openstation update <task> <field:value>...` — update metadata
   - `openstation dispatch <agent>` — show agent launch info

2. **Symlink management** — all status transitions must move
   symlinks between `tasks/backlog/`, `tasks/current/`,
   `tasks/done/` correctly.

3. **ID auto-increment** — `create` scans `artifacts/tasks/` for
   the highest `NNNN-*` prefix and increments.

4. **Validation** — enforce task spec schema (required frontmatter
   fields, valid status values, symlink integrity).

5. **Zero runtime dependencies** — use only standard library of
   the chosen language (bash or Python). No external packages.

6. **Idempotent operations** — running the same command twice must
   not corrupt state (duplicate symlinks, lost files).

7. **Integration** — the CLI must work both in the source repo
   (root-level structure) and in target projects where
   `install.sh` places files under `.openstation/`.

## Subtasks

### Phase 1 — Research

1. **0022-cli-feature-research** — Research CLI design decisions:
   language choice, CLI patterns, symlink edge cases, integration
   detection strategy

### Phase 2 — Spec

2. **0023-cli-feature-spec** — Write detailed technical spec for
   all commands, file layout, error handling, and testing strategy

### Phase 3 — Implementation

3. **0024-cli-implementation** — Implement the CLI per spec, with
   tests and zero external dependencies

## Verification

- [ ] `openstation create "test task"` creates folder + index.md + symlink
- [ ] `openstation list` shows all tasks with status and agent
- [ ] `openstation list --status ready` filters correctly
- [ ] `openstation ready <task>` moves symlink from backlog to current
- [ ] `openstation done <task>` moves symlink to done, sets status
- [ ] `openstation reject <task> "reason"` sets status to failed
- [ ] `openstation update <task> agent:researcher` updates frontmatter
- [ ] `openstation show <task>` prints full task spec
- [ ] Running `create` twice with same description produces unique IDs
- [ ] Works in both source repo and `.openstation/` installed projects
- [ ] No external dependencies required
