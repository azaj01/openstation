---
kind: task
name: 0230-review-and-merge-pr-3
type: feature
status: ready
assignee: developer
owner: user
created: 2026-03-25
---

# Review And Merge Pr #3 — Type Annotations

## Requirements

1. Review PR #3 (`feat: add type annotations to core and tasks modules`) — verify annotations are correct and complete for all 42 public functions
2. Check for the same CRLF line-ending issue (PR touches the same files); normalize if needed
3. Verify `py.typed` marker file is present and empty
4. Confirm no logic changes — annotations only on function signatures
5. Run type checker (mypy or pyright) to confirm annotations are valid
6. Ensure all existing tests pass
7. Merge the PR once review is satisfactory

## Verification

- [ ] Type annotations are present on all listed public functions in `core.py` (29) and `tasks.py` (13)
- [ ] `from __future__ import annotations` is at the top of both files
- [ ] `py.typed` marker file exists and is empty
- [ ] No logic changes — only signature annotations
- [ ] Files use LF line endings (no CRLF)
- [ ] All existing tests pass
- [ ] PR #3 is merged
