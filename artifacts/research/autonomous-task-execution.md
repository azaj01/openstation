---
kind: research
name: autonomous-task-execution
task: 0013-autonomous-task-execution
created: 2026-02-27
---
c
# Autonomous Task Execution

Research into enabling Open Station agents to run autonomously
(without interactive prompts) and in detached/background sessions,
with appropriate guardrails.

---

## Executive Summary

Open Station agents currently run via `claude --agent <name>`,
which launches an interactive session requiring a human to approve
permission prompts. For agents executing well-scoped tasks —
writing research docs, authoring specs — this interaction overhead
is unnecessary and prevents batch or background execution.

Claude Code already provides all the primitives needed for
autonomous execution. The `-p` (print) flag enables non-interactive
mode, `--allowedTools` provides fine-grained tool approval with
glob patterns, `--max-budget-usd` caps costs, and hooks
(`PreToolUse`, `PostToolUse`) enable guardrail enforcement. No
upstream changes or feature requests are required.

This document proposes a **three-tier execution model**: (1)
semi-autonomous with user watching, (2) fully autonomous with
pre-configured permissions, and (3) detached background execution
with post-hoc review. Each tier increases autonomy while
maintaining safety through progressively stricter guardrails.

---

## Claude Code Autonomous Capabilities

Ground-truth reference of CLI flags relevant to autonomous
execution, verified against official documentation (Feb 2026).

### Core Flags

| Flag | Behavior |
|------|----------|
| `-p` / `--print` | Non-interactive mode. Runs query, prints response, exits. |
| `--agent <name>` | Load an agent spec for the session. |
| `--allowedTools "..."` | Fine-grained tool allowlist with glob patterns. Tools listed here execute without permission prompts. |
| `--disallowedTools "..."` | Tools removed from context entirely — cannot be used. |
| `--tools "..."` | Restrict which built-in tools are available. |
| `--permission-mode <mode>` | `default` \| `acceptEdits` \| `plan` \| `dontAsk` \| `bypassPermissions` |
| `--dangerously-skip-permissions` | Bypass all permission checks. Requires trusted environment. |
| `--max-budget-usd <n>` | Cost cap in dollars. Print mode only. |
| `--max-turns <n>` | Limit agentic turns. Print mode only. Exits with error when reached. |
| `--output-format <fmt>` | `text` \| `json` \| `stream-json`. JSON enables machine parsing. |

### Session Persistence

| Flag | Behavior |
|------|----------|
| `--resume <id>` / `-r` | Resume a specific session by ID or name. |
| `--continue` / `-c` | Resume the most recent session in the current directory. |
| `--session-id <uuid>` | Use a specific session UUID. |
| `--no-session-persistence` | Disable session persistence (print mode only). |

### Isolation

| Flag | Behavior |
|------|----------|
| `--worktree` / `-w` | Start in an isolated git worktree at `.claude/worktrees/<name>`. |
| `--teammate-mode <mode>` | Controls agent team display: `auto` \| `in-process` \| `tmux`. Not a standalone detached mode. |

### Hooks (Guardrail Enforcement)

Claude Code hooks run at lifecycle events and can enforce
guardrails programmatically.

| Hook Event | Timing | Can Block? | Use for Guardrails |
|------------|--------|------------|-------------------|
| `PreToolUse` | Before tool execution | Yes (`"deny"`) | Block writes outside allowed paths, block destructive commands |
| `PostToolUse` | After successful execution | Yes (`"block"`) | Validate outputs, enforce invariants |
| `Stop` | When Claude finishes | Yes (`"block"`) | Prevent premature completion |
| `SessionStart` | Session begins | No | Initialize logging, validate environment |
| `SessionEnd` | Session terminates | No | Send notifications, archive logs |

Hook types: `command` (shell), `http` (webhook), `prompt` (LLM),
`agent` (sub-agent). Command hooks support `async: true` for
non-blocking execution.

**PreToolUse guardrail example** (`.claude/settings.json`):

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tools": ["Write", "Edit"] },
        "hooks": [
          {
            "type": "command",
            "command": "python3 scripts/check-write-path.py \"$TOOL_INPUT\""
          }
        ]
      }
    ]
  }
}
```

The hook script exits 0 with `{"permissionDecision": "allow"}` to
permit or `{"permissionDecision": "deny", "reason": "..."}` to
block.

### Confirmed Absent

| Feature | Status |
|---------|--------|
| `--detached` | Does not exist. No built-in background/daemon mode. |
| `--tmux` (standalone) | Does not exist. Only `--teammate-mode tmux` for agent teams. |

---

## Three Execution Tiers

### Tier 1: Semi-Autonomous

**Use case:** Developer watches the terminal but doesn't want to
approve every file write.

```bash
claude --agent researcher --permission-mode acceptEdits
```

| Aspect | Detail |
|--------|--------|
| Mode | Interactive with reduced prompts |
| Risk | Low — user is watching |
| Control | `acceptEdits` auto-approves file changes; Bash/network still prompt |
| Best for | First-time runs, complex tasks, unfamiliar agents |

### Tier 2: Fully Autonomous

**Use case:** Pre-configured agent runs a scoped task to
completion without any prompts.

```bash
claude -p \
  "Execute your ready tasks" \
  --agent researcher \
  --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch" \
                 "Write" "Edit" "Bash(ls *)" "Bash(readlink *)" \
  --max-budget-usd 5 \
  --max-turns 50 \
  --output-format json
