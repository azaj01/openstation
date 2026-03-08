---
kind: research
name: run-command-ux-patterns
agent: researcher
task: "[[0079-research-cli-run-command-ux]]"
created: 2026-03-08
---

# CLI Run Command UX Patterns

Research into how well-known CLIs communicate progress, separate
visual sections, and handle partial failure — with concrete
recommendations for `openstation run`.

---

## 1. Progress Patterns

How CLIs communicate multi-step progress to users.

### 1a. CLIs Surveyed

| CLI | Pattern | Example |
|-----|---------|---------|
| **cargo** | Verb prefix + target | `Compiling mylib v0.1.0` → `Finished dev [unoptimized] in 2.34s` |
| **docker** (BuildKit) | Numbered steps `#N` | `#1 [internal] load build definition` / `#1 DONE 0.1s` |
| **docker** (classic) | `Step X/Y` | `Step 3/7 : RUN apt-get install` |
| **terraform** | Resource-level status + timer | `aws_instance.web: Creating...` → `Creation complete after 13s [id=i-abc]` |
| **npm** | Summary-only (default) | `added 127 packages in 4s` |
| **gh** | Minimal — single action line | `Creating pull request for feature-branch into main...` → `https://github.com/...` |

### 1b. Common Patterns

**Verb prefix (cargo style)**
```
   Compiling  openstation v0.4.0
   Compiling  serde v1.0.152
    Finished  dev [unoptimized] in 2.34s
```
- Green bold verb, right-aligned to a fixed column
- Tense shifts: gerund (`Compiling`) → past participle (`Finished`)
- No step numbers — the verb carries semantic weight

**Step N/Total (docker classic style)**
```
Step 1/7 : FROM python:3.12
Step 2/7 : WORKDIR /app
Step 3/7 : COPY requirements.txt .
```
- Explicit denominator gives users a mental model of total work
- Easy to estimate "am I halfway done?"

**Resource-level status (terraform style)**
```
aws_instance.web: Creating...
aws_instance.web: Still creating... [10s elapsed]
aws_instance.web: Creation complete after 13s [id=i-abc123]

Apply complete! Resources: 3 added, 0 changed, 0 destroyed.
```
- Per-resource status lines with elapsed time
- "Still creating..." heartbeat prevents silence anxiety
- Final summary block with counts

**Summary-only (npm style)**
```
added 127 packages, and audited 128 packages in 4s
23 packages are looking for funding
  run `npm fund` for details
found 0 vulnerabilities
```
- Minimal during execution (progress bar in TTY only)
- Summary at end with actionable next-step hints

### 1c. Key Takeaways

1. **Show something within 100ms** — silence feels broken (clig.dev).
2. **Tense matters** — use gerund for in-progress (`Resolving...`),
   past for done (`Resolved`). Logs should reflect completed state.
3. **Step N/Total** works well when the total is known and small
   (our subtask case).
4. **Verb prefix** works well for heterogeneous steps where a
   number would be misleading.
5. **Summary block** at the end is near-universal.

---

## 2. Readability Patterns

How CLIs visually separate sections in multi-step operations.

### 2a. Techniques

| Technique | Used by | Example |
|-----------|---------|---------|
| **Bold/colored verb prefix** | cargo, terraform | `Compiling`, `Creating...` in green |
| **Indentation for sub-steps** | docker BuildKit | Main step at col 0, transfer details indented |
| **Blank line separators** | terraform, npm | Blank line between plan and apply phases |
| **Section headers** | npm audit, gh | `# npm audit report` |
| **Visual checkmarks/crosses** | many modern CLIs | `✓ All checks passed`, `✗ Build failed` |
| **Color coding by severity** | terraform, cargo | Green = add/success, Yellow = change/warning, Red = destroy/error |
| **Right-aligned timing** | cargo, terraform | Duration aligned to right margin |

### 2b. Anti-patterns

- **Uniform density** — walls of identically-formatted lines
  (early cargo output of `Compiling` × 200 crates).
