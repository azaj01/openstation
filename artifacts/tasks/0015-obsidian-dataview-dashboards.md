---
kind: task
name: 0015-obsidian-dataview-dashboards
status: done
assignee: author
owner: manual
created: 2026-02-27
---

# Implement Obsidian Dataview Dashboards

## Requirements

Replace the symlink-based project structure browsing with Dataview
query dashboards so Obsidian users can navigate tasks and agents
without relying on intra-vault symlinks (which Obsidian ignores
due to the disjoint rule — see `artifacts/research/obsidian-symlink-support.md`).

### Task Dashboard

Create `tasks-dashboard.md` at the vault root with Dataview
queries that replicate the lifecycle bucket views:

1. **Current** — table of tasks where `status` is `ready`,
   `in-progress`, or `review`, sorted by `created` ascending.
2. **Backlog** — table of tasks where `status` is `backlog`.
3. **Done** — table of tasks where `status` is `done` or `failed`,
   sorted by `created` descending.
4. Each table should show: task link, `status`, `agent`, `owner`,
   `created`.

### Agents Dashboard

Create `agents-dashboard.md` at the vault root with a Dataview
query listing all agent specs from `artifacts/agents/`, showing:
`name`, `description`, `model`.

### Documentation

- Add a brief note in `docs/` or the dashboard files explaining
  why Dataview is used instead of folder browsing (link to
  research artifact).

## Findings

Created two Dataview dashboard files at the vault root:

- **`tasks-dashboard.md`** — three `TABLE` queries (Current,
  Backlog, Done) sourced from `"artifacts/tasks"`, filtered by
  `kind = "task"` and the appropriate `status` values. Each table
  shows task link, status, agent, owner, and created date.

- **`agents-dashboard.md`** — single `TABLE` query sourced from
  `"artifacts/agents"`, filtered by `kind = "agent"`, showing
  name, description, and model.

Both dashboards include an inline explanation of why Dataview is
used (the disjoint rule) with a link to the research artifact.
No separate `docs/` file was needed since the context is
self-contained in the dashboard headers.

Design choices:
- Used `TABLE WITHOUT ID` with `link(file.path, name)` to render
  clickable task/agent links in Obsidian.
- Added `WHERE kind = "task"` / `kind = "agent"` guards so
  non-spec files in those directories are excluded.
- Gave both files `kind: dashboard` frontmatter so they can be
  identified programmatically if needed later.

## Verification

- [ ] `tasks-dashboard.md` exists and renders three Dataview
      tables (current, backlog, done)
- [ ] `agents-dashboard.md` exists and lists all agents from
      `artifacts/agents/`
- [ ] Dashboards query from `artifacts/` canonical paths, not
      symlink paths
- [ ] Dataview queries use correct frontmatter field names
      matching `docs/task.spec.md`
