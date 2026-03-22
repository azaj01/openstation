---
kind: task
name: 0177-self-update-detect-and-warn
type: implementation
status: rejected
assignee: developer
owner: user
parent: "[[0175-fix-self-update-version-detection]]"
created: 2026-03-19
---

# Self-Update Detect And Warn About Path Shadowing

## Problem

`self-update` re-links `~/.local/bin/openstation` to the latest version, but
if another `openstation` binary exists earlier in PATH (e.g., pip-installed
at `~/.pyenv/versions/*/bin/openstation`), the user silently runs the old one.

## Requirements

- After a successful update, resolve `which openstation` (or equivalent)
- If the resolved binary is NOT `~/.local/bin/openstation`, print a warning:
  ```
  warning: another openstation binary shadows the updated one
    active:  /Users/x/.pyenv/versions/3.9.6/bin/openstation
    updated: /Users/x/.local/bin/openstation
    hint: remove the old binary or adjust PATH order
  ```
- Also warn if `~/.local/bin` is not on PATH at all

## Architecture

- `src/openstation/update.py` — `cmd_self_update()`, add check after relink
- Use `shutil.which("openstation")` to find the active binary
- Compare resolved path against the expected `BIN_DIR / "openstation"`

## Verification

- [ ] When another binary shadows, warning is printed with both paths
- [ ] When no shadowing, no warning
- [ ] When `~/.local/bin` not on PATH, appropriate hint is shown
