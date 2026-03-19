---
kind: research
name: worktree-integration
agent: researcher
task: "[[0123-research-worktree-integration]]"
created: 2026-03-13
---

# Worktree Integration

Living research artifact for the worktree integration epic (0122).
Consolidates findings from task 0121 and tracks new investigation
as the feature evolves.

---

## 1. `claude --worktree` — Mechanics and Behavior

### 1.1 Core Usage

| Aspect | Detail |
|--------|--------|
| **Flag** | `claude --worktree [name]` or `claude -w [name]` |
| **Location** | `<repo>/.claude/worktrees/<name>/` |
| **Branch** | `worktree-<name>` (branched from default remote branch) |
| **Auto-naming** | Omit name → Claude generates a random one (e.g. `bright-running-fox`) |
| **Mid-session** | Ask "work in a worktree" during any session |
| **Platforms** | CLI, Desktop app, IDE extensions, web, mobile |

### 1.2 Subagent Isolation

Custom agents can declare `isolation: worktree` in their
frontmatter. When the Agent tool is invoked with
`isolation: "worktree"`, each subagent gets its own worktree
automatically. This powers `/team-build` and batched code
migrations.

**Key distinction:** Open Station agents are launched via
`claude --agent`, not via the in-session Agent tool. The
`isolation: worktree` parameter is for in-session subagent
dispatch. However, if an Open Station agent spawns subagents
during execution, those subagents *can* use worktree isolation
internally.

### 1.3 Cleanup Behavior

| Condition | Behavior |
|-----------|----------|
| No changes made | Worktree and branch auto-removed on session end |
| Changes or commits exist | Claude prompts to keep or remove |
| Manual cleanup | `git worktree list` + `git worktree remove` |

**Tip:** Add `.claude/worktrees/` to `.gitignore` to prevent
worktree contents appearing as untracked files.

### 1.4 Limitations

| Limitation | Impact on Open Station |
|------------|----------------------|
| Branches from default remote only | Cannot base worktrees on arbitrary branches — workaround: create worktrees manually with `git worktree add` |
| Worktrees inside `.claude/worktrees/` | Nested under repo, not sibling directories — some tools may have issues |
| No built-in orchestration | Each session is independent — no multi-task coordination |
| No shared state across worktrees | No awareness of what other sessions are doing |
| No task awareness | `--worktree` knows nothing about Open Station tasks or status |
| Branch naming is fixed | `worktree-<name>` format, not customizable — doesn't match task-based naming conventions |

### 1.5 `--tmux` Flag

Claude Code also supports `--tmux` to launch sessions in their
own tmux session. This can be combined with `--worktree` for
fully detached parallel sessions:

```bash
claude --worktree feature-a --tmux
claude --worktree bugfix-123 --tmux
```

### 1.6 Non-Git Version Control

Claude supports `WorktreeCreate` and `WorktreeRemove` hooks for
custom worktree logic with non-git VCS. Not relevant for Open
Station (git-only).

### 1.7 Agent Teams

Claude Code docs reference "agent teams" for automated
coordination of parallel sessions with shared tasks and
messaging. This is a distinct feature from `--worktree` and
may overlap with Open Station's multi-agent orchestration goals.
**Status: needs further investigation.**

---

## 2. External Tools

### 2.1 Worktrunk (`wt`)

