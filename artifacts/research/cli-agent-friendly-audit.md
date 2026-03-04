# CLI Agent-Friendly Audit — `bin/openstation`

## Summary

The `openstation` CLI has solid foundations: meaningful exit codes,
stderr/stdout separation, `--dry-run` support, and no interactive
prompts. The biggest gaps are **no structured (JSON) output** and
**sparse `--help` text** — both critical for agent consumption. Below
is a per-rule assessment followed by a prioritized improvement list.

---

## Rule-by-Rule Assessment (Source 1)

### Rule 1: Structured Output

**Current state:** All output is plain text. `list` emits a formatted
table to stdout. `show` prints raw markdown. `run --dry-run` prints a
shell command string. Informational messages (`info()`) and errors
(`err()`) correctly go to stderr.

**Gap:** No `--json` flag on any subcommand. Agents must parse
human-formatted tables or raw markdown, which is fragile.

**Recommendation:**
- Add `--json` flag to `list` — emit a JSON array of task objects
  (keys: `id`, `name`, `status`, `agent`, `owner`, `bucket`).
- Add `--json` flag to `show` — emit the parsed frontmatter as a JSON
  object with an additional `body` field containing the markdown body.
- Make `run --dry-run --json` emit a JSON object
  (`{"command": [...], "task": "...", "agent": "..."}`).
- Keep current human-readable formats as the default (no `--json`).

**Rating:** Major gap

---

### Rule 2: Exit Codes

**Current state:** Six named exit codes defined as constants:

| Code | Constant          | Meaning                  |
|------|-------------------|--------------------------|
| 0    | EXIT_OK           | Success                  |
| 1    | EXIT_USAGE        | Bad arguments            |
| 2    | EXIT_NO_AGENT     | Agent spec not found     |
| 3    | EXIT_NO_CLAUDE    | claude CLI missing        |
| 4    | EXIT_AGENT_ERROR  | Agent execution failed   |
| 5    | EXIT_TASK_NOT_READY | Task not in ready state |

**Gap — minor inconsistencies:**
- `cmd_show` returns hard-coded `3` for "missing spec" and "cannot
  read" — collides semantically with `EXIT_NO_CLAUDE`.
- `resolve_task` returns `3` (not found) and `4` (ambiguous), using
  bare integers instead of named constants.
- No constant for "not in an Open Station project" (returns `2` in
  `main()`, collides with `EXIT_NO_AGENT`).
- Exit codes are not documented in `--help`.

**Recommendation:**
- Add `EXIT_NOT_FOUND` and `EXIT_AMBIGUOUS` constants, or renumber
  to avoid collisions — e.g., `0=ok, 1=usage, 2=not-found,
  3=conflict/ambiguous, 4=agent-error, 5=task-not-ready, 6=env-missing`.
- Use named constants everywhere (eliminate bare `return 3`).
- Add an exit code reference in `--help` epilog.

**Rating:** Minor gap (codes exist and are mostly distinct, but
collisions and lack of documentation reduce reliability)

---

### Rule 3: Idempotent Commands

**Current state:** The CLI has no write commands (no create, update,
delete). `list` and `show` are read-only (naturally idempotent). `run`
launches an external agent — it's not idempotent by nature, but
`--force` allows re-running regardless of status.

**Gap:** No gap for current scope. If write subcommands are added later
(e.g., `create`, `update`, `done`), idempotency should be designed in
from the start (e.g., `create --if-not-exists`, `done` returning 0 if
already done).

**Recommendation:** No action needed now. Add an "idempotency" note to
the design guidelines for future write commands.

**Rating:** No gap (read-only + run-agent is the expected scope)

---

### Rule 4: Self-Documenting

**Current state:** Uses Python `argparse` which auto-generates
`--help`. Current help strings are minimal:

```
list    — "List tasks"
show    — "Show a task spec"
run     — "Launch an agent"
```

Arguments have short help strings (e.g., `"Filter by status (default:
active, use 'all' for everything)"`). No usage examples. No exit code
documentation.

**Gap:** An agent reading `openstation run --help` would struggle to
understand the two modes (by-agent vs by-task), tier system, or what
`--force` skips. No examples demonstrate common workflows.

