---
kind: task
name: 0202-document-tmux-integration
type: documentation
status: backlog
assignee: author
owner: user
parent: "[[0199-tmux-integration-for-detached-agent]]"
created: 2026-03-21
---

# Document Tmux Integration

## Requirements

1. Update `docs/cli.md` to document tmux behavior in detached mode
2. Document the `openstation sessions` command (or equivalent)
3. Add tmux prerequisite note (optional dependency, graceful fallback)
4. Update `CLAUDE.md` if the run examples change

## Verification

- [ ] `docs/cli.md` documents tmux session behavior for detached runs
- [ ] `openstation sessions` (or equivalent) is documented with synopsis, flags, examples
- [ ] Fallback behavior when tmux is missing is documented
- [ ] `CLAUDE.md` examples are accurate
