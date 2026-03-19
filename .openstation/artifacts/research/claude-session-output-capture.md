---
kind: research
name: claude-session-output-capture
agent: researcher
task: "[[0095-research-printing-claude-session-to]]"
created: 2026-03-10
---

# Claude Session Output Capture for Run Logs

## Summary

**Feasible: Yes.** Claude Code provides three viable mechanisms for
capturing session output in `openstation run` logs. The recommended
approach uses `--output-format stream-json` piped to stdout, which
provides a rich, real-time transcript including tool calls, assistant
messages, and metadata.

---

## 1. CLI Flags for Output/Session Capture

### `--print` (`-p`)

Non-interactive mode. Claude executes the prompt and writes output
to stdout, then exits. This is already used by `openstation run`.

- **stdout**: Contains the session output (format depends on
  `--output-format`)
- **stderr**: Contains progress/status messages (spinners, tool
  execution notices in interactive mode — minimal in print mode)

### `--output-format` (print mode only)

Three formats, each with different content:

| Format | Stdout content | Tool calls included? | Streaming? |
|--------|---------------|---------------------|------------|
| `text` | Final assistant text only | No | No |
| `json` | Single JSON object with final result | No | No |
| `stream-json` | NDJSON stream of all messages | **Yes** | Yes |

**`text`** — Only the final assistant response text. No tool calls,
no intermediate messages. Currently used by `_exec_or_run` (single
task / by-agent mode).

**`json`** — A single JSON object after completion. Contains the
final result but not intermediate tool calls or conversation turns.
Currently used by `run_single_task` (subtask queue mode), captured
to `artifacts/logs/<task>.json`.

**`stream-json`** — NDJSON (newline-delimited JSON) stream emitted
in real-time. Each line is a JSON object representing a message
event. Includes:
- User messages
- Assistant text responses
- Tool use requests (tool name, input)
- Tool results
- System messages (init with session_id, result summary)

### `--include-partial-messages`

Only works with `--output-format=stream-json`. Includes partial
streaming chunks as they arrive (token-by-token). Not useful for
log capture — increases volume substantially for minimal benefit.

### `--session-id <uuid>`

Forces a specific session UUID. Useful for correlating the run
log with the on-disk session JSONL file stored by Claude Code.

### `--no-session-persistence`

Disables writing the session to `~/.claude/projects/`. Print mode
only. If enabled, no on-disk session file is created — only stdout
capture remains.

### `--verbose`

Enables verbose logging — shows full turn-by-turn output. Works
in both interactive and print modes. Writes to stderr.

## 2. Session Artifacts on Disk (`~/.claude/`)

### Location

```
~/.claude/projects/<project-path-with-dashes>/<session-uuid>.jsonl
```

Example for this project:
```
~/.claude/projects/-Users-leonid-workspace-open-station/<uuid>.jsonl
```

### Format

JSONL (newline-delimited JSON). Each line is a message event
containing the full conversation transcript: user messages,
assistant responses, tool calls, tool results, thinking blocks.

### Subagent sessions

Subagent sessions are stored as separate files:
```
~/.claude/projects/<project-path>/<session-uuid>/<agent-uuid>.jsonl
```
(Note the session directory containing agent-specific files.)

### Third-party tools

Several community tools exist for processing these files:
- `simonw/claude-code-transcripts` — converts JSONL to HTML
- `daaain/claude-code-log` — converts JSONL to readable HTML
- `extract-transcripts` CLI — converts JSONL to Markdown

### Caveats

- These files are an **internal, undocumented format** — schema
  may change between Claude Code versions without notice
- Files are per-project, keyed by a mangled absolute path
- No official API to query session files programmatically
- `--no-session-persistence` suppresses these files entirely

## 3. Claude Agent SDK (Programmatic Alternative)

The Claude Agent SDK (Python/TypeScript) provides a `query()`
function that yields message objects in real-time — the richest
capture mechanism. Each message includes type, content, tool
calls, results, and session metadata.

However, using the SDK would require replacing the current
`subprocess.run(["claude", ...])` approach with a Python library
dependency, which is a larger architectural change.

## 4. Limitations and Trade-offs

### `--output-format text`

- **No tool calls** — only final assistant text
- No session metadata (no session_id, no cost info)
- Cannot reconstruct what the agent did, only what it said last
- Currently used in `_exec_or_run` with `os.execvp` — stdout
  goes to terminal, not captured

### `--output-format json`

- Contains final result only — no intermediate turns
- No tool call history
- Currently captured to `artifacts/logs/<task>.json` in
  `run_single_task`
- Useful for success/failure status but not for understanding
  *what happened*

### `--output-format stream-json`

- **Richest output** — full conversation transcript
- Real-time streaming (can tee to terminal and file)
- Each line is a self-contained JSON object
- **Large volume** — a typical agent session can produce hundreds
  of lines (tens of KB to several MB)
- Includes partial messages if `--include-partial-messages` is set
  (not recommended for logs — very noisy)

### Session JSONL files

- **Undocumented internal format** — may break between versions
- Requires knowing the session UUID to locate the file
- Path derivation (`~/.claude/projects/`) uses a mangled cwd
- Not available when `--no-session-persistence` is used
- Would require post-hoc file copy rather than real-time capture

### Streaming vs. buffered

- `stream-json` streams in real-time — can be captured with
  `subprocess.Popen` + line-by-line reading
- `json` is buffered — single write after completion
- `text` is buffered — single write after completion

### Size concerns

- A typical 5-minute agent session with `stream-json` produces
  50-500 KB of JSONL
- A complex multi-tool session can reach several MB
- Log rotation or size limits may be warranted

## 5. Recommendation

### Approach: Use `--output-format stream-json` with `tee`-style capture

**Rationale**: This is the only stdout-based mechanism that captures
the full session transcript (tool calls, intermediate messages,
final result) without depending on undocumented internal files.

### Integration sketch for `run_single_task`

```python
def run_single_task(...):
    cmd = build_command(..., output_format="stream-json")

    log_file = log_dir / f"{task_name}.jsonl"  # .jsonl not .json

    with open(log_file, "w") as f:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=str(root))
        for line in proc.stdout:
            f.write(line.decode())  # capture to log
            # Optionally: parse JSON, extract assistant text,
            # print summary to stderr for operator visibility
        proc.wait()

    return proc.returncode
```

### Integration sketch for `_exec_or_run`

The `_exec_or_run` path currently uses `os.execvp`, which replaces
the process — no capture possible. Two options:

1. **Switch to `subprocess.run`** — lose the "pass-through terminal"
   behavior but gain log capture
2. **Use `--session-id`** — pass a known UUID, then after the
   session completes (or on next run), copy the session JSONL from
   `~/.claude/projects/` to `artifacts/logs/`. Fragile (depends on
   internal format) but preserves `execvp` behavior.

Recommended: option 1 for consistency with `run_single_task`.

### Key design decisions

| Decision | Recommendation |
|----------|---------------|
| Output format | `stream-json` (richest, real-time) |
| Log file extension | `.jsonl` (reflects actual format) |
| Capture method | `subprocess.Popen` + line iteration |
| Terminal echo | Optional: parse stream, print assistant text to stderr |
| Session persistence | Keep enabled (default) — provides backup via `~/.claude/` |
| Size management | Add log rotation or max-size flag in future if needed |
| `execvp` replacement | Switch to `subprocess.run` for capture |
