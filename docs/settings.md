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
  "hooks": { ... }
}
```

## Keys

| Key | Type | Description | Details |
|-----|------|-------------|---------|
| `hooks` | object | Lifecycle hooks that run on status transitions | [hooks.md](hooks.md) |

Keys not listed above are ignored.

## Example

Minimal settings file with one hook:

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
  }
}
```

See [hooks.md](hooks.md) for the full hook schema, matchers,
environment variables, and execution model.
