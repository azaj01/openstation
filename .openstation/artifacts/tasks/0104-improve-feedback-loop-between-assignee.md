---
kind: task
name: 0104-improve-feedback-loop-between-assignee
type: spec
status: done
assignee: architect
owner: user
artifacts:
  - "[[artifacts/specs/assignee-reviewer-feedback-loop]]"
created: 2026-03-10
subtasks:
  - "[[0127-update-feedback-loop-spec-with]]"
  - "[[0128-implement-feedback-loop-changes-from]]"
---

# Improve feedback loop between assignee and reviewer

Define conventions and/or task spec changes that improve communication between the agent executing a task (assignee) and the person verifying it (reviewer/owner).

## Requirements

### User Stories

1. **As a reviewer verifying task 0092 (worktree support)**, I found working code and passing tests — but no explanation of what was built, how it works, or what design decisions were made. I had to read the code and tests myself to understand the results. If the developer had written a summary of their work, review would have been faster and documentation gaps would have been obvious.

2. **As a reviewer verifying task 0086 (module split spec)**, the architect wrote a `## Findings` section that summarized the design clearly. This made verification straightforward — I could check each claim against the artifact. Research and spec tasks do this well; implementation tasks don't.

3. **As a PM creating documentation tasks after implementation**, I only discover that a feature is undocumented during review — after the implementing agent's session is over. If the assignee had flagged "this needs docs" or "this changes user-facing behavior", I could have created a docs task in parallel.

### What to define

1. What information must an assignee provide before moving a task to `review`?
2. Should `## Findings` be required for all task types, not just research?
3. How should the assignee flag downstream work (docs needed, follow-up tasks)?
4. What changes to `docs/task.spec.md` and `docs/lifecycle.md` are needed?
5. Should verification checklists include a "findings written" item by convention?

## Findings

Designed 5 changes to close the feedback gap between assignees
and reviewers:

1. **`## Findings` becomes required for all task types** — not
   just research/spec. Implementation tasks must summarize what
   was built, design decisions, and gotchas. Type-specific
   guidance tells agents what to include.

2. **New `## Downstream` optional section** — assignees flag
   follow-up work (docs needed, behavior changes, gaps noticed)
   so reviewers discover them before the agent session ends.

3. **Pre-review checklist in `lifecycle.md`** — a concrete gate
   before `in-progress → review`: findings written, downstream
   flagged, artifacts stored.

4. **Verification convention** — new tasks SHOULD include a
   "Findings section documents what was done" verification item.

5. **Execute skill update** — remove the "skip for implementation
   tasks" escape hatch, add type-specific guidance, add a new
   "Flag Downstream Work" step.

The root cause was that the execute skill explicitly told
implementation agents to skip findings. Removing that single
escape hatch, combined with type-specific guidance, addresses
all three user stories.

Full spec: `artifacts/specs/assignee-reviewer-feedback-loop.md`

## Verification

- [x] User stories document real pain points from this project
- [x] Spec defines what assignees must provide before `review`
- [x] Spec addresses all task types (not just research)
- [x] Changes to `task.spec.md` and `lifecycle.md` are specified
- [x] Downstream work flagging mechanism is defined
