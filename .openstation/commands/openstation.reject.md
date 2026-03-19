---
name: openstation.reject
description: Reject a task in review and mark it failed. $ARGUMENTS = task-name [reason...]. Use when user says "reject task", "fail task", "send back", or wants to reject work after review.
---

# Reject Task

Mark a task in `review` as `failed`.

## Input

`$ARGUMENTS` — the task name, optionally followed by a reason.

Examples:
- `0010-refactor-commands-lifecycle`
- `0010-refactor-commands-lifecycle missing unit tests`

## Procedure

1. Parse the task name (first argument) and optional reason
   (remaining text) from `$ARGUMENTS`.
2. Resolve the task file per `docs/task.spec.md` § Task Resolution.
3. Read the task frontmatter. Verify `status: review` — refuse
   with an error if the task is not in review. Only
   `review` → `failed` is a valid transition for this command.
4. Set the status using the CLI:

   ```bash
   openstation status <task-name> failed
   ```

   **Manual fallback** — if the CLI is unavailable, edit
   `status: review` → `status: failed` directly in the task
   frontmatter.

5. If a reason was provided, append to the task body:

   ```markdown

   ## Rejection

   **Date:** YYYY-MM-DD
   **Reason:** <reason text>
   ```

6. Confirm with: task name, reason (if any), and file path.
