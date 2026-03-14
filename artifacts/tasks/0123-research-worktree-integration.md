---
kind: task
name: 0123-research-worktree-integration
type: research
status: done
assignee: researcher
owner: user
parent: "[[0122-worktree-integration]]"
artifacts:
  - "[[artifacts/research/worktree-integration]]"
created: 2026-03-13
---

# Research: Worktree Integration

Consolidate all worktree research into a single living artifact. Absorbs findings from task 0121 and adds new investigation as the feature evolves. This is the team's reference for design decisions, trade-offs, and external tool evaluations.

## Requirements

1. Absorb and organize findings from task 0121's research artifact (`artifacts/research/worktree-integration-for-parallel-agents.md`)
2. Document `claude --worktree` mechanics, limitations, and compatibility with `openstation run`
3. Document worktrunk and workmux as optional external complements (not dependencies)
4. Track open questions and design decisions as they arise during implementation milestones
5. Update as new findings emerge — this is a living document

## Findings

Research artifact: `artifacts/research/worktree-integration.md`

**Key findings:**

1. **`claude --worktree` is the right foundation.** Zero-dependency, built-in to Claude CLI, works with `--agent` in both attached and detached modes. Creates worktrees at `.claude/worktrees/<name>/` with auto-cleanup. Also supports `--tmux` for detached terminal sessions.

2. **`find_root()` worktree resolution is already implemented.** The critical blocker from task 0092 has been resolved — `core.py` uses `git rev-parse --git-common-dir` to resolve the vault from linked worktrees. Agents in worktrees can already find `.openstation/`.

3. **Worktrunk** is a clean, lightweight worktree lifecycle manager (single Rust binary). Useful for users who want richer merge workflows and build cache sharing. Best as a documented coexistence pattern, not a dependency.

4. **Workmux** is the most feature-rich orchestrator with dashboard, multi-agent support, and terminal multiplexer integration. Too heavy for Open Station's philosophy. Also best as a documented coexistence pattern.

5. **None of the three tools have task awareness.** Open Station's `--worktree` integration provides the unique value of connecting worktrees to the task lifecycle.

6. **Implementation path is clear:** Option A (pass `--worktree` through to Claude CLI) is the minimal first milestone. Branch-scoping (0109) is the logical second step. Pre-creating worktrees (Option B) is deferred until naming control becomes important.

7. **New finding: Claude's "agent teams" feature** may overlap with Open Station's parallel agent model. Needs further investigation — no detailed public docs found yet.

## Recommendations

1. **Next milestone: `--worktree` pass-through** — Add the flag to `build_command()` and `cmd_run()`. Derive worktree name from task name. Minimal code change.
2. **Branch-scoping (0109) is the key enabler** — Without it, agents in worktrees see all tasks. With it, each agent only sees branch-relevant tasks.
3. **Sequential execution first** — Run subtasks one at a time, each in its own worktree. Concurrent execution is a separate feature.
4. **Document external tool coexistence** — Show how worktrunk and workmux can wrap `openstation run` without being dependencies.
5. **Investigate Claude "agent teams"** — May provide coordination primitives that complement or replace custom orchestration.

## Verification

- [ ] Research artifact exists in `artifacts/research/`
- [ ] Covers `claude --worktree`, worktrunk, workmux with structured comparison
- [ ] Documents integration points with `openstation run`
- [ ] Open questions section tracks unresolved decisions
