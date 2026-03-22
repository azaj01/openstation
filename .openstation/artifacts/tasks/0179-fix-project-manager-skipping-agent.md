---
kind: task
name: 0179-fix-project-manager-skipping-agent
type: documentation
status: ready
assignee: author
owner: user
created: 2026-03-20
---

# Fix Project-Manager Skipping Agent List Validation Before Assignment

## Requirements

The `/openstation.create` command (step 4) requires running
`openstation agents list` to confirm the agent name before
creating the task. The project-manager agent skips this step,
assigning agents from memory without validation.

Fix the project-manager agent spec to explicitly require agent
list validation before any task assignment — both during
`/openstation.create` and when assigning tasks outside the
create flow.

1. Update the project-manager agent spec to include a constraint:
   always run `openstation agents list` before assigning an agent
   to a task
2. Verify the constraint is consistent with the existing create
   command procedure (step 4)

## Verification

- [ ] Project-manager agent spec includes a constraint requiring `openstation agents list` before agent assignment
- [ ] Constraint covers both `/openstation.create` flow and direct task assignment
