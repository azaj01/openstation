---
kind: spec
name: settings
---

# Settings

Project-level configuration for Open Station. Settings control
runtime behavior such as lifecycle hooks.

## File Location

| Context | Path |
|---------|------|
| Installed project | `.openstation/settings.json` |
| Source repo | `settings.json` (vault root) |

If the file is missing, Open Station runs with defaults (no
hooks, no overrides).

## Format

JSON object with top-level keys:

```json
{
  "hooks": { ... },
  "defaults": { ... }
}
```

## Keys

| Key | Type | Description | Details |
|-----|------|-------------|---------|
| `hooks` | object | Lifecycle hooks that run on status transitions | [hooks.md](hooks.md) |
| `defaults` | object | Default flag values for CLI commands | See below |

Keys not listed above are ignored.

## `defaults`

Maps command names to default flag values. When a flag is not
explicitly passed on the command line, the corresponding default
is applied.

### Schema

```json
{
  "defaults": {
    "<command>": {
      "<flag>": <value>
    }
  }
}
```

**Command keys** use the subcommand name directly for top-level
commands (`show`, `list`, `status`, `run`, `create`) and dot
notation for nested commands (`agents.show`, `agents.list`,
`artifacts.show`, `artifacts.list`).

**Flag names** match the argparse attribute (long form, dashes
replaced with underscores): `vim`, `json`, `quiet`, `status`,
`assignee`, `dry_run`, etc.

**Values** are the default to apply — `true`/`false` for boolean
flags, strings for value flags.

### Scoping: Human-Only

Defaults apply **only in human CLI context**. When the
`CLAUDECODE` environment variable is set (indicating an agent
session), all defaults are skipped. This prevents defaults like
`"vim": true` from interfering with agent automation.

### Override Precedence

Explicit CLI flags always override defaults:

```
explicit CLI flag  >  settings default  >  argparse default
```

If a user passes `--json` and the default says `"vim": true`,
`--json` wins — the default for `vim` is not applied. This
also respects mutually exclusive flag groups.

### Examples

Open tasks in the editor by default:

```json
{
  "defaults": {
    "show": { "vim": true }
  }
}
```

Default list to ready tasks only:

```json
{
  "defaults": {
    "list": { "status": "ready" }
  }
}
```

Multiple commands:

```json
{
  "defaults": {
    "show": { "vim": true },
    "agents.show": { "vim": true },
    "list": { "status": "ready" }
  }
}
```

## Example

Settings file with a hook and defaults:

```json
{
  "hooks": {
    "StatusTransition": [
      {
        "matcher": "*→done",
        "command": "bin/hooks/auto-commit",
        "phase": "post",
        "timeout": 120
      }
    ]
  },
  "defaults": {
    "show": { "vim": true }
  }
}
```

See [hooks.md](hooks.md) for the full hook schema, matchers,
environment variables, and execution model.

## Architecture

### Module layout

| File | Role |
|------|------|
| `src/openstation/hooks.py` | Settings loading (`load_settings`), hook loading and execution |
| `src/openstation/cli.py` | Default application (`_apply_cli_defaults`), argv scanning (`_explicit_flags`) |

### Integration points

- `hooks.load_settings(root, prefix)` reads and parses
  `settings.json` from the vault root, returning the full dict.
  Used by both the hook system and the defaults system.
- `cli._apply_cli_defaults(args, settings)` is called in
  `main()` after argparse and `find_root()`, before command
  routing. Guarded by `CLAUDECODE` env var check.
- `cli._explicit_flags()` scans `sys.argv` to determine which
  flags were explicitly passed, preventing defaults from
  overriding user intent in mutually exclusive groups.

### Data flow

1. `main()` calls `parser.parse_args()` → `args` namespace
2. `find_root()` locates the vault → `root`, `prefix`
3. If `CLAUDECODE` is not set:
   a. `load_settings(root, prefix)` reads `settings.json`
   b. `_command_key(args)` derives the lookup key (e.g. `"show"`)
   c. `_explicit_flags()` scans `sys.argv` for user-provided flags
   d. `_apply_cli_defaults()` merges unset flags from settings
4. Command handler runs with merged args
