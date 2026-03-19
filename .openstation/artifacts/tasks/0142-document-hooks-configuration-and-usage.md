---
kind: task
name: 0142-document-hooks-configuration-and-usage
type: documentation
status: done
assignee: author
owner: user
parent: "[[0134-task-lifecycle-hooks]]"
artifacts:
  - "[[docs/hooks]]"
created: 2026-03-16
---

# Document Hooks Configuration And Usage For Users

## Requirements

1. Create a user-facing hooks documentation page covering configuration schema, matcher format, environment variables, execution semantics, and examples
2. Add an **Architecture** section to `docs/hooks.md` explaining the internal feature design:
   - Module layout (`src/openstation/hooks.py` — three public functions: `load_hooks`, `match_hooks`, `run_matched`)
   - Integration point: single call site in `cmd_status()` in `tasks.py`, between validation and `update_frontmatter()`
   - Data flow: `settings.json` → `load_hooks` → `match_hooks` → `run_matched` → `subprocess.Popen`
   - Exit code: `EXIT_HOOK_FAILED = 10` in `core.py`
   - Reference the design spec: `artifacts/specs/task-lifecycle-hooks.md`
3. Update `docs/cli.md` to add the `EXIT_HOOK_FAILED` exit code and reference hooks in the `status` command section
4. Update `CLAUDE.md` key docs table to reference the hooks doc

## Findings

Created `docs/hooks.md` — a standalone user-facing guide covering:

- **Configuration**: settings file location, JSON schema, field reference
- **Matchers**: `old→new` pattern syntax with wildcards and ASCII alias
- **Environment variables**: all five `OS_`-prefixed vars with descriptions and examples
- **Execution semantics**: ordering, timing (pre-transition), failure behavior, timeout handling, output inheritance
- **Examples**: lint before review, notify on completion, log all transitions, multi-hook setup
- **Scope**: what fires hooks (only `openstation status`) and what's deferred
- **Architecture**: module layout (`hooks.py` — three public functions), integration point (single call site in `cmd_status()` between validation and `update_frontmatter()`), data flow diagram (`settings.json` → `load_hooks` → `match_hooks` → `run_matched` → `subprocess.Popen`), exit code (`EXIT_HOOK_FAILED = 10` in `core.py`), and reference to the design spec

Updated `docs/cli.md`:
- Added `EXIT_HOOK_FAILED` (code 10) to the exit codes table
- Added a Hooks subsection under the `status` command referencing `docs/hooks.md`

Updated `CLAUDE.md`:
- Added hooks doc to the key docs table in the `openstation:start` managed section

## Rejection

Missing Architecture section. All main components need self-describing
specs in their docs. The hooks doc covers usage well but doesn't
explain the internal design: module layout, integration point in
`cmd_status()`, data flow, or exit code. Added requirement 2 and
a verification item.

## Progress

### 2026-03-16 — author

Read parent task (0134), sibling tasks (0135 spec, 0136 implementation),
hooks spec (`artifacts/specs/task-lifecycle-hooks.md`), and implementation
(`src/openstation/hooks.py`). Wrote `docs/hooks.md`, updated `docs/cli.md`
and `CLAUDE.md`. All documentation derived from the implemented spec.

### 2026-03-16 — author (rework)

Added Architecture section to `docs/hooks.md` addressing rejection
feedback. Section covers module layout (three public functions in
`hooks.py`), integration point (`cmd_status()` call site), data flow
diagram, and exit code reference. Verified requirements 3 and 4
(cli.md, CLAUDE.md) remain intact from the first pass.

## Verification

- [x] `docs/hooks.md` exists and covers configuration, matchers, env vars, execution, and examples
- [x] `docs/hooks.md` has an Architecture section covering module layout, integration point, data flow, and exit code
- [x] `docs/cli.md` includes `EXIT_HOOK_FAILED` exit code
- [x] `docs/cli.md` `status` section mentions hooks
- [x] `CLAUDE.md` key docs table references hooks doc