**Repository:** [github.com/max-sixty/worktrunk](https://github.com/max-sixty/worktrunk)
**License:** Apache 2.0
**Install:** `brew install worktrunk` / `cargo install worktrunk`
**Binary:** Single Rust binary, cross-platform (macOS, Linux, Windows)

#### Capabilities

| Feature | Detail |
|---------|--------|
| `wt switch -c -x claude feat` | Create worktree + launch Claude |
| `wt list` | Status overview with change indicators |
| `wt remove` | Single-command cleanup |
| `wt merge` | Squash/rebase/merge with cleanup |
| `wt step` | Build cache sharing across worktrees |
| `wt hook` | Lifecycle hooks (create, pre-merge, post-merge) |
| LLM commits | Auto-generate commit messages from diffs |

#### Integration Model

Worktrunk wraps `claude` invocation:

```bash
wt switch -x claude -c feature-a -- 'Add user authentication'
```

Creates a worktree, switches to it, and launches Claude with
the prompt.

#### Relevance to Open Station

| Aspect | Assessment |
|--------|------------|
| Worktree lifecycle | **Strong** — handles create, merge, cleanup |
| Agent orchestration | **Minimal** — one agent per worktree |
| Task awareness | **None** |
| Branch naming | Configurable templates |
| Merge workflow | Valuable — integrated squash/rebase/merge |
| Build cache | Useful for `node_modules`/`target/` sharing |
| **Dependency cost** | Single binary, low impact |

#### Coexistence Pattern

```bash
# Use worktrunk for worktree lifecycle, openstation for task dispatch
wt switch -x "openstation run --task 0042 --attached" -c task-0042
```

### 2.2 Workmux

**Repository:** [github.com/raine/workmux](https://github.com/raine/workmux)
**Install:** `brew install raine/workmux/workmux` / `cargo install workmux`
**Dependency:** Requires tmux (or Kitty/WezTerm/Zellij)

#### Capabilities

| Feature | Detail |
|---------|--------|
| `workmux add <branch>` | Creates worktree + tmux window |
| `workmux merge` | Merge, delete worktree, close window |
| `workmux dashboard` | TUI for monitoring active agents |
| Pane orchestration | Custom tmux layouts per worktree |
| Agent detection | Auto-detects Claude, Gemini, Codex, Kiro-CLI, Vibe |
| Status tracking | Agent status icons (working 🤖, waiting 💬, done ✅) |
| File operations | Copy/symlink `.env`, `node_modules` into worktrees |
| Lifecycle hooks | `post_create`, `pre_merge`, `pre_remove` |
| Sandbox mode | Container/VM isolation for agents |
| PR integration | `workmux add --pr 123` checks out a GitHub PR |
| Prompt sources | Inline (`-p`), file (`-P`), editor (`-e`), LLM-named (`-A`) |
| Change transfer | `--with-changes`, `--patch` move uncommitted work |
| Environment vars | `WM_HANDLE`, `WM_WORKTREE_PATH`, `WM_PROJECT_ROOT` |

#### Configuration

Two-level hierarchy: global (`~/.config/workmux/config.yaml`)
and project (`.workmux.yaml`). Key options:

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

#### Relevance to Open Station

| Aspect | Assessment |
|--------|------------|
| Worktree lifecycle | **Strong** — full create/merge/cleanup |
| Agent orchestration | **Strong** — multi-agent, pane layouts, status tracking |
| Task awareness | **None** — but prompt injection and env vars could bridge |
| Terminal integration | **Excellent** — tmux/kitty/wezterm/zellij |
| Dashboard | **Useful** for monitoring parallel agents |
| **Dependency cost** | Binary + tmux — heavier than worktrunk |
| **Complexity** | Significant configuration surface area |

#### Coexistence Pattern

```yaml
# .workmux.yaml — use openstation as the agent command
panes:
  - command: "openstation run --task <task-id> --attached"
    focus: true
```

Or with env vars for dynamic task assignment:

```bash
workmux add task-0042 -p "Execute task 0042"
```

---

## 3. Structured Comparison

| Criterion | `claude --worktree` | Worktrunk | Workmux |
|-----------|-------------------|-----------|---------|
| **Worktree creation** | Built-in | Built-in | Built-in |
| **Branch management** | Auto (`worktree-{name}`) | Configurable templates | Configurable |
| **Cleanup** | Auto on session end | Manual (`wt remove`) | Manual (`workmux merge`) |
| **Agent launching** | Native (`--agent`) | Via `-x claude` | Native (auto-detect) |
| **Multi-agent** | Subagent isolation only | No orchestration | Full orchestration |
| **Task awareness** | None | None | None |
| **Terminal multiplexer** | Optional (`--tmux`) | No | Required |
| **Dashboard** | No | No | Yes (TUI) |
| **Merge workflow** | Manual (git) | Integrated | Integrated |
| **Build cache** | No | Yes (`wt step`) | Via symlink/copy |
| **Dependencies** | None (built-in) | Single binary | Binary + tmux |
| **Complexity** | Low | Medium | High |
| **Open Station fit** | **High** | **Medium** | **Low–Medium** |

### Approach Categories

1. **Built-in (`claude --worktree`)** — Zero-dependency, minimal
   friction. Best for "one agent, one task" parallelism where
   each session is launched independently.

2. **External orchestrator** — Rich lifecycle management but no
   task awareness. Requires a bridge layer to connect to Open
   Station's task model.

3. **Custom integration** — `openstation run` adds `--worktree`,
   manages the full lifecycle with task awareness built in. Most
   aligned with project conventions.

---

## 4. Integration with `openstation run`

### 4.1 Current State

The codebase has significant worktree groundwork:

| Component | Status | Detail |
|-----------|--------|--------|
| `find_root()` worktree fallback | **Implemented** | `_git_main_worktree_root()` in `core.py` resolves vault from linked worktrees via `git rev-parse --git-common-dir` |
| Branch-based task scoping spec | **Done** (0094) | `branch` frontmatter field, `--branch` CLI flag designed |
| Branch scoping implementation | **Backlog** (0109) | Not yet implemented |
| Agent skills/docs update | **Backlog** (0108) | Not yet started |
| `--worktree` on `openstation run` | **Not started** | No worktree flags in `build_command()` or `cmd_run()` |

### 4.2 `find_root()` — Already Works

The critical blocker from prior research (task 0092) has been
resolved. `core.py` lines 86–132 implement:

1. Walk up from CWD to find `.openstation/` or source repo markers
2. If not found, call `git rev-parse --git-common-dir` to get
   the main worktree root
3. Check the main worktree root for Open Station markers
4. Graceful fallback when git is unavailable

This means agents running in worktrees **can already find the
vault**. The remaining work is CLI integration and task scoping.

### 4.3 Proposed: `openstation run --worktree`

Add a `--worktree` flag to `openstation run`:

#### Option A: Pass-Through (Recommended First Step)

Minimal — forward `--worktree` to Claude CLI:

```python
# In build_command():
if worktree:
    cmd.extend(["--worktree", worktree_name])
```

**Worktree name derivation:**
- If task has `branch` field → use it as worktree name
- Otherwise → auto-generate from task: `task-{id}-{slug}`

**Pros:** Zero new dependencies, leverages Claude's built-in
cleanup, minimal code change.

**Cons:** Branch naming follows Claude convention
(`worktree-<name>`), not task-aligned.

#### Option B: Pre-Create (Future Enhancement)

`openstation run` creates the worktree via `git worktree add`,
then runs Claude inside it:

```python
# 1. Create worktree
subprocess.run(["git", "worktree", "add",
    f".claude/worktrees/{task_name}",
    "-b", f"task/{task_id}-{slug}"])

# 2. Launch Claude in the worktree directory
cmd = build_command(...)  # no --worktree flag needed
subprocess.Popen(cmd, cwd=worktree_path)
```

**Pros:** Full control over branch naming and worktree location,
task-aligned branch names.

**Cons:** Must manage cleanup (creation, error handling, prune).

#### Option C: Delegate to External Tool

Shell out to `wt` or `workmux` for lifecycle management.

**Not recommended as a dependency.** These tools can coexist
alongside Open Station without being wired in.

### 4.4 Parallel Execution Flows

#### Single Task in Worktree

```bash
openstation run --task 0042 --worktree --attached
```

1. Resolve task 0042, read `branch` field
2. Derive worktree name from task
3. Pass `--worktree <name>` to Claude CLI
4. Agent runs in isolated worktree, finds vault via `find_root()`

#### Multiple Tasks in Parallel (Manual)

```bash
# Terminal 1
openstation run --task 0042 --worktree --attached

# Terminal 2
openstation run --task 0043 --worktree --attached
```

Each agent gets its own worktree and branch. If branch-scoping
(0109) is implemented, each agent only sees its branch-scoped
tasks.

#### Multiple Tasks in Parallel (Automated — Future)

```bash
openstation run --task 0050 --worktree --parallel
```

Would run all ready subtasks concurrently in separate worktrees.
Requires: process pool, log multiplexing, failure handling,
resource budgeting. **Separate feature, significantly more
complex.**

### 4.5 Detached vs Attached Mode

| Mode | Worktree Behavior |
|------|-------------------|
| **Attached** (`os.execvp`) | `--worktree` works natively as a Claude CLI flag |
| **Detached** (`subprocess.Popen`) | `--worktree` creates worktree before session, Claude handles cleanup after. `_stream_and_capture` works unchanged. |

---

## 5. Open Questions and Design Decisions

### Q1: Should `openstation run` create worktrees or delegate to Claude?

**Status:** Undecided — leaning toward delegation (Option A).

**Trade-off:**
- Delegating to Claude: zero implementation, but branch names
  follow `worktree-{name}` convention.
- Creating ourselves: full control over naming and location,
  but must handle lifecycle.

**Recommendation:** Start with Option A (delegation). Revisit
if naming control becomes important for branch-scoping.

### Q2: How should branch names map to tasks?

**Status:** Undecided.

**Options:**
- `worktree-{task-id}` (Claude default with task ID as name)
- `task/{id}-{slug}` (custom, requires Option B)
- User-specified (`branch` field in task frontmatter)

**Recommendation:** Use task's `branch` field if set. If unset,
pass task name as worktree name → Claude creates
`worktree-0042-slug`. Revisit when branch-scoping is
implemented.

### Q3: Sequential or concurrent parallel execution?

**Status:** Sequential first — confirmed.

Sequential-in-worktrees is the natural first step: each subtask
runs in its own worktree, one at a time. Concurrent execution
(process pool, multiplexed logging, partial failure handling)
is a separate, more complex feature.

### Q4: What happens to worktrees after task completion?

**Status:** Delegate to Claude initially.

Claude's auto-cleanup handles it: removes if no changes, prompts
if changes exist. For detached mode, may need a `--cleanup` flag
later.

### Q5: How does `.openstation/` resolution work in worktrees?

**Status:** ✅ Resolved.

`find_root()` in `core.py` already falls back to the main
worktree root via `git rev-parse --git-common-dir`. Agents in
worktrees can find the vault.

### Q6: Should worktrunk/workmux be supported as alternatives?

**Status:** Document coexistence, don't depend.

Both tools can wrap `openstation run` or be wrapped by it.
Document usage patterns (see §§ 2.1, 2.2 above) without adding
either as a dependency.

### Q7: What about `isolation: worktree` for subagents?

**Status:** Understood — separate concern.

This is for in-session subagent dispatch, not top-level agent
launch. Open Station agents using the Agent tool during execution
can leverage worktree isolation for their subagents
independently.

### Q8: How does Claude's `--tmux` flag interact with `openstation run`?

**Status:** Needs investigation.

`--tmux` launches Claude in its own tmux session. Could be
useful for detached mode — `openstation run --task 0042 --worktree --tmux`
would create a fully detached, isolated session. Needs testing
to confirm compatibility with `_stream_and_capture`.

### Q9: What about Claude's "agent teams" feature?

**Status:** Needs investigation.

Claude Code docs mention "agent teams" for automated
coordination of parallel sessions with shared tasks and
messaging. This may overlap with or complement Open Station's
multi-agent orchestration model. No public docs found yet.

### Q10: What's the prerequisite ordering for implementation?

**Status:** Clear.

```
find_root() worktree fallback  ✅ Done (in core.py)
         │
         ▼
Option A: --worktree pass-through  ← Next milestone
         │
         ▼
Branch-scoping implementation (0109)
         │
         ▼
Option B: Pre-create worktrees (if needed)
         │
         ▼
Parallel execution (separate feature)
```

---

## 6. Implementation Recommendations

1. **Milestone 1 — `--worktree` pass-through:** Add
   `--worktree` flag to `openstation run` that forwards to
   Claude CLI. Derive worktree name from task name. Minimal
   code change in `build_command()` and `cmd_run()`.

2. **Milestone 2 — Branch-scoping (0109):** Implement the
   `branch` frontmatter field and `--branch auto` filtering.
   This connects worktrees to task discovery.

3. **Milestone 3 — Agent awareness (0108):** Update agent
   skills and docs to document worktree workflows.

4. **Milestone 4 (optional) — Pre-create worktrees:** If
   branch naming control is needed, switch to Option B with
   `git worktree add` and custom cleanup.

5. **Document coexistence:** Add a section to docs showing
   how to use worktrunk and workmux alongside Open Station
   without making them dependencies.

---

## Sources

- [Claude Code: Common Workflows — Worktrees](https://code.claude.com/docs/en/common-workflows)
- [Claude Code Worktree Announcement (Boris Cherny)](https://www.threads.com/@boris_cherny/post/DVAAnexgRUj)
- [Worktrunk](https://worktrunk.dev/) — [GitHub](https://github.com/max-sixty/worktrunk)
- [Workmux](https://github.com/raine/workmux)
- [Git Worktree Documentation](https://git-scm.com/docs/git-worktree)
- [Better Stack: Git Worktrees in Claude Code](https://betterstack.com/community/guides/ai/git-worktrees-claude/)
- [Extending Claude Code Worktrees for Database Isolation](https://www.damiangalarza.com/posts/2026-03-10-extending-claude-code-worktrees-for-true-database-isolation/)
