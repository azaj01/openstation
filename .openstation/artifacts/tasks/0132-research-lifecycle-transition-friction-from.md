---
kind: task
name: 0132-research-lifecycle-transition-friction-from
type: feature
status: in-progress
assignee: researcher
owner: user
created: 2026-03-13
---

# Research Lifecycle Transition Friction From Agent Logs

## Requirements

1. Analyze existing agent session logs in `artifacts/logs/` to identify cases where lifecycle transitions failed or agents needed multiple status changes to complete work
2. Catalog the specific transition patterns that are too restrictive (e.g., `review` → `in-progress` not allowed, `failed` → `ready` blocked, etc.)
3. Document the frequency and context of each friction point
4. Propose a revised transition model that relaxes the necessary constraints while preserving useful guardrails (e.g., ownership checks, verification requirements)
5. Identify any risks of the relaxed model (e.g., tasks skipping verification)

## Verification

- [ ] At least 3 log files from `artifacts/logs/` analyzed with specific examples cited
- [ ] Each restrictive transition identified with concrete log evidence (timestamps, task IDs, error context)
- [ ] Proposed revised transition model documented as a state diagram or transition table
- [ ] Risks/tradeoffs of relaxed model explicitly listed
