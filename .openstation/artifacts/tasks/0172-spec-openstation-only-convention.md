---
kind: task
name: 0172-spec-openstation-only-convention
type: spec
status: done
assignee: architect
owner: user
subtasks:
  - "[[0173-implement-openstation-only-convention]]"
parent: "[[0122-worktree-integration]]"
artifacts:
  - "[[artifacts/specs/openstation-only-convention]]"
created: 2026-03-19
---

# Spec: .openstation-Only Convention

Drop the dual-path convention (root-level source repo vs
`.openstation/` target project). All vault files live under
`.openstation/` — one convention, everywhere.

## Context

Currently `find_root` detects two patterns:
1. **Source repo** — `agents/` + `install.sh` at root → prefix `""`
2. **Target project** — `.openstation/` dir → prefix `".openstation"`

The `prefix` parameter threads through ~40 function signatures
across every module (`cli.py`, `tasks.py`, `run.py`,
`artifacts.py`, `hooks.py`). Each has `if prefix:` branching
for path construction. This is the main complexity cost.

## Requirements

### 1. Source repo migration strategy

Decide how the open-station source repo itself transitions:

- Move `artifacts/`, `agents/`, `skills/`, `commands/`, `docs/`,
  `templates/` under `.openstation/`
- Define what stays at root (src/, tests/, bin/, Makefile, etc.)
- Address the `install.sh` + `agents/` source-guard check
- Define a new source-repo detection mechanism (or remove it)

### 2. New `find_root` contract

- Return type: just `Path` (or `Path | None`) — no prefix tuple
- `.openstation/` is the only marker directory
- Worktree behavior unchanged (independent vs slave)
- Non-git directories still unsupported

### 3. Path construction

Define the canonical helper that replaces all `if prefix:`
branching:

```python
# Example: always .openstation
def vault_path(root: Path, *parts) -> Path:
    return root / ".openstation" / Path(*parts)
```

List every path pattern currently using prefix and confirm
the new form.

### 4. Migration checklist

Enumerate every file that changes:
- `core.py` — `_check_dir`, `find_root`, `tasks_dir_path`
- `cli.py` — dispatch signatures
- `tasks.py` — all functions taking `(root, prefix)`
- `run.py` — all functions taking `(root, prefix)`
- `artifacts.py` — `_artifacts_base` and dependents
- `hooks.py` — `_settings_path`, `load_settings`, etc.
- `init.py` — source guard, init logic
- `test_find_root.py` — remove source-repo cases
- `test_cli.py`, `test_hooks.py` — fixture updates
- `CLAUDE.md`, docs — path references

### 5. Backward compatibility

- Does `openstation init` need changes for existing projects?
- Any migration path for users who already have `.openstation/`?
  (Should be seamless — they already use the target convention.)

## Findings

Spec produced at `artifacts/specs/openstation-only-convention.md`.

**Key decisions:**

- **Source repo migration**: Move `artifacts/`, `agents/`, `skills/`,
  `commands/`, `docs/`, `templates/`, `settings.json` under
  `.openstation/`. Code (`src/`, `tests/`, `bin/`), build files
  (`Makefile`, `pyproject.toml`), and `install.sh` stay at root.
- **No source-repo detection**: The `agents/ + install.sh` marker
  check is removed entirely. `_check_dir` becomes a single
  `.openstation/` directory check. `EXIT_SOURCE_GUARD` is removed.
- **`find_root` return type**: `Path | None` — no tuple, no prefix.
- **`vault_path(root, *parts)`**: Single canonical helper that
  always constructs `root / .openstation / parts`. Replaces all
  12 `if prefix:` branch sites across 5 modules.
- **~25 functions** lose their `prefix` parameter. The change is
  mechanical — collapse the always-true branch.
- **Backward compatibility**: Seamless for installed projects (they
  already use `.openstation/`). Old CLI versions are
  forward-compatible with the new layout.
- **Worktree behavior**: Structurally identical two-step resolution.
  Only the removed source-repo marker path is gone.

**Migration checklist** covers 7 source files, 7 test files, and
6+ doc files. See spec §4 for the complete enumeration.

artifacts:
  - "[[artifacts/specs/openstation-only-convention]]"

## Progress

- 2026-03-19 — Analyzed all source modules, mapped every `if prefix:`
  branch site (12 occurrences across 5 modules, ~25 function
  signatures). Wrote spec with migration strategy, new `find_root`
  contract, `vault_path` helper, complete file-by-file migration
  checklist, backward compatibility analysis, and worktree
  regression analysis.

## Verification

- [x] Spec defines source repo migration strategy
- [x] Spec defines new `find_root` return type (no prefix)
- [x] Spec defines canonical path helper
- [x] Spec includes complete migration checklist (every file)
- [x] Spec addresses backward compatibility
- [x] Spec addresses worktree behavior (no regression)
