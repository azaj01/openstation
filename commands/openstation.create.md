---
name: openstation.create
description: Create a new task spec in tasks/backlog/. $ARGUMENTS is the task description. Use when user says "add task", "new task", "create task", or describes work to be done.
---

# Create Task

Generate a new task spec from a description.

## Input

`$ARGUMENTS` — the task description (free text).

## Procedure

1. Take the description from `$ARGUMENTS`.
2. Generate a kebab-case slug from the description (short,
   descriptive, no more than 5 words).
3. Determine the next task ID:
   - Scan `artifacts/tasks/` for folders matching the pattern
     `NNNN-*` (4-digit prefix).
   - Extract the highest numeric prefix, increment by 1, and
     zero-pad to 4 digits.
   - If no prefixed folders exist, start at `0001`.
4. The folder name becomes `<ID>-<slug>` and the `name` field
   matches `<ID>-<slug>`.
5. **Interview** — ask the user (via AskUserQuestion) to refine
   the spec before writing anything. Do not create files until the
   interview is complete.

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

   d. **Agent & owner** — suggest an agent based on work type:
      `researcher` for research, `author` for authoring,
      `developer` for implementation. Ask the user to confirm or
      pick a different agent. Ask who verifies (default: `user`).

   e. **Decomposition** — if the requirements suggest multiple
      independent deliverables or span different domains, propose
      breaking the task into sub-tasks. List the suggested
      sub-tasks and ask the user to confirm. If accepted, create
      each sub-task using the standard sub-task convention
      (canonical folder + parent symlink, no bucket symlink).
      See `artifacts/specs/storage-query-layer.md` § 5 for the
      sub-task storage model.
      If the task is simple and self-contained, skip this step.

   f. **Ready to start?** — ask whether the task should go
      straight to `ready` (status: ready, symlink in
      `tasks/current/`) or stay in `backlog`.

6. Create `artifacts/tasks/<ID>-<slug>/index.md` using interview
   answers:

   ```markdown
   ---
   kind: task
   name: <ID>-<slug>
   status: <backlog or ready, from step 5f>
   agent: <from step 5d>
   owner: <from step 5d, default: user>
   created: <today's date YYYY-MM-DD>
   ---

   # <Title from description>

   ## Requirements

   <Approved requirements from step 5b>

   ## Verification

   - [ ] <Approved verification items from step 5c>
   ```

7. **Symlink placement** — depends on whether this is a sub-task:

   **Regular task** (no parent): create a bucket symlink:
   - If status is `backlog`:
     `tasks/backlog/<ID>-<slug> → ../../artifacts/tasks/<ID>-<slug>`
   - If status is `ready`:
     `tasks/current/<ID>-<slug> → ../../artifacts/tasks/<ID>-<slug>`

   **Sub-task** (parent specified in `$ARGUMENTS` or by user):
   - Add `parent: <parent-task-name>` to the frontmatter.
   - Do **not** create a bucket symlink.
   - Create a symlink inside the parent folder:
     `artifacts/tasks/<parent-slug>/<ID>-<slug> → ../<ID>-<slug>`
   - Add an entry to the parent's `## Subtasks` body section.

   See `artifacts/specs/storage-query-layer.md` § 5 for the
   full sub-task storage convention.

8. If sub-tasks were accepted in step 5e, create each sub-task
   now (folder, `index.md`, parent symlink) following the same
   template. Do **not** create bucket symlinks for sub-tasks.

9. Confirm the file was created and show the path.
