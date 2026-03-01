---
kind: task
name: 0013-autonomous-task-execution
status: in-progress
agent: researcher
owner: manual
created: 2026-02-27
---

# Implement Task Execution in Autonomous or Detached Mode

## Requirements

- Define execution modes where agents can run tasks with reduced
  or zero interactive prompts (Tier 1: semi-autonomous, Tier 2:
  fully autonomous)
- Specify how an agent discovers and picks up ready tasks when
  launched in autonomous mode
- Define guardrails for autonomous execution: what actions require
  human approval vs. what can proceed automatically
- Integrate with the existing task lifecycle — autonomous agents
  must still follow status transitions (ready → in-progress →
  review → done/failed)
- Document the autonomous execution workflow and any new CLI flags
  or configuration

**Out of scope:** Tier 3 (detached/background execution via
nohup/tmux). Deferred to a future task.

## Findings

Claude Code already provides all primitives needed for autonomous
agent execution — no upstream changes are required.

**Key discoveries:**

- **`-p` (print mode)** enables fully non-interactive execution.
  Combined with `--agent`, agents run identically to interactive
  mode but without permission prompts.
- **`--allowedTools`** supports glob patterns (e.g.,
  `"Bash(ls *)"`) for fine-grained, per-agent tool approval.
- **`--max-turns`** exists at CLI level (print mode only),
  providing a turn limit safety net.
- **`--max-budget-usd`** caps API costs per invocation.
- **`--detached` does not exist.** Background execution requires
  OS-level wrapping (`nohup`, `tmux`).
- **Hooks** (`PreToolUse`, `PostToolUse`, `Stop`, `SessionEnd`)
  enable runtime guardrails — blocking writes outside allowed
  paths, preventing destructive git commands, sending completion
  notifications.
- **Task discovery is unchanged.** The `openstation-execute` skill
  is prompt-based and works identically in `-p` mode.
- **Lifecycle requires no changes.** Status transitions, ownership,
  artifact storage, and the self-verification ban all apply
  unchanged.

A three-tier model was designed: semi-autonomous (Tier 1), fully
autonomous (Tier 2), and detached/background (Tier 3). Per-agent
`--allowedTools` recipes were developed for all four current agents.

See `artifacts/research/autonomous-task-execution.md` for the
full research document.

## Recommendations

**Now:** Document Tier 1 & 2, add `--allowedTools` recipes to
agent specs, create `openstation-run.sh` launcher (foreground
only), add `PreToolUse` hook guardrails.

**Soon:** Extend `/openstation.dispatch` with autonomous
invocation support.

**Defer:** Tier 3 (detached/background via nohup/tmux), Agent
Teams integration, Agent SDK migration, per-task permission
fields in frontmatter.

## Subtasks

- `0018-autonomous-execution-research` — research (done)
- `0019-autonomous-execution-spec` — implementation spec (ready)
- `0020-autonomous-execution-impl` — implementation (ready)

## Verification

- [ ] Semi-autonomous mode (Tier 1) is defined and documented
- [ ] Fully autonomous mode (Tier 2) is defined and documented
- [ ] Agents can execute ready tasks without interactive prompts
- [ ] Per-agent `--allowedTools` recipes are documented
- [ ] Guardrails for autonomous actions are documented
- [ ] Task lifecycle transitions are preserved in autonomous mode
- [ ] Integration with existing `openstation-execute` skill is maintained
