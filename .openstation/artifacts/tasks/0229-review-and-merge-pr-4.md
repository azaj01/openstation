---
kind: task
name: 0229-review-and-merge-pr-4
type: feature
status: ready
assignee: developer
owner: user
created: 2026-03-25
---

# Review And Merge Pr #4 — Frontmatter Parser Fixes

## Requirements

1. Review PR #4 (`fix: handle quotes, comments, and indented lines in frontmatter parser`) — assess the three parser fixes and 26 new tests for correctness
2. Address the CRLF line-ending issue flagged in the PR comment: normalize `core.py` back to LF endings so the diff is clean
3. Add a `.gitattributes` file (`* text=auto eol=lf`) to prevent future line-ending issues
4. Ensure all existing and new tests pass after the line-ending fix
5. Merge the PR once the diff is clean and review is satisfactory

## Verification

- [ ] `core.py` uses LF line endings (no CRLF)
- [ ] `.gitattributes` with `* text=auto eol=lf` exists in repo root
- [ ] All 26 new frontmatter tests pass
- [ ] All pre-existing tests pass (excluding known `test_hooks.py` Windows failures)
- [ ] PR #4 diff shows only the actual logic changes (not whole-file re-encoding)
- [ ] PR #4 is merged