```

| Aspect | Detail |
|--------|--------|
| Mode | Non-interactive (`-p`) |
| Risk | Medium — no human in loop |
| Control | Explicit tool allowlist, budget cap, turn limit |
| Best for | Well-defined tasks with known tool requirements |

### Tier 3: Detached / Background

**Use case:** Agent runs in the background while developer works
on other things. Results reviewed after completion.

```bash
# Option A: nohup + log redirect
nohup claude -p \
  "Execute your ready tasks" \
  --agent researcher \
  --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch" \
                 "Write" "Edit" "Bash(ls *)" "Bash(readlink *)" \
  --max-budget-usd 5 \
  --max-turns 50 \
  --output-format json \
  > .openstation/logs/researcher-$(date +%Y%m%d-%H%M%S).json 2>&1 &

# Option B: tmux session
tmux new-session -d -s os-researcher \
  "claude -p 'Execute your ready tasks' \
   --agent researcher \
   --allowedTools 'Read' 'Glob' 'Grep' 'WebSearch' 'WebFetch' \
                  'Write' 'Edit' 'Bash(ls *)' 'Bash(readlink *)' \
   --max-budget-usd 5 \
   --max-turns 50 \
   --output-format json \
   | tee .openstation/logs/researcher-\$(date +%Y%m%d-%H%M%S).json"
```

| Aspect | Detail |
|--------|--------|
| Mode | Background process |
| Risk | Medium-High — no real-time oversight |
| Control | Same as Tier 2 + OS-level process management |
| Best for | Long-running tasks, batch execution, CI pipelines |

**Note on worktrees:** `--worktree` provides git-level isolation
but is **not recommended** for Open Station internal tasks. Open
Station uses relative symlinks (`../../artifacts/tasks/...`) that
break when the working directory changes to a worktree path.
Worktrees are appropriate for code-producing tasks in other
projects.

---

## Task Discovery in Autonomous Mode

No changes are needed. The existing `openstation-execute` skill
handles task discovery identically in interactive and `-p` modes:

1. Agent reads its own spec to determine its name.
2. Scans `tasks/current/` for symlinked task folders.
3. Reads each `index.md`, filtering for `agent: <self>` and
   `status: ready`.
4. Picks the earliest `created` date if multiple tasks match.
5. Sets `status: in-progress` and begins work.

The skill's logic is prompt-based (encoded in the agent's system
prompt via the `skills` field), not dependent on interactive I/O.
It works without modification in `-p` mode.

---

## Guardrails and Permission Tiers

### Per-Agent `--allowedTools` Recipes

Each agent has a known set of tools it needs. Pre-approving only
those tools provides least-privilege access.

#### Researcher

```bash
--allowedTools \
  "Read" "Glob" "Grep" \
  "WebSearch" "WebFetch" \
  "Write" "Edit" \
  "Bash(ls *)" "Bash(readlink *)"
```

Rationale: Needs web access for research, file read/write for
artifacts. No git, no arbitrary shell commands.

#### Author

```bash
--allowedTools \
  "Read" "Glob" "Grep" \
  "Write" "Edit" \
  "Bash(ls *)" "Bash(readlink *)" \
  "Bash(ln *)" "Bash(mkdir *)"
```

Rationale: Needs symlink and directory creation for task
management. No web access (vault-only constraint). No git.

#### Architect

```bash
--allowedTools \
  "Read" "Glob" "Grep" \
  "Write" "Edit" \
  "Bash(ls *)" "Bash(readlink *)"
```

Rationale: Similar to author but doesn't create symlinks or
directories (produces specs only). No web access.

#### Project Manager

```bash
--allowedTools \
  "Read" "Glob" "Grep" \
  "Write" "Edit" \
  "Bash(ls *)" "Bash(readlink *)" \
  "Bash(ln *)" "Bash(mkdir *)" "Bash(rm *)"
