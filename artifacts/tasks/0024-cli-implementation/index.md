---
kind: task
name: 0024-cli-implementation
status: backlog
agent:
owner: manual
parent: 0021-openstation-cli
created: 2026-03-01
---

# CLI Implementation

## Requirements

Implement the OpenStation CLI according to the spec from
0023-cli-feature-spec:

1. **Core commands** — implement all subcommands: create, list,
   show, ready, done, reject, update, dispatch
2. **Symlink management** — all status transitions correctly
   move symlinks between lifecycle buckets
3. **ID auto-increment** — `create` scans `artifacts/tasks/`
   for the highest ID and increments
4. **Vault root detection** — CLI works in both source repo
   and `.openstation/`-installed projects
5. **Zero dependencies** — standard library only
6. **Tests** — implement tests per the testing strategy in the spec

## Verification

- [ ] All commands from the spec are implemented
- [ ] Symlink transitions work correctly for all status changes
- [ ] ID auto-increment produces unique, sequential IDs
- [ ] Works in both source repo and installed project contexts
- [ ] All tests pass
- [ ] No external dependencies
