---
kind: task
name: 0058-implement-openstation-init-command-and
status: ready
assignee: developer
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-05
---

# Implement `openstation init` Command and Refactor install.sh

## Requirements

1. Implement `openstation init` per the spec from [[0057-spec-for-openstation-init-command]].
2. Move scaffold logic out of `install.sh` into the new `init` command (directory creation, file downloads/copies, symlinks, CLAUDE.md injection, settings.json merge).
3. Refactor `install.sh` to only install the `openstation` binary/CLI on PATH — optionally call `openstation init` at the end, or instruct the user to run it.
4. `openstation init` must be idempotent: safe to re-run without data loss.
5. Add tests for the `init` command (directory creation, idempotency, flag handling).
6. Ensure existing `install.sh --local` and `--no-agents` flags are preserved or mapped to `init` flags.

## Verification

- [ ] `openstation init` creates correct `.openstation/` structure in a clean dir
- [ ] `openstation init` is idempotent (second run doesn't break anything)
- [ ] `install.sh` only installs the binary, no longer scaffolds
- [ ] `--local` and `--no-agents` functionality preserved
- [ ] Tests pass for the new `init` command
- [ ] Existing tests still pass
