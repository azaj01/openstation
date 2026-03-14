---
kind: task
name: 0133-cli-add-artifacts-support-list
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-14
---

# CLI — Add Artifacts Support

## Requirements

1. Add an `artifacts` subcommand group to the `openstation` CLI with two sub-commands:
   - `openstation artifacts list [--kind KIND] [-q | -j]` — List artifacts from `artifacts/` subdirectories. `--kind` filters by subdirectory (`tasks`, `agents`, `research`, `specs`). Without `--kind`, lists all non-task artifacts (research, specs, agents). Output: name, kind, one-line summary.
   - `openstation artifacts show <name>` — Display a single artifact by name (resolved across `artifacts/research/`, `artifacts/specs/`, `artifacts/agents/`). Follows the same resolution pattern as `show` does for tasks.
2. Resolution: `<name>` matches against filename stems in `artifacts/{research,specs,agents}/`. Ambiguous matches produce an error listing candidates.
3. Output flags mirror existing conventions: `-q` (quiet, one name per line), `-j` (JSON), `-v` (open in editor).
4. Register the new subcommand in `cli.py` alongside the existing `agents` group.
5. Update `docs/cli.md` with the new subcommand reference section.

## Verification

- [ ] `openstation artifacts list` returns all non-task artifacts (research, specs, agents)
- [ ] `openstation artifacts list --kind research` returns only research artifacts
- [ ] `openstation artifacts show <name>` displays the full artifact content
- [ ] Ambiguous name produces error with candidates listed
- [ ] `-q`, `-j`, `-v` output flags work as expected
- [ ] `docs/cli.md` updated with `artifacts` subcommand section
- [ ] Tests added for the new subcommand

## Progress

### 2026-03-14 — developer
> time: 20:41
> log: [[artifacts/logs/0133-cli-add-artifacts-support-list]]

Implemented the `artifacts` subcommand with `list` and `show` sub-actions.

- Created `src/openstation/artifacts.py` with `discover_artifacts()`,
  `resolve_artifact()`, `format_artifacts_table()`, and command handlers
  `cmd_artifacts_list()` / `cmd_artifacts_show()`.
- Registered `artifacts` (alias `art`) subcommand in `cli.py` with
  `list` and `show` sub-parsers, including `--kind`, `-q`, `-j`, `-v` flags.
- Added comprehensive test suite in `tests/test_artifacts_subcommand.py`
  (23 tests covering list, show, JSON/quiet output, kind filtering,
  ambiguous resolution, alias, edge cases).
- Updated `docs/cli.md` with full `artifacts` section including synopsis,
  sub-actions, flags, and examples.
- All 266 tests pass (23 new + 243 existing).

## Findings

### What was built

New `artifacts` subcommand group for the `openstation` CLI:

- **`openstation artifacts list`** — Lists non-task artifacts (agents,
  research, specs) with name, kind, and one-line summary. Supports
  `--kind` filtering, `-q` (quiet), `-j` (JSON) output modes.
- **`openstation artifacts show <name>`** — Displays a single artifact
  resolved across `artifacts/{research,specs,agents}/`. Supports `-j`
  (JSON) and `-v` (editor) output modes.
- **`art` alias** — Short alias for `artifacts`, matching the `ag`
  alias pattern for `agents`.

### Design decisions

- Followed the existing `agents` subcommand pattern exactly: same
  argparse structure, same output format conventions, same resolution
  approach.
- Resolution scans all three non-task artifact directories. Exact stem
  match takes priority; partial matches are used as fallback. Ambiguous
  matches return exit code 4 with candidate list.
- `--kind tasks` is explicitly rejected with a hint to use
  `openstation list` — prevents confusion between task listing and
  artifact browsing.
- Summary field falls back to the first non-empty body line (stripped
  of `#` heading markers) when no `description` frontmatter exists.
