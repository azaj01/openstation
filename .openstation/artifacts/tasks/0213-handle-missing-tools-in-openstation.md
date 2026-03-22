---
kind: task
name: 0213-handle-missing-tools-in-openstation
type: feature
status: ready
assignee: developer
owner: user
created: 2026-03-22
---

# Handle Missing Tools In Openstation Run

## Requirements

1. Add an optional `allowed-tools` field to task frontmatter — a list of additional tool patterns (same format as agent `allowed-tools`) that get merged with the agent's tools at launch time.
2. When `openstation run` builds the command, merge task-level `allowed-tools` into the agent's `allowed-tools` list (agent tools first, then task tools, deduplicated).
3. Add a `--tools` CLI flag to `openstation run` that appends extra tool patterns at launch time (highest priority — added after agent + task tools).
4. In detached mode, if the agent's result text contains a tool-permission request pattern (e.g., "approve the tool", "need your approval", "approve tool permissions"), detect this as a soft failure and print a diagnostic: the agent stalled waiting for tool approval, suggest adding the needed tools to the task's `allowed-tools` field or using `--tools`.
5. Update `docs/task.spec.md` to document the `allowed-tools` field.

## Verification

- [ ] Task frontmatter `allowed-tools` field is parsed and merged with agent `allowed-tools` at launch
- [ ] `--tools` CLI flag appends additional tools to the merged list
- [ ] Detached run that stalls on tool approval prints a diagnostic message with remediation hint
- [ ] `docs/task.spec.md` documents the `allowed-tools` field
- [ ] Existing runs without `allowed-tools` field behave identically (backward compatible)
- [ ] Tests cover: task tools merge, CLI tools merge, dedup, detection of stalled agent
