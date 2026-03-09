---
kind: research
name: run-command-ux-implementation-plan
agent: researcher
task: "[[0082-research-implementation-plan-for-run]]"
created: 2026-03-09
---

# Implementation Plan: Run Command UX

Concrete plan for improving `openstation run` output, mapping
recommendations from `run-command-ux-patterns.md` to specific
code changes in `bin/openstation`.

---

## 1. Code Inventory

### Functions involved

| Function | Lines | Role | Exec model |
|----------|-------|------|------------|
| `cmd_run` | 861–973 | Entry point, arg parsing, mode dispatch | — |
| `run_single_task` | 796–852 | Resolve agent, build cmd, `subprocess.run` | subprocess |
| `_exec_or_run` | 976–1026 | Single-task (no queue), resolves agent then `execvp` | execvp |
| `build_command` | 522–548 | Assemble `claude` CLI argv | — |
| `find_ready_subtasks` | 622–652 | Read parent frontmatter, filter ready children | — |
| `info` | 655–657 | Print `info:` to stderr | — |
| `err` | 57–58 | Print `error:` to stderr | — |

### Execution paths

```
cmd_run
├─ BY-TASK MODE (task_ref set)
│  ├─ has subtasks → subtask loop: run_single_task × N (subprocess.run)
│  └─ no subtasks → _exec_or_run (os.execvp)
└─ BY-AGENT MODE (agent_name set)
   └─ os.execvp (replaces process)
```

**Key constraint**: `os.execvp` replaces the process — no code
runs after it. Post-execution output (summary, timing) is only
possible on the subtask-loop path.

---

## 2. Output Module

### 2a. Location

Add a new section in `bin/openstation` between the existing
`info`/`err` helpers (line 655) and the write-command helpers
(line 660). All output functions stay in the single file —
no new module needed. This keeps the zero-dependency,
single-file CLI design intact.

### 2b. Functions to add

```python
# --- Output helpers (after line 658) ----------------------------------

import time  # add to imports at top (line 8 area)

_quiet = False  # module-level flag, set by cmd_run

def _use_color():
    return sys.stderr.isatty() and not os.environ.get("NO_COLOR")

def _green(s):  return f"\033[32m{s}\033[0m" if _use_color() else s
def _red(s):    return f"\033[31m{s}\033[0m" if _use_color() else s
def _bold(s):   return f"\033[1m{s}\033[0m" if _use_color() else s
def _dim(s):    return f"\033[2m{s}\033[0m" if _use_color() else s

def header(text):
    if _quiet: return
    width = 48
    line = f"── {text} " + "─" * max(0, width - len(text) - 4)
    print(_bold(line), file=sys.stderr)

def step(n, total, name):
    if _quiet: return
    print(f"\n{_bold(f'[{n}/{total}]')} {name}", file=sys.stderr)

def detail(label, value):
    if _quiet: return
    print(f"      {_dim(label + ':')} {value}", file=sys.stderr)

def success(msg):
    if _quiet: return
    print(f"      {_green('✓')} {msg}", file=sys.stderr)

def failure(msg):
    # Always print failures, even in quiet mode
    print(f"      {_red('✗')} {msg}", file=sys.stderr)

def remaining_line(msg):
    if _quiet: return
    print(f"      · {msg}", file=sys.stderr)

def hint(msg):
    if _quiet: return
    print(f"  {_dim(msg)}", file=sys.stderr)

def format_duration(seconds):
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"

def summary_block(completed, failed, pending,
                  resume_cmd=None, next_task=None):
    print(file=sys.stderr)
    header("Summary")
    if completed: success(f"{completed} completed")
    if failed:    failure(f"{failed} failed")
    if pending:   remaining_line(f"{pending} remaining")
    if next_task:
        print(f"\n  Next: {next_task}", file=sys.stderr)
    if resume_cmd and pending > 0:
        print(f"\n  To continue:", file=sys.stderr)
        print(f"    {resume_cmd}", file=sys.stderr)
```

### 2c. Modify existing `info()`

Keep `info()` but gate it on `_quiet`:

```python
def info(msg):
    if not _quiet:
        print(f"info: {msg}", file=sys.stderr)
```

This preserves backward compatibility for non-run callers while
allowing the new semantic functions to coexist.

---