```

Rationale: Needs full task lifecycle operations including
symlink management.

### Hook-Based Guardrails

For stronger enforcement, hooks can validate tool inputs at
runtime, independent of `--allowedTools`:

**Path restriction** — Block writes outside `artifacts/` and
`tasks/`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tools": ["Write", "Edit"] },
        "hooks": [
          {
            "type": "command",
            "command": "python3 .openstation/hooks/validate-write-path.py"
          }
        ]
      }
    ]
  }
}
```

**Destructive git prevention** — Block `push --force`,
`reset --hard`, `checkout .`, etc.:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tools": ["Bash"] },
        "hooks": [
          {
            "type": "command",
            "command": "python3 .openstation/hooks/block-destructive-git.py"
          }
        ]
      }
    ]
  }
}
```

**Notification on completion** — Send a webhook or desktop
notification when an agent finishes:

```json
{
  "hooks": {
    "Stop": [
      {
        "type": "command",
        "command": "osascript -e 'display notification \"Agent finished\" with title \"Open Station\"'",
        "async": true
      }
    ]
  }
}
```

### Permission Mode Selection Guide

| Scenario | Recommended Mode |
|----------|-----------------|
| First run of a new agent | `--permission-mode default` (interactive) |
| Trusted agent, user watching | `--permission-mode acceptEdits` |
| Autonomous with allowlist | `-p` + `--allowedTools "..."` |
| Autonomous, fully trusted | `-p` + `--dangerously-skip-permissions` |
| CI/CD pipeline | `-p` + `--allowedTools "..."` + `--max-budget-usd` |

---

## Detached / Background Execution

Claude Code has no built-in `--detached` flag. Background
execution must be achieved through OS-level process management.

### Approach 1: nohup + Log Redirect (Simplest)

```bash
nohup claude -p "Execute your ready tasks" \
  --agent researcher \
  --allowedTools "Read" "Glob" "Grep" "WebSearch" "WebFetch" \
                 "Write" "Edit" "Bash(ls *)" "Bash(readlink *)" \
  --max-budget-usd 5 \
  --max-turns 50 \
  --output-format json \
  > .openstation/logs/researcher-$(date +%Y%m%d-%H%M%S).json 2>&1 &
```

**Pros:** Zero dependencies, works everywhere.
**Cons:** No way to interact mid-run. Must check logs manually.

### Approach 2: tmux Session

```bash
tmux new-session -d -s os-researcher "claude -p ..."
```

**Pros:** Can attach to watch progress (`tmux attach -t os-researcher`). Multiple agents in parallel via tmux windows.
**Cons:** Requires tmux. Still no built-in notification.

### Approach 3: Launcher Script

A convenience wrapper that standardizes invocation:

```bash
#!/bin/bash
# openstation-run.sh — Launch an agent autonomously
set -euo pipefail

AGENT="${1:?Usage: openstation-run.sh <agent> [--background]}"
BACKGROUND="${2:-}"
LOGDIR=".openstation/logs"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
LOGFILE="${LOGDIR}/${AGENT}-${TIMESTAMP}.json"

mkdir -p "$LOGDIR"

# Per-agent tool recipes
case "$AGENT" in
  researcher)
    TOOLS='"Read" "Glob" "Grep" "WebSearch" "WebFetch" "Write" "Edit" "Bash(ls *)" "Bash(readlink *)"'
    ;;
  author)
    TOOLS='"Read" "Glob" "Grep" "Write" "Edit" "Bash(ls *)" "Bash(readlink *)" "Bash(ln *)" "Bash(mkdir *)"'
    ;;
  architect)
    TOOLS='"Read" "Glob" "Grep" "Write" "Edit" "Bash(ls *)" "Bash(readlink *)"'
    ;;
  project-manager)
    TOOLS='"Read" "Glob" "Grep" "Write" "Edit" "Bash(ls *)" "Bash(readlink *)" "Bash(ln *)" "Bash(mkdir *)" "Bash(rm *)"'
    ;;
  *)
    echo "Unknown agent: $AGENT" >&2
    exit 1
    ;;
esac

CMD="claude -p 'Execute your ready tasks' \
  --agent $AGENT \
  --allowedTools $TOOLS \
  --max-budget-usd 5 \
  --max-turns 50 \
  --output-format json"

if [ "$BACKGROUND" = "--background" ]; then
  echo "Launching $AGENT in background..."
  echo "Log: $LOGFILE"
  eval nohup $CMD > "$LOGFILE" 2>&1 &
  echo "PID: $!"
else
  echo "Launching $AGENT (foreground)..."
  eval $CMD | tee "$LOGFILE"
fi
```

### Parallel Agent Execution

Multiple agents can run simultaneously since they operate on
different task files. Each agent filters for `agent: <self>` in
task frontmatter, so there is no contention.

```bash
# Launch researcher and author in parallel
./openstation-run.sh researcher --background
./openstation-run.sh author --background
```

**Caveat:** If two agents modify the same file (e.g., both try to
update `CLAUDE.md`), conflicts will occur. This is prevented by
the task assignment model — each task has exactly one `agent`
field.

---

## Monitoring and Review Workflow

### Log Directory Convention

```
.openstation/logs/
  researcher-20260227-143022.json
  author-20260227-143510.json
