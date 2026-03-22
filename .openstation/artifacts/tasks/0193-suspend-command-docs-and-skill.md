---
kind: task
name: 0193-suspend-command-docs-and-skill
type: feature
status: done
assignee: author
owner: user
parent: "[[0196-task-suspension-backward-transitions-from]]"
created: 2026-03-21
---

# Suspend Command, Docs, And Skill Updates — Slash Command, Lifecycle, Task Spec,

## Context

Spec: `[[artifacts/specs/task-suspension-model]]` (from task
`[[0188-research-task-suspension-model-design]]`). Depends on
`[[0189-cli-suspend-subcommand-add-openstation]]` for the CLI
subcommand and transition table.

## Requirements

Create the `/openstation.suspend` slash command and update all
docs and skills to reflect the new suspension model.

### 1. Slash Command — `commands/openstation.suspend.md`

User-friendly entry point for suspending tasks. The git workflow
is handled by hooks (see 0189), so the slash command is thin:

1. Parse args: `<task> [ready|backlog] ["reason"]`
2. Resolve task, validate `status: in-progress`
3. Call `openstation status <task> <target>` (triggers the
   suspend hook which handles branch creation and `## Suspended`)
4. Print confirmation

### 2. Doc Updates

**`docs/lifecycle.md`** — add two transition lines:
```
in-progress → ready      (suspend — /openstation.suspend)
in-progress → backlog    (suspend — /openstation.suspend backlog)
```
Add suspend to the guardrails section.

**`docs/task.spec.md`** — add `## Suspended` to canonical
section order (between Progress and Findings).

**`docs/cli.md`** — document that `openstation status` now
supports `in-progress → ready/backlog` transitions.

### 3. Execute Skill Update

Add a note to `skills/openstation-execute/` about `## Suspended`
section discovery per spec § 6.

## Findings

Created `/openstation.suspend` slash command and updated all
docs and skills for the suspension model:

1. **`commands/openstation.suspend.md`** — thin command that
   parses args, validates `in-progress` status, delegates to
   `openstation status`, and confirms. No git logic — that's
   handled by hooks per 0189.

2. **`docs/lifecycle.md`** — added two transition lines
   (`in-progress → ready`, `in-progress → backlog`) and a
   guardrail entry for `/openstation.suspend`.

3. **`docs/task.spec.md`** — added `## Suspended` to canonical
   section order (position 6, between Progress and Findings)
   and to the optional sections table.

4. **`docs/cli.md`** — added suspend transitions to the valid
   transitions diagram in the `status` command section.

5. **`skills/openstation-execute/SKILL.md`** — added
   `## Suspended` discovery note in "Load Context" step and
   `/openstation.suspend` to the slash commands table.

## Progress

- 2026-03-21: Created slash command, updated lifecycle.md, task.spec.md, cli.md, and execute skill per spec requirements.

## Verification

- [x] `commands/openstation.suspend.md` exists with correct arg parsing
- [x] Slash command delegates to `openstation status` (no git logic)
- [x] `docs/lifecycle.md` includes both new transitions and guardrail entry
- [x] `docs/task.spec.md` lists `## Suspended` in canonical section order
- [x] `docs/cli.md` documents the new transitions
- [x] Execute skill mentions `## Suspended` discovery

## Verification Report

*Verified: 2026-03-21*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `commands/openstation.suspend.md` exists with correct arg parsing | PASS | File exists with `<task-name> [ready|backlog] ["reason text"]` parsing, examples, and usage error handling |
| 2 | Slash command delegates to `openstation status` (no git logic) | PASS | Step 4 calls `openstation status`, no git commands; states "git workflow handled by lifecycle hooks" |
| 3 | `docs/lifecycle.md` includes both new transitions and guardrail entry | PASS | Lines 24-25: both transitions; lines 69-71: guardrail for `/openstation.suspend` |
| 4 | `docs/task.spec.md` lists `## Suspended` in canonical section order | PASS | Position 6 between Progress and Findings; also in optional sections table |
| 5 | `docs/cli.md` documents the new transitions | PASS | `status` command valid transitions diagram includes `in-progress → ready/backlog (suspend)` |
| 6 | Execute skill mentions `## Suspended` discovery | PASS | SKILL.md lines 112-115: discovery with branch/diff guidance; line 63: command in slash commands table |

### Summary

6 passed, 0 failed. All verification criteria met.
