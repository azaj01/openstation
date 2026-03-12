---
kind: research
name: worktree-integration-for-parallel-agents
agent: researcher
task: "[[0121-research-worktree-integration-for-parallel]]"
created: 2026-03-12
---

# Worktree Integration for Parallel Agent Sessions

Research into how git worktrees can enable parallel agent execution
in Open Station, evaluating built-in Claude support and external
orchestrators.

---

## 1. `claude --worktree` — How It Works

### Overview

Claude Code has built-in git worktree support via the `--worktree`
(`-w`) flag. Each agent session gets an isolated working directory
and branch — no file conflicts between parallel sessions.

### Mechanics

| Aspect | Detail |
|--------|--------|
| **Flag** | `claude --worktree [name]` or `claude -w [name]` |
| **Location** | `.claude/worktrees/{name}/` |
| **Branch** | `worktree-{name}` (auto-created from default remote branch) |
| **Auto-naming** | `claude --worktree` without a name — Claude picks one |
| **Mid-session** | Request "work in a worktree" during any session |

### Subagent Isolation

Custom agents can declare `isolation: worktree` in their
frontmatter. When the Agent tool is invoked with
`isolation: "worktree"`, each subagent gets its own worktree
automatically. This is the mechanism behind `/team-build` and
batched code migrations.

### Cleanup

- **No changes made** — worktree auto-removed on session end.
- **Changes exist** — Claude prompts to keep or remove.
- **Manual** — `git worktree list` + `git worktree prune`.

### Limitations

| Limitation | Impact |
|------------|--------|
| Branches from default remote only | Cannot base worktrees on arbitrary branches or commits |
| Worktrees inside `.claude/` | Nested under repo, not sibling directories — may confuse some tools |
| No built-in orchestration | Each `claude --worktree` is a standalone session; no multi-task coordination |
| No shared state across worktrees | Each session is independent — no awareness of what other sessions are doing |
| Interactive only | `--worktree` works with interactive sessions; combining with `-p` (print mode) is undocumented |

### Compatibility with `openstation run`

The `--worktree` flag works with `--agent` and interactive
(attached) mode. Confirmed compatible flags:

```bash
claude --worktree feature-a --agent researcher \
  --allowedTools Read Edit Bash Grep Glob \
  "Execute task 0042..."
```

The flag is also confirmed compatible in non-interactive (`-p`)
mode based on the attached-mode research (`--worktree` appears
in the "works in interactive mode" list).

---

## 2. Worktrunk (`wt`)

### Overview

Worktrunk is a purpose-built CLI for git worktree management,
specifically designed for running AI agents in parallel.

### Key Capabilities

| Feature | Detail |
|---------|--------|
| `wt switch -x claude` | Creates worktree and launches Claude with prompt |
| `wt list` | Shows all worktrees with status |
| `wt remove` | Cleans up worktree and branch |
| `wt merge` | Squash/rebase/merge workflow |
| `wt step` | Build cache sharing between worktrees |
| `wt hook` | Lifecycle hooks (create, pre-merge, post-merge) |
| LLM commit messages | Auto-generates commit messages from diffs |

### Integration Model

Worktrunk wraps `claude` invocation:

```bash
wt switch -x claude -c feature-a -- 'Add user authentication'
```

This creates a worktree named `feature-a`, switches to it, and
launches Claude with the prompt. The `-x` flag specifies the
command to run inside the worktree.

### Relevance to Open Station

| Aspect | Assessment |
|--------|------------|
| Worktree lifecycle | Strong — handles create, merge, cleanup |
| Agent orchestration | Minimal — launches one agent per worktree, no multi-task awareness |
| Task awareness | None — no concept of tasks, status, or assignment |
| Branch naming | Configurable templates, useful for convention enforcement |
| Merge workflow | Valuable — integrated squash/rebase/merge with cleanup |

### Pros

