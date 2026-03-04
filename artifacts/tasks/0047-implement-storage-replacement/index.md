---
kind: task
name: 0047-implement-storage-replacement
status: ready
agent: developer
owner: user
parent: 0045-replace-storage-obsidian-cli
created: 2026-03-04
---

# Implement storage layer replacement

Update CLI, commands, execute skill, and install script to remove
bucket symlink operations and adopt Obsidian CLI as the primary
query engine with filesystem fallback.

Based on research in `artifacts/research/storage-layer-replacement.md`
(task 0044).

## Requirements

**CLI (`bin/openstation`):**
- Replace `discover_tasks()` with Obsidian CLI calls:
  `obsidian search vault=<name> query='[kind: task] ...' format=json`
- Keep filesystem scanning (`artifacts/tasks/*/index.md` + YAML
  parsing) as fallback when Obsidian is not running
- Remove `resolve_bucket()` function and `bucket` key from task dicts
- Detect Obsidian availability (try CLI, catch failure, fall back)

**Commands:**
- `/openstation.create` — remove symlink creation steps (steps 7-8
  for regular tasks). Keep frontmatter-only creation. Consider
  using `obsidian create` + `obsidian property:set` when available.
- `/openstation.ready` — remove symlink move step (step 8). Keep
  frontmatter `status` edit only.
- `/openstation.done` — remove symlink move step (step 5). Keep
  frontmatter edit + artifact promotion logic.
- `/openstation.reject` — remove symlink move step (step 6). Keep
  frontmatter edit only.

**Execute skill (`skills/openstation-execute/`):**
- Update fallback discovery from `tasks/current/` scan to
  `artifacts/tasks/` scan with frontmatter status filter
- Primary path can use `obsidian search query='[kind: task]
  [status: ready] [agent: $AGENT]'` for faster task discovery

**Install script (`install.sh`):**
- Stop creating `tasks/{backlog,current,done}` directories and
  `.gitkeep` files
- Keep all `artifacts/` directory creation unchanged

**Context to read:**
- `artifacts/research/storage-layer-replacement.md` — full research
  with Obsidian CLI command reference and mapping table
- `bin/openstation` — current CLI source
- `commands/` — current command specs
- `skills/openstation-execute/SKILL.md` — current execute skill

## Verification

- [ ] `openstation list` works via Obsidian CLI when Obsidian is running
- [ ] `openstation list` falls back to filesystem scan when Obsidian is not running
- [ ] `/openstation.create` creates task without bucket symlink
- [ ] `/openstation.ready`, `/openstation.done`, `/openstation.reject` edit frontmatter only (no symlink moves)
- [ ] Execute skill discovers tasks from `artifacts/tasks/` (not `tasks/current/`)
- [ ] `install.sh` no longer creates `tasks/{backlog,current,done}` directories
