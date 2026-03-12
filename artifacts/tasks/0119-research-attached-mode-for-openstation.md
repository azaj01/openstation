---
kind: task
name: 0119-research-attached-mode-for-openstation
type: feature
status: done
assignee: researcher
owner: user
artifacts:
  - "[[artifacts/research/attached-mode-for-openstation-run]]"
created: 2026-03-12
---

# Research attached mode for `openstation run`

## Context

`openstation run` currently launches Claude with `-p` (non-interactive,
stream-json output). The session runs detached — the user gets a
session ID and must `claude --resume <id>` to interact. We want an
`--attached` flag that opens an interactive Claude session the user
can participate in directly.

See `src/openstation/run.py` — `build_command()`, `_exec_or_run()`,
and `_stream_and_capture()` for the current launch logic.

## Requirements

1. Investigate how `claude` CLI supports interactive sessions with
   a pre-loaded task context (e.g., `--prompt` vs `-p`, `--resume`,
   `--agent` flag combinations). Run `claude --help` and test
   combinations.
2. Determine which existing `run` flags are compatible with an
   interactive session (`--max-budget-usd`, `--max-turns`,
   `--allowedTools`, etc.)
3. Clarify whether log capture is possible or desirable in attached
   mode (stdout is the terminal, not a pipe).
4. Identify how subtask orchestration (multiple subtasks in sequence)
   should behave in attached mode — does it make sense, or is
   attached only for single-task runs?
5. Propose the CLI interface (`--attached`, `-a`, or alternative)
   and the `build_command` changes needed.

## Findings

Full research in [[artifacts/research/attached-mode-for-openstation-run]].

**Req 1 — Interactive + pre-prompted sessions:** `claude --agent <name> "prompt text"` (positional prompt, no `-p`) starts an interactive REPL with the agent loaded and the prompt sent as the first message. No `--prompt` flag exists; the prompt is a positional argument.

**Req 2 — Flag compatibility:** `--agent`, `--allowedTools`, `--permission-mode`, `--model`, and `--effort` all work in interactive mode. `--max-budget-usd`, `--output-format`, and `--input-format` are print-only (incompatible). `--max-turns` is not documented in `claude --help` at all — likely ignored or undocumented.

**Req 3 — Log capture:** Not feasible without PTY tricks. Recommendation: skip log capture in attached mode. Claude's built-in session persistence (`--resume`) provides replay. Optionally use `--debug-file` for troubleshooting.

**Req 4 — Subtask orchestration:** Attached mode should be single-task only. Interactive sessions replace the process via `os.execvp`; looping through N interactive sessions is not viable. Error when a task has ready subtasks — force the user to target a specific subtask.

**Req 5 — CLI interface:** `--attached` / `-a` boolean flag. Uses `os.execvp` (process replacement, same as existing dispatch/tier-1). `build_command` gains an `attached` parameter that drops `-p`, budget, output-format, and turns flags, keeping `--agent` and `--allowedTools`. Consider deprecating `--tier` in favor of `--attached`.

## Recommendations

1. Add `--attached` / `-a` flag to `openstation run`. Incompatible with `--json`, `--quiet`, and multi-subtask orchestration.
2. Deprecate `--tier 1` — `--attached` is the complete replacement (adds task prompt + tool restrictions that tier 1 lacks).
3. Verify whether `--max-turns` is silently accepted or rejected by Claude CLI before relying on it in detached mode either.
4. For attached dry-run, show the command that would be `execvp`'d — still useful for debugging.

## Verification

- [ ] Documents which `claude` CLI flags enable interactive + pre-prompted sessions
- [ ] Lists incompatibilities and edge cases (e.g., `--json` + attached)
- [ ] Recommends a design for the `--attached` flag with rationale
