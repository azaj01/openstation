---
kind: task
name: 0205-pipeline-command-for-multi-step
type: feature
status: backlog
assignee: 
owner: user
created: 2026-03-22
---

# Pipeline Command For Multi-Step Task Execution

## Requirements

TBD — design and requirements will be defined during research/spec phase.

## Early Thinking

**Concept:** A new `openstation pipeline <task>` command that
orchestrates a parent task's subtasks as a sequential pipeline:

1. Find all subtasks in execution order
2. Run each one autonomously
3. Auto-verify each on completion
4. Auto-accept if verification passes
5. Report aggregate results

This is a step up from Level 1 (hook-based chaining in 0204) —
instead of reactive hooks, the pipeline command is an explicit
orchestrator that owns the full execution loop.

**Open questions:**
- Should this be a new CLI command or a mode of `openstation run`?
- How does it interact with the hook system?
- Error handling: retry, skip, or abort on failure?
- Progress reporting for long-running pipelines
- Parallel execution of independent subtasks?

**Depends on:** 0204 (hook-based chaining) for the auto-verify
and auto-accept primitives, or can be self-contained.

## Verification

- [ ] (to be defined during spec phase)
