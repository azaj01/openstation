---
kind: task
name: 0219-add-enabled-property-to-hooks
type: feature
status: verified
assignee: developer
owner: user
created: 2026-03-22
---

# Add Enabled Property To Hooks For Toggling On And Off

## Requirements

1. Add an optional `enabled` boolean property to each hook entry in `settings.json` (default: `true` when omitted, for backward compatibility).
2. Update the hook execution logic in `hooks.py` to skip hooks where `enabled` is `false`.
3. Update `openstation hooks list` (if it lands from 0218, otherwise the existing hook display) to show the enabled/disabled state.
4. Update `docs/hooks.md` to document the `enabled` property with examples.
5. Update `docs/settings.md` if it documents hook entry format.

## Verification

- [x] Hook with `"enabled": false` is skipped during status transitions
- [x] Hook with `"enabled": true` fires normally
- [x] Hook with no `enabled` field fires normally (backward compatible)
- [x] `docs/hooks.md` documents the `enabled` property
- [x] Tests cover: enabled=true, enabled=false, enabled omitted

## Verification Report

*Verified: 2026-03-23*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Hook with `"enabled": false` is skipped during status transitions | PASS | `hooks.py:86` — `if hook.get("enabled", True) is False: continue` skips disabled hooks in `match_hooks()` |
| 2 | Hook with `"enabled": true` fires normally | PASS | `test_hooks.py:124-126` — `test_enabled_true_fires` asserts match returns 1 result; integration test `test_enabled_true_hook_fires` at line 238 confirms execution |
| 3 | Hook with no `enabled` field fires normally (backward compatible) | PASS | Default `True` in `hook.get("enabled", True)`; `test_hooks.py:132-134` — `test_enabled_omitted_fires` confirms backward compat |
| 4 | `docs/hooks.md` documents the `enabled` property | PASS | Property table row at line 59, example at line 44, dedicated "Disabling hooks" section at line 255 with code example |
| 5 | Tests cover: enabled=true, enabled=false, enabled omitted | PASS | Unit tests: `test_enabled_true_fires`, `test_enabled_false_skipped`, `test_enabled_omitted_fires`, `test_enabled_false_among_others`; integration: `test_enabled_true_hook_fires`, line 226 disabled integration test; CLI: `test_enabled_column_on/off/header`, `test_show_displays_enabled_on/off` |

### Summary

5 passed, 0 failed. All verification criteria met.
