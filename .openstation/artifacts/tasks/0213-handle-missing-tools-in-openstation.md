---
kind: task
name: 0213-handle-missing-tools-in-openstation
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-22
---

# Handle Missing Tools In Openstation Run

## Requirements

1. Add an optional `allowed-tools` field to task frontmatter — a list of additional tool patterns (same format as agent `allowed-tools`) that get merged with the agent's tools at launch time.
2. When `openstation run` builds the command, merge task-level `allowed-tools` into the agent's `allowed-tools` list (agent tools first, then task tools, deduplicated).
3. Add a `--tools` CLI flag to `openstation run` that appends extra tool patterns at launch time (highest priority — added after agent + task tools).
4. In detached mode, if the agent's result text contains a tool-permission request pattern (e.g., "approve the tool", "need your approval", "approve tool permissions"), detect this as a soft failure and print a diagnostic: the agent stalled waiting for tool approval, suggest adding the needed tools to the task's `allowed-tools` field or using `--tools`.
5. Update `docs/task.spec.md` to document the `allowed-tools` field.

## Findings

Implemented three-tier tool merging (agent → task → CLI) and
tool-stall detection across all `openstation run` paths.

### Changes

**`src/openstation/run.py`**:
- `merge_tools(*tool_lists)` — deduplicates and merges tool lists
  preserving first-seen order. Agent tools come first, then task
  tools, then CLI tools.
- `detect_tool_stall(result_text)` — regex-based detection of
  tool-approval stall patterns in agent output. Prints a
  diagnostic with remediation hint when triggered.
- `parse_allowed_tools()` reused for both agent specs and task
  specs (same YAML frontmatter format).
- All run paths updated: by-task (`_exec_or_run`, `run_single_task`),
  by-agent, and `--verify` mode all merge tools from all sources.
- Tool-stall detection added to both detached execution paths
  (`run_single_task` and `_exec_or_run`).

**`src/openstation/cli.py`**:
- Added `--tools PATTERN [PATTERN ...]` flag to the `run`
  subparser. Accepts one or more tool patterns as separate args.

**`docs/task.spec.md`**:
- Added `allowed-tools` to the frontmatter schema block, field
  reference table, and a new "Allowed Tools Field" section with
  usage examples.

**`tests/test_run_tools.py`** (new, 22 tests):
- `TestMergeTools` — 6 unit tests for merge/dedup logic
- `TestDetectToolStall` — 9 unit tests for stall pattern detection
- `TestTaskAllowedToolsMerge` — 3 CLI integration tests for
  task-level tool merging
- `TestCliToolsFlag` — 4 CLI integration tests for `--tools` flag

## Verification

- [x] Task frontmatter `allowed-tools` field is parsed and merged with agent `allowed-tools` at launch
- [x] `--tools` CLI flag appends additional tools to the merged list
- [x] Detached run that stalls on tool approval prints a diagnostic message with remediation hint
- [x] `docs/task.spec.md` documents the `allowed-tools` field
- [x] Existing runs without `allowed-tools` field behave identically (backward compatible)
- [x] Tests cover: task tools merge, CLI tools merge, dedup, detection of stalled agent

## Verification Report

*Verified: 2026-03-24*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Task frontmatter `allowed-tools` parsed and merged at launch | PASS | `parse_allowed_tools()` called on task spec in `run_single_task()` (line 310), `_exec_or_run()` (line 390), and verify mode (line 641); merged via `merge_tools(agent_tools, task_tools, extra_tools)` |
| 2 | `--tools` CLI flag appends additional tools | PASS | `--tools` defined in cli.py:313 with `nargs="+"`, extracted at run.py:574, passed as `extra_tools`/`cli_tools` to all run paths including by-agent mode (line 834) |
| 3 | Detached stall detection with diagnostic | PASS | `detect_tool_stall()` at run.py:184 uses 8 regex patterns; called in `run_single_task()` (line 352) and `_exec_or_run()` (line 459) with `core.warn()` diagnostic and hint |
| 4 | `docs/task.spec.md` documents `allowed-tools` | PASS | Field in schema block (line 111), field reference table (line 136), dedicated "Allowed Tools Field" section (lines 219-235) with YAML examples |
| 5 | Backward compatible without `allowed-tools` | PASS | `parse_allowed_tools()` returns `[]` when field absent; `merge_tools(agent_tools, [], [])` returns only agent tools; test `test_no_task_tools_backward_compat` confirms |
| 6 | Tests cover merge, dedup, CLI tools, stall detection | PASS | 22 tests: `TestMergeTools` (6), `TestDetectToolStall` (9), `TestTaskAllowedToolsMerge` (3), `TestCliToolsFlag` (4) |

### Summary

6 passed, 0 failed. All verification criteria met — implementation covers three-tier tool merging, stall detection, documentation, backward compatibility, and comprehensive test coverage.
