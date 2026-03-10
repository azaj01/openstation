---
kind: task
name: 0095-research-printing-claude-session-to
type: research
status: review
assignee: researcher
owner: user
parent: "[[0078-improve-run-command-readability-and]]"
created: 2026-03-10
artifacts:
  - "[[artifacts/research/claude-session-output-capture]]"
---

# Research Printing Claude Session To Run Output Log

## Requirements

1. Investigate whether Claude Code exposes session output (stdout/stderr) in a way that `openstation run` can capture and include in its log.
2. Research Claude Code CLI flags, environment variables, and session artifacts (e.g., `~/.claude/` session files) that might contain or stream the conversation/session transcript.
3. Determine whether the Claude Code `--print` flag, `--output-format`, or piped stdout can provide a usable session transcript after execution completes.
4. Identify any limitations (streaming vs. buffered, truncation, binary content, token limits) that would affect including session output in the run log.
5. Provide a recommendation: feasible or not, and if feasible, a suggested approach for integration into `openstation run`.

## Findings

**Feasible: Yes.** Three capture mechanisms exist; `--output-format stream-json` is the best fit.

### CLI Output Formats

- **`text`** — Final assistant text only. No tool calls. Currently used by `_exec_or_run`.
- **`json`** — Single JSON result object. No intermediate turns. Currently used by `run_single_task` and saved to `artifacts/logs/<task>.json`.
- **`stream-json`** — NDJSON stream of all messages: user, assistant, tool use, tool results, system init. The only format that captures the full session transcript via stdout.

### Session Files on Disk

Claude Code stores sessions as JSONL at `~/.claude/projects/<mangled-path>/<uuid>.jsonl`. These contain the full transcript but use an **undocumented internal format** that may change between versions. Community tools (simonw/claude-code-transcripts, daaain/claude-code-log) parse these files.

### Key Limitations

- `stream-json` produces 50 KB–several MB per session (proportional to session length)
- `_exec_or_run` uses `os.execvp` which replaces the process — no capture possible without switching to `subprocess.run`/`Popen`
- Session JSONL files are internal/undocumented — fragile for production use
- No environment variables control output format (CLI flags only)

## Recommendations

1. **Switch `run_single_task` to `--output-format stream-json`** with `subprocess.Popen` and line-by-line capture to `.jsonl` log files.
2. **Replace `os.execvp` in `_exec_or_run`** with `subprocess.run` to enable log capture in single-task mode.
3. **Optionally tee assistant text to stderr** for operator visibility during execution.
4. **Do not depend on `~/.claude/` session files** — they are undocumented internals.

See `artifacts/research/claude-session-output-capture.md` for full analysis and integration sketches.

## Verification

- [ ] Research covers Claude Code CLI flags related to output/session capture
- [ ] Research covers session artifacts stored on disk (`~/.claude/`)
- [ ] Limitations and trade-offs are documented
- [ ] A clear feasibility recommendation is provided with rationale
- [ ] If feasible, a suggested integration approach is outlined
