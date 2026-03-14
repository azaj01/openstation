---
kind: task
name: 0136-hooks-implementation-implement-hooks-in
type: implementation
status: backlog
assignee: developer
owner: user
parent: "[[0134-task-lifecycle-hooks]]"
created: 2026-03-14
---

# Hooks Implementation — Implement Hooks In Cli

## Requirements

1. Implement hook configuration loading from the settings file per the spec from `0135-hooks-spec-design-configuration-schema`
2. Add hook engine: match transitions, execute commands with env vars, enforce timeouts
3. Integrate hook execution into `openstation status` command — fire hooks on successful transition
4. Abort transition and report error if a hook command fails (non-zero exit)
5. Add tests for hook matching, execution, failure handling, and timeout

## Verification

- [ ] Hook config is loaded from settings file
- [ ] `openstation status` fires matching hooks on transitions
- [ ] Env vars (task name, old/new status, path) are passed to hook commands
- [ ] Failed hooks abort the transition with clear error output
- [ ] Multiple hooks run in declaration order
- [ ] Timeout kills long-running hooks
- [ ] Tests pass
