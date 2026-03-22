---
kind: task
name: 0194-add-decomposition-guidelines-to-task
type: documentation
status: done
assignee: author
owner: user
created: 2026-03-21
---

# Add Decomposition Guidelines To Task Spec — Sizing Heuristics, When To Split Vs

## Requirements

Add a decomposition guidelines section to `docs/task.spec.md`
(or a dedicated doc referenced from it). Should cover:

### 1. Sizing Heuristics

When is a task the right size? Rules of thumb for "too big"
and "too small". Consider:
- Single-agent, single-session scope
- One coherent deliverable
- Verification items should be testable in one review

### 2. When to Split vs Keep Together

Decision framework for decomposition:
- Same assignee + same domain + same deliverable → keep together
- Different assignees or independent domains → split
- Anti-pattern: splitting by file type (docs task, code task,
  config task) when they're all part of one change

### 3. Subtasks vs Independent Tasks

When to use `--parent` subtasks vs standalone tasks:
- Subtasks: work must complete before parent can review
  (blocking rule applies)
- Independent: related but not blocking, no ordering constraint
- When to use a dependency note instead of parent/child

### 4. Parent Task Patterns

Guidance on parent task roles:
- "Container" parent (no own work, just coordinates subtasks)
- "Milestone" parent (phased delivery, subtasks per phase)
- When nesting is appropriate vs flat task list

Also update `/openstation.create` command's decomposition
guidance (step 2) to reference these guidelines.

## Findings

Created `docs/decomposition.md` as a dedicated guide covering all
four required areas:

1. **Sizing Heuristics** — concrete table with 6 signals (requirements
   count, files touched, agent roles, domains, verification scope,
   session time) with right-sized vs too-big thresholds. Also defines
   "too small" (no independent deliverable).
2. **When to Split vs Keep Together** — decision framework with
   keep-together criteria, split criteria, and three named
   anti-patterns (splitting by file type, splitting by step,
   over-decomposition).
3. **Subtasks vs Independent Tasks** — criteria for `--parent` use,
   independent tasks, and dependency notes. Includes an ASCII
   decision tree.
4. **Parent Task Patterns** — container parent and milestone parent
   patterns with when-to-use guidance. Nesting-vs-flat criteria with
   a max depth of 2 levels.

`task.spec.md` retains a short `## Decomposition` section that
references the dedicated doc (keeps the schema spec focused on
format, not operational guidance).

Cross-references updated:
- `/openstation.create` command (step 2) → `docs/decomposition.md`
- `openstation-execute` skill (step 2) → `docs/decomposition.md`

## Progress

- 2026-03-21 — Added decomposition guidelines section to task.spec.md, updated /openstation.create and openstation-execute skill to cross-reference. All four requirement areas covered.
- 2026-03-21 — Fixed placement per verification feedback: extracted content to dedicated `docs/decomposition.md`, replaced inline section in task.spec.md with a short reference, updated all cross-references.

## Verification

- [x] Guidelines section exists in `docs/task.spec.md` (or linked doc)
- [x] Sizing heuristics are concrete (not vague platitudes)
- [x] Split-vs-keep decision framework is documented with examples
- [x] Subtask vs independent task guidance with clear criteria
- [x] Parent task patterns described (container, milestone)
- [x] `/openstation.create` references the guidelines

## Verification Report

*Verified: 2026-03-21*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Guidelines section exists in `docs/task.spec.md` (or linked doc) | PASS | `task.spec.md` §Decomposition (line 344) references `docs/decomposition.md`; dedicated doc exists with full content |
| 2 | Sizing heuristics are concrete (not vague platitudes) | PASS | Table with 6 signals (requirements count, files touched, agent roles, domains, verification scope, session time) with specific right-sized vs too-big thresholds |
| 3 | Split-vs-keep decision framework documented with examples | PASS | Keep-together criteria, split criteria, and 3 named anti-patterns (splitting by file type, splitting by step, over-decomposition) with concrete examples |
| 4 | Subtask vs independent task guidance with clear criteria | PASS | Criteria for `--parent` use, independent tasks, and dependency notes; includes ASCII decision tree |
| 5 | Parent task patterns described (container, milestone) | PASS | Container parent and milestone parent patterns with when-to-use guidance, nesting-vs-flat criteria, max depth of 2 |
| 6 | `/openstation.create` references the guidelines | PASS | Step 2 decomposition guidance (line 38) references `docs/decomposition.md` |

### Summary

6 passed, 0 failed. All verification criteria met.