- Clean worktree lifecycle management (create → work → merge → cleanup)
- Build cache sharing avoids cold starts in new worktrees
- Hook system for project-specific setup
- Cross-platform (macOS, Linux, Windows)
- Lightweight, single binary (Rust)

### Cons

- No task awareness — cannot filter tasks by branch
- No orchestration — one agent per `wt switch` invocation
- Overlaps with `claude --worktree` for worktree creation
- Adds a dependency to an otherwise zero-dependency system
- Configuration is worktree-focused, not task-focused

---

## 3. Workmux

### Overview

Workmux is a workflow orchestrator combining git worktrees with
terminal multiplexers (tmux, kitty, WezTerm, Zellij). It provides
the most comprehensive agent integration of the three tools.

### Key Capabilities

| Feature | Detail |
|---------|--------|
| `workmux add <branch>` | Creates worktree + tmux window with configured pane layout |
| `workmux merge` | Merges branch, deletes worktree, cleans up |
| `workmux dashboard` | TUI for monitoring active agents |
| Pane orchestration | Custom tmux layouts (editor, shell, agent) per worktree |
| Agent auto-detection | Recognizes claude, gemini, codex; injects prompts correctly |
| Status tracking | Agent status icons in tmux window names (working/waiting/done) |
| File operations | Copy/symlink `.env`, `node_modules` into new worktrees |
| Lifecycle hooks | `post_create`, `pre_merge`, `pre_remove` |
| Sandbox support | Container/VM isolation for agents |
| PR integration | `workmux add --pr 123` checks out a GitHub PR |

### Integration Model

Workmux deeply integrates with AI agents:

```bash
# Create worktree with Claude agent and prompt
workmux add feature-auth -p "implement user authentication"

# Multi-agent: different agents for different worktrees
workmux add feature-auth -a claude -p "implement auth"
workmux add feature-tests -a claude -p "write test suite"
```

Configuration (`.workmux.yaml`):

```yaml
agent: claude
panes:
  - command: <agent>
    focus: true
  - command: "npm run dev"
    split: horizontal
files:
  copy: [.env]
  symlink: [node_modules]
```

### Relevance to Open Station

| Aspect | Assessment |
|--------|------------|
| Worktree lifecycle | Strong — full create/merge/cleanup |
| Agent orchestration | Strong — multi-agent, pane layouts, status tracking |
| Task awareness | None — no task concept, but prompt injection could bridge |
| Terminal integration | Excellent — tmux/kitty/wezterm/zellij support |
| Dashboard | Useful for monitoring parallel agents |
| Merge workflow | Complete — squash/rebase/merge options |

### Pros

- Most feature-rich orchestrator of the three
- Dashboard for monitoring multiple parallel agents
- Agent status tracking (working/waiting/done)
- Multi-agent support with different agents per worktree
- File operations (copy/symlink) for project setup
- PR checkout integration
- Sandbox/container support for isolation
- Active development with broad community adoption

### Cons

- Requires tmux (or alternative multiplexer) as a dependency
- Heavy for Open Station's zero-dependency philosophy
- Configuration complexity for simple use cases
- No task awareness — all orchestration is worktree-centric
- Terminal-centric — doesn't map to `openstation run`'s
  subprocess model

---

## 4. Comparison Matrix

| Criterion | `claude --worktree` | Worktrunk | Workmux |
|-----------|-------------------|-----------|---------|
| **Worktree creation** | Built-in | Built-in | Built-in |
| **Branch management** | Auto (`worktree-{name}`) | Configurable | Configurable |
| **Cleanup** | Auto on session end | Manual (`wt remove`) | Manual (`workmux merge/remove`) |
| **Agent launching** | Native (`--agent`) | Via `-x claude` | Native (auto-detect) |
| **Multi-agent** | Subagent isolation only | No orchestration | Full orchestration |
| **Task awareness** | None | None | None |
| **Terminal multiplexer** | No | No | Required (tmux, etc.) |
| **Dashboard** | No | No | Yes (TUI) |
| **Merge workflow** | Manual (git) | Integrated | Integrated |
| **Build cache** | No | Yes (`wt step`) | Via symlink/copy |
| **Dependencies** | None (built-in) | Single binary | Binary + tmux |
| **Complexity** | Low | Medium | High |
| **Open Station fit** | High | Medium | Low-Medium |

