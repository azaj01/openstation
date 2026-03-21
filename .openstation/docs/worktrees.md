---
kind: doc
name: worktrees
---

# Worktree Modes

Open Station supports running agents in git worktrees. When
`find_root()` resolves the vault, it produces one of two modes
depending on whether the worktree has its own Open Station
markers.

## Modes

### Independent Mode

The worktree contains `.openstation/` — it owns its vault and
artifacts. All paths resolve relative to the worktree root.

### Linked Mode

The worktree has no markers. `find_root()` falls back to the
main worktree root and uses its vault.

In linked mode:

- `artifacts/`, `docs/`, `skills/`, and `commands/` live in
  the **main repo**, not the agent's working directory
- The agent's CWD is the worktree (for code changes), but
  all task operations go through the main repo's vault
- CLI commands (`openstation show/list/create/status`) resolve
  the correct root automatically — agents do not need to
  know which mode they are in

## How `find_root()` Resolves

Two-step resolution with no directory walk-up. Returns
`Path | None`.

```
Step 1: git rev-parse --show-toplevel
        → _check_dir(toplevel)
        → If True: return toplevel              ← Independent mode

Step 2: git rev-parse --git-common-dir
        → Derive main worktree root (parent of .git common dir)
        → _check_dir(main_root)
        → If True: return main_root             ← Linked mode

Neither: return None                            ← Not an OS project
```

Non-git directories are not supported and always return `None`.

## Architecture

### Module Layout

| File | Role |
|------|------|
| `src/openstation/core.py` | `find_root()`, `_check_dir()`, `_git_toplevel()`, `_git_main_worktree_root()` |
| `src/openstation/run.py` | `cmd_run()` — captures `exec_cwd` at entry, threads it to all execution paths |

### Key Abstractions

- **`_check_dir(d)`** — checks whether `d / ".openstation"` exists,
  returns `bool`
- **`_git_toplevel(start)`** — runs `git rev-parse --show-toplevel`,
  returns the worktree root (or main repo root if not in a worktree)
- **`_git_main_worktree_root(start)`** — runs
  `git rev-parse --git-common-dir` and returns its parent (the
  main worktree root)

### Data Flow

```
Agent invoked in worktree CWD
  → cmd_run() captures exec_cwd = Path.cwd()
  → find_root() resolves vault root (may differ from CWD)
  → Prompt includes artifact location hint (linked mode only)
  → Claude session starts with CWD = exec_cwd (worktree)
  → CLI commands resolve vault via find_root() internally
```

In linked mode, `exec_cwd` (the worktree) differs from `root`
(the main repo). The run command separates these so the agent
works in the worktree while CLI commands find the shared vault.

## CLI Behavior by Mode

| Command | Independent Mode | Linked Mode |
|---------|-------------|-------------|
| `openstation list` | Reads tasks from local vault | Reads tasks from main repo vault |
| `openstation show` | Resolves against local tasks dir | Resolves against main repo tasks dir |
| `openstation create` | Creates task in local vault | Creates task in main repo vault |
| `openstation status` | Updates task in local vault | Updates task in main repo vault |
| `openstation run` | CWD = local root | CWD = worktree, vault = main repo |

All commands work identically from the agent's perspective —
the difference is transparent. The `info:` line from `create`
and `status` shows the absolute path of the modified file,
confirming which vault was used.

## Agent Guidelines

- **Always use CLI commands** for task operations — they resolve
  the correct vault automatically
- **Do not use filesystem checks** (`ls`, `find`, `git status`)
  to verify task operations — use `openstation show <task>`
- In linked mode, `artifacts/` is not in the agent's CWD — the
  CLI handles the indirection
- The run prompt includes an artifact location hint when
  operating in linked mode
