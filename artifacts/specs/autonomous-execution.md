---
kind: spec
name: autonomous-execution
task: 0019-autonomous-execution-spec
created: 2026-03-01
---

# Autonomous Task Execution

Enable Open Station agents to execute tasks with reduced or zero
interactive prompts, while guardrails prevent destructive actions.

**Research:** `artifacts/research/autonomous-task-execution.md`

## Problem

Running an agent today requires a human to sit at the terminal
and approve every tool call. This limits throughput — agents can
only work when a human is watching. We need a way to launch
agents that run to completion on their own, with safety
constraints that make unsupervised execution acceptable.

## Scope

**In scope:** Tier 1 (semi-autonomous) and Tier 2 (fully
autonomous) foreground execution.

**Out of scope:** Tier 3 (detached/background via nohup/tmux),
`.openstation/logs/` convention, notification hooks,
`/openstation.dispatch` autonomous mode, per-task permission
fields.

---

## Execution Tiers

### Tier 1 — Semi-Autonomous

Human watches the terminal. Permission prompts are reduced
(auto-accept edits) but the session is interactive. The user
can interrupt at any time.

| Property | Value |
|----------|-------|
| Mode | Interactive (`claude --agent`) |
| Permission | `--permission-mode acceptEdits` |
| Budget / turns | Not enforced (human is watching) |
| Use case | First-time runs, sensitive tasks |

### Tier 2 — Fully Autonomous

No human present. Agent runs in print mode with explicit tool
allowlists, budget caps, and turn limits.

| Property | Value |
|----------|-------|
| Mode | Print (`claude -p`) |
| Permission | `--allowedTools` per agent (see § Tool Recipes) |
| Budget | `--max-budget-usd` (default: $5) |
| Turns | `--max-turns` (default: 50) |
| Output | `--output-format json` |
| Use case | Batch runs, CI, overnight work |

### What Doesn't Change

- Task discovery: the `openstation-execute` skill works
  identically in both tiers.
- Lifecycle: status transitions, ownership, artifact storage,
  and the self-verification ban apply unchanged.
- Agent identity: the `--agent` flag loads the same agent spec
  regardless of tier.

---

## Architecture

### Runtime Flow

```
User
 │
 │  openstation-run.sh researcher --tier 2
 │
 ▼
┌──────────────────────────────────────────────┐
│  Launcher (C1)                               │
│                                              │
│  1. Read agents/researcher.md                │
│  2. Parse allowed-tools from frontmatter(C4) │
│  3. Build claude -p invocation               │
│  4. exec (replaces shell process)            │
└──────────────┬───────────────────────────────┘
               │
               ▼
┌──────────────────────────────────────────────┐
│  Claude Code                                 │
│                                              │
│  --agent researcher                          │
│  --allowedTools Read Glob Grep ...           │
│  --max-budget-usd 5                          │
│  --max-turns 50                              │
│                                              │
│  ┌────────────────────────────┐              │
│  │  openstation-execute skill │              │
│  │  (discovers ready tasks,   │              │
│  │   follows lifecycle)       │              │
│  └────────────┬───────────────┘              │
│               │                              │
│               │ tool call                    │
│               ▼                              │
│  ┌────────────────────────────┐              │
│  │  PreToolUse hooks          │              │
│  │                            │              │
│  │  Write/Edit ──► C2         │              │
│  │  (path validation)         │              │
│  │                            │              │
│  │  Bash ──► C3               │              │
│  │  (destructive-git block)   │              │
│  └────────────┬───────────────┘              │
│               │ allow / deny                 │
│               ▼                              │
│  Tool executes (or blocked with reason)      │
└──────────────────────────────────────────────┘
```

### Layer Separation

Three independent safety layers constrain what an autonomous
agent can do. Each layer is enforced by a different mechanism
and none depend on the others:

| Layer | Mechanism | What it constrains | Enforced by |
|-------|-----------|-------------------|-------------|
| **Tool allowlist** | `--allowedTools` flag | Which tools the agent can invoke at all | Claude Code CLI |
| **Write-path hook** | PreToolUse hook (C2) | Which files Write/Edit can target | Hook script |
| **Git safety hook** | PreToolUse hook (C3) | Which Bash commands are permitted | Hook script |

An agent must pass **all three** layers for a tool call to
succeed. For example, the `author` agent's allowlist permits
`Write`, but the write-path hook further restricts it to vault
directories only.

### Data Flow

The launcher is the only new entry point. Everything downstream
uses existing Claude Code primitives:

```
openstation-run.sh          ← new (C1)
  └─ reads: agents/*.md     ← modified (C4: allowed-tools field)
  └─ execs: claude CLI      ← existing

.claude/settings.json       ← modified (C5: hook entries)
  └─ triggers: hooks/*.sh   ← new (C2, C3)

install.sh                  ← modified (C5: deploys hooks + launcher)
```

