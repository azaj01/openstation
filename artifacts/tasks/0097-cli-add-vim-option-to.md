---
kind: task
name: 0097-cli-add-vim-option-to
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-11
---

# CLI — Add `--vim` Option to `list`

## Requirements

1. Add a `-v` / `--vim` flag to the `list` subcommand that opens all matching task files in vim as a buffer list (e.g. `vim file1.md file2.md …`).
2. The flag is mutually exclusive with `--json` and `--quiet` — if combined, print an error and exit.
3. All existing filters (`--status`, `--assignee`, `--type`, positional filter) apply before opening — vim receives only the filtered set.
4. If the filtered result is empty, print a message ("no matching tasks") and exit `0` without launching vim.
5. Follow the same pattern as `show --vim` (launch vim directly via `os.execvp`).

## Verification

- [ ] `openstation list --vim` opens active tasks in vim
- [ ] `openstation list --status ready --vim` opens only ready tasks
- [ ] `openstation list --vim` with no matching tasks prints a message, doesn't launch vim
- [ ] `openstation list --vim --json` produces an error
- [ ] Existing `list` behavior (table, quiet, json) unchanged
- [ ] Tests cover the new flag
