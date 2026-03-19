---
kind: task
name: 0114-implement-agents-subcommand-expansion
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0111-cli-expand-agents-command-with]]"
created: 2026-03-11
---

# Implement agents subcommand expansion

Implement the expanded `agents` subcommand following the spec from `[[0113-spec-agents-subcommand-expansion]]`.

## Requirements

1. Add sub-parser for `agents` with sub-actions: `list`, `show`, `dispatch`
2. `agents list` — refactor `cmd_agents` to support `--json` and `--quiet`
3. `agents show <name>` — print full agent spec, support `--vim`
4. `agents dispatch <name>` — launch `claude --agent <name>`
5. Bare `agents` stays backward-compatible (alias for `agents list`)
6. Write tests for each sub-action
7. All existing tests pass

## Verification

- [ ] `openstation agents` still lists agents (backward-compatible)
- [ ] `openstation agents list` works with `--json` and `--quiet`
- [ ] `openstation agents show <name>` prints full spec
- [ ] `openstation agents show <name> --vim` opens in editor
- [ ] `openstation agents dispatch <name>` launches claude session
- [ ] New tests cover all sub-actions
- [ ] Existing tests pass