## 3. Changes Per Execution Path

### 3a. Multi-task path (subtask loop) — lines 910–936

This is the primary beneficiary. Full before/during/after control.

**Before loop** (replace lines 910–916):

```python
# Current:
info(f"Task collection: {task_name}")
# ...
info(f"Found {len(subtasks)} ready subtask(s)")

# New:
header(f"openstation run --task {task_name}")
print(f"\n  Task collection: {task_name}", file=sys.stderr)
print(f"  Found {len(subtasks)} ready subtasks\n", file=sys.stderr)
```

**Per-task in loop** (replace lines 920–931):

```python
# Current:
info(f"[{completed + 1}/{max_tasks}] Executing subtask: {sub_name}")
rc = run_single_task(...)
if rc == EXIT_OK:
    completed += 1; remaining -= 1
else:
    err(f"Subtask {sub_name} failed (exit {rc})")
    break

# New:
step(completed + 1, min(len(subtasks), max_tasks), sub_name)
# Agent resolution detail comes from run_single_task (see §3d)
start = time.time()
rc = run_single_task(...)
elapsed = time.time() - start
if rc == EXIT_OK:
    success(f"Done (exit 0, {format_duration(elapsed)})")
    completed += 1; remaining -= 1
else:
    failure(f"Failed (exit {rc}, {format_duration(elapsed)})")
    break
```

**After loop** (replace lines 933–935):

```python
# Current:
info(f"Summary: {completed} completed, {remaining} remaining of {len(subtasks)} subtask(s)")
if remaining > 0 and completed >= max_tasks:
    info(f"Task limit reached ({max_tasks}). Re-run to continue.")

# New:
# Determine next pending task for resume hint
next_sub = None
if remaining > 0:
    executed_count = completed + (1 if rc != EXIT_OK else 0)
    if executed_count < len(subtasks):
        next_sub = subtasks[executed_count][1]

summary_block(
    completed=completed,
    failed=1 if rc != EXIT_OK and completed < max_tasks else 0,
    pending=remaining,
    resume_cmd=f"openstation run --task {task_name}",
    next_task=next_sub,
)
```

### 3b. Single-task path (`_exec_or_run`) — lines 976–1026

Limited to **preamble only** (before `execvp`). Replace the bare
`os.execvp` block:

```python
# Before execvp (after dry_run check, ~line 1022):
header(f"openstation run --task {task_name}")
detail("Task", task_name)
detail("Agent", agent)
print(file=sys.stderr)
hint(f"Launching {shlex_join(cmd[:4])}...")

os.chdir(str(root))
os.execvp(cmd[0], cmd)
```

### 3c. By-agent path (`cmd_run` lines 942–973)

Same constraint as 3b — `execvp` replaces the process.
Add preamble:

```python
# Before execvp (~line 969):
header(f"openstation run {agent_name}")
detail("Agent", agent_name)
print(file=sys.stderr)
hint(f"Launching {shlex_join(cmd[:4])}...")

os.chdir(str(root))
os.execvp(cmd[0], cmd)
```

### 3d. `run_single_task` changes — lines 796–852

Currently prints `info(f"task {task_name} → agent {agent}")` and
`info(f"Launching agent {agent}...")`. Replace with semantic output:

```python
# Line 816 — replace info() with detail():
detail("agent", agent)

# Line 850 — replace info() with hint():
hint(f"Launching {shlex_join(cmd[:4])}...")
```

This integrates cleanly with the `step()` already printed by the
caller in the subtask loop.

---

## 4. `--quiet` and `--json` Threading

### 4a. `--quiet` flag

**Not yet defined** on the `run` subparser. Add it:

```python
# In argument parser (~line 1689):
run_p.add_argument("-q", "--quiet", action="store_true",
                   help="Suppress progress output (errors still shown)")
```

Thread it into `cmd_run`:

```python
# At top of cmd_run (~line 891):
global _quiet
_quiet = getattr(args, "quiet", False)
```

**Behavior**: suppresses all `info`/`header`/`step`/`detail`/`hint`
output. `failure()` and `err()` still print. `summary_block` still
prints on failure (useful for CI).

### 4b. `--json` flag

Already defined on the `run` subparser but only used with
`--dry-run`. Extend to live runs:

