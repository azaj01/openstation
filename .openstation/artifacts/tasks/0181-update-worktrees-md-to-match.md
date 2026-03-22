---
kind: task
name: 0181-update-worktrees-md-to-match
type: bug
status: done
assignee: author
owner: user
created: 2026-03-20
---

# Update worktrees.md to match post-0173 code

`docs/worktrees.md` still documents the pre-0173 dual-marker
design. Task 0173 removed the `agents/` + `install.sh` source-repo
marker and the `(root, prefix)` tuple API. The doc needs to
reflect the current code.

## Requirements

1. Remove the two-row markers table (lines 20-25). The only
   marker is `.openstation/` — no prefix concept exists.
2. Update `_check_dir()` description: returns `bool`, checks
   only `.openstation/`.
3. Update `find_root()` pseudocode: returns `Path | None`,
   not `(root, prefix)` tuples. Remove `(None, None)` references.
4. Rename "Primary Mode" → "Independent Mode" to match code
   and task 0168 terminology.
5. Keep the rest of the doc (linked mode behavior, CLI table,
   agent guidelines) — those are still accurate.

## Findings

Updated `docs/worktrees.md` to reflect the post-0173 codebase:

- Removed the two-row markers table and prefix concept — Independent
  Mode section now states the sole marker is `.openstation/`
- Updated `_check_dir()` in Key Abstractions to document `bool` return
- Rewrote `find_root()` pseudocode: returns `Path | None`, steps
  use `_check_dir()` calls, no tuple references
- Renamed "Primary Mode" → "Independent Mode" throughout (section
  heading and CLI table column)
- Preserved linked mode, CLI table, agent guidelines, data flow,
  and module layout sections unchanged

## Progress

- 2026-03-20 — author: Updated `docs/worktrees.md` per all five
  requirements. Verified against `core.py` that `_check_dir` returns
  `bool` and `find_root` returns `Path | None`.

## Verification

- [x] No mention of `agents/` + `install.sh` marker in worktrees.md
- [x] No `(root, prefix)` or `(None, None)` tuple references
- [x] `_check_dir` documented as returning bool
- [x] `find_root` documented as returning `Path | None`
- [x] Mode called "Independent" not "Primary"

## Verification Report

*Verified: 2026-03-20*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | No mention of `agents/` + `install.sh` marker | PASS | Grep for `install.sh` and `agents/.*marker` — no matches |
| 2 | No `(root, prefix)` or `(None, None)` tuple references | PASS | Grep for both patterns — no matches |
| 3 | `_check_dir` documented as returning bool | PASS | Line 67: "returns `bool`" |
| 4 | `find_root` documented as returning `Path \| None` | PASS | Line 38: "`Path \| None`" |
| 5 | Mode called "Independent" not "Primary" | PASS | Line 15: "### Independent Mode", line 91: "Independent Mode" column; grep for "Primary" — no matches |

### Summary

5 passed, 0 failed. All verification criteria met.
