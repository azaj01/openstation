---
kind: task
name: 0121-research-worktree-integration-for-parallel
type: feature
status: review
assignee: researcher
owner: user
artifacts:
  - "[[artifacts/research/worktree-integration-for-parallel-agents]]"
created: 2026-03-12
---

# Research Worktree Integration For Parallel Agent Sessions

## Context

When running multiple agents in parallel (e.g., researcher on task A,
developer on task B), they currently share the same working directory
and can conflict. Git worktrees offer isolated branches with shared
history — a natural fit for parallel agent execution.

Existing solutions to evaluate: `claude --worktree`,
[worktrunk.dev](https://worktrunk.dev/),
[workmux](https://github.com/raine/workmux).

## Requirements

1. Investigate `claude --worktree` — how it works, what it enables
   (parallel agent sessions on isolated git worktrees), limitations
2. Evaluate [worktrunk.dev](https://worktrunk.dev/) — capabilities,
   integration model with Claude/AI agents, relevance to Open Station
3. Evaluate [workmux](https://github.com/raine/workmux) — same
   analysis: capabilities, integration model, relevance
4. Compare approaches: built-in `--worktree` vs external orchestrators
   vs custom integration
5. Identify how worktree support could integrate with `openstation run`
   — e.g., auto-creating worktrees per task, running multiple agents
   in parallel on separate branches
6. Surface open questions and design decisions for a potential
   implementation

## Findings

Research artifact: `artifacts/research/worktree-integration-for-parallel-agents.md`

**`claude --worktree`** is the best fit for Open Station. It's built-in, zero-dependency, creates isolated worktrees per session, and works with `--agent` in both attached and detached modes. Worktrees are created at `.claude/worktrees/{name}/` with auto-cleanup. Limitation: no orchestration or task awareness — each session is independent.

**Worktrunk** is a clean worktree lifecycle manager (create/merge/cleanup) with build cache sharing and hooks. Useful as an external complement but adds a dependency and has no task awareness.

**Workmux** is the most feature-rich orchestrator with dashboard, multi-agent support, and terminal multiplexer integration. Too heavy for Open Station's zero-dependency philosophy; best as optional external tooling.

**Recommended integration:** Pass `--worktree` through to the Claude CLI from `openstation run` (Option A — minimal implementation), combined with the branch-based task scoping system (spec 0094) for task filtering. Prerequisites: `find_root()` worktree resolution (task 0092) must be completed first.

## Recommendations

1. **Implement Option A (pass-through)** — Add `--worktree` flag to `openstation run` that forwards to `claude --worktree`. Minimal code change, zero new dependencies.
2. **Complete task 0092** — `find_root()` worktree resolution is a hard prerequisite. Without it, agents in worktrees can't find the vault.
3. **Complete task 0109** — Branch-based task scoping implementation connects worktrees to task filtering.
4. **Sequential-in-worktrees first** — Run each subtask in its own worktree sequentially. Concurrent multi-process execution is a separate, more complex feature.
5. **Document worktrunk/workmux coexistence** — Show users how to use these tools alongside Open Station without making them dependencies.

## Verification

- [ ] Documents how `claude --worktree` works and its limitations
- [ ] Evaluates worktrunk.dev and workmux with pros/cons
- [ ] Compares approaches in a structured format
- [ ] Proposes integration points with `openstation run`
- [ ] Research artifact written to `artifacts/research/`
