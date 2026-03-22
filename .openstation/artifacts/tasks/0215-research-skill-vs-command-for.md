---
kind: task
name: 0215-research-skill-vs-command-for
type: feature
status: ready
assignee: researcher
owner: user
parent: "[[0214-session-listing-per-task]]"
created: 2026-03-22
---

# Research Skill Vs Command For Session Listing

## Requirements

1. Compare skill vs slash-command as the delivery mechanism for a session-listing feature. Evaluate on: discoverability, argument handling, output formatting control, and whether the feature needs tool access (Bash) or can work purely with Read/Glob.
2. Consider a third option: CLI subcommand (`openstation sessions`), since the project already has a Python CLI that could parse JSONL natively.
3. Document the Claude Code session storage layout (`~/.claude/projects/`) and JSONL schema as discovered facts — these inform implementation regardless of approach.
4. Deliver a recommendation with reasoning.

## Verification

- [ ] Comparison covers skill, command, and CLI subcommand options
- [ ] Pros/cons address discoverability, argument handling, tool access, and output control
- [ ] Session storage layout and JSONL schema documented
- [ ] Clear recommendation with reasoning
