---
kind: task
name: 0084-refactor-cli-into-src-package
status: in-progress
assignee: developer
owner: user
created: 2026-03-09
subtasks:
  - "[[0085-research-install-and-distribution-impact]]"
  - "[[0086-spec-module-split-for-src]]"
  - "[[0087-implement-src-package-refactor]]"
---

# Refactor CLI into src/ package structure

Extract `bin/openstation` (1879 lines, ~83 functions) into a
proper `src/openstation/` Python package. Keep `bin/openstation`
as a thin wrapper that imports and calls `main()`.

## Context

The CLI is a single extensionless Python file that has grown
to ~1900 lines. It handles argument parsing, task CRUD,
agent resolution, run orchestration, output formatting, and
init logic all in one file. This makes it hard to test
individual functions, navigate the code, and onboard new
contributors.

## Requirements

- Create `src/openstation/` package with modules split by
  concern (exact module split to be determined by architect spec)
- Keep `bin/openstation` as a thin entry-point wrapper
- All existing tests must pass with minimal changes
- CLI behavior unchanged from user perspective
- `install.sh` and distribution model must still work
  (see research subtask for approach)

## Subtasks

- [[0085-research-install-and-distribution-impact]] — research
  install/distribution impact and recommend approach
- [[0086-spec-module-split-for-src]] — architect designs module
  split and import graph
- [[0087-implement-src-package-refactor]] — developer executes
  after spec is done

## Verification

- [ ] `src/openstation/` package exists with logical modules
- [ ] `bin/openstation` is a thin wrapper (~5 lines)
- [ ] All 163+ existing tests pass
- [ ] `openstation` CLI works identically from user perspective
- [ ] Install/distribution model works (per research findings)
- [ ] No circular imports