### Approach Categories

1. **Built-in (`claude --worktree`)** — Zero-dependency, minimal
   friction, but no orchestration. Best for "one agent, one task"
   parallelism where each session is launched independently.

2. **External orchestrator (worktrunk/workmux)** — Rich lifecycle
   management but no task awareness. Would need a bridge layer to
   connect to Open Station's task model.

3. **Custom integration** — Open Station's `openstation run` adds
   `--worktree` flag, creates worktrees, and manages the full
   lifecycle with task awareness built in. Most aligned with the
   project's conventions but requires implementation effort.

---

## 5. Integration with `openstation run`

### Current State

Open Station already has significant worktree groundwork:

- **Task 0107** (in-progress): Parent task for git worktree support
- **Task 0092** (failed): `find_root()` worktree resolution —
  resolving `.openstation/` from linked worktrees
- **Task 0094** (done): Branch-based task scoping spec — `branch`
  frontmatter field, `--branch` CLI flag
- **Task 0109**: Implement branch-based task scoping (pending)

The branch-based task scoping spec (0094) already designs the
filtering model: tasks can have a `branch` field, and
`--branch auto` detects the current branch from git.

### Proposed Integration: `openstation run --worktree`

Add a `--worktree` flag to `openstation run` that:

1. **Creates a git worktree** for the task's branch
2. **Passes `--worktree`** to the `claude` CLI command
3. **Scopes tasks** via `--branch auto` so the agent only sees
   relevant tasks

#### Flow: Single Task

```bash
openstation run --task 0042 --worktree
```

1. Read task 0042's `branch` field (e.g., `feature/auth`)
2. If no branch set, create one: `worktree-0042-slug`
3. Create git worktree at `.claude/worktrees/0042-slug/`
   (or use `claude --worktree` to let Claude handle it)
4. Launch: `claude --worktree 0042-slug --agent researcher ...`
5. Agent runs in isolated worktree, picks up branch-scoped tasks

#### Flow: Parallel Agents

```bash
# Terminal 1
openstation run --task 0042 --worktree --attached

# Terminal 2
openstation run --task 0043 --worktree --attached
```

Each agent gets its own worktree and branch. Task scoping
ensures agent 1 only sees tasks for branch A, agent 2 only
sees tasks for branch B.

#### Implementation Options

| Option | Mechanism | Complexity | Task Awareness |
|--------|-----------|------------|----------------|
| **A: Pass-through** | Add `--worktree` to `build_command`, let Claude handle isolation | Low | Relies on `--branch auto` filtering |
| **B: Pre-create** | `openstation run` creates the worktree via `git worktree add`, then runs Claude inside it | Medium | Full control over branch naming and worktree location |
| **C: Delegate to worktrunk/workmux** | Shell out to `wt` or `workmux` for lifecycle | Medium | Bridge layer needed |

**Recommendation: Option A (pass-through) first, Option B later.**

Option A is minimal:

```python
# In build_command():
if worktree:
    cmd.extend(["--worktree", worktree_name])
```

This leverages Claude's built-in worktree support with zero new
dependencies. Option B adds control over branch naming and
worktree placement but requires managing worktree lifecycle
(creation, cleanup, error handling).

#### Detached Mode Consideration

In detached mode (`subprocess.Popen`), `--worktree` creates the
worktree before the session starts and cleans up after. The
`_stream_and_capture` pipeline works unchanged — it still reads
stdout from the subprocess regardless of which worktree the
subprocess operates in.

In attached mode (`os.execvp`), `--worktree` works natively
since it's a Claude CLI flag.

---

## 6. Open Questions and Design Decisions

### Q1: Should `openstation run` create worktrees or delegate to Claude?

