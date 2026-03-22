---
kind: task
name: 0187-document-tmux-integration
type: documentation
status: rejected
assignee: author
owner: user
parent: "[[0183-native-tmux-integration-for-openstation]]"
created: 2026-03-21
---

# Document tmux Integration

Update project docs to reflect the new tmux-based session
management.

## Requirements

1. **`docs/cli.md`** — add `attach`, `ps`, `stop` commands;
   update `run` flags (`-d`/`--detached` replaces `--attached`
   as the non-default)
2. **`docs/worktrees.md`** — document how tmux sessions interact
   with worktree mode
3. **`CLAUDE.md`** — update the "Running an Agent" section with
   tmux examples
4. **Agent skills** — update `openstation-execute` skill if it
   references attached/detached mode

## Context

- Depends on: 0186 (run refactor) — docs describe implemented
  behavior, not planned behavior

## Verification

- [ ] `docs/cli.md` documents `attach`, `ps`, `stop` commands
- [ ] `docs/cli.md` documents updated `run` flags
- [ ] `docs/worktrees.md` covers tmux + worktree interaction
- [ ] `CLAUDE.md` "Running an Agent" section is updated
- [ ] Agent skills updated if they reference old attached/detached mode
