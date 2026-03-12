---
kind: spec
name: assignee-reviewer-feedback-loop
agent: architect
task: "[[0104-improve-feedback-loop-between-assignee]]"
---

# Assignee–Reviewer Feedback Loop

Spec for improving communication between the agent executing a
task (assignee) and the person verifying it (reviewer/owner).

---

## Problem

Research and spec tasks produce a `## Findings` section that
makes verification straightforward — the reviewer can check
claims against artifacts. Implementation tasks skip this by
convention, forcing reviewers to read code and tests themselves
to understand what was built, what decisions were made, and
whether anything needs follow-up.

This creates two concrete costs:

1. **Slower reviews.** The reviewer reverse-engineers the work
   instead of reading a summary.
2. **Late discovery of downstream work.** Documentation gaps,
   follow-up tasks, and behavior changes only surface during
   review — after the implementing agent's session is over.

---

## Design Decisions

### Decision 1: Require `## Findings` for all task types

**Status:** Decided

**Rationale:** The current convention ("skip for pure
implementation tasks") is the root cause. Every task type
produces information the reviewer needs:

| Task type        | What the reviewer needs to know          |
|------------------|------------------------------------------|
| `research`       | What was discovered, sources, confidence |
| `spec`           | What was designed, trade-offs, decisions  |
| `implementation` | What was built, how it works, what changed |
| `documentation`  | What was written/updated, scope of changes |
| `feature`        | Combination of the above                 |

The section name `## Findings` already works for all types —
it means "what this task found or produced." No rename needed.

**What changes:**

- `docs/task.spec.md`: Move `## Findings` from Optional Sections
  to Required Sections. Update the description from "Results
  discovered during research tasks" to a type-neutral description.
- `docs/task.spec.md`: Update the Progressive Disclosure table
  to show Findings at Completed stage for all task types, not
  just research.
- Execute skill: Remove the "skip for pure implementation tasks"
  escape hatch from step 5 (Record Findings).

### Decision 2: Define minimum content per task type

**Status:** Decided

**Rationale:** "Required" without guidance on what to write
leads to low-value boilerplate. Each type needs a concrete
minimum:

| Task type        | Minimum Findings content                          |
|------------------|---------------------------------------------------|
| `research`       | Key results, sources consulted, confidence levels  |
| `spec`           | Summary of design, key trade-offs made             |
| `implementation` | What was built/changed, design decisions, gotchas  |
| `documentation`  | What was written/updated, scope of changes         |
| `feature`        | What was built, how it works, notable decisions    |

**What changes:**

- `docs/task.spec.md`: Add a "Findings by Task Type" subsection
  under the `## Findings` section description, with one-liner
  guidance per type.
- Execute skill: Add type-specific guidance to step 5.

### Decision 3: Add `## Downstream` section for flagging follow-up work

**Status:** Decided

**Rationale:** Reviewers currently discover documentation gaps
and follow-up needs during review, when the assignee's session
is over. The assignee is best positioned to flag these — they
just did the work and know what's missing.

A separate section (not buried in Findings) makes it scannable.
The reviewer can create follow-up tasks from it or ignore items
that aren't needed.

**What changes:**

- `docs/task.spec.md`: Add `## Downstream` to Optional Sections.
  Description: "Follow-up work the assignee identified during
  execution. Each item is a bullet describing what needs to
  happen and why." Place it after Findings, before Verification.
- Execute skill: Add a new step 6 "Flag Downstream Work" between
  current steps 5 (Record Findings) and 6 (Create Sub-Tasks).
  Guidance: "If your work introduced behavior changes, new
  conventions, or gaps you noticed, add a `## Downstream`
  section listing items the reviewer should consider creating
  tasks for."

**Why not require it:** Most tasks have no downstream work. A
required empty section adds noise. The execute skill should
prompt agents to consider it, but not mandate the section.

### Decision 4: Add "findings written" convention to verification

**Status:** Decided

**Rationale:** If Findings is required but not verified, agents
will skip it under time pressure. A verification item makes it
enforceable.

**What changes:**

- `docs/task.spec.md`: Add guidance that verification checklists
  SHOULD include a "Findings section documents what was done"
  item. This is a convention, not enforced by tooling — task
  authors add it when writing verification items.
- Note: Existing tasks without this item are not affected. This
  applies to newly created tasks going forward.

### Decision 5: Update lifecycle pre-review checklist

**Status:** Decided

**Rationale:** The lifecycle doc defines when transitions happen
but not what must be true before them. Adding a pre-review
checklist to `docs/lifecycle.md` gives agents a concrete gate.

**What changes:**

- `docs/lifecycle.md`: Add a "Pre-Review Checklist" subsection
  under the `in-progress → review` transition. Contents:

  ```markdown
  Before setting `status: review`, the assignee must ensure:
  1. All requirements in the task spec are addressed
  2. `## Findings` section summarizes the work done
  3. `## Downstream` section lists follow-up work (if any)
  4. Artifacts are stored in `artifacts/<category>/` and
     recorded in the task's `artifacts` frontmatter
  ```

---

## Changes Required

### File: `docs/task.spec.md`

#### 1. Move `## Findings` to Required Sections

In the "Required Sections" area (after `## Verification`), add:

```markdown
#### `## Findings`

Summary of what the task produced or discovered. Written by the
assignee during execution, not by the task author upfront.

Every completed task must have a Findings section. Content
varies by task type:

| Task type        | What to include                                    |
|------------------|----------------------------------------------------|
| `research`       | Key results, sources consulted, confidence levels   |
| `spec`           | Summary of design, key trade-offs made              |
| `implementation` | What was built/changed, design decisions, gotchas   |
| `documentation`  | What was written/updated, scope of changes          |
| `feature`        | What was built, how it works, notable decisions     |

Link to artifacts where relevant. Lead with conclusions, not
process narrative.
```

#### 2. Remove `## Findings` from Optional Sections table

Remove the row `| \`## Findings\` | Results discovered during
research tasks |` from the Optional Sections table.

#### 3. Add `## Downstream` to Optional Sections table

Add a new row:

```
| `## Downstream`      | Follow-up work identified during execution (docs needed, behavior changes, refactoring opportunities) |
```

#### 4. Update Progressive Disclosure table

Change the Completed row from:

```
| **Completed** | `status: done` | + `## Findings`, `## Recommendations` (research tasks) |
```

To:

```
| **Completed** | `status: done` | + `## Findings` (all types), `## Recommendations` (if applicable), `## Downstream` (if applicable) |
```

#### 5. Update body section ordering

The canonical section order becomes:

1. `# Title` (required)
2. `## Context` (optional)
3. `## Requirements` (required)
4. `## Subtasks` (optional)
5. `## Findings` (required — written during execution)
6. `## Downstream` (optional — written during execution)
7. `## Recommendations` (optional — written during execution)
8. `## Verification` (required)

### File: `docs/lifecycle.md`

#### 1. Add Pre-Review Checklist

Under the `in-progress → review` line in Status Transitions,
or as a new subsection under Guardrails, add:

```markdown
### Pre-Review Checklist

Before transitioning to `review`, the assignee must ensure:

1. All requirements in the task spec are addressed
2. `## Findings` section summarizes the work produced
3. `## Downstream` section lists follow-up work (if any were
   identified — omit the section if none)
4. Artifacts are stored in `artifacts/<category>/` and recorded
   in the task's `artifacts` frontmatter list
```

### File: Execute skill (`skills/openstation-execute/`)

Note: The execute skill content is loaded at runtime. The
changes below describe what to modify in the skill file
(wherever it is stored — likely `.claude/skills/` or
`skills/openstation-execute/`).

#### 1. Update step 5 (Record Findings)

Replace:

> After completing the work, add a `## Findings` section to the
> task file summarizing what you discovered or produced. [...]
> Skip this step if the task produced no findings worth recording
> (e.g., pure implementation tasks with nothing to summarize
> beyond the code itself).

With:

> After completing the work, add a `## Findings` section to the
> task file summarizing what you produced. This is required for
> all task types.
>
> Content varies by type:
> - **research**: Key results, sources, confidence levels
> - **spec**: Design summary, trade-offs, key decisions
> - **implementation**: What was built/changed, design decisions,
>   gotchas
> - **documentation**: What was written/updated, scope
> - **feature**: What was built, how it works, notable decisions
>
> Lead with conclusions. Link to artifacts. Keep it concise —
> a reviewer should understand the work without reading every
> file you touched.

#### 2. Add step 6 (Flag Downstream Work)

After the updated step 5, insert a new step:

> ### 6. Flag Downstream Work (if applicable)
>
> If your work introduced any of the following, add a
> `## Downstream` section to the task file:
>
> - Behavior changes that need documentation updates
> - New conventions or patterns others should know about
> - Gaps you noticed but didn't address (out of scope)
> - Follow-up tasks that would improve the result
>
> Each item is a bullet describing what needs to happen and why.
> The reviewer will decide whether to create tasks for them.
>
> Omit this section if there is no downstream work to flag.

#### 3. Renumber subsequent steps

Current steps 6 (Create Sub-Tasks) and 7 (Update Documentation)
become steps 7 and 8.

---

## What This Does NOT Change

- **Existing completed tasks** are not retroactively updated.
- **Tooling** — no CLI changes, no new commands. This is purely
  a convention change enforced through documentation and the
  execute skill.
- **`## Recommendations`** stays optional and is not renamed or
  merged with Findings.
- **Verification automation** — the "findings written" check
  remains a manual convention item, not enforced by `openstation
  status`.

---

## Migration

This is a documentation-only change. No code migration needed.

1. Update `docs/task.spec.md` per the changes above.
2. Update `docs/lifecycle.md` per the changes above.
3. Update the execute skill per the changes above.
4. New tasks created after these changes take effect will follow
   the new conventions. Existing tasks are unaffected.

Implementation should be a single task assigned to `author`.
