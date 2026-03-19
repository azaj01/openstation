---
kind: task
name: 0130-add-aliases-to-agents-for
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-13
---

# Add aliases to agents for use in CLI commands

## Requirements

1. Add an `aliases` field to agent frontmatter (list of short names, e.g., `aliases: [pm]`)
2. CLI commands that accept an agent name (`openstation run <agent>`, `openstation agents show <name>`) resolve aliases to the canonical agent name
3. Define aliases for existing agents: `pm` → `project-manager`, `dev` → `developer`, `arch` → `architect`, `res` → `researcher`, `dr` → `devrel`
4. Aliases must be unique across all agents — duplicate alias raises a clear error
5. Update `openstation agents list` to show aliases alongside agent names

## Progress

### 2026-03-13 — developer

Implemented all 5 requirements:

- Added `aliases` field to all 6 agent frontmatter files (`pm`, `dev`, `arch`, `res`, `dr`, `au`)
- Added `parse_inline_list()` to `core.py` for parsing inline YAML lists like `[pm]`
- Updated `discover_agents()` in `run.py` to parse and return aliases
- Added `resolve_agent_alias()` function — resolves alias to canonical name, detects duplicate aliases
- Updated `format_agents_table()` to show an "Aliases" column in `agents list` output
- Updated `cmd_agents_show()` and `cmd_run()` (by-agent mode) to resolve aliases before lookup
- Updated `_agent_not_found()` to show aliases in the "available agents" hint
- Added 8 new tests in `TestAgentAliases` class covering alias resolution, duplicate detection, JSON output, and not-found handling
- All 37 agent/run-related tests pass

## Verification

- [ ] Agent frontmatter includes `aliases` field for all existing agents
- [ ] `openstation run pm --attached` resolves to `project-manager`
- [ ] `openstation agents show dev` resolves to `developer`
- [ ] Duplicate alias across agents raises a clear error
- [ ] `openstation agents list` output includes aliases
- [ ] Existing tests pass; new tests cover alias resolution
