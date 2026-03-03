---
kind: task
name: 0028-cli-run-integration
status: ready
agent: developer
owner: manual
created: 2026-03-01
---

# Integrate openstation-run.sh with CLI and improve readability

## Requirements

- Integrate `openstation-run.sh` into the Open Station CLI so
  agents can be launched via a unified command (e.g.,
  `/openstation.dispatch` or a `run` subcommand) rather than
  calling the shell script directly.
- Improve readability of `openstation-run.sh`:
  - Add section comments and inline documentation for
    non-obvious logic (frontmatter parsing, tier selection,
    streaming pipeline).
  - Simplify complex conditionals where possible.
  - Ensure consistent formatting and naming conventions.
- Preserve all existing functionality: tier 1/2 execution,
  `--task` resolution, `--dry-run`, allowed-tools parsing,
  budget/turns limits, and live streaming progress (stream-json).
- Update `/openstation.dispatch` command to reference the
  integrated run path if applicable.

## Findings

Refactored `openstation-run.sh` with the following improvements:

1. **Added file-level docstring** — describes purpose, tiers, and
   execution flow at the top of the script.
2. **Extracted helper functions** — `resolve_task_agent()`,
   `find_agent_spec()`, and `build_command()` replace inline code
   blocks, each with a docstring explaining inputs/outputs.
3. **Added `info()` helper** — alongside `err()` for consistent
   colored output.
4. **Improved `find_project_root()`** — split compound conditional
   into two separate `if` blocks for readability.
5. **Enhanced `parse_allowed_tools()` docs** — added example input
   format and description of quote-stripping behavior.
6. **Compacted argument parsing** — one-liner validation with
   `[[ ]] && { err; exit; }` pattern reduces vertical noise while
   preserving all error paths.
7. **Numbered main flow** — steps 1-5 at the bottom of the script
   make the execution order explicit.
8. **Updated `/openstation.dispatch`** — now shows tier 1, tier 2,
   and `--task` launch instructions referencing `openstation-run.sh`.
9. **Synced `.openstation/` copy** — both copies now include
   `--task` support and all readability improvements.

**Note**: Full Python CLI integration (as a `run` subcommand of
`bin/openstation`) depends on task 0024-cli-implementation
completing first. The shell script remains the canonical run
mechanism until then.

## Subtasks

### P0

1. **Spec: CLI run subcommand** (0038-cli-run-spec) — Define
   the interface, execution model, and error handling for the
   `openstation run` subcommand. Agent: researcher.

### P1

2. **Implement CLI run subcommand** (0039-cli-run-implement) —
   Build the `run` subcommand in Python based on the spec,
   port shell logic, update dispatch command. Agent: developer.
   Depends on 0038.

## Verification

- [ ] Spec produced and approved (0038)
- [ ] `openstation run` subcommand implemented and functional (0039)
- [ ] All existing flags work via the new CLI path
- [ ] `/openstation.dispatch` references the new run command
