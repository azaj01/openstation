---
kind: task
name: 0143-require-architecture-section-in-feature
type: spec
status: done
assignee: architect
owner: user
created: 2026-03-16
---

# Require Architecture Section In Feature Documentation

## Requirements

All main components should be self-describing — their docs should
explain not just usage but also how the feature is built. Currently
documentation tasks have no convention requiring architectural
content, which leads to docs that cover "how to use" but not
"how it works."

1. Define what an Architecture section should contain for feature
   docs (module layout, integration points, data flow, key
   abstractions)
2. Determine where this requirement lives — `docs/task.spec.md`
   (documentation type guidance), execute skill, or both
3. Specify when it applies — all `docs/*.md` for features with
   code, not simple convention/process docs
4. Update the relevant specs and skills to codify the convention

### Context

Discovered during hooks documentation review (0142): the author
wrote thorough usage docs but omitted architecture. This should
be a standard expectation, not a per-task rejection.

## Findings

Convention codified in `docs/task.spec.md` as a new
**§ Type-Specific Documentation Standards** subsection under
Field Reference. Two changes:

1. **New section** (§ Type-Specific Documentation Standards →
   Architecture Section): defines what to include (module layout,
   integration points, data flow, key abstractions) and an
   applicability table distinguishing feature-with-code docs
   (required) from convention/process docs (not required).

2. **Updated Findings table**: the `documentation` and `feature`
   rows now cross-reference § Type-Specific Documentation
   Standards, reminding agents to confirm Architecture sections
   in produced artifacts.

**Placement rationale**: task.spec.md is the single source of
truth for task format and type-specific guidance. The execute
skill already references it (step 3 of On Startup), so agents
pick up the new standard without a separate skill update.
Duplicating in the execute skill would create a sync burden
with no added discovery benefit.

## Progress

- 2026-03-16 — architect: Designed and implemented Architecture
  section convention in task.spec.md. Added § Type-Specific
  Documentation Standards with content requirements and
  applicability table; updated Findings guidance table for
  documentation and feature types.

## Verification

- [x] Architecture section requirements are defined (what to include)
- [x] Applicability criteria are clear (which docs need it, which don't)
- [x] Convention is codified in task spec or execute skill (not just this task)
- [x] Existing type-specific guidance table in task.spec.md is updated
