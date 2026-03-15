---
kind: task
name: 0141-implement-task-dependencies-in-cli
type: implementation
status: backlog
assignee: developer
owner: user
parent: "[[0140-introduce-task-dependencies-depends-on]]"
created: 2026-03-15
---

# Implement Task Dependencies in CLI

Blocked on 0137 (spec). Implement per the spec produced by the
architect.

## Requirements

1. Parse `depends_on` wikilink list from task frontmatter
2. Add dependency check to `cmd_status()` — block `backlog → ready`
   when dependencies are unmet; `--force` overrides
3. Show dependency status in `openstation show` output
4. Add blocked indicator to `openstation list` output
5. Support inverse "unblocks" query
6. Update `docs/task.spec.md` and `docs/lifecycle.md`

## Verification

- [ ] `depends_on` field parsed correctly from frontmatter
- [ ] `backlog → ready` blocked when dependencies unmet
- [ ] `--force` overrides dependency check
- [ ] `openstation show` displays dependencies with status
- [ ] `openstation list` shows blocked indicator
- [ ] Inverse query works
- [ ] Docs updated
- [ ] Tests cover all dependency scenarios
