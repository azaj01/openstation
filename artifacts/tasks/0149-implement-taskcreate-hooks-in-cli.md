---
kind: task
name: 0149-implement-taskcreate-hooks-in-cli
type: implementation
status: backlog
assignee: developer
owner: user
parent: "[[0147-hooks-improvements-support-task-creation]]"
created: 2026-03-17
---

# Implement Taskcreate Hooks In Cli

## Requirements

1. Implement `TaskCreate` hook loading from `settings.json` (reuse or extend `load_hooks`)
2. Add creation hook matching per the spec from 0148
3. Integrate hook execution into `cmd_create()` in `tasks.py` at the timing specified by the spec
4. Pass creation-specific environment variables to hook commands
5. Handle failure per the spec (abort or cleanup)
6. Add tests for creation hook matching, execution, failure, and timeout
7. Update `docs/hooks.md` with `TaskCreate` usage and examples

## Verification

- [ ] `TaskCreate` hooks load from `settings.json`
- [ ] `openstation create` fires matching creation hooks
- [ ] Environment variables are passed correctly
- [ ] Failed hooks behave per spec (abort/cleanup)
- [ ] Tests cover creation hook scenarios
- [ ] `docs/hooks.md` documents `TaskCreate` hooks
