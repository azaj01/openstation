---
kind: research
name: attached-mode-for-openstation-run
agent: researcher
task: "[[0119-research-attached-mode-for-openstation]]"
created: 2026-03-12
---

# Attached Mode for `openstation run`

Research into how `openstation run` can launch an interactive
(attached) Claude session with pre-loaded task context.

---

## 1. Claude CLI: Interactive Sessions with Pre-Loaded Context

### How it works

The Claude CLI starts an **interactive session by default**. The
`-p`/`--print` flag switches to non-interactive mode. Key
mechanisms for pre-loading context:

| Mechanism | Syntax | Mode | Behavior |
|-----------|--------|------|----------|
| Positional prompt | `claude "do X"` | Interactive | Opens REPL with the prompt as the first user message |
| `-p` flag | `claude -p "do X"` | Non-interactive | Prints response and exits |
| `--agent` | `claude --agent name` | Either | Loads agent system prompt |
| `--resume` | `claude --resume <id>` | Interactive | Resumes a prior session |
| `--continue` | `claude --continue` | Interactive | Continues most recent session in cwd |
| `--system-prompt` | `claude --system-prompt "..."` | Either | Custom system prompt |
| `--append-system-prompt` | `claude --append-system-prompt "..."` | Either | Appends to default system prompt |

**Key insight:** `claude --agent <name> "Execute task X..."` starts
an interactive session with the agent loaded AND the task prompt
sent as the first message. The user can then interact freely. This
is the exact pattern needed for attached mode.

### Confirmed combinations

```bash
# Attached mode — interactive with agent + prompt
claude --agent researcher "Execute task 0042-foo. Read its spec at artifacts/tasks/0042-foo.md and work through the requirements."

# With tool restrictions
claude --agent researcher --allowedTools Read Edit Bash Grep Glob "Execute task 0042-foo..."

# With permission mode
claude --agent researcher --permission-mode default "Execute task 0042-foo..."
```

### `--max-turns` flag

**Not documented** in `claude --help`. The current `build_command`
passes `--max-turns` but this flag does not appear in the CLI help
output. It may be silently ignored or undocumented. This should be
verified before relying on it for either mode.

---

## 2. Flag Compatibility Matrix

Flags currently used by `build_command` (tier 2) and their
compatibility with interactive (attached) mode:

| Flag | Tier 2 (current) | Interactive mode | Notes |
|------|-------------------|------------------|-------|
| `--agent` | Yes | **Compatible** | Works in both modes |
| `-p` (prompt) | Yes | **Remove** | Makes it non-interactive — the whole point |
| `--allowedTools` | Yes | **Compatible** | Works in both modes |
| `--max-budget-usd` | Yes | **Incompatible** | "only works with `--print`" per help |
| `--max-turns` | Yes | **Unknown** | Not in `--help`; may be ignored |
| `--output-format` | Yes | **Incompatible** | "only works with `--print`" per help |
| `--verbose` | Yes | **Compatible** | Works in both modes |
| `--permission-mode` | No (tier 1 only) | **Compatible** | Works in both modes |
| `--debug-file` | No | **Compatible** | Writes debug logs to file |

### Flags that are print-only (incompatible with attached)

- `--max-budget-usd`
- `--output-format`
- `--input-format`
- `--fallback-model`
- `--no-session-persistence`
- `--include-partial-messages`
- `--replay-user-messages`

### Flags that work in interactive mode

- `--agent`
- `--allowedTools` / `--disallowedTools`
- `--permission-mode`
- `--verbose`
- `--debug-file`
- `--system-prompt` / `--append-system-prompt`
- `--model`
- `--effort`
- `--worktree`
- `--add-dir`
- `--mcp-config`

---

## 3. Log Capture in Attached Mode

### The problem

In detached mode, stdout is piped through `subprocess.Popen` →
`_stream_and_capture()` writes every line to a `.jsonl` log file.
In attached mode, stdout IS the terminal — there's nothing to
capture.

### Options

| Approach | Feasibility | Trade-offs |
|----------|------------|------------|
| **No log capture** | Simple | Session is still persisted by Claude internally; can `--resume` later. Lose the `.jsonl` artifact. |
| **`--debug-file`** | Works | Writes debug-level logs (API calls, tool usage) to a file. Verbose, not the same format as stream-json. |
| **`script` command** | Works | `script -q logfile claude ...` captures terminal output. Messy (includes ANSI escapes, user input). |
| **`tee` with PTY** | Complex | Requires `script` or `expect`-style PTY allocation to tee stdout while keeping interactive. Over-engineered. |

### Recommendation

**Skip log capture for attached mode.** Claude's built-in session
persistence (`--resume`) provides the same replay capability.
Optionally pass `--debug-file` for troubleshooting. The `.jsonl`
log artifact is a detached-mode feature only.

---

## 4. Subtask Orchestration in Attached Mode

### Current behavior (detached)

`cmd_run` with `--task` finds ready subtasks, loops through them
sequentially, calling `run_single_task()` for each. Each subtask
runs as a `subprocess.Popen` → `_stream_and_capture()` cycle.

