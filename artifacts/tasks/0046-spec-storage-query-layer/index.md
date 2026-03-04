---
kind: task
name: 0046-spec-storage-query-layer
status: done
agent: author
owner: user
parent: 0045-replace-storage-obsidian-cli
created: 2026-03-04
---

# Spec storage & query layer

Rewrite `docs/storage-query-layer.md` and related documentation to
reflect the new architecture: tasks are single files (not folders),
no symlinks (except discovery symlinks for Claude Code agent
resolution), frontmatter as single source of truth for all
relationships, Obsidian CLI with Dataview queries as the primary
query engine, filesystem fallback for headless/CI.

Based on research in `artifacts/research/storage-layer-replacement.md`
(task 0044). The chosen approach leverages Obsidian CLI combined with
Dataview queries for task discovery and filtering.

## Requirements

### Eliminate all symlinks except discovery

Remove **all** symlink types from the storage model except discovery
symlinks (agents/ → artifacts/agents/), which are required for
Claude Code `--agent` resolution. Specifically:

- Remove sub-task symlinks (current § 2a) — replace with
  frontmatter `subtasks` list in the parent task
- Remove traceability symlinks (current § 2c) — replace with
  frontmatter `artifacts` list (already exists) plus `task` and
  `agent` fields on artifact frontmatter
- Keep discovery symlinks (current § 2b) — rename to § 2a since
  it becomes the only symlink type

### Frontmatter-based associations

All relationships are encoded in frontmatter fields:

1. **Parent → children:** parent task lists subtasks in a
   `subtasks` frontmatter field:
   ```yaml
   subtasks:
     - 0046-spec-storage-query-layer
     - 0047-implement-storage-replacement
   ```
2. **Child → parent:** subtask declares its parent (already
   exists):
   ```yaml
   parent: 0045-replace-storage-obsidian-cli
   ```
3. **Artifact provenance:** artifacts declare which agent
   generated them and which task they belong to:
   ```yaml
   agent: researcher
   task: 0044-storage-layer-replacement
   ```
   Use `agent: manual` and omit `task` for manually created
   artifacts.

### File-level changes

**`docs/storage-query-layer.md`:**
- Rewrite § 2 (Symlink Graph) — keep only discovery symlinks
  (§ 2a becomes the sole subsection); remove sub-task and
  traceability symlink subsections entirely
- Remove § 3 (lifecycle bucket mapping) — already done in
  previous pass
- Add documentation for the new frontmatter association fields
  (`subtasks`, artifact `task`/`agent` provenance)
- Update § 4 (Sub-task Storage) — remove symlink creation steps,
  replace with frontmatter `subtasks` field on parent + `parent`
  field on child
- Update § 3 (Artifact Routing) — add provenance fields
  (`task`, `agent`) to artifact frontmatter requirements
- Update query patterns (§§ 7, 10, 12) — show Obsidian CLI as
  primary with filesystem fallback (already partially done)
- Update § 5 (Install layout) — remove bucket directories
- Update § 6 (Design Rationale) — explain symlink elimination,
  frontmatter-only associations, dual-path query model

**`docs/lifecycle.md`:**
- Remove "Bucket Mapping" section entirely
- Remove all symlink references from transitions — frontmatter-
  only edits
- Update "Artifact Promotion" — no symlink moves, just
  frontmatter status update
- Remove sub-task symlink creation from any workflow descriptions

**`docs/task.spec.md`:**
- Remove all symlink references (bucket, sub-task, traceability)
- Add `subtasks` field to parent task schema
- Document artifact provenance fields (`task`, `agent`) for
  artifact specs

**`CLAUDE.md`:**
- Update vault structure diagram — remove `tasks/` bucket tree,
  simplify symlink description to discovery-only
- Update managed `<!-- openstation:start -->` section similarly
- Document Obsidian CLI + Dataview as optional dependency

**Context to read:**
- `artifacts/research/storage-layer-replacement.md` — full research
  with Obsidian CLI command reference
- `docs/storage-query-layer.md` — current spec (what to rewrite)
- `docs/lifecycle.md` — current lifecycle doc
- `docs/task.spec.md` — current task spec

## Findings

Rewrote four files to eliminate all non-discovery symlinks and
convert tasks from folders to single files:

- **`docs/storage-query-layer.md`** — Major rewrite. § 2 now
  covers only discovery symlinks. New § 3 documents frontmatter
  associations (parent/child via `subtasks`/`parent`, artifact
  provenance via `task`/`agent`). § 5 (sub-task storage) uses
  frontmatter-only creation steps. § 7 (design rationale) explains
  symlink elimination. Query patterns (§§ 8–13) all show Obsidian
  CLI primary + filesystem fallback. Section numbering shifted
  (old §§ 7,10,12 → new §§ 8,11,13).

- **`docs/lifecycle.md`** — Removed all symlink references.
  Sub-tasks section now references frontmatter fields. Artifact
  promotion uses neutral "discovery entry" language instead of
  "discovery symlinks".

- **`docs/task.spec.md`** — Added `subtasks` field to frontmatter
  schema and field reference table. Added "Artifact Provenance
  Fields" section documenting `task`/`agent`. Updated sub-task
  example to show frontmatter-based linking (no symlinks in
  folder structure). Updated cross-references to new § numbers.

- **`CLAUDE.md`** — Updated storage-query-layer description.
  Added "Query Model" section documenting Obsidian CLI as optional
  dependency. Updated managed `<!-- openstation:start -->` section
  to describe frontmatter-only associations.

## Verification

- [x] `docs/storage-query-layer.md` § 2 contains only discovery symlinks — no sub-task or traceability symlinks
- [x] Sub-task relationships use frontmatter only: `subtasks` on parent, `parent` on child
- [x] Artifact provenance documented: `task` and `agent` fields on artifact frontmatter
- [x] Query patterns (§§ 7, 10, 12) show Obsidian CLI as primary, filesystem as fallback
- [x] Install layout (§ 5) no longer includes `tasks/{backlog,current,done}`
- [x] `docs/lifecycle.md` has no symlink references; transitions are frontmatter-only
- [x] `docs/task.spec.md` has no symlink references; includes `subtasks` field docs
- [x] `CLAUDE.md` vault structure updated in both locations
- [x] Tasks are documented as single files (`NNNN-slug.md`), not folders with `index.md`
