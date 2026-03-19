---
kind: task
name: 0070-cli-enhancement-flexible-task-id
status: done
assignee: developer
owner: user
created: 2026-03-07
---

# Flexible Task ID Resolution

## Requirements

Enhance `resolve_task()` in `bin/openstation` to accept multiple
input formats. Currently only full name and zero-padded ID prefix
work. Add:

1. **Short ID (no leading zeros):** `58` → match `0058-*`. Zero-pad
   the input to 4 digits, then use existing prefix match logic.
2. **Slug-only lookup:** `implement-openstation-init-command-and` →
   match against the slug portion (everything after the `NNNN-`
   prefix). Use substring or prefix matching; error on ambiguity.

Resolution priority (first match wins):
1. Exact match (full name)
2. Zero-padded ID prefix match
3. Slug match

All subcommands that call `resolve_task()` (`show`, `status`, `run`)
get this for free.

## Verification

- [ ] `openstation show 58` resolves to `0058-implement-openstation-init-command-and`
- [ ] `openstation show 0058` still works (existing behavior)
- [ ] `openstation show 0058-implement-openstation-init-command-and` still works
- [ ] `openstation show implement-openstation-init-command-and` resolves correctly
- [ ] Ambiguous slug match returns an error with candidates listed
- [ ] Tests added for all resolution formats
- [ ] Existing tests still pass
