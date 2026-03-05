---
kind: task
name: 0059-update-docs-for-install-vs
status: ready
agent: author
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-05
---

# Update Docs for Install vs Init Split

## Requirements

1. Update `CLAUDE.md` (both the source repo version and the managed section injected by init) to document the `openstation init` command.
2. Update any references to `install.sh` in docs that now need to mention the two-step flow (`install` then `init`).
3. Update `install.sh` header comments / usage text if not already handled by the implementation task.
4. Review and update: `docs/lifecycle.md`, `docs/storage-query-layer.md`, and any other docs referencing installation or project setup.
5. Ensure the Quick Start section in the managed CLAUDE.md block reflects the new workflow.

## Verification

- [ ] CLAUDE.md documents both `install` and `init` commands
- [ ] Managed CLAUDE.md section (openstation:start/end) updated
- [ ] No stale references to the old single-step install flow
- [ ] Quick Start reflects the two-step workflow
- [ ] All doc files reviewed for install references
