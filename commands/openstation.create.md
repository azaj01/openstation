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
5. Create `artifacts/tasks/<ID>-<slug>/index.md` with this structure:

   ```markdown
   ---
   kind: task
   name: <ID>-<slug>
   status: backlog
   agent:
   owner: manual
   created: <today's date YYYY-MM-DD>
   ---

   # <Title from description>

   ## Requirements

   <Expand the description into concrete requirements>

   ## Verification

   - [ ] <Verification items derived from requirements>
   ```

6. **Symlink placement** — depends on whether this is a sub-task:

   **Regular task** (no parent): create a bucket symlink:
   `tasks/backlog/<ID>-<slug> → ../../artifacts/tasks/<ID>-<slug>`

   **Sub-task** (parent specified in `$ARGUMENTS` or by user):
   - Add `parent: <parent-task-name>` to the frontmatter.
   - Do **not** create a bucket symlink.
   - Create a symlink inside the parent folder:
     `artifacts/tasks/<parent-slug>/<ID>-<slug> → ../<ID>-<slug>`
   - Add an entry to the parent's `## Subtasks` body section.

   See `docs/lifecycle.md` § "Sub-Tasks" and `docs/task.spec.md`
   § "Sub-tasks" for the full convention.

7. Ask the user:
   - Should an agent be assigned? If yes, which one?
   - Should the status be changed from `backlog` to `ready`?
     If yes, move the symlink to `tasks/current/` (regular tasks
     only — sub-tasks never get bucket symlinks).
8. Update the frontmatter with their answers.
9. Confirm the file was created and show the path.
