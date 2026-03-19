---
kind: task
name: 0113-spec-agents-subcommand-expansion
type: spec
status: done
assignee: architect
owner: user
parent: "[[0111-cli-expand-agents-command-with]]"
artifacts:
  - "[[artifacts/specs/agents-subcommand-expansion]]"
created: 2026-03-11
---

# Spec agents subcommand expansion

Update the CLI spec in docs to cover the expanded `agents` subcommand.

## Requirements

1. Read the current `agents` implementation in `src/openstation/run.py` and `src/openstation/cli.py`
2. Spec the sub-actions: `agents list` (default), `agents show <name>`, `agents dispatch <name>`
3. Define argparse structure — how bare `agents` stays backward-compatible while supporting sub-actions
4. Define output formats (`--json`, `--quiet`, `--vim`) per sub-action
5. Write spec to `artifacts/specs/`

## Findings

Spec written to `artifacts/specs/agents-subcommand-expansion.md`. Key decisions:

- **Nested subparsers** for `agents list`, `agents show`, `agents dispatch` — avoids positional heuristic collisions.
- **Bare `agents` defaults to `list`** via `agents_action is None` check — zero breaking change.
- **Output flags per sub-action**: `list` gets `--json`/`--quiet` (mutually exclusive, matching `openstation list` conventions); `show` gets `--json`/`--vim` (matching `openstation show`); `dispatch` has no output flags (replaces process with `execvp`).
- **`dispatch` is intentionally minimal** — no tier/budget/turns flags; those stay on `openstation run`. `dispatch` = interactive shortcut.
- Three new handler functions in `run.py` (`cmd_agents_list`, `cmd_agents_show`, `cmd_agents_dispatch`) replace the current `cmd_agents`.
- One new helper needed: `core.extract_body(text)` for `show --json`.

## Verification

- [ ] Spec covers all three sub-actions (list, show, dispatch)
- [ ] Backward compatibility with bare `agents` is addressed
- [ ] Output format flags defined per sub-action
- [ ] Argparse structure specified
- [ ] Artifact written to `artifacts/specs/`
