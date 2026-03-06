---
kind: task
name: 0064-improve-list-table-view-show
status: done
assignee: developer
owner: user
created: 2026-03-06
---

# Improve List Table View — Show Subtasks Grouped Under Parent

## Requirements

1. `openstation list` groups subtasks visually under their parent task in the output table.
2. Subtasks are indented with a tree prefix (e.g., `  └─`) below their parent row.
3. Parent tasks without subtasks display as before (flat row).
4. Top-level tasks sorted by ID; subtasks sorted by ID within their parent group.
5. Status filters still apply — if a parent matches but no subtasks match, show only the parent (and vice versa).
6. Subtasks that match filters but whose parent doesn't match are shown as top-level rows (no orphan hiding).
7. **Rename "Agent" column to "Assignee"** in `openstation list` output and update all references across the repo: CLI code, commands, docs, skills, CLAUDE.md, and tests. The frontmatter field stays `agent` — only the display label changes.

8. **Tree prefix in Name column, not ID column** — subtask IDs must remain visible. The `└─` prefix belongs in the Name column so the ID column always shows the numeric ID.

Example output:
```
ID     Name                                               Status    Assignee
----   ------------------------------------------------   -------   ----------
0055   cli-init-command-separate-project                   ready
0056     └─ research-install-vs-init-patterns              review    researcher
0057     └─ spec-for-openstation-init-command               in-prog   architect
0058     └─ implement-openstation-init-command-and          ready     developer
0059     └─ update-docs-for-install-vs                      ready     author
0064   improve-list-table-view-show                        ready     developer
```

## Verification

- [x] Subtasks appear indented under their parent in `openstation list` output
- [x] Top-level tasks without subtasks display unchanged
- [x] Sorting: parents by ID, subtasks by ID within group
- [x] Status/agent filters work correctly with grouped view
- [x] "Agent" column renamed to "Assignee" in CLI output
- [x] All repo references to the column label updated (commands, docs, skills, tests)
- [x] Frontmatter field remains `agent` (no schema change)
- [x] Existing tests updated and passing
- [x] New tests cover grouped output formatting
- [x] Subtask IDs visible in ID column (tree prefix in Name column)
