---
kind: task
name: 0013-autonomous-task-execution
status: review
agent: researcher
owner: manual
created: 2026-02-27
---

# Implement Task Execution in Autonomous or Detached Mode

## Requirements

- Define an execution mode where agents can run tasks autonomously (without interactive user prompts) or in a detached/background session
- Specify how an agent discovers and picks up ready tasks when launched in autonomous mode
- Define guardrails for autonomous execution: what actions require human approval vs. what can proceed automatically
- Support detached execution where the agent runs in the background (e.g., via `claude --agent <name> --detached` or similar mechanism)
- Provide a way to monitor progress and review results of detached runs
- Integrate with the existing task lifecycle — autonomous agents must still follow status transitions (ready → in-progress → review → done/failed)
- Document the autonomous execution workflow and any new CLI flags or configuration

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

**Now:** Document tiers, add `--allowedTools` recipes to agent
specs, create `openstation-run.sh` launcher, establish
`.openstation/logs/` convention.

**Soon:** Add `PreToolUse` hook guardrails, extend
`/openstation.dispatch` with autonomous invocation support, add
`Stop` hook for completion notifications.

**Defer:** Agent Teams integration, Agent SDK migration, per-task
permission fields in frontmatter.

## Verification

- [ ] Autonomous mode is defined and documented
- [ ] Agents can execute ready tasks without interactive prompts
- [ ] Detached/background execution mechanism is specified
- [ ] Guardrails for autonomous actions are documented
- [ ] Progress monitoring and result review workflow exists
- [ ] Task lifecycle transitions are preserved in autonomous mode
- [ ] Integration with existing `openstation-execute` skill is maintained