### Invariants

- The launcher never runs in the background — one process, one
  terminal, foreground only.
- Hooks are stateless — each invocation reads stdin, writes
  stdout, no side effects.
- The `openstation-execute` skill is unchanged — agents discover
  and execute tasks identically in interactive and autonomous
  modes.
- No new runtime dependencies. The only prerequisite is `claude`
  on `$PATH`.

---

## Components

| # | Component | Location | Purpose |
|---|-----------|----------|---------|
| C1 | Launcher script | `openstation-run.sh` | Constructs the `claude` invocation for a given agent + tier |
| C2 | Write-path hook | `hooks/validate-write-path.sh` | Blocks writes outside the vault directory set |
| C3 | Destructive-git hook | `hooks/block-destructive-git.sh` | Blocks destructive git commands |
| C4 | Agent tool recipes | `artifacts/agents/*.md` | Per-agent `allowed-tools` in frontmatter |
| C5 | Install script update | `install.sh` | Deploys hooks, launcher, and hook config |

---

## C1: Launcher Script

**File:** `openstation-run.sh` (repo root); installed at
`.openstation/openstation-run.sh`.

### CLI Contract

```
openstation-run.sh <agent-name> [OPTIONS]

Options:
  --tier 1|2    Execution tier (default: 2)
  --budget N    Max spend in USD (default: 5)
  --turns N     Max agentic turns (default: 50)
  --dry-run     Print the command without executing
  --help        Show usage

Exit codes:
  0   Success
  1   Usage error (bad args, missing allowed-tools)
  2   Agent spec not found
  3   Claude CLI not found
  4   Agent exited with error
```

### Behavior

1. Validate `claude` is on `$PATH` and agent spec exists.
2. Read `allowed-tools` from agent frontmatter — fail if absent.
3. Build the `claude` command for the requested tier.
4. `exec` the command (replaces the shell process for clean
   signal propagation).

### Constraints

- Pure bash, zero external dependencies beyond `claude`.
- No `eval` — argument array only.
- Foreground only — no `nohup`, `&`, `tmux`.
- Must work from any working directory within the project.

---

## Hook Wire Format

Both hooks (C2, C3) implement the Claude Code `PreToolUse` hook
protocol. This is the interface contract they must conform to.

**Input** (JSON on stdin from Claude Code):

```json
{
  "tool_name": "Write",
  "tool_input": { "file_path": "/absolute/path", "content": "..." }
}
```

For Bash: `tool_input` has a `command` field instead of
`file_path`.

**Output** (JSON on stdout):

```json
{"permissionDecision": "allow"}
```

```json
{"permissionDecision": "deny", "reason": "Human-readable reason"}
```

**Exit code:** Always 0. The decision is in the JSON, not the
exit code.

---

## C2: Write-Path Validation Hook

**File:** `hooks/validate-write-path.sh`; installed at
`.openstation/hooks/validate-write-path.sh`.

**Hook type:** `PreToolUse`, matcher `Write|Edit`.

### Contract

- **Trigger:** `Write` and `Edit` tool calls.
- **Allow** if `file_path` resolves to a path under any of:
  `artifacts/`, `tasks/`, `agents/`, `docs/`, `skills/`,
  `commands/`, `hooks/`, or `CLAUDE.md` (relative to project
  root). In installed projects, the same set under
  `.openstation/`.
- **Deny** otherwise, with a reason identifying the blocked path.
- **Ignore** all other tools (pass through as allow).

### Constraints

- Prefer `jq` for JSON parsing; fall back to `grep`/`sed` if
  unavailable (zero-dependency guarantee).
- Handle both absolute and relative `file_path` values.
- Always exit 0 (hook protocol — decision is in JSON output).

---

## C3: Destructive-Git Blocking Hook

**File:** `hooks/block-destructive-git.sh`; installed at
`.openstation/hooks/block-destructive-git.sh`.

**Hook type:** `PreToolUse`, matcher `Bash`.

### Contract

- **Trigger:** `Bash` tool calls.
- **Deny** if `command` matches any blocked pattern (below).
- **Allow** otherwise.

### Blocked Patterns

| Pattern | Reason |
|---------|--------|
| `git push --force` / `git push -f` | Destroys remote history |
| `git reset --hard` | Destroys local changes |
| `git checkout .` / `git checkout -- .` | Discards all changes |
| `git restore .` | Discards all changes |
| `git clean -f` | Deletes untracked files |
| `git branch -D` | Force-deletes branches |
| `rm -rf .git` | Destroys repository |

**Not blocked:** `git rebase`. Rebase is not inherently
destructive — only force-push after rebase is, and force-push
is already blocked.

### Constraints

Same as C2: prefer `jq`, fall back gracefully, always exit 0.

---

## C4: Agent Tool Recipes

**Files:** `artifacts/agents/*.md` (each agent spec).

