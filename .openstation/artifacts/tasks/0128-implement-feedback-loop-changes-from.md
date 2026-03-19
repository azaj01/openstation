---
kind: task
name: 0128-implement-feedback-loop-changes-from
type: implementation
status: done
assignee: author
owner: user
parent: "[[0104-improve-feedback-loop-between-assignee]]"
created: 2026-03-13
---

# Implement feedback loop changes

Implement all changes from the 0104 feedback loop spec, including
the Progress convention and the new `/openstation.progress` command.

## Requirements

### 1. Execute skill (`skills/openstation-execute/skill.md`)

- Update step 5 (Record Findings): remove the "skip for pure
  implementation tasks" escape hatch, add type-specific guidance
- Add new step: **Record Progress** — append a progress entry
  under `## Progress` summarizing what was done. Heading format:
  `### YYYY-MM-DD HH:MM–HH:MM — <agent> (log: <path>)` where
  the times are task start and end, and the log path points to
  the session log in `artifacts/logs/` (if available)
- Add new step: **Flag Downstream Work** — add `## Downstream`
  if follow-up work was identified
- Renumber subsequent steps

### 2. Task spec (`docs/task.spec.md`)

- Move `## Findings` from Optional to Required Sections with
  type-specific guidance table
- Add `## Progress` to Optional Sections (append-only, written
  during execution)
- Add `## Downstream` to Optional Sections
- Update Progressive Disclosure table
- Update canonical section ordering

### 3. Lifecycle (`docs/lifecycle.md`)

- Add Pre-Review Checklist under `in-progress → review`:
  requirements addressed, findings written, progress entry added,
  downstream flagged (if any), artifacts stored

### 4. `/openstation.progress` command

Create `commands/openstation.progress.md` — a slash command that:
- Takes `$ARGUMENTS` as `<task-name> <message>`
- Locates the task file (exact match or prefix match)
- Appends a `### YYYY-MM-DD HH:MM–HH:MM — <agent> (log: <path>)`
  entry under `## Progress` (creates the section if it doesn't
  exist). Times and log path are optional (omit when not available)
- The agent name comes from the agent spec if running as an agent,
  or defaults to `user`
- Never modifies existing progress entries

## Progress

### 2026-03-13 — author

Implemented all four requirements from the feedback loop spec.
Updated the execute skill with Record Progress (step 7), Flag
Downstream (step 6), and type-specific Findings guidance (step 5).
Updated task.spec.md with Findings as required, Progress and
Downstream as optional, canonical section ordering, and progressive
disclosure changes. Added pre-review checklist to lifecycle.md.
Created the `/openstation.progress` command.

## Findings

Implemented all changes specified in the assignee-reviewer feedback
loop spec (Decisions 1-6) across four files:

- **Execute skill** (`skills/openstation-execute/SKILL.md`): Replaced
  step 5 with type-specific Findings guidance (no more "skip for
  implementation" escape hatch). Added step 6 (Flag Downstream Work)
  and step 7 (Record Progress). Renumbered former steps 6-7 to 8-9.

- **Task spec** (`docs/task.spec.md`): Moved `## Findings` to
  Required Sections with a type-guidance table. Added `## Progress`
  and `## Downstream` to Optional Sections. Updated Progressive
  Disclosure table (Completed stage now shows all types). Added
  canonical section ordering subsection.

- **Lifecycle** (`docs/lifecycle.md`): Added Pre-Review Checklist
  subsection under Status Transitions with five gate items
  (requirements, findings, downstream, progress, artifacts).

- **Progress command** (`commands/openstation.progress.md`): New
  slash command accepting `<task-name> <message>`, resolving task
  files, determining author (agent name or `user`), and appending
  timestamped entries to `## Progress` (creating the section if
  absent). Follows existing command conventions (frontmatter,
  procedure steps, input format).

## Rejection

Progress heading format is missing task time and session log
reference. The heading must include start–end times and a log
path when available. Updated requirements reflect the new format:
`### YYYY-MM-DD HH:MM–HH:MM — <agent> (log: <path>)`

## Verification

- [ ] Execute skill has Record Progress and Flag Downstream steps
- [ ] Execute skill requires Findings for all task types with type-specific guidance
- [ ] Progress heading format includes date, time range, agent name, and log path
- [ ] `docs/task.spec.md` has `## Findings` as required, `## Progress` and `## Downstream` as optional
- [ ] `docs/lifecycle.md` has pre-review checklist
- [ ] `commands/openstation.progress.md` exists and follows command conventions
- [ ] Progress command appends entries, never overwrites
