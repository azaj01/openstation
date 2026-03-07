---
kind: task
name: 0055-cli-init-command-separate-project
status: done
assignee: 
owner: user
created: 2026-03-05
subtasks:
  - "[[0056-research-install-vs-init-patterns]]"
  - "[[0057-spec-for-openstation-init-command]]"
  - "[[0058-implement-openstation-init-command-and]]"
  - "[[0059-update-docs-for-install-vs]]"
  - "[[0061-generalize-agent-templates-for-any]]"
  - "[[0067-research-agent-driven-template-customization]]"
---

# CLI `init` Command — Separate Project Scaffolding From Install

## Requirements

1. **New `openstation init` CLI command** — scaffolds the `.openstation/` directory structure in the current project (dirs, commands, skills, docs, agent templates, symlinks).
2. **Refactor `install.sh`** — reduce to only installing the `openstation` binary/CLI on PATH. It no longer scaffolds `.openstation/`.
3. **Separation of concerns:** `install` = get the tool; `init` = set up a project.
4. **`init` must be idempotent** — safe to re-run (skip existing user files, overwrite AS-owned files).
5. Current scaffold logic from `install.sh` (directory creation, file downloads, symlinks) moves into the `init` command.

## Subtasks

- [[0056-research-install-vs-init-patterns]] — Research install-vs-init patterns in CLI tools
- [[0057-spec-for-openstation-init-command]] — Technical spec for the init command
- [[0058-implement-openstation-init-command-and]] — Implement init command, refactor install.sh
- [[0059-update-docs-for-install-vs]] — Update documentation for the split

## Verification

- [ ] `openstation init` creates a working `.openstation/` scaffold in a clean directory
- [ ] `install.sh` only installs the CLI binary, does not create `.openstation/`
- [ ] Running `openstation init` twice is safe (idempotent)
- [ ] All 4 subtasks completed and verified
- [ ] Documentation reflects the new install/init split
