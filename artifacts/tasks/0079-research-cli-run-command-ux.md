---
kind: task
name: 0079-research-cli-run-command-ux
status: done
assignee: researcher
owner: user
parent: "[[0078-improve-run-command-readability-and]]"
artifacts:
  - "[[artifacts/research/run-command-ux-patterns]]"
created: 2026-03-08
---

# Research CLI run command UX patterns

Research best practices for CLI progress output, readability,
and session resumability to inform the implementation of
`openstation run` UX improvements.

## Context

The current `openstation run` command (see `bin/openstation`,
`cmd_run` at line 861) has three UX problems:
1. Output is hard to read — no visual hierarchy
2. Middle steps are silent (agent resolution, tool parsing, etc.)
3. No actionable resume instructions on partial completion

## Requirements

- **Progress patterns** — study how well-known CLIs (npm, cargo,
  docker, terraform, gh) communicate multi-step progress. Focus
  on: step numbering, spinners vs. static lines, color/emoji
  usage, verbose vs. quiet modes.

- **Readability patterns** — how do CLIs visually separate
  sections when running multiple sub-operations? Look at
  indentation, headers, dividers, summary blocks.

- **Resumability patterns** — how do CLIs handle partial failure
  in multi-step operations? Study: resume commands, checkpoint
  files, "run again to continue" UX, showing remaining work.

- **Our constraints** — the run command uses `subprocess.run`
  for subtask execution and `os.execvp` for single-task/agent
  mode. Output goes to stderr (`info()`/`err()`). Must preserve
  `--json` and `--quiet` behavior.

- **Recommendations** — produce concrete, actionable
  recommendations for the three problem areas, with code-level
  suggestions where possible (e.g., specific output format
  templates, helper functions).

## Artifact

Output: `artifacts/research/run-command-ux-patterns.md`

## Findings

Research covered 6 CLIs (cargo, docker, terraform, npm, gh, plus
clig.dev meta-guidelines) across the three problem areas. Full
analysis in [[artifacts/research/run-command-ux-patterns]].

**Progress**: The dominant patterns are step numbering (`[1/3]`)
for bounded work and verb-prefix (`Compiling...` → `Finished`)
for unbounded. Tense shifts from gerund to past tense are
near-universal. All studied CLIs print something within 100ms.

**Readability**: Two levels of visual hierarchy (phase headers +
step lines) covers most cases. Symbols (✓/✗) beat color alone
for scanability. Most important info goes at the bottom.

**Resumability**: Our status model already provides natural
idempotency (done tasks are skipped on re-run). The gap is
output: need to print a copy-pasteable resume command, name the
failed and next-pending tasks, and show completed/remaining counts.

**Constraints**: `execvp` limits single-task mode to preamble
improvements only. Multi-task loop has full control. `--json`
and `--quiet` addressed with a global flag wrapping output
functions.

## Recommendations

1. Replace `info:` prefix with semantic output functions
   (`header`, `step`, `detail`, `success`, `failure`) — concrete
   Python code provided in artifact §5b.
2. Add timing (`time.time()` around `subprocess.run`) and
   display elapsed duration per task.
3. Print copy-pasteable resume command + next task name in
   the summary block.
4. Respect `NO_COLOR` env var and TTY detection per no-color.org.
5. Emit JSON summary object at end of subtask loop for `--json`.

See artifact §5 for full implementation templates.

## Verification

- [ ] Research covers at least 4 well-known CLIs
- [ ] Each of the 3 problem areas has specific recommendations
- [ ] Recommendations are concrete (format examples, not just
      "make it better")
- [ ] Constraints section addressed (json, quiet, execvp)
- [ ] Artifact written to `artifacts/research/`
