---
kind: task
name: 0038-cli-run-spec
status: done
agent: researcher
owner: manual
parent: "[[0028-cli-run-integration]]"
artifacts:
  - artifacts/specs/cli-run-spec.md
created: 2026-03-03
---

# Spec: CLI run subcommand

## Requirements

Design the `openstation run` subcommand that replaces direct
invocation of `openstation-run.sh`. The spec should define:

- **CLI interface** — arguments, flags, and their mapping to
  existing `openstation-run.sh` options (`--task`, `--tier`,
  `--budget`, `--turns`, `--dry-run`, `--force`).
- **Execution model** — how the Python CLI delegates to
  `claude` (subprocess, exec, or other), how streaming output
  is handled, and how tier 1 vs tier 2 execution is selected.
- **Agent resolution** — how the command resolves agent specs
  from the vault (reuse existing `find_agent_spec` /
  `resolve_task_agent` logic or rewrite in Python).
- **Allowed-tools parsing** — how the `allowed_tools` frontmatter
  field is parsed and passed to `claude`.
- **Error handling** — what happens when agent is not found,
  task is invalid, or `claude` is not installed.
- **Integration with existing CLI** — how `run` fits alongside
  `list`, `show`, `create`, and other subcommands in
  `bin/openstation`.

Deliver a spec document at `artifacts/specs/cli-run-spec.md`.

## Findings

Verified and finalized the spec at `artifacts/specs/cli-run-spec.md`.
The spec covers all six areas required:

1. **CLI interface** — 1:1 flag mapping from `openstation-run.sh`
   (7 flags + positional agent), with mutual exclusion rules.
2. **Execution model** — `os.execvp` for by-agent mode (clean
   signal propagation), `subprocess.run` for by-task queue (must
   survive to iterate). Tier 1/2 command construction documented.
3. **Agent resolution** — `find_agent_spec()` checks installed
   path then source path. Task-to-agent via frontmatter `agent`
   field.
4. **Allowed-tools parsing** — Dedicated `parse_allowed_tools()`
   with line-by-line algorithm. Rationale for not extending
   `parse_frontmatter()` (avoids YAML dependency).
5. **Error handling** — Exit codes 0–5 matching shell script.
   10 error scenarios with specific messages.
6. **Integration** — Subcommand registration, shared functions
   (`find_root`, `parse_frontmatter`, `resolve_task`), single-file
   constraint preserved (~400 lines).

Additional coverage: testing strategy (mock `claude`), migration
plan, component table (C1–C7), 5 design decisions with trade-offs.

See `artifacts/specs/cli-run-spec.md`.

## Context

- Current shell implementation: `openstation-run.sh` (root and
  `.openstation/` copies)
- CLI entry point: `bin/openstation` (Python)
- Related tasks: 0024-cli-implementation, 0035-cli-agent-session
- The Findings section in the parent task (0028) documents
  readability refactors already applied to `openstation-run.sh`.

## Verification

- [x] Spec covers all existing flags and their CLI equivalents
- [x] Execution model (subprocess vs exec) is justified
- [x] Agent and task resolution logic is defined
- [x] Error cases are enumerated with expected behavior
- [x] Spec is saved to `artifacts/specs/cli-run-spec.md`
