---
kind: task
name: 0127-update-feedback-loop-spec-with
type: spec
status: done
assignee: author
owner: user
parent: "[[0104-improve-feedback-loop-between-assignee]]"
created: 2026-03-13
---

# Update feedback loop spec with Progress convention

Add Decision 6 to `artifacts/specs/assignee-reviewer-feedback-loop.md`
defining the `## Progress` section convention.

## Requirements

1. Add **Decision 6: Append-only Progress section** to the spec:
   - `## Progress` is an optional section where agents record
     timestamped work entries during execution
   - Each entry is a `### YYYY-MM-DD — <agent-name>` heading
     followed by a short paragraph summarizing what was done
   - Entries are **append-only** — previous entries are never
     modified or removed
   - Agents should add an entry before transitioning to `review`
     or `failed`
   - The section accumulates across multiple runs (tasks may be
     executed more than once)

2. Add corresponding changes to the **Changes Required** section:
   - `docs/task.spec.md`: add `## Progress` to Optional Sections
   - Execute skill: add a "Record Progress" step
   - `docs/lifecycle.md`: add "progress entry written" to the
     pre-review checklist

3. Add a note about the new `/openstation.progress` command that
   will be created to make appending entries easy for users and
   agents outside the execute skill flow.

## Findings

Added Decision 6 (Append-only Progress section) to the feedback
loop spec with the following changes:

- **Decision 6 block** — full rationale, format definition with
  example, append-only rules, and status set to "Decided"
- **Changes Required updates:**
  - `docs/task.spec.md`: new item 5 adds `## Progress` to Optional
    Sections; item 6 (renumbered) updates body section ordering to
    include Progress before Findings
  - `docs/lifecycle.md`: pre-review checklist gains item 4
    "progress entry written"
  - Execute skill: new "Record Progress" step (item 3) with
    heading format and append-only instructions; subsequent steps
    renumbered
- **Companion Tooling section** — describes the planned
  `/openstation.progress` command (auto-heading, append-or-create,
  default to current task) and notes it's tracked separately
- **"What This Does NOT Change"** — removed the "no new commands"
  bullet since `/openstation.progress` is now planned

## Verification

- [ ] Decision 6 is added to the spec with rationale and status
- [ ] `## Progress` format is defined (heading format, append-only rule)
- [ ] Changes Required section updated for task spec, skill, and lifecycle
- [ ] `/openstation.progress` command mentioned as companion tooling
