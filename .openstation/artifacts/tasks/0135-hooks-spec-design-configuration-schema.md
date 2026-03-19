---
kind: task
name: 0135-hooks-spec-design-configuration-schema
type: spec
status: done
artifacts:
  - "[[artifacts/specs/task-lifecycle-hooks]]"
assignee: architect
owner: user
parent: "[[0134-task-lifecycle-hooks]]"
created: 2026-03-14
---

# Hooks Spec — Design Configuration Schema And Execution Model

## Requirements

1. Design the hook configuration schema (settings file location, JSON structure, fields per hook entry)
2. Define the matcher format for status transitions (e.g., glob/regex on `old→new`, wildcard support like `*→done`)
3. Specify the environment variables passed to hook commands (task name, old status, new status, file path)
4. Define execution semantics: ordering, synchronous execution, failure behavior (abort transition), timeout handling
5. Document CLI integration points — where in `openstation status` the hook engine is invoked
6. Produce a spec artifact in `artifacts/specs/`

## Verification

- [x] Spec artifact exists in `artifacts/specs/`
- [x] Configuration schema is fully defined with examples
- [x] Matcher format supports common patterns (specific transitions, wildcards, catch-all)
- [x] Environment variable contract is documented
- [x] Failure and timeout semantics are specified
- [x] CLI integration points are identified

## Findings

Produced `artifacts/specs/task-lifecycle-hooks.md` — a complete
spec covering all six requirements:

1. **Configuration schema** (§ 1): Hooks live in `settings.json`
   under `hooks.StatusTransition` — an array of `{matcher,
   command, timeout}` entries. Reuses the existing settings file.

2. **Matcher format** (§ 2): Simple `old→new` pattern with `*`
   wildcard. ASCII `->` alias accepted. No regex — the 7 valid
   transitions don't warrant it.

3. **Environment variables** (§ 3): Five `OS_`-prefixed vars —
   `OS_TASK_NAME`, `OS_OLD_STATUS`, `OS_NEW_STATUS`,
   `OS_TASK_FILE`, `OS_VAULT_ROOT`.

4. **Execution semantics** (§ 4): Pre-transition (before file
   write), synchronous, sequential in declaration order. Non-zero
   exit aborts the transition. 30s default timeout with
   SIGTERM→SIGKILL escalation.

5. **CLI integration** (§ 5): Single insertion point in
   `cmd_status()` between validation and `update_frontmatter()`.
   New `hooks.py` module with `load_hooks`, `match_hooks`,
   `run_matched`. New exit code `EXIT_HOOK_FAILED = 10`.

6. **Scope exclusions**: Post-transition hooks, create-time
   hooks, dry-run mode, and structured output capture are
   explicitly deferred.

## Progress

### 2026-03-14 — architect
> log: [[artifacts/logs/0135-hooks-spec-design-configuration-schema]]

Read parent task, explored CLI codebase (`cmd_status`, `core.py`,
`settings.json`), reviewed Claude Code hook format for design
inspiration. Previous attempt had findings but missing artifact —
transitioned to review prematurely.

### 2026-03-15 — architect
> log: [[artifacts/logs/0135-hooks-spec-design-configuration-schema]]

Rework. Re-explored CLI codebase (`cmd_status` lines 629–678,
`core.py` exit codes and transitions, `update_frontmatter`).
Confirmed no existing settings infrastructure. Wrote complete
spec at `artifacts/specs/task-lifecycle-hooks.md` covering all
6 requirements. Transitioned to review.
