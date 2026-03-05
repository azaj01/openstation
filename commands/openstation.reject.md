---
name: openstation.reject
description: Reject a task in review and mark it failed. $ARGUMENTS = task-name [reason...]. Use when user says "reject task", "fail task", "send back", or wants to reject work after review.
---

# Reject Task

Mark a task in `review` as `failed` by editing its frontmatter.

## Input

`$ARGUMENTS` — the task name, optionally followed by a reason.

Examples:
- `0010-refactor-commands-lifecycle`
- `0010-refactor-commands-lifecycle missing unit tests`

## Procedure

1. Parse the task name (first argument) and optional reason
   (remaining text) from `$ARGUMENTS`.
2. Locate the task file:
   - Try exact match: `artifacts/tasks/<task-name>.md`
   - If not found, try glob fallback: `artifacts/tasks/*-<task-name>.md`
   - If still not found, report an error and suggest using
     `openstation list` to find the correct name.
3. Read the task frontmatter. Verify `status: review` — refuse
   with an error if the task is not in review. Only
   `review` → `failed` is a valid transition for this command.
4. Set `status: failed` in the task frontmatter.
5. If a reason was provided, append to the task body:

   ```markdown

   ## Rejection

   **Date:** YYYY-MM-DD
   **Reason:** <reason text>
   ```

6. Confirm with: task name, reason (if any), and file path.
