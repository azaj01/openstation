---
kind: task
name: 0175-fix-self-update-version-detection
type: feature
status: rejected
assignee: 
owner: user
created: 2026-03-19
subtasks:
  - "[[0176-bake-version-into-dist-zipapp]]"
  - "[[0177-self-update-detect-and-warn]]"
---

# Fix Self-Update Version Detection And Path Issues

## Problem

`openstation self-update` reports success (`Updated: v0.10.0 → v0.11.0`)
but `openstation --version` still shows `0.9.1`. Root causes:

1. **Zipapp version = "dev"**: `dist/openstation` is a zipapp that uses
   `importlib.metadata.version("openstation")` — but there's no installed
   package metadata inside the zipapp, so `__version__` falls back to `"dev"`.
2. **PATH shadowing**: A pip-installed `openstation` at
   `~/.pyenv/versions/*/bin/openstation` (v0.9.1) takes PATH priority over
   `~/.local/bin/openstation`. Self-update updates the latter but `which`
   resolves the former.
3. **install.sh stale version**: `OPENSTATION_VERSION` is hardcoded to
   `v0.10.0` — should be `v0.11.0`.

## Requirements

- The dist zipapp must report the correct version (not "dev")
- `self-update` must detect when a different `openstation` binary shadows
  `~/.local/bin/openstation` and warn the user
- `install.sh` version bump is a release chore (track separately or fix inline)

## Verification

- [ ] `~/.local/bin/openstation --version` reports correct semver after self-update
- [ ] `openstation self-update` warns when another binary shadows the updated one
- [ ] `install.sh` OPENSTATION_VERSION matches latest release tag