### Problem with attached + multiple subtasks

Interactive sessions replace the process (`os.execvp`) or take
over the terminal. You can't loop through N interactive sessions
programmatically — each one requires the user to interact and
finish before the next starts.

### Recommendation

**Attached mode should be single-task only.** Rationale:

1. The user wants to participate in a specific task, not watch
   N tasks run sequentially.
2. Multi-task orchestration is inherently a detached concern.
3. If `--task` resolves to subtasks, attached mode should either:
   - (a) Error: "Attached mode not supported for tasks with ready subtasks. Use `--task <subtask-id>` directly."
   - (b) Run only the first subtask and stop.

Option (a) is cleaner — it forces the user to be explicit about
which subtask they want to participate in.

---

## 5. Proposed CLI Interface

### Flag design

```
openstation run --task <id> --attached
openstation run --task <id> -a            # short form
```

`--attached` / `-a` is a boolean flag. It modifies the execution
mode from detached (default) to interactive.

#### Why `--attached` over alternatives

| Alternative | Verdict | Reason |
|------------|---------|--------|
| `--interactive` / `-i` | Rejected | Conflicts with common `-i` conventions (e.g., `grep -i`, `docker -i`) |
| `--attached` / `-a` | **Chosen** | Clear metaphor (vs "detached" default), no common conflicts |
| `--tier 1` (existing) | Rejected | Tier 1 already exists but doesn't pass the task prompt or tools |
| `--live` | Rejected | Ambiguous — could mean "live reload" |

### `build_command` changes

Add an `attached` parameter (default `False`):

```python
def build_command(agent_name, tier, budget, turns, prompt, tools,
                  output_format="json", attached=False):
    if attached:
        cmd = ["claude", "--agent", agent_name]
        cmd.extend(["--allowedTools"] + tools)
        cmd.append(prompt)  # positional prompt, not -p
        return cmd

    # ... existing tier 1/2 logic unchanged ...
```

Key differences from detached:
- No `-p` flag (interactive mode)
- No `--max-budget-usd` (print-only)
- No `--max-turns` (undocumented, print-only behavior)
- No `--output-format` (print-only)
- No `--verbose` (not needed without stream-json)
- Prompt is a **positional argument**, not after `-p`
- `--allowedTools` is preserved (works in both modes)
- `--agent` is preserved (works in both modes)

### Execution changes

In `_exec_or_run` and `run_single_task`:

```python
if attached:
    # Validate: no subtask orchestration
    # Build command with attached=True
    # Use os.execvp (replace process) — same as tier 1 dispatch
    cmd = build_command(..., attached=True)
    os.execvp(cmd[0], cmd)
```

Use `os.execvp` (not `subprocess.Popen`) because:
- The user needs direct terminal I/O
- No log capture is needed
- Process replacement is simpler than managing a child process

### Incompatibilities to enforce

| Flag combo | Behavior |
|-----------|----------|
| `--attached` + `--json` | Error: "JSON output not supported in attached mode" |
| `--attached` + `--quiet` | Error or warning: quiet has no effect in attached mode |
| `--attached` + `--dry-run` | **Allowed** — still useful to preview the command |
| `--attached` + `--budget` | Warning: budget limit not enforced in interactive mode |
| `--attached` + `--turns` | Warning: turn limit not enforced in interactive mode |
| `--attached` + task with subtasks | Error: "Use `--task <subtask-id>` for attached mode" |

### Full example flow

```bash
# Detached (current default)
$ openstation run --task 0042
  ▸ openstation run --task 0042-research-foo
  Task  0042-research-foo
  Agent researcher
  ...
  # runs in background, captures logs

# Attached (new)
$ openstation run --task 0042 --attached
  # replaces process with:
  # claude --agent researcher --allowedTools Read Edit Bash ... \
  #   "Execute task 0042-research-foo..."
  # user is now in an interactive Claude session
```

---

## 6. Relationship to Existing Tier 1

Tier 1 (`--tier 1`) currently builds a minimal command:
```python
["claude", "--agent", agent_name, "--permission-mode", "acceptEdits"]
```

This is similar to attached mode but lacks:
- Task-specific prompt
- Tool restrictions from agent spec
- Any prompt at all

**Recommendation:** `--attached` should **replace** `--tier 1`
semantically. Tier 1 was the prototype; `--attached` is the
complete version. Consider deprecating `--tier` entirely in favor
of `--attached` as a cleaner abstraction.

---

## Summary

| Requirement | Finding |
|-------------|---------|
| Interactive + pre-prompted | `claude --agent <name> "prompt"` (positional prompt, no `-p`) |
| Compatible flags | `--agent`, `--allowedTools`, `--permission-mode`, `--model`, `--effort` |
| Incompatible flags | `--max-budget-usd`, `--output-format`, `--max-turns` (all print-only) |
| Log capture | Skip it; use `--resume` for replay, `--debug-file` for troubleshooting |
| Subtask orchestration | Single-task only; error on tasks with ready subtasks |
| CLI interface | `--attached` / `-a` flag; `os.execvp` execution |
