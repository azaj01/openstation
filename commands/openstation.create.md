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
2. **Interview** — ask the user (via AskUserQuestion) to refine
   the spec before creating anything. Do not create files until
   the interview is complete.

   a. **What type of work?** — ask the user to classify:
      research, authoring (specs/docs), implementation, or other.
      This informs the agent suggestion in step (d).

   b. **Requirements** — expand the description into a concrete
      requirements draft. Present the draft to the user and ask if
      anything is missing or needs changing. Iterate (re-ask) until
      the user approves the requirements.

   c. **Verification criteria** — propose verification items
      derived from the approved requirements. Ask the user to
      confirm or adjust.

   d. **Agent & owner** — run `openstation agents` to list available
      agents, then suggest one based on work type: `researcher` for
      research, `architect` for specs, `author` for prompts/docs,
      `developer` for implementation. Present the agent list so the
      user can confirm
      or pick a different agent. Ask who verifies (default: `user`).

   e. **Decomposition** — if the requirements suggest multiple
      independent deliverables or span different domains, propose
      breaking the task into sub-tasks. List the suggested
      sub-tasks and ask the user to confirm. If accepted, each
      sub-task will be created as a separate file with `parent`
      frontmatter. See `docs/storage-query-layer.md` § 5 for
      the sub-task storage model.
      If the task is simple and self-contained, skip this step.

   f. **Ready to start?** — ask whether the task should go
      straight to `ready` (status: ready) or stay in `backlog`.

3. **Create the task file** using the CLI:

   ```bash
   openstation create "<description>" \
     --agent <from step 2d> \
     --owner <from step 2d, default: user> \
     --status <backlog or ready, from step 2f> \
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

4. **Edit the generated file** — replace the template body with
   the approved interview content:

   ```markdown
   ---
   kind: task
   name: <ID>-<slug>
   status: <backlog or ready>
   agent: <agent>
   owner: <owner>
   created: <today's date>
   ---

   # <Title from description>

   ## Requirements

   <Approved requirements from step 2b>

   ## Verification

   - [ ] <Approved verification items from step 2c>
   ```

5. **Sub-task handling** — if sub-tasks were accepted in step 2e,
   create each sub-task using:

   ```bash
   openstation create "<sub-task description>" \
     --agent <agent> --owner <owner> \
     --parent <parent-task-name>
   ```

   The CLI automatically adds `parent` frontmatter to the
   sub-task and appends to the parent's `subtasks` list.
   Edit each sub-task's body with its specific requirements.

   Add an entry to the parent's `## Subtasks` body section.

   **Manual fallback** — if the CLI is unavailable, create each
   sub-task file manually with `parent: "[[<parent>]]"`
   frontmatter and update the parent's `subtasks` list.

6. Confirm the file(s) were created and show the path(s).
