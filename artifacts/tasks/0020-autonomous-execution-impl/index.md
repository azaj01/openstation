---
kind: task
name: 0020-autonomous-execution-impl
status: done
agent: author
owner: manual
parent: 0013-autonomous-task-execution
created: 2026-02-28
---

# Implement Autonomous Task Execution

## Requirements

- Implement all components defined in
  `artifacts/specs/autonomous-execution.md`
- **Scope: Tier 1 and Tier 2 only** (per parent task scope)
- Components to implement:
  - C1: `openstation-run.sh` launcher script
  - C2: `hooks/validate-write-path.sh` write-path hook
  - C3: `hooks/block-destructive-git.sh` destructive-git hook
  - C4: `allowed-tools` field in all five agent specs
  - C5: `install.sh` updates (deploy hooks, launcher, settings)
- Follow the build sequence in the spec: C4 first, then
  C1/C2/C3 in parallel, C5 last
- All implementations must pass the verification criteria from
  the spec

## Verification

- [ ] All five spec components implemented
- [ ] Launcher script works for all five agents (foreground)
- [ ] Hook guardrails block disallowed operations
- [ ] Per-agent `allowed-tools` recipes added to agent specs
- [ ] `install.sh` deploys hooks, launcher, and settings config
