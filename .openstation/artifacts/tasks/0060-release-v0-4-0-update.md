---
kind: task
name: 0060-release-v0-4-0-update
status: done
assignee: project-manager
owner: user
created: 2026-03-05
---

# Release V0.4.0: Update Changelog And Create Git Tag

## Requirements

1. Write a `## v0.4.0` section in `CHANGELOG.md` summarizing the 7 commits since v0.3.0, following the existing changelog style (grouped by category headers like CLI, Architecture, Docs, etc.)
2. Create git tag `v0.4.0` on the release commit

Key changes to document:
- **CLI** — `openstation create` and `openstation status` write commands
- **Architecture** — Single-file tasks replacing folder+symlink model (storage layer rewrite)
- **Docs** — Storage & query layer spec (`docs/storage-query-layer.md`), updated lifecycle/task docs for single-file model
- **CLI** — `openstation list` defaults to active-only, auto-detect task ID vs agent name in `openstation run`

## Verification

- [ ] `CHANGELOG.md` has a `## v0.4.0` section above `## v0.3.0`
- [ ] All 7 commits since v0.3.0 are represented in the changelog
- [ ] Style matches existing changelog entries
- [ ] Git tag `v0.4.0` exists and points to the correct commit