**Subtask loop**: when `json_output=True`, suppress all stderr
progress and emit a JSON summary to stdout at the end:

```python
if json_output:
    _quiet = True  # suppress stderr progress

# ... (subtask loop runs normally) ...

if json_output:
    result = {
        "task": task_name,
        "subtasks": task_results,  # list built during loop
        "completed": completed,
        "failed": failed_count,
        "remaining": remaining,
    }
    print(json.dumps(result, indent=2))
```

Build `task_results` list during the loop:

```python
task_results = []
# After each subtask:
task_results.append({
    "name": sub_name,
    "status": "done" if rc == EXIT_OK else "failed",
    "exit_code": rc,
    "duration_s": round(elapsed, 1),
})
```

**Single-task / by-agent paths**: `--json` has no meaningful
post-exec output (process is replaced). Keep current behavior
(only works with `--dry-run`). Document this limitation.

---

## 5. `execvp` vs `subprocess.run` Trade-off

### Current state

| Path | Uses | Reason |
|------|------|--------|
| Multi-task (subtask loop) | `subprocess.run` | Must iterate, collect exit codes |
| Single-task (no subtasks) | `os.execvp` | No post-exec work needed |
| By-agent | `os.execvp` | No post-exec work needed |

### Can we switch single-task to `subprocess.run`?

**Pros**:
- Could print post-execution summary (timing, exit code, ✓/✗)
- Consistent behavior across all paths
- Could capture/parse claude CLI JSON output

**Cons**:
- Extra process layer (minor overhead)
- Signal handling changes: with `execvp`, signals (SIGINT, SIGTERM)
  go directly to the claude process. With `subprocess.run`, the
  parent must forward signals or handle them
- PID changes: the claude process gets a child PID instead of
  replacing the parent — could affect process managers or shell
  job control
- `execvp` is simpler and idiomatic for "hand off to another tool"

### Recommendation

**Keep `execvp` for now.** The preamble improvements (§3b, §3c)
give users enough context before launch. Post-execution summary
only matters for the subtask loop, where `subprocess.run` is
already used.

If post-execution output becomes a requirement for single-task
mode later, switch to `subprocess.run` with a signal-forwarding
wrapper:

```python
import signal

def run_with_signals(cmd, cwd):
    """Run subprocess and forward SIGINT/SIGTERM."""
    proc = subprocess.Popen(cmd, cwd=cwd)
    def forward(sig, _frame):
        proc.send_signal(sig)
    old_int = signal.signal(signal.SIGINT, forward)
    old_term = signal.signal(signal.SIGTERM, forward)
    try:
        proc.wait()
    finally:
        signal.signal(signal.SIGINT, old_int)
        signal.signal(signal.SIGTERM, old_term)
    return proc.returncode
```

This is a Phase 2 enhancement, not needed for the initial
implementation.

---

## 6. Claude CLI JSON Output Handling

### The problem

`build_command` sets `--output-format json` for tier 2 (line 546).
The `claude` CLI dumps a raw JSON blob to stdout when it finishes.
In the subtask loop, `subprocess.run` does NOT capture this —
it goes directly to the parent's stdout.

### Current impact

- **Multi-task**: JSON blobs from each subtask interleave with
  any `--json` summary we add — stdout gets polluted
- **Single-task**: `execvp` replaces the process, so the JSON
  output goes directly to the terminal — expected behavior

### Options

| Approach | Effort | Trade-off |
|----------|--------|-----------|
| **A. Capture and discard** | Low | `subprocess.run(cmd, stdout=subprocess.DEVNULL)` — loses claude output entirely |
| **B. Capture and summarize** | Medium | `subprocess.run(cmd, capture_output=True)`, parse JSON, extract cost/turns/result |
| **C. Redirect to file** | Low | `subprocess.run(cmd, stdout=open(logfile, 'w'))` — preserves output for debugging |
| **D. Leave as-is** | None | Current behavior — user sees raw JSON scroll by |

### Recommendation

**Option C (redirect to file)** for the initial implementation:

```python
import tempfile

# In run_single_task, before subprocess.run:
log_dir = root / prefix / "artifacts" / "logs" if prefix else root / "artifacts" / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / f"{sub_name}.json"

with open(log_file, "w") as f:
    result = subprocess.run(cmd, cwd=str(root), stdout=f)
```

