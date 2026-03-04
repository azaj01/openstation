---
kind: task
name: 0042-create-storage-query-spec
status: done
agent: author
owner: user
parent: 0041-storage-query-layer-spec
artifacts:
  - artifacts/specs/storage-query-layer.md
created: 2026-03-04
---

# Create Storage & Query Layer Spec

## Requirements

Write `artifacts/specs/storage-query-layer.md` as a standalone
retrospective spec covering all 13 topics from the parent task:

**Storage Layer** (items 1-7): canonical storage model, symlink
graph, lifecycle bucket mapping, artifact routing, sub-task
storage, install-time layout, design rationale.

**Query Layer** (items 8-13): find tasks by status, get artifacts
for a task, get sub-tasks of a parent, find tasks by agent, agent
discovery, query patterns summary table.

Cross-check accuracy against `docs/lifecycle.md`,
`docs/task.spec.md`, and `install.sh`.

## Verification

- [x] Spec file exists at `artifacts/specs/storage-query-layer.md` with valid `kind: spec` frontmatter
- [x] All 7 storage layer topics are covered
- [x] All 6 query layer topics are covered
- [x] Query patterns summary table is present
- [x] Design rationale section is present
- [x] Content is accurate against current implementation
