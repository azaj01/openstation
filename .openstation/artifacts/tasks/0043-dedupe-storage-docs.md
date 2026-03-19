---
kind: task
name: 0043-dedupe-storage-docs
status: done
assignee: author
owner: user
parent: "[[0041-storage-query-layer-spec]]"
created: 2026-03-04
---

# Dedupe Storage Docs

## Requirements

Audit existing docs that repeat storage/symlink/query instructions
now covered by `docs/storage-query-layer.md`. Replace
duplicated content with references to the new canonical spec.

Files to audit:

- `docs/lifecycle.md`
- `docs/task.spec.md`
- `CLAUDE.md`
- Any skills or commands that repeat storage conventions

For each file: keep domain-specific context, remove repeated
storage/query mechanics, add a cross-reference to the new spec.

## Findings

Audited 7 files across docs, CLAUDE.md, skills, and commands.
Applied 14 edits total:

**`docs/lifecycle.md`** (4 edits) — Removed: Symlink Move Procedure,
Creating a Sub-Task + Symlink Convention subsections, artifact
category list, Routing Table, Agent Promotion subsection, and
entire Directory Purposes section. Kept: status transitions,
guardrails, ownership, blocking rule, lifecycle for sub-tasks,
brief artifact storage/promotion summaries.

**`docs/task.spec.md`** (3 edits) — Removed: Bucket Symlinks
subsection with table, Symlink placement + Status tracking
sub-sections for sub-tasks, traceability symlink code block.
Kept: canonical path mention, naming/schema, `parent:` field,
parent body section, artifacts field semantics.

**`CLAUDE.md`** (3 edits) — Simplified Task Structure to one
sentence + reference. Replaced 5-step manual task creation with
pointer to `/openstation.create` and specs. Added storage spec
to How Docs Connect legend and to injected `openstation:start`
section.

**`skills/openstation-execute/SKILL.md`** (2 edits) — Removed
inline routing table from Store Artifacts. Simplified Create
Sub-Tasks from 5 steps to 3. Both now reference storage spec.

**`commands/openstation.create.md`** (2 edits) — Updated two
sub-task convention references from lifecycle.md/task.spec.md
to storage spec § 5.

**Not changed:** `openstation.done`, `openstation.ready`,
`openstation.reject` — their symlink steps are procedural (what
the command does), not repeated reference material.

## Verification

- [x] `docs/lifecycle.md` references the new spec instead of repeating storage details
- [x] `docs/task.spec.md` references the new spec instead of repeating storage details
- [x] `CLAUDE.md` references the new spec where applicable
- [x] No contradictions between remaining content and the new spec
- [x] All cross-references use correct relative paths
