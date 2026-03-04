---
kind: task
name: 0046-spec-storage-query-layer
status: review
agent: author
owner: user
parent: 0045-replace-storage-obsidian-cli
created: 2026-03-04
---

# Spec storage & query layer

Rewrite `docs/storage-query-layer.md` and related documentation to
reflect the new architecture: Obsidian CLI with Dataview queries as
the primary query engine, filesystem fallback for headless/CI, no
bucket symlinks.

Based on research in `artifacts/research/storage-layer-replacement.md`
(task 0044). The chosen approach leverages Obsidian CLI combined with
Dataview queries for task discovery and filtering.

## Requirements

**`docs/storage-query-layer.md`:**
- Remove SS 2a (bucket symlinks) — bucket symlinks are eliminated
- Remove SS 3 (lifecycle bucket mapping) — no more bucket-to-status
  mapping or symlink move procedures
- Update SS 8 (find tasks by status) — show Obsidian CLI with
  Dataview queries (`search query='[kind: task] [status: X]'`) as
  primary, filesystem `grep` as fallback
- Update SS 11 (find tasks by agent) — same dual-path pattern
  (Obsidian CLI + Dataview query primary, grep fallback)
- Update SS 13 (query patterns summary) — replace bucket-based
  operations with Obsidian CLI/Dataview + fallback equivalents
- Update SS 6 (install layout) — remove `tasks/{backlog,current,done}`
  directories from the layout diagram
- Update SS 7 (design rationale) — explain the Obsidian CLI +
  Dataview adoption rationale and the dual-path query model

**`docs/lifecycle.md`:**
- Remove "Bucket Mapping" section entirely
- Simplify transition descriptions to frontmatter-only edits
  (no symlink moves)
- Update "Artifact Promotion" to remove bucket symlink references

**`docs/task.spec.md`:**
- Remove any references to bucket symlinks or bucket placement

**`CLAUDE.md`:**
- Update vault structure diagram (remove `tasks/` bucket tree)
- Update the managed `<!-- openstation:start -->` section similarly
- Document Obsidian CLI + Dataview as optional dependency (enhances
  query performance, not required — filesystem fallback always works)

**Context to read:**
- `artifacts/research/storage-layer-replacement.md` — full research
  with Obsidian CLI command reference
- `docs/storage-query-layer.md` — current spec (what to rewrite)
- `docs/lifecycle.md` — current lifecycle doc
- `docs/task.spec.md` — current task spec

## Findings

All four target files updated. Key changes:

- **storage-query-layer.md** — Full rewrite. Removed §§ 2a
  (bucket symlinks) and 3 (lifecycle bucket mapping). Renumbered
  all subsequent sections (old 4→3, 5→4, 6→5, 7→6, 8→7, etc.).
  Added "Frontmatter as single source of truth" and "Dual-path
  query model" to design rationale. Query patterns (§§ 7, 10, 12)
  now show Obsidian CLI as primary with filesystem fallback.
  Install layout (§ 5) no longer includes `tasks/` bucket tree.

- **lifecycle.md** — Removed "Bucket Mapping" section. Updated
  guardrails to say "updates the status" instead of "moves the
  folder". Artifact Promotion now says "sets `status: done` in
  frontmatter" instead of "moves the task symlink to
  `tasks/done/`". Updated all cross-references to new § numbers.

- **task.spec.md** — Removed bucket symlink references from File
  Location, sub-task description, and examples. Updated § cross-
  references (2d→2c, 4→3, 5→4).

- **CLAUDE.md** — Removed `tasks/` bucket tree from both vault
  structure diagrams (source and managed section). Removed bucket-
  related text from "Task Structure" and "Creating a New Task".

## Recommendations

Other files that reference storage-query-layer.md section numbers
and will need updating in sibling tasks:

- `skills/openstation-execute/` — references §§ 2d, 4, 5
  (now §§ 2c, 3, 4)
- `commands/` — may reference bucket operations
- `docs/openstation-run.md` — references symlinks but no § numbers

## Verification

- [ ] `docs/storage-query-layer.md` has no bucket symlink references (SS 2a, 3 removed)
- [ ] Query patterns (SS 8, 13) show Obsidian CLI as primary, filesystem as fallback
- [ ] Install layout (SS 6) no longer includes `tasks/{backlog,current,done}`
- [ ] `docs/lifecycle.md` "Bucket Mapping" section removed; transitions are frontmatter-only
- [ ] `docs/task.spec.md` has no bucket references
- [ ] `CLAUDE.md` vault structure updated in both locations (source and managed section)
