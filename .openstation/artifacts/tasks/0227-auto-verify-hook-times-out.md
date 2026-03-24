---
kind: task
name: 0227-auto-verify-hook-times-out
type: bug
status: done
assignee: developer
owner: user
created: 2026-03-23
---

# Auto-verify hook times out during dispatch

## Root Cause

The `*→review` and `*→ready` hooks in `settings.json` have a 10s
timeout. The hook scripts (`auto-verify`, `auto-start`) run a
Python interpreter to check settings, then call `os-dispatch` to
spawn a tmux window. The combined startup overhead (python3 +
bash + tmux) can exceed 10s, causing the hook runner to kill the
process with a timeout error.

## Affected Files

- `.openstation/settings.json`: `*→review` and `*→ready` hooks have `timeout: 10`

## Requirements

1. Increase the timeout for `*→review` and `*→ready` hooks to a value that accommodates dispatch overhead (e.g., 30s)
2. Alternatively, optimize the hook scripts to reduce startup time (e.g., replace the python3 settings check with a lightweight jq/bash equivalent)

## Findings

Applied both remediation approaches from the requirements:

1. **Timeout increase**: `*→ready` and `*→review` hooks bumped from 10s → 30s in `settings.json`, providing 3× headroom for dispatch overhead.
2. **Script optimization**: Replaced all `python3` invocations in `auto-verify` and `auto-start` with lightweight alternatives:
   - Settings check: `python3 -c "import json …"` → `jq -r '.autonomous.enabled // false'`
   - Assignee extraction (auto-start only): `python3 -c "import yaml …"` → `sed` frontmatter parse
   - This eliminates Python interpreter startup (~0.5–1s per call, 2 calls in auto-start) from the critical path.

Note: `jq` output is lowercase `"true"`/`"false"`, so the comparison strings were updated accordingly (previously compared against Python's `"True"`).

## Progress

- 2026-03-23 — Increased hook timeouts from 10s to 30s; replaced python3 settings/YAML parsing with jq and sed in both hook scripts; all 511 tests pass.

## Verification

- [x] `openstation hooks run <task> in-progress review` completes without timeout
- [x] `openstation hooks run <task> backlog ready` completes without timeout
- [x] Hook timeout values in `settings.json` are sufficient for dispatch overhead

## Verification Report

*Verified: 2026-03-24*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `openstation hooks run <task> in-progress review` completes without timeout | PASS | Completed in 0.210s (timeout: 30s); `auto-verify` uses `jq` not `python3` |
| 2 | `openstation hooks run <task> backlog ready` completes without timeout | PASS | Completed in 0.202s (timeout: 30s); `auto-start` uses `jq`/`sed` not `python3` |
| 3 | Hook timeout values in `settings.json` are sufficient for dispatch overhead | PASS | Both `*→ready` and `*→review` hooks set to `timeout: 30` (3× previous 10s); no `python3` in either script |

### Summary

3 passed, 0 failed. All verification criteria met — hooks complete in ~0.2s, well within the 30s timeout.
