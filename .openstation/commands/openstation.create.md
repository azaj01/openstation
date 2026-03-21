---
name: openstation.create
description: Create a new task spec in artifacts/tasks/. $ARGUMENTS is the task description. Use when user says "add task", "new task", "create task", or describes work to be done.
---

# Create Task

Generate a new task spec from a description.

## Input

`$ARGUMENTS` — the task description (free text).

## Procedure

1. Take the description from `$ARGUMENTS`.

2. **Round 1 — Draft spec.** From the description, auto-infer
   everything and present a complete draft in one message. Do not
   create files yet.

   Present:

   - **Type** — infer from keywords in the description. Use
     `type` values: `feature`, `research`, `spec`,
     `implementation`, or `documentation`.
   - **Requirements** — expand the description into concrete,
     testable requirements.
   - **Verification** — derive checklist items from the
     requirements.
   - **Agent & owner** — suggest the best agent based on the
     inferred type. Default owner: `user`.
   - **Status** — recommend `ready` or `backlog` based on
     whether requirements are concrete enough to execute.
   - **Decomposition** (only if warranted) — if requirements
     clearly span multiple independent domains, suggest sub-tasks
     inline. Otherwise omit entirely. Apply the sizing heuristics
     and split-vs-keep criteria from `docs/task.spec.md`
     § Decomposition Guidelines.

   End the message with: **"Approve, or tell me what to change."**

3. **Round 2 — Iterate only if needed.** If the user approves,
   proceed to step 4 immediately. If they request changes, apply
   them, present the updated draft, and ask again. Repeat until
   approved.

4. **Create the task file.** Run `openstation agents list` to
   confirm the agent name, then create via the CLI with `--body`
   to include the full body in one step:

   ```bash
   openstation create "<description>" \
     --assignee <from draft> \
     --owner <from draft, default: user> \
     --status <backlog or ready, from draft> \
     [--parent <parent-task-name>] \
     --body "## Requirements

   <Approved requirements from draft>

   ## Verification

   - [ ] <Approved verification items from draft>"
   ```

   The CLI handles ID assignment, slug generation, atomic file
   creation, parent linking, and body content — no manual editing
   needed.

   The command prints the created task name (e.g., `0055-my-task`).

   **Manual fallback** — if `openstation create` is unavailable:
   - Scan `artifacts/tasks/` for the highest `NNNN-*.md` prefix,
     increment by 1, zero-pad to 4 digits.
   - Generate a kebab-case slug (max 5 words).
   - Create `artifacts/tasks/<ID>-<slug>.md` directly.

5. **Sub-task handling** — if sub-tasks were included in the
   approved draft, create each sub-task using:

   ```bash
   openstation create "<sub-task description>" \
     --assignee <agent> --owner <owner> \
     --parent <parent-task-name> \
     --body "## Requirements

   <Sub-task requirements>

   ## Verification

   - [ ] <Sub-task verification items>"
   ```

   The CLI automatically adds `parent` frontmatter to the
   sub-task, appends to the parent's `subtasks` list, and
   includes the full body — no manual editing needed.

   Add an entry to the parent's `## Subtasks` body section.

   **Manual fallback** — if the CLI is unavailable, create each
   sub-task file manually with `parent: "[[<parent>]]"`
   frontmatter and update the parent's `subtasks` list.

6. Confirm the file(s) were created and show the path(s).
