---
kind: task
name: 0211-linked-worktree-agents-cannot-find
type: bug
status: done
assignee: developer
owner: user
created: 2026-03-22
---

# Linked worktree agents cannot find artifacts — introduce OPENSTATION_HOME

When `openstation run --worktree` launches an agent in linked mode, the
agent's CWD is the worktree — not the main repo. Agents use `Search`/`Glob`
with relative patterns like `**/tasks/*.md` which resolve from CWD,
returning 0 results because `.openstation/` lives in the main repo. The
current mitigation is a prompt hint ("Artifacts are in the main repo at
`{root}`; use CLI commands"), but agents routinely ignore it and attempt
filesystem search first. The fix is mechanical: expose the vault root as
`OPENSTATION_HOME` so agents and skills resolve paths reliably in every mode.

## Requirements

1. **Set `OPENSTATION_HOME` in `src/openstation/run.py`** — before launching
   the Claude session (in `run_single_task()`, `_exec_or_run()`, and the
   by-agent `os.execvp` paths), set `os.environ["OPENSTATION_HOME"]` to
   `str(root / ".openstation")`. This must happen in all launch paths:
   detached, attached, and verify. The var should be an absolute path.

2. **Update `.openstation/skills/openstation-execute/SKILL.md`** — add an
   `## Environment` section (before "On Startup") documenting
   `OPENSTATION_HOME`: what it contains, that it's set automatically by
   `openstation run`, and the pattern for resolving vault paths:
   `$OPENSTATION_HOME/artifacts/tasks/`, `$OPENSTATION_HOME/docs/`, etc.

3. **Update the execute skill's "On Startup" step 4 fallback** — replace
   the relative pattern `artifacts/tasks/*.md` with
   `$OPENSTATION_HOME/artifacts/tasks/*.md`. This is the filesystem fallback
   when the CLI is unavailable.

4. **Update the execute skill's "Worktree Awareness" section** — replace the
   "do not use filesystem checks" guidance with: "Use `$OPENSTATION_HOME` to
   build absolute paths for any filesystem access to vault artifacts. This
   works in all modes (linked, independent, non-worktree)." Remove the
   separate linked-mode caveats — the env var makes them unnecessary.

5. **Update the run prompt hint in `run.py`** — in `run_single_task()`
   (line ~275) and `_exec_or_run()` (line ~348), replace the linked-mode
   hint with: `"Vault artifacts are at $OPENSTATION_HOME ({value}). Use CLI
   commands or absolute paths from this variable — do not use Search/Glob
   with relative patterns."` Include the var in all modes (not just linked),
   so agents always have it.

6. **Fallback when unset** — the CLI's `find_root()` must remain the
   fallback. Do not make `OPENSTATION_HOME` required for CLI commands
   (`openstation list/show/create/status`). The var is a hint for the agent
   session, not a hard dependency.

7. **Preserve:** Do not change `find_root()` logic, `_check_dir()`,
   worktree mode detection, or `core.py`. Independent-mode and non-worktree
   runs must continue to work identically (the var is simply set to the same
   root the agent is already in).

## Progress

### 2026-03-22 — developer
> time: 11:05
> log: [[artifacts/logs/0211-linked-worktree-agents-cannot-find]]

Implemented OPENSTATION_HOME env var across all run.py launch paths, updated execute skill with Environment section and $OPENSTATION_HOME-based path resolution, replaced linked-mode prompt hint with universal hint. 437 tests pass.

## Findings

Set `OPENSTATION_HOME` env var across all launch paths in `run.py` (4 locations:
`run_single_task`, `_exec_or_run`, verify mode, by-agent mode). Value is always
`str(root / ".openstation")` — an absolute path to the vault directory.

Replaced the linked-mode-only prompt hint with a universal hint that includes
the `$OPENSTATION_HOME` value in all modes, directing agents to use CLI commands
or absolute paths instead of relative patterns.

Updated the execute skill (`SKILL.md`) with:
- New `## Environment` section before "On Startup" documenting the variable
- Step 4 fallback now uses `$OPENSTATION_HOME/artifacts/tasks/*.md`
- "Worktree Awareness" rewritten to center on `$OPENSTATION_HOME` instead of
  linked-mode caveats

`core.py` and `find_root()` are untouched. 437 tests pass (1 pre-existing
failure in `test_autonomous_hooks.py` unrelated to this change).

## Verification

- [x] `run_single_task()` sets `OPENSTATION_HOME` before launching the subprocess
- [x] `_exec_or_run()` sets `OPENSTATION_HOME` before launching (both attached and detached paths)
- [x] By-agent attached path (`os.execvp` in `cmd_run`) sets `OPENSTATION_HOME` before exec
- [x] Verify mode path sets `OPENSTATION_HOME` before launching
- [x] `OPENSTATION_HOME` value is an absolute path to `.openstation/` (not the repo root)
- [x] Execute skill contains an `## Environment` section documenting `OPENSTATION_HOME`
- [x] Execute skill step 4 fallback uses `$OPENSTATION_HOME/artifacts/tasks/*.md`, not a relative path
- [x] Execute skill "Worktree Awareness" references `$OPENSTATION_HOME` for path resolution
- [x] Run prompt includes `OPENSTATION_HOME` value in all modes (not only linked)
- [x] `find_root()` in `core.py` is unchanged
- [x] Existing tests pass (`pytest tests/` — no regressions)

## Verification Report

*Verified: 2026-03-22*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `run_single_task()` sets `OPENSTATION_HOME` before launching | PASS | run.py L294: `os.environ["OPENSTATION_HOME"] = os_home` before `_stream_and_capture` |
| 2 | `_exec_or_run()` sets `OPENSTATION_HOME` (attached + detached) | PASS | run.py L353: set before attached `os.execvp` (L373) and detached `_stream_and_capture` (L404) |
| 3 | By-agent attached path sets `OPENSTATION_HOME` before exec | PASS | run.py L755: set before `os.execvp` at L774 |
| 4 | Verify mode sets `OPENSTATION_HOME` before launching | PASS | run.py L588: set before verify prompt build and `os.execvp`/`_stream_and_capture` |
| 5 | Value is absolute path to `.openstation/` (not repo root) | PASS | All 4 locations use `str(root / ".openstation")` — appends `.openstation` to project root |
| 6 | Execute skill has `## Environment` section | PASS | SKILL.md L86-101: documents var, auto-set behavior, and path examples |
| 7 | Step 4 fallback uses `$OPENSTATION_HOME/artifacts/tasks/*.md` | PASS | SKILL.md L113: `$OPENSTATION_HOME/artifacts/tasks/*.md` |
| 8 | Worktree Awareness references `$OPENSTATION_HOME` | PASS | SKILL.md L69-84: centers on `$OPENSTATION_HOME` for all modes |
| 9 | Prompt includes `OPENSTATION_HOME` in all modes | PASS | run.py L275-277 and L348-350: unconditional (not gated on worktree) |
| 10 | `find_root()` in `core.py` unchanged | PASS | `git diff HEAD -- src/openstation/core.py` shows no changes |
| 11 | Existing tests pass | PASS | 437 passed; 1 pre-existing failure in `test_autonomous_hooks.py` (unrelated) |

### Summary

11 passed, 0 failed. All verification criteria satisfied.
