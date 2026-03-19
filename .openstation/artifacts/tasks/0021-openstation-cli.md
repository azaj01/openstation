---
kind: task
name: 0021-openstation-cli
status: done
assignee: researcher
owner: manual
created: 2026-02-28
subtasks:
  - "[[0022-cli-feature-research]]"
  - "[[0023-cli-feature-spec]]"
  - "[[0024-cli-implementation]]"
---

# OpenStation CLI — List & Show

## Requirements

Build a minimal CLI tool (`openstation`) that implements the two
read-only commands: `list` and `show`. This is an MVP scoped to
replace the prompt-driven equivalents with deterministic,
scriptable commands.

1. **Commands** — two subcommands only:
   - `openstation list [--status <s>] [--agent <a>]` — list tasks
     as a formatted table. Exclude `done`/`failed` by default;
     `--status done` or `--status all` overrides.
   - `openstation show <task>` — display full task spec (frontmatter
     + body) for a given task ID or slug.

2. **Task discovery** — scan `artifacts/tasks/*/index.md`, parse
   YAML frontmatter, and resolve symlink buckets to determine
   lifecycle stage.

3. **Zero runtime dependencies** — use only the standard library
   of the chosen language (bash or Python). No external packages.

4. **Integration** — the CLI must work both in the source repo
   (root-level structure) and in target projects where
   `install.sh` places files under `.openstation/`.

5. **Output** — `list` outputs a markdown table to stdout; `show`
   outputs the raw spec file content.

## Subtasks

### Phase 1 — Research (done)

1. **0022-cli-feature-research** — Research CLI design decisions:
   language choice, argument parsing, root detection strategy

### Phase 2 — Spec (review)

2. **0023-cli-feature-spec** — Technical spec for `list` and
   `show` commands, file layout, error handling, testing strategy

### Phase 3 — Implementation

3. **0024-cli-implementation** — Implement `list` and `show`
   per spec, with integration tests and zero dependencies

## Verification

- [x] `openstation list` shows non-done tasks with status, agent, owner
- [x] `openstation list --status ready` filters correctly
- [x] `openstation list --status all` includes done/failed tasks
- [x] `openstation list --agent researcher` filters by agent
- [x] `openstation show <task>` prints full task spec
- [x] `openstation show` with invalid task prints an error message
- [x] Works in both source repo and `.openstation/` installed projects
- [x] No external dependencies required
