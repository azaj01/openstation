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

   Run `openstation agents` to get the agent list, then present:

   - **Type** — infer from keywords in the description. Use
     `type` values: `feature`, `research`, `spec`,
     `implementation`, or `documentation`.
   - **Requirements** — expand the description into concrete,
     testable requirements.
   - **Verification** — derive checklist items from the
     requirements.
   - **Agent & owner** — suggest the best agent from the list
     based on the inferred type. Default owner: `user`.
   - **Status** — recommend `ready` or `backlog` based on
     whether requirements are concrete enough to execute.
   - **Decomposition** (only if warranted) — if requirements
     clearly span multiple independent domains, suggest sub-tasks
     inline. Otherwise omit entirely.

   End the message with: **"Approve, or tell me what to change."**

3. **Round 2 — Iterate only if needed.** If the user approves,
   proceed to step 4 immediately. If they request changes, apply
   them, present the updated draft, and ask again. Repeat until
   approved.

4. **Create the task file** using the CLI:

   ```bash
   openstation create "<description>" \
     --assignee <from draft> \
     --owner <from draft, default: user> \
     --status <backlog or ready, from draft> \
     [--parent <parent-task-name>]
   ```

   The CLI handles ID assignment, slug generation, atomic file
   creation, and parent linking (appends to the parent's
   `subtasks` frontmatter list).

   The command prints the created task name (e.g., `0055-my-task`).

   **Manual fallback** — if `openstation create` is unavailable:
   - Scan `artifacts/tasks/` for the highest `NNNN-*.md` prefix,
     increment by 1, zero-pad to 4 digits.
   - Generate a kebab-case slug (max 5 words).
   - Create `artifacts/tasks/<ID>-<slug>.md` directly.

5. **Edit the generated file** — replace the template body with
   the approved draft content:

   ```markdown
   ---
   kind: task
   name: <ID>-<slug>
   status: <backlog or ready>
   assignee: <agent>
   owner: <owner>
   created: <today's date>
   ---

   # <Title from description>

   ## Requirements

   <Approved requirements from draft>

   ## Verification

   - [ ] <Approved verification items from draft>
   ```

6. **Sub-task handling** — if sub-tasks were included in the
   approved draft, create each sub-task using:

   ```bash
   openstation create "<sub-task description>" \
     --assignee <agent> --owner <owner> \
     --parent <parent-task-name>
   ```

   The CLI automatically adds `parent` frontmatter to the
   sub-task and appends to the parent's `subtasks` list.
   Edit each sub-task's body with its specific requirements.

   Add an entry to the parent's `## Subtasks` body section.

   **Manual fallback** — if the CLI is unavailable, create each
   sub-task file manually with `parent: "[[<parent>]]"`
   frontmatter and update the parent's `subtasks` list.

7. Confirm the file(s) were created and show the path(s).
