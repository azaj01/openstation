---
kind: task
name: 0023-cli-feature-spec
status: done
assignee: architect
owner: manual
parent: "[[0021-openstation-cli]]"
artifacts:
  - artifacts/specs/cli-feature-spec.md
created: 2026-03-01
---

# CLI Feature Spec

## Requirements

Write the detailed technical specification for the OpenStation CLI
based on research findings from 0022-cli-feature-research:

1. **Command interface** — define every subcommand, its flags,
   arguments, and expected output format
2. **File layout** — specify where the CLI source lives, how it's
   installed, and how it discovers the vault root
3. **Error handling** — define error codes, messages, and behavior
   for invalid input, missing tasks, and broken symlinks
4. **Idempotency rules** — specify exactly what "safe to re-run"
   means for each command
5. **Testing strategy** — how the CLI will be tested (unit tests,
   integration tests, or both)

## Findings

Full spec in `artifacts/specs/cli-feature-spec.md`.

The spec defines 2 read-only commands matching parent scope:
- `list` — filtered task table to stdout
- `show` — raw task spec to stdout

Key design decisions:
- Single-file Python script at `bin/openstation` with shebang
- Vault root detection walks up from CWD (matches `openstation-run.sh`)
- Simple `str.split(':', 1)` YAML parsing — no full parser needed
- Exit codes 0-4 covering success, usage, project, not-found, and ambiguous errors
- Integration tests using `tempfile` fixtures and `subprocess.run()`

## Verification

- [x] Spec covers all commands listed in parent task requirements
- [x] Each command has defined inputs, outputs, and error cases
- [x] File layout and installation path documented
- [x] Testing strategy defined
