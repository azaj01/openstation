---
kind: task
name: 0057-spec-for-openstation-init-command
status: ready
agent: architect
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-05
---

# Spec for `openstation init` Command

## Requirements

1. Write a technical spec for the `openstation init` command, informed by research from [[0056-research-install-vs-init-patterns]].
2. Define: command signature, arguments/flags (e.g., `--local`, `--no-agents`), directory structure created, files downloaded/copied, symlink strategy, idempotency rules.
3. Specify what remains in `install.sh` (binary installation only) vs what moves to `init`.
4. Define the boundary: which files are AS-owned (always overwritten) vs user-owned (skip if exists).
5. Specify error handling (not in a git repo, already initialized, missing dependencies).
6. Deliver spec artifact at `artifacts/specs/cli-init-command.md`.

## Verification

- [ ] Spec covers command signature with all arguments/flags
- [ ] Idempotency rules clearly defined (AS-owned vs user-owned files)
- [ ] install.sh vs init boundary explicitly specified
- [ ] Error handling cases documented
- [ ] Spec artifact delivered to `artifacts/specs/`
