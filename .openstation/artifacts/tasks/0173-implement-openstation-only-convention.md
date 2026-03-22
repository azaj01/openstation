---
kind: task
name: 0173-implement-openstation-only-convention
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-19
---

# Implement .openstation-Only Convention

Mechanical refactor: drop the `prefix` parameter from all
module signatures, hardcode `.openstation/` as the only vault
convention, and restructure the source repo accordingly.

Follows the spec from 0172.

## Requirements

### 1. Source repo restructure

Move vault directories under `.openstation/` per the spec.
Update all internal references.

### 2. Remove prefix from all signatures

Eliminate the `(root, prefix)` tuple pattern. Every function
that currently takes `prefix` should take only `root`.

Affected modules:
- `core.py` — `find_root`, `tasks_dir_path`, `_check_dir`
- `cli.py` — all dispatch calls
- `tasks.py` — `discover_tasks`, `resolve_task`, `cmd_*`
- `run.py` — `discover_agents`, `find_agent_spec`, `cmd_*`,
  `run_single_task`, `_exec_or_run`
- `artifacts.py` — `_artifacts_base`, `discover_artifacts`,
  `resolve_artifact`, `cmd_*`
- `hooks.py` — `_settings_path`, `load_settings`, `load_hooks`,
  `run_hooks`

### 3. Canonical path helper

Implement the `vault_path(root, *parts)` helper (or equivalent
from the spec) and use it everywhere.

### 4. Update tests

- `test_find_root.py` — remove source-repo fixtures/cases,
  update return type assertions
- `test_cli.py` — update prefix in fixtures
- `test_hooks.py` — update prefix in fixtures
- Add test: source repo (with `.openstation/`) is found correctly

### 5. Update docs and CLAUDE.md

- Update vault structure references
- Update path examples
- Remove references to root-level convention

## Verification

- [x] `find_root` returns `Path | None` (no prefix)
- [x] No `prefix` parameter in any module signature
- [ ] All tests pass
- [x] Source repo has `.openstation/` with vault contents
- [x] `openstation list` works in source repo
- [ ] `openstation list` works in a target project
- [x] Worktree tests pass (independent + slave modes)
- [ ] Docs and CLAUDE.md updated

## Progress

### 2026-03-20 — developer
> time: 11:09

Fixed CLAUDE.md stale references (vault structure, discovery section), updated test fixtures (make_local_source, TestInitUserMode) to use .openstation/ paths. All 416 tests pass.

## Findings

### What was done

1. **CLAUDE.md updated** — Vault Structure block now shows all paths
   under `.openstation/`. Removed the stale "In target projects..."
   note. Discovery section updated to reference `.openstation/` paths.

2. **Test fixtures fixed** — `make_local_source()` in `test_cli.py`
   created source directories at root level instead of under
   `.openstation/`. Updated to use `.openstation/` prefix.
   `TestInitUserMode::test_user_creates_agent_symlinks` had the same
   issue — fixed.

3. **All 416 tests pass** — full suite green.

4. **`openstation list` works in source repo** — confirmed.

5. **Target project init** — cannot test outside sandbox; covered
   by `TestInitCommand` (20 tests) and `TestInitUserMode` (5 tests).
