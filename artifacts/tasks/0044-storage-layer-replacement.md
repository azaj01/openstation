---
kind: task
name: 0044-storage-layer-replacement
status: done
assignee: researcher
owner: user
artifacts:
  - artifacts/research/storage-layer-replacement.md
created: 2026-03-04
---

# Research storage layer replacement

## Requirements

Research whether the current symlink-based storage and query layer
can be replaced with a simpler, frontmatter-query approach. Evaluate
two alternatives:

1. **Dataview-style queries** — The Obsidian dashboard
   (`tasks/dashboard.md`) already uses frontmatter queries to render
   task views, making the `tasks/backlog/`, `tasks/current/`,
   `tasks/done/` symlinks redundant for browsing. Investigate whether
   the CLI (`openstation list`, `openstation show`) and the execute
   skill can work purely from frontmatter queries on `artifacts/tasks/`
   — eliminating bucket symlinks entirely.

2. **Obsidian CLI** — Evaluate https://help.obsidian.md/cli for
   vault management capabilities. Can it replace or complement our
   custom CLI for task discovery, querying, and lifecycle transitions?

**Context to read:**
- `docs/storage-query-layer.md` — current storage spec (symlinks,
  canonical folders, sub-task conventions)
- `tasks/dashboard.md` — existing dataview-based dashboard
- Current CLI source (`bin/openstation`) — how it discovers tasks today

**Deliverables:**
- Research artifact (`artifacts/research/storage-layer-replacement.md`)
  with:
  - Current architecture summary (what symlinks do today)
  - Per-alternative assessment (feasibility, trade-offs, migration path)
  - Recommendation: replace, hybrid, or keep current approach
  - If replacement is recommended, outline what changes are needed
    (CLI, skill, docs, install script)

## Findings

Research artifact: `artifacts/research/storage-layer-replacement.md`

**Recommendation: REPLACE bucket symlinks + ADOPT Obsidian CLI**
as the primary query engine. Keep discovery, traceability, and
sub-task symlinks.

Key findings:

1. **The system is already 90% there.** The CLI (`discover_tasks()`)
   scans `artifacts/tasks/` directly and reads frontmatter. The
   dashboard uses Dataview queries on `artifacts/tasks/`. Bucket
   symlinks are only actively maintained by the four lifecycle
   commands — nothing reads them on the primary query paths.

2. **Bucket symlinks are pure overhead.** They duplicate the
   frontmatter `status` field, create state-split risk, and add
   complexity to every lifecycle command for no query benefit.

3. **Obsidian CLI is viable and powerful.** An official CLI ships
   with Obsidian 1.12+ (80+ commands). It supports frontmatter
   property queries with AND combination (`[kind: task] [status:
   ready] [agent: researcher]`), property read/write, file
   operations, and JSON output. It can replace `discover_tasks()`
   and frontmatter parsing. Requires Obsidian running — filesystem
   fallback needed for headless/CI environments.

4. **Migration is low-risk.** Changes are confined to removing
   symlink operations from commands, adopting Obsidian CLI queries
   with filesystem fallback, and doc updates. Bucket symlinks can
   be left in place (inert) or removed — no data loss either way.

## Recommendations

Proceed with a phased implementation:

- **Phase 1 (core):** Replace `discover_tasks()` with Obsidian CLI
  queries (filesystem fallback). Remove bucket symlink operations
  from commands. Update execute skill.
- **Phase 2 (docs):** Update storage-query-layer.md, lifecycle.md,
  task.spec.md, CLAUDE.md.
- **Phase 3 (cleanup):** Optionally remove `tasks/{backlog,current,done}`
  directories from existing vaults.

## Verification

- [x] Research artifact exists at `artifacts/research/storage-layer-replacement.md`
- [x] Current symlink architecture is summarized (what symlinks do, where they exist, what depends on them)
- [x] Dataview-style query approach is assessed with feasibility, trade-offs, and migration path
- [x] Obsidian CLI is evaluated for vault management capabilities relevant to our use case
- [x] Clear recommendation is provided (replace, hybrid, or keep) with rationale
- [x] If replacement is recommended, required changes are outlined (CLI, skill, docs, install script)
