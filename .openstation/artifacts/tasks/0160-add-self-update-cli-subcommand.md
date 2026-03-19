---
kind: task
name: 0160-add-self-update-cli-subcommand
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-17
---

# Add Self-Update CLI Subcommand

## Requirements

1. Add `openstation self-update` CLI subcommand that updates the
   local install cache (`~/.local/share/openstation/` or
   `$OPENSTATION_DIR`)
2. Fetch latest tag from the remote (or accept `--version <tag>`
   to pin a specific version)
3. Handle dirty install cache gracefully — force-checkout after
   fetching (the cache is not user-editable)
4. Re-link the CLI binary
   (`~/.local/bin/openstation → dist/openstation`)
5. Print the old and new version after update
6. If run inside a project with `.openstation/`, suggest running
   `openstation init` to update the project (do not auto-run)
7. Add `self-update` to `docs/cli.md`

## Progress

- 2026-03-18: Implemented `self-update` subcommand — new module
  `src/openstation/update.py`, registered in `cli.py`, documented
  in `docs/cli.md`. 16 unit tests added in `tests/test_self_update.py`,
  all passing. 264 existing tests unaffected.

## Findings

Implemented `openstation self-update` as a new CLI subcommand in
`src/openstation/update.py`. The command operates on the git-based
install cache at `~/.local/share/openstation/` (or `$OPENSTATION_DIR`).

**Key design decisions:**

- Reuses `OPENSTATION_HOME` from `init.py` for install cache location
- Runs before `find_root()` in cli.py routing (like `init`) since it
  doesn't need a project context
- Uses `git checkout --force` + `git clean -fd` to handle dirty caches
- Auto-prefixes bare version numbers with `v` (e.g., `0.10.0` → `v0.10.0`)
- Determines latest version via `git tag --list v* --sort=-version:refname`
- All git operations are wrapped in a `_git()` helper for testability

**Files created/modified:**

- `src/openstation/update.py` — new module (core logic)
- `src/openstation/cli.py` — import + subparser + routing
- `docs/cli.md` — quick reference table entry + full section
- `tests/test_self_update.py` — 16 unit tests

## Verification

- [x] `openstation self-update` updates the install cache to the latest tag
- [x] `openstation self-update --version v0.10.0` pins to a specific version
- [x] Dirty install cache (modified files) is handled without error
- [x] CLI binary symlink is refreshed after update
- [x] Old → new version is printed
- [x] Suggests `openstation init` when run inside a project
- [x] `docs/cli.md` documents the new subcommand
