---
kind: task
name: 0045-replace-storage-obsidian-cli
status: done
agent: developer
owner: user
created: 2026-03-04
subtasks:
  - "[[0046-spec-storage-query-layer]]"
  - "[[0047-implement-storage-replacement]]"
---

# Replace storage layer with Obsidian CLI

Replace the symlink-based storage layer with Obsidian CLI as the
primary query engine, with filesystem+grep fallback. Remove bucket
symlinks (`tasks/backlog/`, `tasks/current/`, `tasks/done/`). Keep
discovery, traceability, and sub-task symlinks.

Based on research in `artifacts/research/storage-layer-replacement.md`
(task 0044).

## Requirements

1. Rewrite `docs/storage-query-layer.md` and related docs to
   reflect the new architecture (sub-task 0046).
2. Update CLI, commands, execute skill, and install script to
   remove bucket symlink operations and adopt Obsidian CLI queries
   (sub-task 0047).

## Subtasks

- 0046-spec-storage-query-layer — rewrite storage & query docs
- 0047-implement-storage-replacement — implement CLI + command changes

## Verification

- [x] Sub-task 0046 is done (docs updated)
- [x] Sub-task 0047 is done (implementation complete)
- [x] No bucket symlinks are created or moved by any command
- [x] `openstation list` works with and without Obsidian running
