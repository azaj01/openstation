---
kind: task
name: 0086-spec-module-split-for-src
status: done
assignee: architect
owner: user
parent: "[[0084-refactor-cli-into-src-package]]"
artifacts:
  - "[[artifacts/specs/src-package-module-split]]"
created: 2026-03-09
---

# Spec module split for src/ package refactor

Design the module structure for extracting `bin/openstation`
(~1900 lines) into a `src/openstation/` Python package.

## Context

- Current: single file `bin/openstation` with ~83 functions
- Logical groupings visible in the code:
  - CLI entry point + argparse (~lines 1650-1879)
  - Run orchestration: `cmd_run`, `run_single_task`,
    `_exec_or_run`, `build_command` (~lines 522-1060)
  - Output helpers: `info`, `err`, `header`, `step`, `detail`,
    `success`, `failure`, etc. (~lines 655-751)
  - Task operations: `cmd_create`, `cmd_status`, `cmd_list`,
    `cmd_show`, frontmatter parsing (~lines 82-620)
  - Agent operations: `find_agent_spec`, `parse_allowed_tools`,
    `cmd_agents` (~lines 460-520)
  - Init: `cmd_init` (~lines 1100-1650)
  - Utilities: `find_root`, `slugify`, `resolve_task`
- Research on install impact: `artifacts/research/
  src-refactor-install-impact.md` (from task 0085)

## Requirements

- **Read the full `bin/openstation`** and map every function to
  a logical module
- **Propose a module structure** under `src/openstation/`:
  - Module names and responsibilities
  - Which functions go where
  - Public API of each module
  - Import graph (no circular deps)
- **Define the entry point**: what `bin/openstation` becomes
  (thin wrapper)
- **Address test migration**: how `tests/test_cli.py` changes
  (it currently runs `bin/openstation` as subprocess)
- **Incorporate install findings** from task 0085's research
  artifact
- Keep the number of modules reasonable (3-7, not 15)

## Artifact

Output: `artifacts/specs/src-package-module-split.md`

## Findings

Designed a 5-module split for the 1968-line, 68-function codebase:

1. **`core.py`** (27 functions) — Vault discovery, frontmatter
   parsing, output helpers, path utilities, constants. Shared
   foundation with no internal imports.
2. **`tasks.py`** (19 functions) — Task CRUD, lifecycle transitions,
   discovery, formatting, tree operations. Imports `core`.
3. **`run.py`** (9 functions) — Agent discovery/formatting, spec
   parsing, command building, run orchestration. Imports `core`
   and `tasks`.
4. **`init.py`** (12 functions) — Init subcommand, self-contained.
   Imports `core`.
5. **`cli.py`** (1 function) — Thin argparse dispatcher. Imports
   all modules.

Import graph is strictly acyclic: `cli → {tasks, run, init} → core`.

`bin/openstation` becomes a dev wrapper that adds `src/` to
`sys.path`. Distribution uses zipapp (per 0085 research).
Test migration Phase 1 switches to `python -m openstation`
invocation — all 167 tests keep passing.

Full spec: `artifacts/specs/src-package-module-split.md`

## Verification

- [x] Every function in `bin/openstation` is assigned to a module
- [x] Module count is 3-7
- [x] Import graph has no circular dependencies
- [x] Entry point wrapper defined
- [x] Test migration strategy included
- [x] Install/distribution approach incorporated from 0085
- [x] Artifact written to `artifacts/specs/`
