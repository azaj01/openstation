---
kind: task
name: 0216-implement-session-listing
type: feature
status: backlog
assignee: developer
owner: user
parent: "[[0214-session-listing-per-task]]"
created: 2026-03-22
---

# Implement Session Listing

## Requirements

1. Implement the session listing feature using the approach chosen in research subtask 0215.
2. Accept a task name, branch name, or ticket ID as input. When no argument is given, use the current branch/worktree.
3. Resolve the `~/.claude/projects/` directory matching the input, parse JSONL session files, and present a sorted table with: date, session ID, message count, first user message (truncated to 150 chars).
4. Handle edge cases: multiple matching directories, empty sessions, current session marking.
5. Include the reference implementation from the parent task description as a starting point.

## Context

Reference implementation (shell-based) provided in parent task 0214. Adapt to the recommended approach from 0215.

## Verification

- [ ] Feature implemented using the research-recommended approach
- [ ] Accepts task name, branch, or ticket ID; defaults to current branch
- [ ] Output is a sorted table with date, session ID, message count, first message
- [ ] Edge cases handled: multiple dirs, empty sessions, current session
- [ ] Tests cover core parsing and resolution logic
