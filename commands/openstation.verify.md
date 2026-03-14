---
name: openstation.verify
description: Verify a task in review status. $ARGUMENTS = task name. Use when user says "verify task", "check task", "review task", or wants to verify work before marking done.
---

# Verify Task

Verify a task in `review` status by checking each item in its
`## Verification` section against the actual implementation.

## Input

`$ARGUMENTS` — the task name (ID-prefixed or slug).

Example: `0042-add-login-page` or `add-login-page`

## Procedure

1. Parse the task name from `$ARGUMENTS`.
2. Resolve the task file per `docs/task.spec.md` § Task Resolution.
3. Read the full task file. Verify `status: review` — refuse
   with an error if the task is not in review.
4. Extract the `## Verification` section. Parse each checklist
   item (`- [ ] ...`) into a list of verification criteria.
5. For **each** verification item, gather evidence:
   - Read referenced files, code, tests, or artifacts mentioned
     in the task requirements or verification items.
   - Use Glob/Grep to locate relevant files if paths are not
     explicit (e.g., search for filenames mentioned in criteria).
   - Check that artifacts listed in the `artifacts` frontmatter
     field actually exist.
   - Inspect actual file contents — do not rely on self-reported
     claims in the task body.
6. Determine pass/fail for each item based on the evidence
   gathered. An item passes only if concrete evidence confirms it.
7. **Update the task file** — for each passing item, change
   `- [ ]` to `- [x]` in the `## Verification` section. Leave
   failing items unchecked.
8. Present a **verification report** to the user:

   ```
   ## Verification Report: <task-name>

   | # | Criterion | Result | Evidence |
   |---|-----------|--------|----------|
   | 1 | <item>    | ✅ PASS | <brief evidence> |
   | 2 | <item>    | ❌ FAIL | <what's missing or wrong> |
   ```

9. If **all items pass**:
   - Tell the user all verification criteria passed.
   - Ask the user to confirm before proceeding.
   - On confirmation, run `/openstation.done <task-name>` to
     complete the task (handles status transition and artifact
     promotion).

10. If **any items fail**:
    - Report which items failed and why.
    - Do **not** transition the task status.
    - Suggest what needs to be fixed before re-verification.
