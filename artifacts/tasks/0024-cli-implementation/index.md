---
kind: task
name: 0024-cli-implementation
status: done
agent: developer
owner: manual
parent: 0021-openstation-cli
created: 2026-03-01
---

# CLI Implementation

## Requirements

Implement the OpenStation CLI according to the spec in
`artifacts/specs/cli-feature-spec.md`:

1. **Two commands** — `list` and `show` only
2. **Vault root detection** — walk up from CWD, support both
   source repo and `.openstation/`-installed projects
3. **Task discovery** — scan `artifacts/tasks/*/index.md`, parse
   YAML frontmatter with `str.split(':', 1)`
4. **Zero dependencies** — Python 3.8+ standard library only
5. **Single file** — `bin/openstation` with shebang
6. **Tests** — integration tests in `tests/test_cli.py` per the
   testing strategy in the spec

## Verification

- [x] `openstation list` shows non-done tasks with status, agent, owner
- [x] `openstation list --status ready` filters correctly
- [x] `openstation list --status all` includes done/failed tasks
- [x] `openstation list --agent researcher` filters by agent
- [x] `openstation show <task>` prints full task spec
- [x] `openstation show` with invalid task prints error message
- [x] Works in both source repo and `.openstation/` installed projects
- [x] No external dependencies
- [x] All tests pass
