---
name: openstation-execute
description: Teaches agents how to operate within Open Station — find tasks, execute work, update state, and store artifacts.
user-invocable: false
---

# Open Station Executor

You are operating within **Open Station**, a task management system
where all state is stored as markdown files with YAML frontmatter.

## Vault Structure

```
docs/              — Project documentation (lifecycle, task spec, README)
artifacts/         — Canonical artifact storage (source of truth)
  tasks/           —   Task files (NNNN-slug.md, single files, never moved)
  agents/          —   Agent specs (canonical location)
  research/        —   Research outputs
  specs/           —   Specifications & designs
agents/            — Agent discovery (symlinks → artifacts/agents/)
skills/            — Skills (including this one)
commands/          — User-invocable slash commands
```

All tasks are single files in `artifacts/tasks/` — e.g.,
`artifacts/tasks/0010-add-login-page.md`. There are no task
folders or bucket directories.

## CLI Tool

The `openstation` CLI provides scriptable access to the task vault.
Prefer it for discovery, inspection, and status transitions:

```
openstation list [--status <s>] [--assignee <name>]
openstation agents
openstation show <task>
openstation create "<description>" [--assignee <a>] [--owner <o>] [--status <s>] [--parent <p>]
openstation status <task> <new-status>
```

**Always call `openstation` directly** — never `python3 bin/openstation`
or any other indirect path. The binary is on `$PATH` during agent
sessions. Fall back to direct file reads/edits only if the command
is not found.

The `status` subcommand validates lifecycle transitions (see
`docs/lifecycle.md`) and updates frontmatter atomically.

## On Startup

1. Determine your agent name from your agent spec (`name` field in
   your frontmatter).
2. Read `docs/lifecycle.md` for lifecycle rules (statuses,
   transitions, ownership, artifact routing, guardrails).
3. Read `docs/task.spec.md` for task format (fields, naming,
   body structure, editing guardrails).
4. Run `openstation list --status ready --assignee <your-name>` to find
   assigned ready tasks. If the CLI is unavailable, fall back to
   scanning `artifacts/tasks/*.md` for files where `assignee` matches
   your name AND `status` is `ready`.
5. If multiple ready tasks exist, pick the one with the earliest
   `created` date.
6. If no ready tasks exist, report: "No ready tasks assigned to
   agent [name]." and stop.

## Executing a Task

### 1. Load Context

- Run `openstation show <task-name>` to load the full task spec
  (or read `artifacts/tasks/<task-name>.md` directly). Note
  requirements and verification checklist.
- Transition the task to in-progress:

  ```bash
  openstation status <task-name> in-progress
  ```

  **Fallback** — if the CLI is unavailable, edit `status: ready`
  → `status: in-progress` directly in the task frontmatter.

### 2. Evaluate Complexity (optional)

If the task is too large for a single pass, decompose it into
sub-tasks before starting work. Signs a task needs decomposition:

- Multiple independent deliverables
- Requirements span different domains or skills
- Estimated effort exceeds what one agent session can handle

If decomposition is needed, skip to step 6 (Create Sub-Tasks),
set `status: review`, and stop. The owner will promote the
sub-tasks for execution.

### 3. Work Through Requirements

- Follow the requirements section of the task spec.
- Apply your agent capabilities and constraints as defined in your
  agent spec.
- Break complex work into logical steps.

### 4. Store Artifacts

- Store artifacts in `artifacts/<category>/` (the canonical
  location) and record them in the task's `artifacts` frontmatter
  list using Obsidian wikilinks: `"[[artifacts/research/name]]"`.
- Set provenance fields (`agent`, `task`) on each artifact.
  Use wikilinks for the `task` field: `task: "[[0047-name]]"`.
- **Do NOT create discovery or promotion symlinks** (e.g.
  `agents/<name>.md`). `/openstation.done` handles promotion
  after verification.
- See `docs/storage-query-layer.md` §§ 3c–3d, 4 for
  routing and provenance conventions.

### 5. Record Findings

After completing the work, add a `## Findings` section to the
task file summarizing what you discovered or produced. Place it
between `## Requirements` and `## Verification`.

- Summarize key results — don't repeat the full artifact contents.
- Link to artifacts where relevant (e.g., "See
  `artifacts/research/topic-name.md`").
- Add `## Recommendations` after Findings if the task warrants
  actionable suggestions.
- Skip this step if the task produced no findings worth recording
  (e.g., pure implementation tasks with nothing to summarize
  beyond the code itself).

### 6. Create Sub-Tasks (if needed)

If a task requires decomposition:

1. Use `/openstation.create` to create each sub-task. This gives
   each sub-task its own canonical file in `artifacts/tasks/`.
2. Set `parent: "[[<current-task-name>]]"` in each sub-task's
   frontmatter (Obsidian wikilink format).
3. Add `"[[<sub-task-name>]]"` to the parent's `subtasks`
   frontmatter list and add an entry to the parent's
   `## Subtasks` body section.

See `docs/storage-query-layer.md` § 5 for the full
sub-task storage model and `docs/lifecycle.md` § "Sub-Tasks"
for blocking rules.

### 7. Update Documentation

If your changes affect behavior, conventions, or structures
documented in `docs/` or `CLAUDE.md`, update those files to
stay in sync.

When updating an artifact, check its `task` frontmatter field.
If the linked task has a `## Findings` section that conflicts
with your changes, update the Findings to match.

Skip this step if no documentation or findings are affected.

## Completing a Task

After working through all requirements:

1. Transition the task to review:

   ```bash
   openstation status <task-name> review
   ```

   **Fallback** — if the CLI is unavailable, edit
   `status: in-progress` → `status: review` directly in the
   task frontmatter.

2. Stop. The designated owner handles verification from here.

See `docs/lifecycle.md` § "Status Transitions" for guardrails.

## Verifying a Task (when you are the owner)

Only the designated owner may approve or reject a task. The
`owner` field in task frontmatter names the owner — either
an agent name or `user` (meaning a human verifies).

### Agent Owner

If `owner` is your agent name:

1. Read the task spec and its **Verification** section.
2. Check each verification item against the artifacts and changes
   produced.
3. If ALL items pass: run `/openstation.done <task-name>`.
4. If ANY item fails: set `status: failed` and document which
   items failed and why (add a note in the task body or as an
   artifact).

### User Owner

If `owner` is `user`, a human operator handles verification.
Do not verify on their behalf.
