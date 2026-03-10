---
kind: task
name: 0078-improve-run-command-readability-and
status: review
assignee: developer
owner: user
created: 2026-03-08
subtasks:
  - "[[0079-research-cli-run-command-ux]]"
  - "[[0082-research-implementation-plan-for-run]]"
  - "[[0083-implement-run-command-ux-improvements]]"
  - "[[0095-research-printing-claude-session-to]]"
---

# Improve run command readability and UX

The `openstation run` command works but has three UX problems
that make it frustrating for operators.

## Problems

1. **Output is hard to read** — info messages (`info()`) are
   plain text with no visual hierarchy. When running multiple
   subtasks, it's difficult to scan progress at a glance.

2. **No info about middle steps** — the command resolves agents,
   parses tools, builds commands, and launches processes, but
   most of these steps are silent. Users see "Launching agent..."
   then nothing until success/failure.

3. **No clear way to resume a session** — when a subtask fails
   or `max_tasks` is reached, the summary says "Re-run to
   continue" but doesn't tell the user the exact command to
   resume, which subtasks remain, or what completed.

## Requirements

- Improve visual formatting of run output (structured sections,
  status indicators, clear task/subtask boundaries)
- Add progress reporting for intermediate steps (agent
  resolution, tool parsing, command building, launch)
- Provide actionable resume instructions on partial completion
  or failure (exact command, remaining task list)
- Maintain backward compatibility — `--json` output and exit
  codes must not change
- Keep output concise in `--quiet` mode

## Subtasks

- [[0079-research-cli-run-command-ux]] — research best
  practices for CLI progress output and resumability
- [[0082-research-implementation-plan-for-run]] — research
  implementation plan against current codebase
- [[0083-implement-run-command-ux-improvements]] — implement
  output helpers, subtask loop refactor, preambles, log redirect

## Verification

- [ ] Run output has clear visual sections for each subtask
- [ ] Intermediate steps (agent resolve, tool parse, launch)
      are logged
- [ ] Partial completion shows exact resume command
- [ ] `--json` output unchanged
- [ ] `--quiet` mode remains concise
- [ ] Existing tests pass
