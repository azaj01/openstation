---
kind: task
name: 0152-add-cli-defaults-to-settings
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-17
---

# Add CLI Defaults to Settings with Human-Only Scoping

## Requirements

1. Add a `defaults` top-level key to `settings.json` that maps
   command names to default flag values:
   ```json
   {
     "defaults": {
       "show": { "vim": true }
     }
   }
   ```
2. Defaults apply **only in human CLI context** — skip when
   `CLAUDECODE` env var is set (indicates an agent session).
3. Explicit CLI flags always override defaults.
4. Update `docs/settings.md` with the new key, schema, and
   scoping behavior.

## Progress

### 2026-03-17 — developer
> time: 16:41

Implemented defaults key in settings.json with human-only scoping (CLAUDECODE guard), explicit flag override via argv scanning, and mutually exclusive group safety. Added load_settings() to hooks.py, _apply_cli_defaults() to cli.py, updated docs/settings.md, wrote 29 tests (all passing).

## Findings

Implemented CLI defaults with human-only scoping. Key design
decisions:

- **Settings loading refactored**: extracted `load_settings()` in
  `hooks.py` as a general-purpose settings loader. `load_hooks()`
  now delegates to it. This avoids duplicating file I/O logic.

- **Argv scanning for explicit flags**: `_explicit_flags()` scans
  `sys.argv` to detect which flags the user actually passed. This
  prevents defaults from overriding choices in mutually exclusive
  groups (e.g., `--json` passed explicitly blocks `vim` default).

- **Mutually exclusive group safety**: when applying a boolean
  `True` default, the code checks if any other explicitly-passed
  flag is already `True` on the namespace, preventing conflicts
  like both `--vim` and `--json` being active simultaneously.

- **Command key scheme**: top-level commands use their name
  (`show`, `list`); nested sub-actions use dot notation
  (`agents.show`, `artifacts.list`). Aliases (`ag`, `art`) are
  normalized before lookup.

Files changed:
- `src/openstation/hooks.py` — added `load_settings()`, refactored `load_hooks()`
- `src/openstation/cli.py` — added `_command_key()`, `_explicit_flags()`, `_apply_cli_defaults()`; integrated into `main()`
- `docs/settings.md` — documented `defaults` key, schema, scoping, architecture
- `tests/test_cli_defaults.py` — 29 tests (unit + integration)

## Verification

- [x] `openstation show <task>` opens in vim when `defaults.show.vim` is `true` and run by a human
- [x] `openstation show <task>` ignores defaults when `CLAUDECODE` is set (agent context)
- [x] Explicit flags still work as expected
- [x] `docs/settings.md` documents the `defaults` key and scoping