Then in the summary, print the log path:

```python
detail("log", str(log_file.relative_to(root)))
```

**Why not B (parse)?** Parsing the claude CLI JSON output couples
us to its schema, which is undocumented and may change. Better
to capture raw and let users inspect it.

**Alternative**: if log files are unwanted overhead, use Option A
(discard) and rely on the task's artifacts and status transitions
as the source of truth for what happened.

---

## 7. Test Impact

### Existing tests that need updates

| Test class | Test | Why |
|-----------|------|-----|
| `TestRunDryRun` | `test_no_subtasks_runs_parent` (line 885) | Asserts `"No subtasks found"` in stderr — text will change to use `header()` format |
| `TestRunSubtasks` | All tests checking stderr messages | `info:` prefix changes to semantic output (e.g., `[1/3]` instead of `info: [1/3]`) |
| `TestRunDryRunJson` | `test_by_task_dry_run_json` (line 1743) | May need update if `--json` behavior extends beyond `--dry-run` |

### New tests to add

| Test | Purpose |
|------|---------|
| `test_quiet_suppresses_progress` | `--quiet` suppresses `header`/`step`/`detail` but not `failure` |
| `test_json_output_summary` | `--json` (without `--dry-run`) emits JSON summary to stdout |
| `test_output_no_color` | Set `NO_COLOR=1`, verify no ANSI escapes in stderr |
| `test_format_duration` | Unit test: `format_duration(45)` → `"45s"`, `format_duration(125)` → `"2m 05s"` |
| `test_summary_block_resume_cmd` | Verify resume command appears when tasks remain |
| `test_header_format` | Verify `header()` produces `── text ──...` format |
| `test_step_format` | Verify `step(1, 3, "name")` produces `[1/3] name` |

### Test approach

All new output functions are pure (write to stderr, no side
effects). Test by capturing stderr in `run_cli()` — the test
harness already captures both stdout and stderr. No mocking
needed.

---

## 8. Feasibility Assessment

### Research recommendations that are fully feasible

| Recommendation | Feasibility | Notes |
|----------------|-------------|-------|
| Semantic output functions | ✅ Straightforward | Drop-in replacements for `info()` |
| `NO_COLOR` / TTY detection | ✅ Straightforward | 5-line function |
| Duration formatting | ✅ Straightforward | Pure function, easy to test |
| Resume command hint | ✅ Straightforward | Data already available in loop |
| Summary block | ✅ Straightforward | End of subtask loop |
| `--quiet` flag | ✅ Straightforward | New argparse flag + global |

### Recommendations that need adjustment

| Recommendation | Issue | Adjustment |
|----------------|-------|------------|
| `--json` for live runs | Only works on subtask-loop path; `execvp` paths can't emit post-run JSON | Document limitation: `--json` summary only available with subtask execution |
| Per-task timing in `step()` | Research shows `detail("Tier", ...)` — but tier is a run-level setting, not per-task | Show tier in the preamble header only, not per-task |
| Claude JSON output handling | Research proposes parsing it — too fragile | Redirect to file instead (§6) |

### Nothing impractical

All recommendations from task 0079 are implementable. The
adjustments above are scope refinements, not rejections.

---

## 9. Implementation Sequence

Recommended order (each step is independently mergeable):

1. **Add output helpers** — `_use_color`, color functions,
   `header`, `step`, `detail`, `success`, `failure`,
   `remaining_line`, `hint`, `format_duration`, `summary_block`.
   Gate `info()` on `_quiet`. Add `time` import.
   Add unit tests for `format_duration` and `_use_color`.

2. **Refactor subtask loop** — Replace `info()` calls with
   semantic output. Add timing. Add `summary_block`. Update
   affected tests.

3. **Add preambles** — Add `header`/`detail`/`hint` before
   `execvp` in `_exec_or_run` and by-agent path.

4. **Add `--quiet` flag** — Parser change + `_quiet` global.
   Add test.

5. **Extend `--json` for live runs** — JSON summary on subtask
   loop. Add test.

6. **Handle claude CLI output** — Redirect subprocess stdout
   to log file. Add `detail("log", ...)` line.

Steps 1–3 are the core UX improvement. Steps 4–6 are additive
enhancements that can be separate tasks if needed.
