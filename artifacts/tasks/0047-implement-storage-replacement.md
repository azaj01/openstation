---
kind: task
name: 0047-implement-storage-replacement
status: done
assignee: developer
owner: user
parent: "[[0045-replace-storage-obsidian-cli]]"
created: 2026-03-04
---

# Implement storage layer replacement

Implement the storage model defined in `docs/storage-query-layer.md`
(task 0046). Migrate tasks from folders (`NNNN-slug/index.md`) to
single files (`NNNN-slug.md`), remove all symlinks except discovery,
and update all code that reads/writes tasks.

## Requirements

### Migrate existing tasks to single files

- Convert every `artifacts/tasks/NNNN-slug/index.md` to
  `artifacts/tasks/NNNN-slug.md`
- Remove the now-empty task folders
- Delete all bucket symlinks (`tasks/backlog/`, `tasks/current/`,
  `tasks/done/`) and their contents
- Delete all sub-task symlinks from parent task folders
- Delete all traceability symlinks from task folders

### Update CLI (`bin/openstation`)

- Change `discover_tasks()` to scan `artifacts/tasks/*.md` instead
  of `artifacts/tasks/*/index.md`
- Remove `resolve_bucket()` and `bucket` key from task dicts
- Update `cmd_create` to write a single file, not a folder
- Update all task read/write paths to use `NNNN-slug.md`

### Update commands

- `/openstation.create` — create single file, no symlinks
- `/openstation.ready` — frontmatter edit only, no symlink moves
- `/openstation.done` — frontmatter edit only, keep agent
  discovery symlink creation for agent specs
- `/openstation.reject` — frontmatter edit only, no symlink moves

### Update execute skill (`skills/openstation-execute/`)

- Update task discovery paths from `*/index.md` to `*.md`
- Remove any references to bucket directories

### Update install script (`install.sh`)

- Stop creating `tasks/{backlog,current,done}` directories
- Keep `artifacts/` directory creation unchanged

### Add `subtasks` field to parent tasks

- Update existing parent tasks to include `subtasks` list in
  frontmatter per `docs/storage-query-layer.md` § 3a

**Spec to implement:** `docs/storage-query-layer.md`
**Additional context:** `artifacts/research/storage-layer-replacement.md`

## Verification

- [ ] No task folders remain — all tasks are single `.md` files in `artifacts/tasks/`
- [ ] No bucket directories (`tasks/backlog/`, `tasks/current/`, `tasks/done/`)
- [ ] No sub-task or traceability symlinks anywhere
- [ ] `openstation list` works with single-file tasks
- [ ] `openstation create` creates a single file (not a folder)
- [ ] Commands edit frontmatter only (no symlink operations)
- [ ] Execute skill discovers tasks from `artifacts/tasks/*.md`
- [ ] Parent tasks have `subtasks` frontmatter field
- [ ] Existing tests pass (update as needed for new paths)
