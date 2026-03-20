---
kind: task
name: 0161-update-run-prompts-to-include
type: feature
status: rejected
assignee: developer
owner: user
parent: "[[0154-detached-openstation-run-in-worktree]]"
created: 2026-03-18
---

# Update Run Prompts with Worktree Context

## Problem

When `openstation run` spawns an agent in a worktree, the agent
has no idea it's in one. The prompts don't mention the worktree,
the vault root, or where to make changes vs. where to read tasks.
The agent may try to read task files relative to CWD (worktree)
and fail, or make code changes in the wrong location.

## Requirements

1. When a worktree session is detected (CWD ≠ vault root, or
   `--worktree` flag), append worktree context to the prompt
   sent to the agent.
2. The context must tell the agent:
   - **CWD is a worktree** — code changes happen here
   - **Vault root path** — task specs and artifacts live at
     `<vault_root>/artifacts/` (absolute path)
   - **CLI operates on the vault** — `openstation status`,
     `openstation show`, etc. resolve to the main repo
3. When not in a worktree, prompts remain unchanged (no
   regression).

### Affected prompts in `src/openstation/run.py`

| Location | Prompt | Mode |
|----------|--------|------|
| `run_single_task` ~L279 | `"Execute task {task_name}..."` | detached by-task |
| `_exec_or_run` ~L346 | `"Execute task {task_name}..."` | attached/detached by-task |
| `cmd_run` ~L586 | `"/openstation.verify {task_name}"` | verify |
| `cmd_run` ~L771 | `"Execute your ready tasks."` | by-agent |

### Approach

Add a helper (e.g., `_worktree_context(root, cwd)`) that returns
an empty string when CWD == root, or a context block like:

```
You are running in a git worktree.
- Working directory (code changes): /path/to/worktree
- Vault root (tasks, artifacts, CLI): /path/to/main-repo
Read task specs using absolute paths under the vault root.
Commit code changes in the current working directory.
```

Append the result to each prompt above.

## Verification

- [ ] `openstation run --task <id> --dry-run --worktree` output includes worktree context in the prompt
- [ ] `openstation run --task <id> --dry-run` (no worktree) prompt is unchanged
- [ ] `openstation run <agent> --dry-run --worktree` output includes worktree context
- [ ] `openstation run --task <id> --verify --dry-run --worktree` output includes worktree context
- [ ] Context block includes both the worktree path and the vault root path
- [ ] When CWD == vault root, no worktree context is appended (even if technically in a worktree)
