---
kind: task
name: 0059-update-docs-for-install-vs
status: done
assignee: author
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-05
---

# Update Docs for Install vs Init Split

## Requirements

1. Remove the `install.sh` reference from CLAUDE.md line 22 — reword to say files live under `.openstation/` in target projects, without mentioning how they get there.
2. Add installation instructions to README.md covering the two-step flow: `install.sh` puts the CLI on PATH, `openstation init` scaffolds the project.
3. Review other docs (`docs/lifecycle.md`, `docs/storage-query-layer.md`) for stale install references and fix any found.

Principle: CLAUDE.md tells agents how to *use* the system. README.md tells humans how to *install* it.

## Verification

- [ ] CLAUDE.md has no install/init instructions — usage only
- [ ] README.md documents the two-step install → init workflow
- [ ] No stale references to the old single-step install flow in docs