Add an `allowed-tools` YAML field to each agent's frontmatter.
This is the source of truth the launcher (C1) reads to construct
`--allowedTools` arguments for Tier 2 execution.

### Field Format

```yaml
allowed-tools:
  - ToolName
  - "Bash(pattern *)"    # glob patterns must be YAML-quoted
```

### Per-Agent Recipes

| Agent | Tools | Rationale |
|-------|-------|-----------|
| **researcher** | Read, Glob, Grep, WebSearch, WebFetch, Write, Edit, `Bash(ls *)`, `Bash(readlink *)` | Needs web access for research; no git, no arbitrary shell |
| **author** | Read, Glob, Grep, Write, Edit, `Bash(ls *)`, `Bash(readlink *)`, `Bash(ln *)`, `Bash(mkdir *)` | Needs symlink/dir creation for task management; no web, no git |
| **architect** | Read, Glob, Grep, Write, Edit, `Bash(ls *)`, `Bash(readlink *)` | Specs only — no symlinks, no web |
| **developer** | Read, Glob, Grep, Write, Edit, `Bash(bun *)`, `Bash(npx *)`, `Bash(ls *)`, `Bash(readlink *)`, `Bash(mkdir *)`, `Bash(chmod *)` | Needs build/test tooling; no git, no web, no symlink management |
| **project-manager** | Read, Glob, Grep, Write, Edit, `Bash(ls *)`, `Bash(readlink *)`, `Bash(ln *)`, `Bash(mkdir *)`, `Bash(mv *)`, `Bash(rm *)` | Full lifecycle operations including archival |

### Placement

The `allowed-tools` field goes after `skills` in frontmatter.

---

## C5: Install Script Update

**File:** `install.sh`

### New Responsibilities

1. Deploy `hooks/*.sh` to `.openstation/hooks/`, mark executable.
2. Deploy `openstation-run.sh` to `.openstation/`, mark
   executable.
3. Create or merge hook configuration into
   `.claude/settings.json`:

   ```json
   {
     "hooks": {
       "PreToolUse": [
         {
           "matcher": "Write|Edit",
           "type": "command",
           "command": "bash .openstation/hooks/validate-write-path.sh"
         },
         {
           "matcher": "Bash",
           "type": "command",
           "command": "bash .openstation/hooks/block-destructive-git.sh"
         }
       ]
     }
   }
   ```

### Settings Merge Constraint

If `.claude/settings.json` already exists, the installer must
merge the `hooks` key without overwriting other settings. The
installer writes to the project-level file (`.claude/settings.json`,
checked into git). Users can override in
`.claude/settings.local.json`.

**Note:** Hooks apply globally — every session, not just
autonomous ones. This is intentional: the blocked operations are
rarely legitimate in any Open Station workflow. Users who need
a blocked operation temporarily edit settings.

---

## Build Sequence

```
C4 (agent tool recipes)
 │
 ├──► C1 (launcher) ──► C5 (install)
 │
 C2 (write-path hook) ──► C5
 │
 C3 (git hook) ─────────► C5
```

C4 first (C1 depends on the `allowed-tools` field).
C2 and C3 are independent of C4 and can be parallel.
C5 last — it deploys everything else.

---

## Verification

| Component | Criterion |
|-----------|-----------|
| C1 | `--dry-run` prints the correct `claude` invocation for each tier |
| C1 | Unknown agent exits with code 2 |
| C1 | Missing `allowed-tools` exits with code 1 |
| C2 | Pipe JSON with path outside vault → deny |
| C2 | Pipe JSON with `artifacts/...` path → allow |
| C2 | Non-Write/Edit tools → allow (pass-through) |
| C3 | `git push --force` → deny |
| C3 | `git status` → allow |
| C3 | Non-Bash tools → allow (pass-through) |
| C4 | Each agent spec has valid `allowed-tools` in frontmatter |
| C5 | `install.sh` deploys hooks and launcher to `.openstation/` |
| C5 | `.claude/settings.json` contains hook entries after install |

---

## Design Decisions

### DD-1: Zero external dependencies

Hooks prefer `jq` but fall back to string extraction.
**Trade-off:** Regex JSON parsing is fragile, but Claude Code's
hook protocol produces predictable single-line fields.

### DD-2: Tool recipes in frontmatter, not companion files

Single source of truth — agent identity and permissions in one
file. **Trade-off:** YAML quoting for glob patterns is awkward
but the lists are small.

### DD-3: Global hooks, not per-session

Guardrails apply to all sessions. **Trade-off:** Users must edit
settings to force-push. This is a feature — it forces deliberate
action.

### DD-4: `exec` not subshell

Launcher replaces itself with `claude` for clean signal
propagation. **Trade-off:** No post-exec cleanup, but there's
nothing to clean up in foreground mode.

### DD-5: `git rebase` not blocked

Only force-push is destructive; rebase itself is safe when
force-push is blocked.