**Recommendation:**
- Add `epilog` text to each subparser with 2–3 concrete examples:
  ```
  Examples:
    openstation list --status ready --agent researcher
    openstation show 0040
    openstation run researcher
    openstation run --task 0040 --dry-run
    openstation run --task 0040 --tier 1
  ```
- Add a top-level epilog documenting exit codes.
- Document the two `run` modes (by-agent vs by-task) explicitly in the
  `run` subparser description.
- Expand `--status` help to list valid values: `"Filter by status
  (backlog|ready|in-progress|review|done|failed|active|all,
  default: active)"`.
- Use `argparse.RawDescriptionHelpFormatter` to preserve formatting.

**Rating:** Major gap

---

### Rule 5: Composability

**Current state:** No `--quiet` / `-q` flag. No stdin support. No
field selection (`--field`). Filtering is limited to `--status` and
`--agent` on `list`. No batch operations.

**Gap:** An agent that wants just task names (e.g., to pipe into
another command) must parse the table output. No way to select specific
fields or get bare values.

**Recommendation:**
- Add `--quiet` / `-q` to `list` — emit one task name per line (bare,
  no header). Useful for piping:
  `openstation list -q | xargs -I{} openstation show {}`.
- Field selection can be deferred — `--json` + `jq` covers this case.
- Stdin piping for batch operations is low priority given current
  subcommand set.

**Rating:** Moderate gap

---

### Rule 6: Dry-Run & Confirmation Bypass

**Current state:**
- `run --dry-run` prints the command that would be executed.
- `run --force` skips task status validation.
- No interactive prompts anywhere in the CLI — all operations
  proceed without confirmation.
- Non-TTY safe — no readline or input() calls.

**Gap:** `--dry-run` output is plain text (a shell command string).
With `--json` (once added), it should emit structured data.

**Recommendation:**
- When `--json` is added, make `--dry-run --json` emit:
  `{"command": [...], "task": "...", "agent": "...", "tier": 2}`.
- No other action needed — the CLI is already non-interactive.

**Rating:** Mostly good (minor: structured dry-run output)

---

### Rule 7: Actionable Errors

**Current state:** Errors go to stderr via `err()`. Messages
include some context:

```
error: Agent spec not found: researcher
error: Task 0040-foo has status 'in-progress' (expected 'ready')
error: ambiguous task '004', matches:
  0040-cli-agent-friendly-audit
  0041-something-else
```

**Gap:**
- No structured error output (no JSON error objects).
- No error type/code in the message (agent must regex-match to
  classify).
