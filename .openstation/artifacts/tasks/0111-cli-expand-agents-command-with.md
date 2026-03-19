---
kind: task
name: 0111-cli-expand-agents-command-with
type: feature
status: done
assignee:
owner: user
created: 2026-03-11
subtasks:
  - "[[0113-spec-agents-subcommand-expansion]]"
  - "[[0114-implement-agents-subcommand-expansion]]"
  - "[[0115-update-prompts-for-agents-subcommand]]"
  - "[[0116-add-ag-alias-for-agents]]"
---

# CLI — Expand Agents Command with List, Show, Dispatch

Currently `openstation agents` only lists agents in a table. Expand it into a richer subcommand with sub-actions.

## Requirements

1. **`openstation agents list`** (default, backward-compatible) — List all agents with name and description. Support `-j`/`--json` and `-q`/`--quiet` output modes, matching `list` conventions.
2. **`openstation agents show <name>`** — Display the full agent spec (frontmatter + body), similar to `openstation show` for tasks. Support `--json` and `--vim` flags.
3. **`openstation agents dispatch <name>`** — Launch an interactive Claude session with the agent (`claude --agent <name>`). Equivalent to the current `openstation run <agent>` by-agent mode but under `agents` for discoverability.
4. **Backward compatibility** — bare `openstation agents` (no sub-action) continues to list agents, same as today.

## Subtasks

### P1

1. **Spec agents subcommand** — update CLI spec in docs (`[[0113-spec-agents-subcommand-expansion]]`)

### P2

2. **Implement agents subcommand** — code changes (`[[0114-implement-agents-subcommand-expansion]]`)

### P3

3. **Update prompts** — update commands, skills, CLAUDE.md (`[[0115-update-prompts-for-agents-subcommand]]`)
4. **Improvements** — `ag` alias, `--dangerously-skip-permissions` on dispatch (`[[0116-add-ag-alias-for-agents]]`)

## Verification

- [x] `openstation agents` still lists all agents (backward-compatible)
- [x] `openstation agents list` works with `--json` and `--quiet`
- [x] `openstation agents show <name>` prints the full agent spec
- [x] `openstation agents show <name> --vim` opens in editor
- [x] Existing tests pass
- [x] New tests cover the added sub-actions

> **Note:** `agents dispatch` criterion removed — superseded by
> task 0120 which replaced it with `openstation run <agent>`.
