---
kind: task
name: 0049-cli-obsidian-integration
status: backlog
agent:
owner: user
created: 2026-03-04
---

# Obsidian integration in the CLI

Add optional Obsidian CLI integration to the `openstation` CLI
as a faster query path, falling back to filesystem when Obsidian
is not available.

## Requirements

- Detect whether the Obsidian CLI is available and Obsidian is
  running
- Use `obsidian search` for task queries (`list`, `show`) when
  available, with automatic fallback to the current filesystem
  implementation
- Support Obsidian property queries: `[kind: task]`,
  `[status: X]`, `[agent: X]`, `[parent: X]`
- Parse JSON output from `obsidian search format=json`

## Verification

- [ ] `openstation list` uses Obsidian CLI when available
- [ ] `openstation list` falls back to filesystem when Obsidian is not running
- [ ] Query results match between Obsidian and filesystem paths
- [ ] No hard dependency on Obsidian — all commands work without it
