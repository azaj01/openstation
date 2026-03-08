---
kind: task
name: 0080-rewrite-roadmap-in-taskmd-format
status: backlog
assignee: author
owner: user
created: 2026-03-08
---

# Rewrite Roadmap in taskmd Format with Task Links

## Requirements

1. Rewrite `artifacts/tasks/roadmap.md` using taskmd-style format:
   - Each item is a checkbox linked to its task via `[[wikilink]]`
   - Parent/subtask relationships shown via nesting
   - Items grouped by milestone (e.g., v0.7, v0.8) rather than vague "Release vN"
2. Include all done tasks (checked) and backlog tasks (unchecked) from the vault
3. Group backlog items under an "Unscheduled" section
4. Keep format compatible with Obsidian rendering (wikilinks resolve)

Example:
```markdown
## v0.7 — README & Polish
- [x] [[0075-cli-agent-friendly-improvements-json]] — JSON output, help, exit codes
- [ ] [[0076-improve-readme-presentation-and-explanation]] — Rewrite README
  - [x] [[0077-research-competitor-approaches-to-readme]] — Competitor analysis
```

## Verification

- [ ] `artifacts/tasks/roadmap.md` uses taskmd checkbox + wikilink format
- [ ] All existing tasks from the vault are represented
- [ ] Done tasks are checked, backlog/active tasks are unchecked
- [ ] Parent/subtask nesting is correct
- [ ] Milestones group tasks logically (not just sequentially)
