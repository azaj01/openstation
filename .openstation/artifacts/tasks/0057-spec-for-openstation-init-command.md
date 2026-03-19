---
kind: task
name: 0057-spec-for-openstation-init-command
status: done
assignee: architect
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
artifacts:
  - "[[artifacts/specs/cli-init-command]]"
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

## Findings

Spec delivered at `artifacts/specs/cli-init-command.md`. Key
design decisions:

1. **Command signature:** `openstation init [--local <path>] [--agents <name,...>] [--no-agents] [--dry-run] [--force]` — non-interactive, no positional args, operates on CWD.

2. **File ownership model (two tiers):**
   - **AS-owned** (commands, skills, docs, symlinks) — always overwritten on re-init.
   - **User-owned** (agent specs from templates) — skipped if they exist, unless `--force`.

3. **install.sh boundary:** Reduced to binary installation only (download/copy `bin/openstation` to PATH), then delegates to `openstation init` for all scaffolding.

4. **Implementation approach:** New `cmd_init()` function in `bin/openstation` using `urllib.request` (stdlib) for downloads — no curl dependency. Follows existing subcommand pattern.

5. **Idempotency:** Fully idempotent following git/terraform model. Safe to re-run. Directories use `exist_ok=True`, AS-owned files overwritten, user-owned skipped, symlinks recreated.

6. **Error handling:** Source repo guard, local path validation, git repo warning (non-fatal), network error handling.

7. **New capabilities beyond install.sh:** `--dry-run` (show what would happen without writing), `--force` (overwrite user-owned files for reset scenarios), and `--agents` (select specific templates to install).

## Verification

- [ ] Spec covers command signature with all arguments/flags
- [ ] Idempotency rules clearly defined (AS-owned vs user-owned files)
- [ ] install.sh vs init boundary explicitly specified
- [ ] Error handling cases documented
- [ ] Spec artifact delivered to `artifacts/specs/`
