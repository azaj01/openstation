---
kind: task
name: 0096-add-session-id-to-run
type: feature
status: done
assignee: developer
owner: user
parent: "[[0078-improve-run-command-readability-and]]"
created: 2026-03-11
---

# Add Session ID to Run Output Log

## Requirements

1. After `openstation run` launches a Claude session, capture the session ID from the Claude Code output.
2. Include the session ID in the run summary log so the operator can see it after execution completes.
3. Print a resume command (`claude --resume <session-id>`) in the summary, especially on partial completion or failure.
4. Use `--output-format stream-json` or parse stdout to extract the session ID — per findings in task 0095.

## Context

- Research: [[0095-research-printing-claude-session-to]]

## Verification

- [ ] Run output includes the Claude session ID after execution
- [ ] A `claude --resume <session-id>` command is printed on failure or partial completion
- [ ] Session ID is present in the JSON log (`artifacts/logs/`)
- [ ] Existing tests pass
