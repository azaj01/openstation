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
Prefer it for discovery, inspection, and status transitions.
See `docs/cli.md` for the full reference (all flags, exit codes,
resolution rules).

**Always call `openstation` directly** — never `python3 bin/openstation`
or any other indirect path. The binary is on `$PATH` during agent
sessions. Fall back to direct file reads/edits only if the command
is not found.

Key commands:

| Command | Purpose |
|---------|---------|
| `openstation list --status ready --assignee <you>` | Find your tasks |
| `openstation show <task>` | Read a task spec |
| `openstation status <task> <new-status>` | Transition lifecycle state |
| `openstation create "<desc>" [--parent <p>]` | Create a task or sub-task |

## Available Slash Commands

These are user-invocable commands you may also use during
execution when appropriate:

| Command | Purpose |
|---------|---------|
| `/openstation.create` | Create a new task (with decomposition support) |
| `/openstation.list` | List tasks with filters |
| `/openstation.show` | Show full task details |
| `/openstation.ready` | Promote backlog → ready |
| `/openstation.done` | Mark verified → done (with artifact promotion) |
| `/openstation.reject` | Mark review → failed (with reason) |
| `/openstation.verify` | Verify a task's checklist against evidence |
| `/openstation.update` | Edit task metadata (not status) |
| `/openstation.progress` | Append a timestamped progress entry to a task |

## Worktree Awareness

When running in a **linked worktree** (no local `.openstation/`
or `agents/` markers), the vault lives in the main repo, not
your working directory.

- `artifacts/`, `docs/`, and `commands/` are in the main repo
- **Always use CLI commands** (`openstation show/list/create/status`)
  — they resolve the correct root automatically
- **Do NOT use filesystem checks** (`ls`, `find`, `git status`)
  to verify task operations — use `openstation show <task>` instead
- The `info:` line from `create`/`status` shows the absolute path
  of the modified file, confirming which vault was used
- The run prompt includes an artifact location hint when you are
  in linked mode

See `docs/worktrees.md` for full details on primary vs linked
modes and how `find_root()` resolves the vault.

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
- If the task has a `parent` field, read the parent task for
  background context.
- Transition the task to in-progress:

  ```bash
  openstation status <task-name> in-progress
  ```

  **Fallback** — if the CLI is unavailable, edit `status: ready`
  → `status: in-progress` directly in the task frontmatter.

### 2. Evaluate Complexity (optional)

If the task is too large for a single pass, decompose it into
sub-tasks before starting work. Decompose when **any** of these
are true:

- Requirements list **6+ independent items** (count them)
- Work spans **2+ agent roles** (e.g., code + docs, spec + research)
- Task requires creating or modifying **4+ files**
- Requirements reference **2+ unrelated domains** (e.g., CLI + skills + lifecycle)

If decomposition is needed, skip to step 8 (Create Sub-Tasks),
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
  **Every produced artifact must appear in the `artifacts` list** —
  this is how verification and promotion find them.
- Set provenance fields (`agent`, `task`) on each artifact.
  Use wikilinks for the `task` field: `task: "[[0047-name]]"`.
- **Do NOT create discovery or promotion symlinks** (e.g.
  `agents/<name>.md`). `/openstation.done` handles promotion
  after verification.
- See `docs/storage-query-layer.md` §§ 3c–3d, 4 for
  routing and provenance conventions.

### 5. Record Findings

After completing the work, add a `## Findings` section to the
task file summarizing what you produced. This is required for
all task types.

Content varies by type:
- **research**: Key results, sources, confidence levels
- **spec**: Design summary, trade-offs, key decisions
- **implementation**: What was built/changed, design decisions,
  gotchas
- **documentation**: What was written/updated, scope
- **feature**: What was built, how it works, notable decisions

Lead with conclusions. Link to artifacts. Keep it concise —
a reviewer should understand the work without reading every
file you touched.

### 6. Flag Downstream Work (if applicable)

If your work introduced any of the following, add a
`## Downstream` section to the task file:

- Behavior changes that need documentation updates
- New conventions or patterns others should know about
- Gaps you noticed but didn't address (out of scope)
- Follow-up tasks that would improve the result

Each item is a bullet describing what needs to happen and why.
The reviewer will decide whether to create tasks for them.

Omit this section if there is no downstream work to flag.

### 7. Record Progress

Use `/openstation.progress <task-name> <message>` to append a
timestamped progress entry. The command handles format, placement,
and append-only rules. See the command for full details.

- Include the log path (`artifacts/logs/<task-name>.jsonl`) if
  your session is being logged
- Add your entry before transitioning to `review` or `failed`

### 8. Create Sub-Tasks (if needed)

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

### 9. Update Documentation

If your changes affect behavior, conventions, or structures
documented in `docs/` or `CLAUDE.md`, update those files to
stay in sync.

When updating an artifact, check its `task` frontmatter field.
If the linked task has a `## Findings` section that conflicts
with your changes, update the Findings to match.

Skip this step if no documentation or findings are affected.

## Completing a Task

After working through all requirements:

1. Self-check: review the `## Verification` items and confirm
   your work addresses each one. Do **not** check the boxes
   yourself — that is the owner's job via `/openstation.verify`.
2. Transition the task to review:

   ```bash
   openstation status <task-name> review
   ```

   **Fallback** — if the CLI is unavailable, edit
   `status: in-progress` → `status: review` directly in the
   task frontmatter.

3. Stop. The designated owner handles verification from here.

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
3. If ALL items pass: run `/openstation.verify <task-name>` to
   transition to `verified`, then `/openstation.done <task-name>`
   to complete the task.
4. If ANY item fails: set `status: failed` and document which
   items failed and why (add a note in the task body or as an
   artifact).

### User Owner

If `owner` is `user`, a human operator handles verification.
Do not verify on their behalf.
