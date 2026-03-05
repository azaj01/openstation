---
name: openstation.update
description: Update task metadata fields (not status). $ARGUMENTS = <task-name> field:value [...]. Use when user says "update task", "assign agent", "change owner", or wants to modify task metadata.
---

# Update Task Metadata

Modify non-status frontmatter fields on an existing task.

For status transitions, use the dedicated lifecycle commands:
- `/openstation.ready` — promote backlog → ready
- `/openstation.done` — complete review → done
- `/openstation.reject` — reject review → failed

## Input

`$ARGUMENTS` — the task name followed by one or more `field:value`
pairs separated by spaces.

Example: `0003-research-obsidian-plugin-api agent:researcher owner:user`

The task name can be either the full ID-prefixed name (e.g.,
`0003-research-obsidian-plugin-api`) or just the slug (e.g.,
`research-obsidian-plugin-api`).

## Allowed Fields

| Field | Notes |
|-------|-------|
| `agent` | Agent name — warn if not found in `agents/` |
| `owner` | Agent name or `user` — warn if agent not found |
| `parent` | Parent task name |
| Other | Any non-status frontmatter field, updated as-is |

## Rejected Fields

If the user attempts to change `status`, respond with the
appropriate redirect:

| Attempted | Response |
|-----------|----------|
| `status:ready` | "Use `/openstation.ready` to promote a task." |
| `status:done` | "Use `/openstation.done` to complete a task." |
| `status:failed` | "Use `/openstation.reject` to reject a task." |
| `status:in-progress` | "Status `in-progress` is set by agents during execution." |
| `status:review` | "Status `review` is set by agents when work is complete." |
| `status:backlog` | "Demoting a task back to backlog is not supported." |

## Procedure

1. Parse the task name (first argument) and field:value pairs from
   `$ARGUMENTS`.
2. Check for any `status:` field. If present, reject with the
   appropriate message from the table above. Do not apply any
   changes.
3. Locate the task file:
   - Try exact match: `artifacts/tasks/<task-name>.md`
   - If not found, try glob fallback: `artifacts/tasks/*-<task-name>.md`
   - If still not found, report an error and list available tasks.
4. Read the current frontmatter from the task file.
5. Validate each field:value pair:
   - `agent` should match an agent in `agents/` (warn if not found,
     but allow it)
   - `owner` should be an agent name or `user` (warn if agent
     not found, but allow it)
   - Other frontmatter fields are updated as-is.
6. Show a before/after comparison of changed fields.
7. Apply the changes, preserving all other frontmatter fields and
   the full body content.
