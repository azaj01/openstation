---
kind: task
name: 0159-add-verify-agent-setting-to
type: feature
status: review
assignee: developer
owner: user
created: 2026-03-17
---

# Add Verify.Agent Setting To Settings.Json

## Requirements

1. Add `verify.agent` key to `settings.json` schema — specifies
   the project-level default agent for `--verify` mode
2. Agent resolution order (highest to lowest priority):
   - `--agent` CLI argument
   - Task `owner` field (skip if `user` or empty)
   - `settings.verify.agent` (project-level default)
   - Hardcoded fallback: `project-manager`
3. Update `docs/settings.md` with the new key
4. Update `docs/cli.md` verify section with resolution order
5. Add tests covering each resolution level

### Context

`owner: user` means "human verifies" but `--verify` tries to
resolve it as an agent name, causing:
```
error: Agent spec not found: user
```

## Findings

Fixed the `--verify` agent resolution in `src/openstation/run.py`
to properly handle `owner: user` (and empty owner) by skipping
them and consulting `settings.verify.agent` before falling back
to `project-manager`.

**Changes:**

- **`src/openstation/run.py`** — Rewrote verify agent resolution
  to implement the 4-level priority chain: `--agent` > task owner
  (skip `user`/empty) > `settings.verify.agent` > `project-manager`.
  Loads settings via `hooks.load_settings()` when needed.
- **`docs/settings.md`** — Added `verify` key to the keys table,
  new `## verify` section with schema, resolution order, and example.
  Updated the full example to include the verify key.
- **`docs/cli.md`** — Replaced the inline resolution description
  in the verify mode paragraph with an explicit numbered list
  matching the implementation.
- **`tests/test_cli.py`** — Added `TestRunVerifyAgentResolution`
  class with 7 tests covering every resolution level and edge case.
  All 15 verify tests pass (8 existing + 7 new).

## Progress

- 2026-03-17 — Implemented verify.agent setting, updated docs and tests. All 15 verify tests pass.

## Verification

- [ ] `settings.verify.agent` is read from settings.json
- [ ] Resolution order: `--agent` > task `owner` > settings > fallback
- [ ] `owner: user` falls through to settings/fallback
- [ ] `docs/settings.md` documents `verify.agent`
- [ ] Tests cover all resolution levels