- **No phase separation** — jumping from resolution to execution
  to summary without visual breaks.
- **Color overload** — when everything is colored, nothing stands
  out (clig.dev: "if everything is a different color, the color
  means nothing").

### 2c. Key Takeaways

1. **Two levels of hierarchy** is usually enough: phase headers
   + individual step lines.
2. **Use symbols sparingly** — a checkmark (✓) for success and
   a cross (✗) for failure is the sweet spot.
3. **Place the most important information last** — users' eyes
   naturally settle at the bottom of output (clig.dev).

---

## 3. Resumability Patterns

How CLIs handle partial failure in multi-step operations.

### 3a. Patterns Observed

| Pattern | Used by | Description |
|---------|---------|-------------|
| **State file** | terraform | Writes `terraform.tfstate` after each resource; re-run resumes from divergent state |
| **Lockfile checkpoint** | npm, cargo | `package-lock.json` / `Cargo.lock` persists resolved state |
| **Explicit resume command** | AWS Step Functions | `redrive` restarts from the last failed state |
| **"Re-run to continue"** | openstation (current) | Prints remaining count + hint to re-run |
| **Idempotent operations** | docker build | Layer cache makes re-runs skip completed steps |
| **Summary with remaining work** | terraform | `Plan: 3 to add, 0 to change, 0 to destroy` |

### 3b. What Works for Multi-Task CLI Runners

For a CLI that runs N tasks sequentially (our case):

1. **Print a copy-pasteable resume command** — not just "re-run",
   but the exact command string the user can paste.
2. **Show completed vs remaining** — `3/5 completed, 2 remaining`.
3. **Name the next task** — so the user knows what failed and
   what's next.
4. **Skip completed tasks on re-run** — tasks that reached
   `review` or `done` are naturally skipped because they're no
   longer `ready`.

### 3c. Key Takeaways

1. Our status-based model (`ready` → `in-progress` → `review`)
   already provides natural idempotency — completed tasks won't
   be re-picked.
2. The gap is **actionable output**: current message says
   "Re-run to continue" but doesn't show the command.
3. Naming the failed task + the next pending task gives users
   enough context to decide whether to re-run or investigate.

---

## 4. Our Constraints

### 4a. Execution Modes

| Mode | Mechanism | Post-exec control |
|------|-----------|-------------------|
| **Single task** (by-task, no subtasks) | `os.execvp` — replaces process | None — can't print after exec |
| **Single agent** (by-agent) | `os.execvp` — replaces process | None |
| **Multi-task** (by-task, with subtasks) | `subprocess.run` in loop | Full control — can print between tasks |

**Implication**: Progress output improvements mainly benefit the
multi-task (subtask loop) path. The single-task/agent path can
only improve the *preamble* (before `execvp` fires).

### 4b. Output Channels

```python
def info(msg):
    print(f"info: {msg}", file=sys.stderr)

def err(msg):
    print(f"error: {msg}", file=sys.stderr)
```

- All human-readable output goes to **stderr** (correct per
  clig.dev: actions/status to stderr, data to stdout).
- `--json` mode prints structured JSON to **stdout** — must
  not be polluted by progress messages.
- `--quiet` should suppress info-level messages.

### 4c. Current Output (Multi-Task Path)

```
info: Task collection: 0078-improve-run-command
info: Found 3 ready subtask(s)
info: [1/3] Executing subtask: 0079-research-cli-run-command-ux
info: task 0079-research-cli-run-command-ux → agent researcher
info: Launching agent researcher for task 0079-research-cli-run-command-ux...
  [... agent runs via subprocess.run ...]
info: [2/3] Executing subtask: 0080-implement-run-output-formatting
  [...]
info: Summary: 2 completed, 1 remaining of 3 subtask(s)
info: Task limit reached (3). Re-run to continue.
```

**Problems identified**:
1. Every line has the same `info:` prefix — no visual hierarchy
2. Resolution steps (agent lookup, tool parsing) are silent —
   then suddenly an agent launches
3. The resume hint says "Re-run to continue" but doesn't give
   the command
4. No visual separation between task executions
5. No success/failure indicators (✓/✗)
6. No timing information

---

## 5. Recommendations

### 5a. Progress Output — Proposed Format

Replace `info:` prefix with semantic prefixes and visual hierarchy.

**Multi-task output (subtask loop):**

```
── openstation run --task 0078-improve-run-command ──

  Task collection: 0078-improve-run-command
  Found 3 ready subtasks

[1/3] 0079-research-cli-run-command-ux
      agent: researcher
      Launching...
      ✓ Done (exit 0, 4m 32s)

[2/3] 0080-implement-run-output-formatting
      agent: developer
      Launching...
      ✗ Failed (exit 1, 2m 15s)

── Summary ──────────────────────────────────
  ✓ 1 completed
  ✗ 1 failed
  · 1 remaining

  Next: 0081-add-resume-instructions

  To continue:
    openstation run --task 0078-improve-run-command
```

**Single-task preamble (before execvp):**

```
── openstation run --task 0079-research-cli-run-command-ux ──

  Task:  0079-research-cli-run-command-ux
  Agent: researcher
  Tier:  2 (autonomous)

  Launching claude --agent researcher ...
```

### 5b. Helper Functions

Replace `info()` with a small output module:

```python
import sys
import time

# Color helpers (disabled when NO_COLOR set or not a TTY)
def _use_color():
    return sys.stderr.isatty() and not os.environ.get("NO_COLOR")

def _green(s):  return f"\033[32m{s}\033[0m" if _use_color() else s
def _red(s):    return f"\033[31m{s}\033[0m" if _use_color() else s
def _bold(s):   return f"\033[1m{s}\033[0m" if _use_color() else s
def _dim(s):    return f"\033[2m{s}\033[0m" if _use_color() else s

def header(text):
    """Print a section header line."""
    width = 48
    line = f"── {text} " + "─" * max(0, width - len(text) - 4)
    print(_bold(line), file=sys.stderr)

def step(n, total, name):
    """Print a step indicator: [1/3] task-name."""
    print(f"\n{_bold(f'[{n}/{total}]')} {name}", file=sys.stderr)

def detail(label, value):
    """Print an indented detail line."""
    print(f"      {_dim(label + ':')} {value}", file=sys.stderr)

def success(msg):
    """Print a success line with checkmark."""
    print(f"      {_green('✓')} {msg}", file=sys.stderr)

def failure(msg):
    """Print a failure line with cross."""
    print(f"      {_red('✗')} {msg}", file=sys.stderr)

def remaining(msg):
    """Print a remaining/pending line."""
    print(f"      · {msg}", file=sys.stderr)

def hint(msg):
    """Print a dim hint line."""
    print(f"  {_dim(msg)}", file=sys.stderr)

def summary_block(completed, failed, pending, resume_cmd=None, next_task=None):
    """Print the end-of-run summary."""
    header("Summary")
    if completed: success(f"{completed} completed")
    if failed:    failure(f"{failed} failed")
    if pending:   remaining(f"{pending} remaining")
    if next_task:
        print(f"\n  Next: {next_task}", file=sys.stderr)
    if resume_cmd:
        print(f"\n  To continue:", file=sys.stderr)
        print(f"    {resume_cmd}", file=sys.stderr)
```

### 5c. Integration Points in `cmd_run`

**Multi-task loop** (lines 915–936):

```python
# Before loop
header(f"openstation run --task {task_name}")
print(f"\n  Task collection: {task_name}", file=sys.stderr)
print(f"  Found {len(subtasks)} ready subtasks\n", file=sys.stderr)

# Per-task
step(i + 1, len(subtasks), sub_name)
detail("agent", agent)
start = time.time()
# ... subprocess.run ...
elapsed = time.time() - start
if rc == EXIT_OK:
    success(f"Done (exit 0, {format_duration(elapsed)})")
else:
    failure(f"Failed (exit {rc}, {format_duration(elapsed)})")

# After loop
summary_block(
    completed=completed,
    failed=1 if rc != EXIT_OK else 0,
    pending=remaining_count,
    resume_cmd=f"openstation run --task {task_name}",
    next_task=next_sub_name if remaining_count > 0 else None,
)
```

**Single-task preamble** (in `_exec_or_run`, before `os.execvp`):

```python
header(f"openstation run --task {task_name}")
detail("Task", task_name)
detail("Agent", agent)
detail("Tier", f"{tier} ({'autonomous' if tier == 2 else 'interactive'})")
print(file=sys.stderr)
hint(f"Launching {shlex_join(cmd[:4])}...")
```

### 5d. `--quiet` and `--json` Behavior

| Flag | Effect |
|------|--------|
| `--quiet` | Suppress all `info`/`header`/`step`/`detail`/`hint` output. Only print `err()` and `summary_block` on failure. |
| `--json` | Print structured JSON to stdout (already works). Suppress all stderr progress output. Summary as JSON object. |
| Neither | Full human-readable output to stderr (proposed format above). |

Implementation: wrap output functions with a global `_quiet` flag:

```python
_quiet = False

def info(msg):
    if not _quiet:
        print(f"  {msg}", file=sys.stderr)
```

For `--json` mode, suppress stderr entirely and emit a JSON
summary at the end of the subtask loop:

```json
{
  "task": "0078-improve-run-command",
  "subtasks": [
    {"name": "0079-research-cli-run-command-ux", "status": "done", "exit_code": 0, "duration_s": 272},
    {"name": "0080-implement-run-output-formatting", "status": "failed", "exit_code": 1, "duration_s": 135}
  ],
  "completed": 1,
  "failed": 1,
  "remaining": 1
}
```

### 5e. Duration Formatting Helper

```python
def format_duration(seconds):
    """Format seconds into human-readable duration."""
    if seconds < 60:
        return f"{seconds:.0f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"
```

### 5f. `NO_COLOR` and TTY Detection

Respect the [no-color.org](https://no-color.org) convention:

```python
def _use_color():
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("TERM") == "dumb":
        return False
    return sys.stderr.isatty()
```

---

## 6. Summary of Recommendations

| Problem | Recommendation | Effort |
|---------|---------------|--------|
| No visual hierarchy | Replace `info:` with semantic output functions (header, step, detail, success, failure) | Medium |
| Silent middle steps | Add `detail()` lines for agent resolution, tool parsing | Low |
| No resume instructions | Print copy-pasteable `openstation run --task ...` command + name the next pending task | Low |
| No timing | Add `time.time()` around `subprocess.run`, print elapsed in success/failure lines | Low |
| No color/symbols | Add `_green()`, `_red()`, `_bold()` helpers with `NO_COLOR` / TTY detection | Low |
| `--quiet` has no effect on new output | Wrap output functions with `_quiet` global | Low |
| `--json` summary missing | Emit JSON summary object at end of subtask loop | Medium |

---

## Sources

- [clig.dev — Command Line Interface Guidelines](https://clig.dev/)
- [Evil Martians — CLI UX Best Practices: 3 Patterns for Progress Displays](https://evilmartians.com/chronicles/cli-ux-best-practices-3-patterns-for-improving-progress-displays)
- [Heroku CLI Style Guide](https://devcenter.heroku.com/articles/cli-style-guide)
- [GitHub Blog — Scripting with GitHub CLI](https://github.blog/engineering/engineering-principles/scripting-with-github-cli/)
- [no-color.org](https://no-color.org)
- [npm Logging Documentation](https://docs.npmjs.com/cli/v11/using-npm/logging/)
- [Cargo Build — The Cargo Book](https://doc.rust-lang.org/cargo/commands/cargo-build.html)
- [Docker BuildKit Documentation](https://docs.docker.com/build/buildkit/)
- [Terraform Apply Command Reference](https://developer.hashicorp.com/terraform/cli/commands/apply)
