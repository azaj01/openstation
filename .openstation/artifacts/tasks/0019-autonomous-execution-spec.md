---
kind: task
name: 0019-autonomous-execution-spec
status: done
artifacts:
  - artifacts/specs/autonomous-execution.md
assignee: architect
owner: manual
parent: "[[0013-autonomous-task-execution]]"
created: 2026-02-28
---

# Spec Autonomous Task Execution

## Requirements

- Write an implementation spec based on the research in
  `artifacts/research/autonomous-task-execution.md`
- **Scope: Tier 1 (semi-autonomous) and Tier 2 (fully autonomous)
  only.** Tier 3 (detached/background) is deferred.
- Define exact files to create/modify with their contracts:
  - `openstation-run.sh` launcher script — foreground only (args,
    exit codes, error handling)
  - Hook scripts for guardrails (path validation,
    destructive-git blocking)
  - Agent spec changes (tool recipe fields or companion files)
- Include a build sequence with dependencies between deliverables

**Out of scope:** `.openstation/logs/` convention, notification
hooks, `/openstation.dispatch` autonomous mode, nohup/tmux
wrapping.

## Findings

Spec written to `artifacts/specs/autonomous-execution.md`.
Defines 5 components with contracts, verification criteria,
and a dependency-ordered build sequence. Spec focuses on
interfaces and constraints — implementation details are left
to the implementing agent (task 0020).

Components: launcher script (C1), write-path hook (C2),
destructive-git hook (C3), agent tool recipes (C4), install
script update (C5). Five design decisions documented with
trade-off rationale.

## Verification

- [x] Spec exists in `artifacts/specs/`
- [x] All deliverables have concrete file paths and interface contracts
- [x] Spec covers Tier 1 and Tier 2 only (no Tier 3)
- [x] Build sequence with dependencies is defined
- [x] Spec is actionable without ambiguity for implementing agents
