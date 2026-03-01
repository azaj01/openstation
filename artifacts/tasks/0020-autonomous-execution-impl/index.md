---
kind: task
name: 0020-autonomous-execution-impl
status: ready
agent: author
owner: manual
parent: 0013-autonomous-task-execution
created: 2026-02-28
---

# Implement Autonomous Task Execution

## Requirements

- Implement all deliverables defined in the spec from task
  0019-autonomous-execution-spec
- Expected deliverables (pending spec finalization):
  - `openstation-run.sh` launcher script
  - Hook scripts for guardrails
  - Agent spec updates with tool recipes
  - `/openstation.dispatch` autonomous mode support
  - `.openstation/logs/` directory convention
- All implementations must pass the verification criteria from
  the spec

## Verification

- [ ] All spec deliverables implemented
- [ ] Launcher script works for all four agents
- [ ] Hook guardrails block disallowed operations
- [ ] `/openstation.dispatch` supports autonomous invocation
- [ ] Log directory convention established and documented