**Context:** Claude's `--worktree` creates worktrees in
`.claude/worktrees/`. Open Station could alternatively create them
with `git worktree add` in a custom location.

**Trade-off:**
- Delegating to Claude: zero implementation, but branch names
  follow Claude's `worktree-{name}` convention, not task-aligned.
- Creating ourselves: full control over naming (`task-0042-slug`)
  and location, but must handle cleanup.

**Recommendation:** Delegate to Claude initially (Option A).
Revisit if naming/location control becomes important.

### Q2: How should branch names map to tasks?

**Options:**
- `worktree-{task-id}` (e.g., `worktree-0042`)
- `task/{task-id}-{slug}` (e.g., `task/0042-add-auth`)
- User-specified (existing `branch` field in task frontmatter)

**Recommendation:** Use the task's `branch` field if set.
If unset, auto-generate `task/{id}-{slug}` and write it back
to the task frontmatter. This connects worktrees to the
branch-scoping system from spec 0094.

### Q3: Should parallel execution be sequential or concurrent?

**Context:** Currently `openstation run --task <parent>` runs
subtasks sequentially. With worktrees, subtasks could run
concurrently in separate worktrees.

**Trade-off:**
- Sequential: simple, current model, one agent at a time.
- Concurrent: true parallelism, but requires process management
  (multiple `subprocess.Popen`), aggregated logging, and
  handling partial failures.

**Recommendation:** Sequential first (current model, each in its
own worktree). Concurrent execution is a separate feature that
adds significant complexity (process pool, log multiplexing,
failure handling, resource budgeting).

### Q4: What happens to worktrees after task completion?

**Options:**
- Auto-remove on task `done` (clean, but loses branch history)
- Keep until explicit cleanup (`openstation worktree prune`)
- Keep until merged to main

**Recommendation:** Let Claude's auto-cleanup handle it (removes
if no changes, prompts if changes exist). For detached mode,
add a `--cleanup` flag that removes the worktree after the
session ends.

### Q5: How does `.openstation/` resolution work in worktrees?

**Status:** Task 0092 (failed) attempted this. The design is
sound — use `git rev-parse --git-common-dir` to find the main
worktree root and resolve `.openstation/` from there.

**Blocker:** This must be re-implemented before worktree
integration works. Without it, agents in worktrees can't find
the task vault.

### Q6: Should workmux/worktrunk be supported as alternatives?

**Recommendation:** Not as dependencies. Both are external tools
that add complexity without task awareness. However, they can
coexist:

- Worktrunk users can use `wt switch -x "openstation run ..."` to
  manage worktree lifecycle externally.
- Workmux users can configure `openstation run` as the agent
  command in `.workmux.yaml`.

Open Station should document these patterns without depending
on either tool.

### Q7: What about the `isolation: worktree` Agent tool parameter?

**Context:** Claude's Agent tool supports `isolation: "worktree"`
for subagent isolation. This is used during `/team-build` and
batched migrations.

**Relevance:** Open Station agents (researcher, developer, etc.)
are launched via `--agent`, not via the Agent tool. The
`isolation: worktree` parameter is for in-session subagent
dispatch, not top-level agent launch. However, if an Open Station
agent spawns subagents during execution, those subagents can use
worktree isolation internally.

---

## Summary

| Finding | Detail |
|---------|--------|
| `claude --worktree` | Built-in, zero-dependency, creates isolated worktrees per session. Works with `--agent` and both attached/detached modes. |
| Worktrunk | Clean worktree lifecycle manager. Best as an external complement, not a dependency. |
| Workmux | Feature-rich orchestrator with dashboard and multi-agent support. Too heavy as a dependency; useful as optional tooling. |
| Best integration path | Pass `--worktree` through to Claude CLI (Option A), combined with branch-based task scoping (spec 0094). |
| Prerequisites | `find_root()` worktree resolution (task 0092) must be re-implemented first. |
| Parallel execution | Sequential-in-worktrees first; concurrent execution is a separate, more complex feature. |
