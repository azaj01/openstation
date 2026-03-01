---
kind: task
name: 0017-add-review-task-command
status: backlog
agent:
owner: manual
created: 2026-02-28
---

# Add Review Task Command

## Requirements

- Create a new slash command (`/openstation.review`) that lists
  tasks in `review` status awaiting owner input
- The command should display each review task with its ID, name,
  agent, owner, and a summary of what needs review (artifacts
  produced, verification checklist)
- Allow the owner to approve (transition to `done`, move symlink
  to `tasks/done/`) or reject (transition to `failed`, keep in
  `tasks/current/`) directly from the command output
- Approval should verify that all `## Verification` checklist
  items are addressed before allowing the `done` transition
- Rejection should require a reason that gets appended to the
  task spec as a `## Rejection` section
- Follow existing command conventions in `commands/` (markdown
  format, procedure-based structure)

## Verification

- [ ] `commands/openstation.review.md` exists and follows vault command conventions
- [ ] Command lists only tasks with `status: review`
- [ ] Approve flow moves symlink to `tasks/done/` and sets `status: done`
- [ ] Reject flow sets `status: failed` and appends rejection reason to spec
- [ ] Approval checks verification items before completing
- [ ] Command is discoverable via `.claude/commands` symlink chain
