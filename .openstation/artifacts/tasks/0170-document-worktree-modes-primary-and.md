---
kind: task
name: 0170-document-worktree-modes-primary-and
type: documentation
status: done
assignee: author
owner: user
parent: "[[0122-worktree-integration]]"
created: 2026-03-19
---

# Document Worktree Modes: Primary and Linked

## Requirements

1. Create `docs/worktrees.md` documenting worktree modes:
   - **Primary mode** — worktree has its own markers (`.openstation/`,
     `agents/` + `install.sh`) → uses worktree root, owns its vault
     and artifacts
   - **Linked mode** — worktree has no markers → uses main repo root,
     shares the primary vault and artifacts
   - How `find_root()` resolves each mode (two-step: check toplevel
     first, fall back to main worktree root)
   - Which CLI commands are affected and how they behave in each mode
2. Update the `openstation-execute` skill
   (`skills/openstation-execute/SKILL.md`) with a worktree awareness
   note:
   - In linked mode, `artifacts/` lives in the main repo, not the
     agent's CWD
   - Always use CLI commands (`openstation show/list/create/status`) —
     they resolve the correct root automatically
   - Do NOT use filesystem checks (ls, find, git status) to verify
     task operations — use `openstation show <task>` instead
   - The `info:` line from `create`/`status` shows the absolute path
     of the modified file
   - Reference `docs/worktrees.md` for full details
3. Update the `run` prompt templates in `src/openstation/run.py` to
   include a hint when running in linked mode (worktree flag set but
   no local markers) — e.g., append "Artifacts are in the main repo
   at `<root>`; use CLI commands to access them."

## Findings

Created `docs/worktrees.md` documenting the two worktree modes
(primary and linked), how `find_root()` resolves each via its
two-step git-based approach, and how CLI commands behave
transparently in both modes. Includes an Architecture section
covering the module layout, key abstractions, and data flow.

Updated the `openstation-execute` skill with a "Worktree
Awareness" section placed before "On Startup", covering all
five guidance points from the requirements and referencing
`docs/worktrees.md`.

Updated both prompt construction sites in `run.py`
(`run_single_task` and `_exec_or_run`) to append an artifact
location hint when `worktree` is set and `exec_cwd` differs
from `root` (the linked-mode condition).

Added `docs/worktrees.md` to the key docs table in `CLAUDE.md`.

## Progress

- 2026-03-19 — author: Created `docs/worktrees.md`, updated
  execute skill with worktree awareness section, added
  linked-mode hint to run prompts in `run.py`, updated
  `CLAUDE.md` key docs table.

## Verification

- [x] `docs/worktrees.md` exists and documents primary vs linked modes
- [x] Execute skill includes worktree awareness guidance and references `docs/worktrees.md`
- [x] Run prompt includes artifact location hint in linked mode
- [x] `CLAUDE.md` key docs table references `docs/worktrees.md`
