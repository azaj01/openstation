---
kind: task
name: 0210-rename-settings-json-to-openstation
type: feature
status: ready
assignee: developer
owner: user
created: 2026-03-22
---

# Rename Settings.Json To Openstation.Yaml

## Requirements

1. Rename `.openstation/settings.json` → `.openstation/openstation.yaml`
2. Convert the settings format from JSON to YAML (the content is already simple key-value/list structure — maps cleanly to YAML)
3. Update `load_settings()` in `hooks.py` to read YAML instead of JSON (use `yaml.safe_load`; PyYAML is likely already a dependency, otherwise add it)
4. Update all code references to `settings.json` → `openstation.yaml` (`core.py`, `hooks.py`, `cli.py`)
5. Update `docs/settings.md` — file location, format section, all JSON examples → YAML
6. Update `CLAUDE.md` vault structure if it mentions `settings.json`
7. Update any commands/skills that reference `settings.json`

## Verification

- [ ] `.openstation/openstation.yaml` exists and is valid YAML
- [ ] `.openstation/settings.json` no longer exists
- [ ] `load_settings()` parses YAML correctly
- [ ] No references to `settings.json` remain in code or docs
- [ ] `docs/settings.md` shows YAML format and examples
- [ ] All hooks still fire correctly (existing behavior preserved)
- [ ] Tests pass
