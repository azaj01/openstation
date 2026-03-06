---
kind: task
name: 0039-cli-run-implement
status: done
assignee: developer
owner: manual
parent: "[[0028-cli-run-integration]]"
created: 2026-03-03
---

# Implement CLI run subcommand

## Requirements

Implement the `openstation run` subcommand based on the spec
produced by 0038-cli-run-spec. Specifically:

- Add a `run` subcommand to the Python CLI (`bin/openstation`)
  that launches agents via `claude`, replacing direct use of
  `openstation-run.sh`.
- Support all existing flags: `--task`, `--tier`, `--budget`,
  `--turns`, `--dry-run`, `--force`.
- Implement agent resolution and allowed-tools parsing in Python
  (porting logic from `openstation-run.sh` or wrapping it).
- Handle tier 1 (interactive) and tier 2 (autonomous) execution
  paths.
- Preserve streaming output behavior (live progress via
  stream-json).
- Update `/openstation.dispatch` command to reference the new
  `openstation run` subcommand.
- Improve readability of any remaining shell script code:
  - Clear section headers and inline comments
  - Named helper functions for complex logic
  - Consistent formatting and naming conventions

## Context

- Depends on: 0038-cli-run-spec (spec must be completed first)
- Current shell implementation: `openstation-run.sh`
- CLI entry point: `bin/openstation` (Python)

## Verification

- [x] `openstation run <agent>` launches an agent session
- [x] All flags (`--task`, `--tier`, `--budget`, `--turns`,
      `--dry-run`) work correctly
- [x] Tier 1 and tier 2 execution paths both function
- [x] `/openstation.dispatch` references the new run command
- [x] Streaming output works for tier 2 execution
- [x] Existing `openstation-run.sh` tests (if any) still pass
      or are migrated
