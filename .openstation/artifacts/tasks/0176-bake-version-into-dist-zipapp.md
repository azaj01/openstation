---
kind: task
name: 0176-bake-version-into-dist-zipapp
type: implementation
status: rejected
assignee: developer
owner: user
parent: "[[0175-fix-self-update-version-detection]]"
created: 2026-03-19
---

# Bake Version Into Dist Zipapp At Build Time

## Problem

`src/openstation/__init__.py` uses `importlib.metadata.version("openstation")`
to determine `__version__`. This works when installed via pip (package metadata
exists), but the `dist/openstation` zipapp has no package metadata — so it
always returns `"dev"`.

## Requirements

- At zipapp build time, bake the version from `pyproject.toml` into the
  package so it's available at runtime without `importlib.metadata`
- Approach options:
  1. Write a `_version.py` file during build (e.g., `__version__ = "0.11.0"`)
     and import it as primary, with `importlib.metadata` as fallback
  2. Use `importlib.metadata` with a fallback that reads version from a
     bundled resource
  3. Include the `.dist-info/METADATA` in the zipapp
- The pip-installed path must continue to work too

## Architecture

- `src/openstation/__init__.py` — version detection
- `dist/openstation` — zipapp binary (built how? check build scripts)
- `pyproject.toml` — source of truth for version

## Verification

- [ ] `python dist/openstation --version` shows correct semver (not "dev")
- [ ] `pip install -e .` + `openstation --version` still works
- [ ] Build process documented or scripted