```

JSON output (`--output-format json`) includes structured data
about each tool call, its result, and the final response.

### Checking on a Running Agent

```bash
# If using tmux
tmux attach -t os-researcher

# If using nohup, tail the log
tail -f .openstation/logs/researcher-20260227-143022.json

# Check if process is still running
ps aux | grep "claude.*--agent researcher"
```

### Reviewing Results

After an autonomous run completes:

1. **Check task status:** The agent should have set
   `status: review` in the task's `index.md`.
2. **Review artifacts:** Check `artifacts/research/` (or
   appropriate category) for outputs.
3. **Read the log:** Parse the JSON output for any errors or
   unexpected behavior.
4. **Verify and close:** Use `/openstation.done <task-name>` to
   run verification and archive the task.

### Session Resumption

If an agent hits `--max-turns` or `--max-budget-usd` before
finishing:

```bash
# Resume the session to continue work
claude --resume <session-id> -p "Continue your work" \
  --agent researcher \
  --allowedTools "..." \
  --max-budget-usd 5
```

The `--session-id` or `--resume` flag restores the full
conversation context.

### Hook-Based Notifications

For proactive monitoring, configure a `Stop` or `SessionEnd` hook
to send notifications:

```json
{
  "hooks": {
    "SessionEnd": [
      {
        "type": "command",
        "command": "python3 .openstation/hooks/notify-completion.py",
        "async": true
      }
    ]
  }
}
```

The notification script can send a macOS notification, Slack
message, or email based on the session outcome.

---

## Lifecycle Integration

Autonomous execution requires **no changes** to the existing task
lifecycle. The status machine, ownership model, and artifact
storage conventions remain identical:

| Lifecycle Aspect | Autonomous Impact |
|-----------------|-------------------|
| Status transitions | Unchanged. Agent sets `ready → in-progress → review`. |
| Ownership | Unchanged. `owner` field controls who verifies. |
| Artifact storage | Unchanged. Agents write to `artifacts/<category>/`. |
| Task discovery | Unchanged. Skill scans `tasks/current/` for matching agent + status. |
| Verification | Unchanged. Human runs `/openstation.done` after review. |
| Self-verification ban | Unchanged. Agents cannot transition `review → done`. |

The key insight is that the `openstation-execute` skill is
prompt-based — it encodes the lifecycle rules into the agent's
system prompt. Whether the agent runs interactively or via `-p`,
the same rules apply. The skill does not depend on interactive
I/O or permission prompts for lifecycle compliance.

---

## Recommendations

### Implement Now

1. **Document the three tiers** in a brief operational guide
   (this research document serves as the foundation).
2. **Add `--allowedTools` recipes to agent specs** — either in the
   agent frontmatter or as a companion `tools.sh` file per agent.
3. **Create the `openstation-run.sh` launcher script** for
   convenient autonomous invocation.
4. **Establish the `.openstation/logs/` convention** for storing
   run output.

### Implement Soon

5. **Add hook-based guardrails** — `PreToolUse` hooks for path
   validation and destructive-command blocking. Start with a
   simple Python script that checks write paths against an
   allowlist.
6. **Extend `/openstation.dispatch`** to support an `--autonomous`
   flag that generates the correct `claude -p ...` invocation for
   a given agent.
7. **Add `Stop` hook for notifications** — macOS notification or
   Slack webhook when an agent completes.

### Defer

8. **Agent Teams** — Claude Code's multi-agent orchestration
   (`--teammate-mode`) could enable complex workflows where
   multiple agents collaborate. Requires more maturity in the
   upstream feature.
9. **Agent SDK Integration** — Anthropic's Agent SDK provides
   programmatic agent orchestration. Could replace shell-level
   automation for complex pipelines.
10. **Per-task permission fields** — Adding a `permissions` field
    to task frontmatter to specify per-task tool allowlists.
    Useful but adds complexity to the spec.

---

## Sources

- [Claude Code CLI Reference](https://code.claude.com/docs/en/cli-reference.md)
- [Claude Code Hooks](https://code.claude.com/docs/en/hooks.md)
- [Claude Code Permissions](https://code.claude.com/docs/en/permissions.md)
- [Claude Code Agent Teams](https://code.claude.com/docs/en/agent-teams.md)
- Open Station `docs/lifecycle.md` — task lifecycle rules
- Open Station `skills/openstation-execute/SKILL.md` — agent execution skill
- Open Station agent specs: `artifacts/agents/researcher.md`, `author.md`, `architect.md`
