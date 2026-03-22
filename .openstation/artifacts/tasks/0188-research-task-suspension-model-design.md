---
kind: task
name: 0188-research-task-suspension-model-design
type: feature
status: done
assignee: architect
owner: user
artifacts:
  - "[[artifacts/specs/task-suspension-model]]"
parent: "[[0196-task-suspension-backward-transitions-from]]"
created: 2026-03-21
---

# Research Task Suspension Model — Design Backward Transitions From In-Progress

## Requirements

Design the `/openstation.suspend` command and supporting
lifecycle changes that allow sending tasks backward from
`in-progress` to `ready` or `backlog`.

### Design Decisions (settled)

1. **Transitions:** `in-progress → ready` and
   `in-progress → backlog`. No backward transitions from
   `review` (out of scope for now).

2. **Work preservation:** The suspend command asks the user
   whether to save work. If yes — create a branch and commit
   task-related changes (same pattern as `bin/hooks/auto-commit`
   which runs on `*→done`). The branch name should reference
   the task (e.g., `suspend/0042-slug`). This gives a clean
   diff to resume from later.

3. **Command:** New `/openstation.suspend` command.
   - Target status argument: `ready` (default) or `backlog`
   - Optional reason argument: `openstation suspend <task> [ready|backlog] ["reason"]`
   - Prompts user: "Save uncommitted work to a branch? (y/n)"
   - If yes: creates branch, auto-commits related changes
     (reuse `bin/hooks/auto-commit` logic), switches back to
     the original branch
   - Updates task frontmatter status
   - Appends a `## Suspended` entry to the task body with:
     reason, date, branch reference (if work was saved)

4. **Agent discovery of prior work:** The `## Suspended`
   section in the task body contains the reason and branch
   reference. When an agent picks up a resumed task, it reads
   the task file and finds prior work via the branch reference
   and any existing `## Progress` entries.

5. **Guardrails:** No hard requirements — reason is optional
   (passed as argument or omitted), saving work is prompted.

### Output

A spec artifact (`artifacts/specs/task-suspension-model.md`)
covering:
- New lifecycle transitions added to `docs/lifecycle.md`
- `/openstation.suspend` command spec (args, flags, behavior)
- Work preservation flow (branch creation, auto-commit reuse)
- Task body format for `## Suspended` section
- CLI `openstation suspend` subcommand spec

## Findings

Produced `artifacts/specs/task-suspension-model.md` — a full
design spec covering all seven verification items.

**Key decisions:**

- Two transitions added: `in-progress → ready` (default) and
  `in-progress → backlog`. No conflicts with existing transitions.
- `/openstation.suspend` command prompts user to save work, creates
  a `suspend/<task-name>` branch, auto-commits via `claude -p`
  (same pattern as `bin/hooks/auto-commit` but with `wip()` prefix),
  and switches back to the original branch.
- CLI `openstation suspend` subcommand handles status transition
  and `## Suspended` section append. Git workflow is in the slash
  command only.
- `## Suspended` section uses Date/Target/Reason/Branch fields.
  Multiple suspensions append with `---` separators.
- Agents discover prior work naturally — the execute skill already
  reads the full task file, so `## Suspended` is found during
  context loading. A small note addition to the skill is recommended.
- Assignee is preserved on suspend (not cleared), matching existing
  `ready → backlog` behavior.
- Hooks fire normally on the new transitions — no special handling.

## Downstream

- `docs/lifecycle.md` needs the two new transition lines added
- `docs/task.spec.md` needs `## Suspended` in canonical section order
- `docs/cli.md` needs the `suspend` subcommand reference
- `skills/openstation-execute/` needs a note about `## Suspended`
- Implementation tasks needed for the CLI subcommand and slash command

## Progress

- 2026-03-21: Produced spec at `artifacts/specs/task-suspension-model.md`.
  Covers lifecycle transitions, command interface, work preservation
  flow, `## Suspended` format, CLI subcommand, agent discovery, and
  compatibility analysis.

## Verification

- [ ] Spec artifact exists at `artifacts/specs/task-suspension-model.md`
- [ ] New transitions (`in-progress → ready`, `in-progress → backlog`) are defined
- [ ] `/openstation.suspend` command interface is fully specified (args, prompts, behavior)
- [ ] Work preservation flow is documented (branch naming, auto-commit reuse, switch-back)
- [ ] `## Suspended` section format is defined (reason, date, branch ref)
- [ ] Agent discovery of prior work via `## Suspended` is addressed
- [ ] No conflicts with existing lifecycle transitions in `docs/lifecycle.md`
