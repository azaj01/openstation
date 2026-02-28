---
kind: dashboard
name: tasks-dashboard
---

# Tasks

> Dataview dashboard replacing symlink-based bucket browsing.
> Obsidian ignores intra-vault symlinks (the "disjoint rule"),
> so lifecycle views are rendered via frontmatter queries instead.
> See `artifacts/research/obsidian-symlink-support.md` for details.

## Current

```dataview
TABLE WITHOUT ID
  link(file.path, name) AS "Task",
  status AS "Status",
  agent AS "Agent",
  owner AS "Owner",
  created AS "Created"
FROM "artifacts/tasks"
WHERE kind = "task"
  AND (status = "ready" OR status = "in-progress" OR status = "review")
SORT created ASC
```

## Backlog

```dataview
TABLE WITHOUT ID
  link(file.path, name) AS "Task",
  agent AS "Agent",
  owner AS "Owner",
  created AS "Created"
FROM "artifacts/tasks"
WHERE kind = "task" AND status = "backlog"
SORT created ASC
```

## Done

```dataview
TABLE WITHOUT ID
  link(file.path, name) AS "Task",
  status AS "Status",
  agent AS "Agent",
  owner AS "Owner",
  created AS "Created"
FROM "artifacts/tasks"
WHERE kind = "task"
  AND (status = "done" OR status = "failed")
SORT created DESC
```
