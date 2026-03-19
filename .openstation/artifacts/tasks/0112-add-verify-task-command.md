---
kind: task
name: 0112-add-verify-task-command
type: feature
status: done
assignee: author
owner: user
created: 2026-03-11
---

# Add `/openstation.verify` Command

## Requirements

1. Create `commands/openstation.verify.md` — a Claude Code slash command (`/openstation.verify <task>`) that verifies a task in `review` status.
2. The command should:
   - Resolve the task file (same resolution as `/openstation.done`)
   - Confirm the task is in `review` status
   - Read the `## Verification` section and check each item against the actual implementation
   - For each checklist item: inspect relevant code, tests, or artifacts to determine pass/fail
   - Present a verification report with pass/fail per item
   - If all items pass, ask the user to confirm, then run `openstation status <task> done`
   - If any items fail, report which failed and why, do not transition status
3. The command should read related files (code changes, test files, artifacts referenced in the task) to make verification evidence-based, not just self-reported.
4. Follow existing command conventions (YAML frontmatter with `name` and `description`, `## Procedure` section).

## Verification

- [ ] `commands/openstation.verify.md` exists with valid frontmatter
- [ ] Command resolves task and checks `review` status
- [ ] Command reads `## Verification` checklist items
- [ ] Command inspects actual code/tests/artifacts for evidence
- [ ] Command presents pass/fail report before transitioning
- [ ] Command only marks done when all items pass and user confirms
- [ ] Command follows existing `/openstation.*` conventions
