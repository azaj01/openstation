---
kind: task
name: 0032-tui-terminal-app
status: backlog
assignee:
owner: user
created: 2026-03-01
---

# TUI Terminal App

Build a terminal UI (TUI) application for Open Station that
provides an interactive interface for task management and agent
operations directly in the terminal.

## References

- [Terminal.Gui](https://github.com/gui-cs/Terminal.Gui) — .NET
  TUI framework (for design inspiration)
- [awesome-tuis](https://github.com/rothgar/awesome-tuis) —
  curated list of TUI projects and frameworks

## Requirements

- Research TUI frameworks suitable for the project stack and
  select one (e.g., Textual for Python, Ink for Node, Bubbletea
  for Go, or similar)
- Provide an interactive dashboard showing task status across
  lifecycle buckets (backlog, current, done)
- Support task operations: create, update, promote, complete
- Display agent specs and allow dispatching agents on ready tasks
- Show task details with frontmatter and body content
- Support keyboard navigation and common TUI conventions
- Integrate with existing Open Station conventions (read
  artifacts/tasks, agents, lifecycle states)

## Verification

- [ ] TUI framework selected with rationale documented
- [ ] App launches and displays task list from artifacts/tasks/
- [ ] Users can navigate between lifecycle buckets
- [ ] Task detail view shows full spec content
- [ ] Task operations (create, update, promote, done) work from TUI
- [ ] Agent dispatch is available for ready tasks
- [ ] Keyboard shortcuts documented and functional