- No recovery suggestions (e.g., "run `openstation list --status
  ready` to see available tasks").
- Transient vs permanent errors are not distinguished.

**Recommendation:**
- Add recovery hints to the most common errors:

  | Error | Recovery hint |
  |-------|---------------|
  | task not found | `run 'openstation list --status all' to see available tasks` |
  | agent spec not found | `check agents/ directory for available agent specs` |
  | not in an Open Station project | `run from a directory containing .openstation/ or agents/ + install.sh` |
  | task not ready | `current status is '{status}'; use --force to override` |
  | no allowed-tools in agent spec | `add an 'allowed-tools:' list to the agent's frontmatter` |

- With `--json`, emit error objects to stdout:
  ```json
  {"error": "task_not_ready", "task": "0040-...",
   "current_status": "in-progress",
   "suggestion": "use --force to override or wait for task to be ready"}
  ```

**Rating:** Moderate gap

---

### Rule 8: Consistent Grammar

**Current state:** Three subcommands use a **verb** pattern:

```
openstation list
openstation show <task>
openstation run <agent>
openstation run --task <task>
```

This is a flat verb-based grammar, not a noun-verb hierarchy like
`openstation task list` / `openstation agent run`.

**Gap:** The current structure works well for a small CLI with 3
commands. A noun-verb refactor would improve discoverability as the
CLI grows but is a breaking change for minimal current benefit.

**Recommendation:**
- **No action now.** The verb pattern is internally consistent.
- Plan for noun-verb migration if the CLI grows beyond 5–6
  subcommands (e.g., adding `create`, `update`, `done`, `ready`,
  `agent list`).
- If migrating, keep verb aliases for backward compatibility.

**Rating:** Acceptable (consistent, albeit not noun-verb)

---

## Source 2: CLI-First Skill Design Patterns

Additional patterns from [CLI-First Skill Design](https://agentic-patterns.com/patterns/cli-first-skill-design/)
not already covered by the 8 rules above.

| Pattern | Status | Notes |
|---------|--------|-------|
| One script, one skill | Pass | Single `bin/openstation` executable |
| Subcommands for operations | Pass | `list`, `show`, `run` |
| Structured output (JSON) | Fail | No `--json` flag (same as Rule 1) |
| TTY auto-detection | Fail | No automatic format switching based on `isatty()` |
| Meaningful exit codes | Pass | 6 distinct codes defined |
| Environment-based config | Pass | No credentials needed; config-free by design |
| Non-interactive by default | Pass | No prompts or `input()` calls |
| Help text via `--help` | Partial | Exists but sparse (same as Rule 4) |
| Stderr for errors, stdout for data | Pass | `err()` → stderr, `info()` → stderr, data → stdout |
| Shebang for direct execution | Pass | `#!/usr/bin/env python3` |

**Additional recommendation from Source 2:**
- Add TTY auto-detection: when stdout is a TTY, emit the human-readable
  table; when piped, auto-switch to a simpler parseable format (or JSON).
  This eliminates the need for agents to remember `--json`.
  Implementation: `sys.stdout.isatty()`.

---

## Prioritized Improvements

### P0 — Critical for Agent Workflows

| # | Improvement | Effort | Rationale |
|---|-------------|--------|-----------|
| 1 | **Add `--json` to `list`** | Small | Agents parse `list` output constantly. Table parsing is fragile and the #1 blocker for reliable automation. |
| 2 | **Add `--json` to `show`** | Small | Agents need to read task metadata programmatically (status, agent, owner) without parsing YAML frontmatter themselves. |
| 3 | **Enrich `--help` with examples and mode descriptions** | Small | Agents use `--help` as their primary discovery mechanism. Current help is too terse for an agent to understand `run`'s two modes or `list`'s filter options. |

### P1 — Important for Reliability

| # | Improvement | Effort | Rationale |
|---|-------------|--------|-----------|
| 4 | **Fix exit code collisions** | Small | Exit codes 2 and 3 are overloaded across different error conditions. Agents making branching decisions on exit codes get wrong signals. |
| 5 | **Add recovery hints to common errors** | Small | Agents can self-recover if told what to try next. Currently errors state what failed but not what to do about it. |
| 6 | **Add `--quiet` / `-q` to `list`** | Small | Enables `openstation list -q --status ready \| xargs` pipelines, which agents use for chaining. |
| 7 | **Make `--dry-run` output structured with `--json`** | Small | When `--json` lands, extend it to dry-run for full structured preview. |

### P2 — Nice to Have / Future-Proofing

| # | Improvement | Effort | Rationale |
|---|-------------|--------|-----------|
| 8 | **TTY auto-detection for output format** | Small | Automatically use JSON when piped, table when interactive. Reduces flag burden for agents. |
| 9 | **Structured error objects with `--json`** | Medium | `{"error": "type", "message": "...", "suggestion": "..."}` enables programmatic error handling. |
| 10 | **Document exit codes in `--help`** | Small | Agents need to know what each code means without reading source. |
| 11 | **Noun-verb grammar migration plan** | N/A | Only needed if CLI grows past 5–6 subcommands. Not actionable now. |

---

## Methodology

- **CLI source:** `bin/openstation` (603 lines, Python 3, argparse)
- **Source 1:** [Writing CLI Tools That AI Agents Actually Want to Use](https://dev.to/uenyioha/writing-cli-tools-that-ai-agents-actually-want-to-use-39no) — 8 rules evaluated individually above
- **Source 2:** [CLI-First Skill Design](https://agentic-patterns.com/patterns/cli-first-skill-design/) — checklist evaluated in the Source 2 section
- **Assessment date:** 2026-03-04

## Tags

#cli #agent-friendly #audit #open-station #research
