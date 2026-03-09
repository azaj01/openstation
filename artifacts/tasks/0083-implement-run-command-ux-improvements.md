---
kind: task
name: 0083-implement-run-command-ux-improvements
status: done
assignee: developer
owner: user
parent: "[[0078-improve-run-command-readability-and]]"
created: 2026-03-09
---

# Implement run command UX improvements

Improve `openstation run` output readability, intermediate step
reporting, and session resumability. All changes in
`bin/openstation`.

## Context

- Research: `artifacts/research/run-command-ux-patterns.md`
- Implementation plan: `artifacts/research/run-command-ux-implementation-plan.md`
- Plan file: `.claude/plans/sorted-soaring-peacock.md`
- Current code: `bin/openstation` — `cmd_run` (line 861),
  `run_single_task` (line 796), `_exec_or_run` (line 976)

## Requirements

### 1. Add output helper functions (after line 658)

Add between `info()`/`err()` and the write-command helpers:

- `_use_color()` — `sys.stderr.isatty()` and `NO_COLOR` env
- `_green`, `_red`, `_bold`, `_dim` — ANSI wrappers
- `header(text)` — `── text ─────────` section separator
- `step(n, total, name)` — `[1/3] task-name`
- `detail(label, value)` — indented `label: value`
- `success(msg)` — `✓ msg` (green)
- `failure(msg)` — `✗ msg` (red, always prints even in quiet)
- `remaining_line(msg)` — `· msg`
- `hint(msg)` — dim hint line
- `format_duration(seconds)` — `45s` or `2m 05s`
- `summary_block(completed, failed, pending, resume_cmd, next_task)`

Add `import time` to imports. Add module-level `_quiet = False`.
Gate `info()` on `_quiet`.

### 2. Add `--quiet` flag to run subparser

Add `-q`/`--quiet` argument. Set `global _quiet` at top of
`cmd_run`.

### 3. Refactor subtask loop (lines 910-936)

- **Before loop**: add `header()`, keep `info()` for collection
  and subtask count
- **Per-task**: use `step()`, wrap `run_single_task` with
  `time.time()`, print `success()`/`failure()` with duration
- **After loop**: use `summary_block()` with resume command and
  next-task name instead of plain `info()` summary

### 4. Update `run_single_task` (lines 796-852)

- Replace `info("task ... → agent ...")` with `detail("agent", agent)`
- Replace `info("Launching agent ...")` with `hint("Launching ...")`

### 5. Add preambles before `execvp` calls

**`_exec_or_run`** and **by-agent path**: add `header()`,
`detail()`, and `hint()` before `os.execvp`.

### 6. Redirect claude JSON output in subtask loop

In `run_single_task`, redirect subprocess stdout to
`artifacts/logs/<task>.json`. Print `detail("log", path)`.
Only affects subprocess path — execvp paths unchanged.

## Expected output

Multi-task:
```
── openstation run --task 0078 ──────────────

  Task collection: 0078-improve-run-command
  Found 3 ready subtasks

[1/1] 0079-research-cli-run-command-ux
      agent: researcher
      Launching claude -p "Execute task..." ...
      ✓ Done (exit 0, 4m 32s)
      log: artifacts/logs/0079-research-cli-run-command-ux.json

── Summary ──────────────────────────────────
      ✓ 1 completed
      · 2 remaining

  Next: 0080-implement-output-formatting

  To continue:
    openstation run --task 0078
```

Single-task (preamble only, then execvp):
```
── openstation run --task 0079 ──────────────

      Task: 0079-research-cli-run-command-ux
      Agent: researcher
      Tier: 2 (autonomous)

  Launching claude -p "Execute task..." ...
```

## Test updates

Existing tests should still pass (info() text unchanged, new
output is additive). Add new tests:
- `test_format_duration` — edge cases
- `test_use_color_no_color_env` — NO_COLOR=1 disables ANSI
- `test_quiet_suppresses_progress` — --quiet flag
- `test_summary_block_output` — resume command appears

## Verification

- [ ] Output helpers added and unit-tested
- [ ] `--quiet` flag suppresses progress, not failures
- [ ] Subtask loop shows step numbers, timing, ✓/✗
- [ ] Summary block shows resume command and next task
- [ ] `run_single_task` shows agent and launch details
- [ ] Preambles appear before execvp (single-task, by-agent)
- [ ] Claude JSON output redirected to log file (subprocess path)
- [ ] NO_COLOR env var respected
- [ ] All existing tests pass
- [ ] New tests added and pass
