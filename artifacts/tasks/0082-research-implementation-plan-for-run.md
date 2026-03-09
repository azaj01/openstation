---
kind: task
name: 0082-research-implementation-plan-for-run
status: done
assignee: researcher
owner: user
parent: "[[0078-improve-run-command-readability-and]]"
artifacts:
  - "[[artifacts/research/run-command-ux-implementation-plan]]"
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

## Findings

Full plan at `artifacts/research/run-command-ux-implementation-plan.md`.

**Key decisions**:

1. **Output helpers stay inline** in `bin/openstation` (no new
   module) — keeps the single-file CLI design.

2. **`execvp` stays** for single-task and by-agent paths. The
   preamble (header, agent detail, launch hint) is the only
   improvement possible before process replacement. Switching to
   `subprocess.run` adds signal-forwarding complexity for minimal
   gain — recommended as Phase 2 only if post-exec output is
   needed later.

3. **Claude CLI JSON output** → redirect to log file
   (`artifacts/logs/<task>.json`) rather than parsing it. Parsing
   couples us to an undocumented schema.

4. **`--quiet`** not yet on the run subparser — needs adding.
   Gates all progress output via a module-level `_quiet` flag.
   `failure()` and `err()` always print.

5. **`--json` for live runs** only works on the subtask-loop
   path (the only path with post-exec control). Document this
   limitation.

6. **All 0079 recommendations are feasible**. Three need minor
   adjustment: `--json` scope limited to subtask path, tier shown
   in preamble only (not per-task), and claude output redirected
   rather than parsed.

7. **6 implementation steps** ordered for independent mergeability.
   Steps 1–3 (output helpers, subtask loop refactor, preambles)
   are the core UX win. Steps 4–6 (quiet, json, log capture) are
   additive.

8. **3 existing test classes** need updates (changed stderr text).
   **7 new tests** recommended for output functions, quiet mode,
   json summary, and NO_COLOR.

## Verification

- [ ] Plan covers both execution paths (multi-task and single)
- [ ] Specific functions and line numbers referenced
- [ ] `--quiet` / `--json` threading explained
- [ ] `execvp` vs `subprocess.run` trade-off analyzed
- [ ] Claude CLI JSON output handling addressed
- [ ] Test impact identified
- [ ] Artifact written to `artifacts/research/`
