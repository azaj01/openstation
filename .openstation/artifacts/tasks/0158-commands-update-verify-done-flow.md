---
kind: task
name: 0158-commands-update-verify-done-flow
type: implementation
status: done
assignee: developer
owner: user
parent: "[[0155-add-verified-status-to-lifecycle]]"
created: 2026-03-17
---

# Commands: Update verify/done Flow

Update `/openstation.verify` and `/openstation.done` commands to
use the new `verified` status.

## Context

Depends on 0156 (docs) and 0157 (CLI transitions). The CLI must
accept `review → verified` before this task can be tested.

## Requirements

1. **`/openstation.verify`** (`commands/openstation.verify.md`) —
   when all verification items pass, transition the task from
   `review` to `verified` using `openstation status`. Remove the
   prompt to run `/openstation.done` — instead confirm the task
   is now `verified` and tell the user they can run
   `/openstation.done` when ready to accept.

2. **`/openstation.done`** (`commands/openstation.done.md`) —
   require task status to be `verified` (not `review`). If task
   is in `review`, tell the user to run `/openstation.verify`
   first. If task is in `verified`, proceed with completion.

3. **`openstation run --verify`** — no code change needed (it
   dispatches `/openstation.verify`), but verify it still works
   end-to-end with the new flow.

## Findings

Updated three files to implement the `verified` status in the
verify/done command flow:

1. **`commands/openstation.verify.md`** — step 9 (all-pass) now
   transitions `review → verified` via `openstation status`, then
   tells the user they can run `/openstation.done` when ready.
   Removed the old prompt that auto-ran `/openstation.done`.

2. **`commands/openstation.done.md`** — step 3 now requires
   `status: verified`. If the task is in `review`, it refuses
   with a message directing the user to run `/openstation.verify`
   first. Any other status also gets a clear rejection message.
   Manual fallback updated to `verified → done`.

3. **`skills/openstation-execute/SKILL.md`** — updated the
   command table (`Mark verified → done`) and the Agent Owner
   verification flow to run `/openstation.verify` before
   `/openstation.done`.

No code changes needed for `openstation run --verify` — it
dispatches `/openstation.verify` as the agent prompt, which
handles the `review → verified` transition per the updated
command.

## Verification

- [x] `/openstation.verify` transitions to `verified` on all-pass
- [x] `/openstation.verify` stays in `review` on any failure
- [x] `/openstation.done` accepts tasks in `verified` status
- [x] `/openstation.done` rejects tasks in `review` with helpful message
- [x] `openstation run --verify` works end-to-end
