---
kind: task
name: 0082-research-implementation-plan-for-run
status: ready
assignee: researcher
owner: user
parent: "[[0078-improve-run-command-readability-and]]"
created: 2026-03-08
---

# Research implementation plan for run command UX

Produce a concrete implementation plan for improving
`openstation run` output, grounded in the current codebase
and the UX research from task 0079.

## Context

- UX research: `artifacts/research/run-command-ux-patterns.md`
  — has proposed output formats, helper functions, and
  integration points
- Current implementation: `bin/openstation`, `cmd_run` (line
  861), `run_single_task` (line 796), `_exec_or_run` (line 976)
- The research proposes semantic output functions, timing,
  resume commands, and NO_COLOR support — but hasn't been
  validated against the actual code paths and edge cases

## Requirements

- **Read the current `cmd_run` implementation** in
  `bin/openstation` end-to-end. Trace both execution paths:
  1. Multi-task (subtask loop via `subprocess.run`)
  2. Single-task / by-agent (`os.execvp`)

- **Read the research artifact** (`artifacts/research/
  run-command-ux-patterns.md`) and its recommendations (§5)

- **Produce an implementation plan** that maps recommendations
  to specific code changes:
  1. Which functions to add/modify (with line references)
  2. Where the new output helpers go (new module vs. inline)
  3. How `--quiet` and `--json` flags thread through
  4. What changes in the subtask loop vs. `_exec_or_run` vs.
     `run_single_task`
  5. Edge cases: what happens when `execvp` is used (single
     task) — can we switch to `subprocess.run` there too?
     Trade-offs?
  6. How to handle the raw JSON blob that `claude` CLI dumps
     to stdout (parse it? suppress it? summarize it?)
  7. Test impact — which existing tests need updating

- **Validate feasibility** — flag any recommendations from
  task 0079 that are impractical or need rethinking

## Artifact

Output: `artifacts/research/run-command-ux-implementation-plan.md`

## Verification

- [ ] Plan covers both execution paths (multi-task and single)
- [ ] Specific functions and line numbers referenced
- [ ] `--quiet` / `--json` threading explained
- [ ] `execvp` vs `subprocess.run` trade-off analyzed
- [ ] Claude CLI JSON output handling addressed
- [ ] Test impact identified
- [ ] Artifact written to `artifacts/research/`
