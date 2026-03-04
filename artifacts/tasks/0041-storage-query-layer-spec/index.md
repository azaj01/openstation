---
kind: task
name: 0041-storage-query-layer-spec
status: done
agent: author
owner: user
created: 2026-03-04
---

# Storage & Query Layer Spec

Write a retrospective specification for Open Station's storage and
query layer — documenting the design as it exists today.

## Requirements

### Storage Layer

1. **Canonical storage model** — `artifacts/` as the single source
   of truth; folders never move once created.
2. **Symlink graph** — bucket symlinks (`tasks/backlog/`,
   `tasks/current/`, `tasks/done/`), sub-task symlinks
   (parent -> child), discovery symlinks (`agents/`), and
   traceability symlinks (task folder -> artifact).
3. **Lifecycle bucket mapping** — which statuses map to which
   buckets; how symlink moves represent state transitions.
4. **Artifact routing** — where different artifact types land
   (`artifacts/research/`, `artifacts/specs/`, `artifacts/agents/`,
   `artifacts/tasks/`).
5. **Sub-task storage** — canonical folder + parent symlink
   convention; no bucket symlinks for sub-tasks.
6. **Install-time layout** — how `install.sh` places the vault
   under `.openstation/` in target projects.
7. **Design rationale** — why symlinks over moves, why flat
   `artifacts/tasks/` over nested, why convention over database.

### Query Layer

8. **Find tasks by status** — how to list all tasks in a given
   status (e.g. all `ready` tasks, all `backlog` tasks) using
   bucket symlinks.
9. **Get all artifacts for a task** — how to discover artifacts
   produced by a task (frontmatter `artifacts` field + traceability
   symlinks in the task folder).
10. **Get all sub-tasks of a parent** — how to enumerate sub-tasks
    by following symlinks inside the parent folder.
11. **Find tasks by agent** — how to find all tasks assigned to a
    given agent (grep frontmatter across a bucket).
12. **Agent discovery** — how `agents/` symlinks resolve to
    canonical specs in `artifacts/agents/`.
13. **Query patterns summary** — a quick-reference table mapping
    common queries to the filesystem operation that answers them.

The spec should be written as a standalone document in
`artifacts/specs/` and conform to Open Station's spec format
(YAML frontmatter with `kind: spec`).

## Subtasks

### P0

1. **Create storage & query spec** (`0042-create-storage-query-spec`)
   — write `docs/storage-query-layer.md` covering all
   13 topics above.

2. **Dedupe storage docs** (`0043-dedupe-storage-docs`) — update
   existing specs to reference the new spec, removing repeated
   storage/symlink/query instructions.

## Verification

- [x] Spec file exists at `docs/storage-query-layer.md` with valid `kind: spec` frontmatter
- [x] All 7 storage layer topics (items 1-7) are covered
- [x] All 6 query layer topics (items 8-13) are covered
- [x] Query patterns summary table is present and covers at least: find by status, find by agent, get artifacts, get sub-tasks, agent discovery
- [x] Design rationale section explains the symlink-over-move and convention-over-database choices
- [x] Spec is accurate against the current implementation (cross-checked with `docs/lifecycle.md`, `docs/task.spec.md`, and `install.sh`)
