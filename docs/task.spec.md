---
kind: spec
name: task-spec
---

# Task Specification

Defines the format for tasks in Open Station. A task is a
unit of work — a single markdown file with YAML frontmatter
and a markdown body.

## File Location

Every task file lives permanently in `artifacts/tasks/`:

```
artifacts/tasks/NNNN-kebab-slug.md
```

Task files are created here once and never move.

## Naming

### Task ID

- 4-digit zero-padded auto-incrementing integer (`0001`, `0042`)
- Unique across all tasks — scan `artifacts/tasks/` to find the
  next available ID

### Slug

- Kebab-case, max 5 words
- Descriptive of the task's goal
- Combined with ID: `NNNN-kebab-slug`

### Filename and `name` field

The filename (without `.md`) and the `name` frontmatter field
must match exactly: `NNNN-kebab-slug`.

### Sub-tasks

Sub-tasks are full tasks with their own ID and canonical file
in `artifacts/tasks/`, linked to a parent task via frontmatter
fields. See `docs/storage-query-layer.md` § 5 for the
full sub-task storage model.

#### Naming

Sub-task filename: `NNNN-kebab-slug.md` (same as any task).
The slug should be descriptive of the sub-task's goal — it
does not need to repeat the parent slug.

#### `parent:` field

Every sub-task sets `parent: "[[<parent-task-name>]]"` in its
frontmatter using an Obsidian wikilink. This is the only
required link back to the parent.

#### Parent body section

The parent task file should include a `## Subtasks` section
listing the sub-tasks with priority groups. See the
"Task with sub-tasks" example below.

## Frontmatter Schema

```yaml
---
kind: task              # Required. Always "task".
name: NNNN-kebab-slug   # Required. Matches filename (without .md).
status: backlog         # Required. See Status Values below.
assignee:               # Optional. Agent name assigned to execute.
owner: user             # Required. Who verifies. Default: "user".
parent:                 # Optional. "[[parent-task-name]]" (wikilink).
subtasks:               # Optional. List of "[[sub-task-name]]" (wikilinks).
artifacts:              # Optional. List of "[[artifact-path]]" (wikilinks).
created: YYYY-MM-DD     # Required. Date the task was created.
---
```

### Editing Guardrails

- Edit only the specific field being changed.
- Preserve all other fields unchanged.
- Always update frontmatter directly — never add a body
  comment as a substitute for a field update.

### Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kind` | string | yes | — | Always `task` |
| `name` | string | yes | — | `NNNN-kebab-slug`, matches filename (without `.md`) |
| `status` | enum | yes | `backlog` | Current lifecycle stage |
| `assignee` | string | no | empty | Agent assigned to execute the task |
| `owner` | string | yes | `user` | Who verifies: agent name or `user` |
| `parent` | string | no | empty | `"[[parent-task-name]]"` wikilink (for sub-tasks) |
| `subtasks` | list | no | empty | `"[[sub-task-name]]"` wikilinks (for parent tasks) |
| `artifacts` | list | no | empty | `"[[artifact-path]]"` wikilinks to produced artifacts |
| `created` | date | yes | — | ISO 8601 date (`YYYY-MM-DD`) |

### Status Values

| Value | Meaning |
|-------|---------|
| `backlog` | Created, not ready for execution |
| `ready` | Requirements defined, agent assigned |
| `in-progress` | Agent is actively working |
| `review` | Work complete, awaiting verification |
| `done` | Verification passed |
| `failed` | Verification failed |

See `docs/lifecycle.md` for valid transitions, ownership rules,
sub-task lifecycle, and artifact routing.

### Artifacts Field

The `artifacts` list uses **Obsidian wikilinks** pointing to the
canonical location in `artifacts/`. Examples:

```yaml
artifacts:
  - "[[artifacts/agents/project-manager]]"
  - "[[artifacts/research/obsidian-plugin-api]]"
```

See `docs/storage-query-layer.md` §§ 3c, 4 for artifact
associations and routing.

### Artifact Provenance Fields

Artifacts (agent specs, research outputs, etc.) should declare
provenance in their own frontmatter:

```yaml
agent: researcher                                # Which agent created this
task: "[[0044-storage-layer-replacement]]"       # Which task (wikilink)
```

Use `agent: manual` and omit `task` for manually created
artifacts. See `docs/storage-query-layer.md` §§ 3d, 3e.

## Body Structure

The markdown body follows the frontmatter. It starts with an
H1 title and contains required and optional sections.

### Required Sections

#### `# Title`

Human-readable task title as an H1 heading. Should clearly
describe the goal.

#### `## Requirements`

What needs to be done. Can contain:
- Prose descriptions
- Numbered sub-steps
- Sub-headings (H3) for grouping related requirements
- Tables, code blocks, and links as needed

Requirements should be concrete and testable.

#### `## Verification`

Checklist of items that must be true when the task is complete.
Each item is a GitHub-flavored markdown checkbox:

```markdown
## Verification

- [ ] First verification criterion
- [ ] Second verification criterion
```

Items are checked (`[x]`) as they are verified.

### Optional Sections

| Section              | Purpose                                                         |
| -------------------- | --------------------------------------------------------------- |
| `## Context`         | Background information, links to related tasks or research      |
| `## Subtasks`        | Decomposition into sub-tasks (H3 per group with numbered items) |
| `## Findings`        | Results discovered during research tasks                        |
| `## Recommendations` | Actionable suggestions based on findings                        |

Optional sections appear between Requirements and Verification
when present.

## Progressive Disclosure

Tasks start minimal and gain detail as they mature. Only add
fields and sections when they become relevant — never front-load
structure that isn't needed yet.

### Stages

| Stage          | Frontmatter                                  | Body                                                                  |
| -------------- | -------------------------------------------- | --------------------------------------------------------------------- |
| **Idea**       | `kind`, `name`, `status: backlog`, `created` | `# Title`, `## Requirements` (rough), `## Verification` (placeholder) |
| **Scoped**     | + `assignee`, `owner`                        | Requirements become concrete and testable                             |
| **Decomposed** | + `parent` wikilink (on sub-tasks)            | + `## Subtasks` with priority groups                                  |
| **In-flight**  | `status: in-progress`                        | + `## Context` if background is needed                                |
| **Completed**  | `status: done`                               | + `## Findings`, `## Recommendations` (research tasks)                |

### Rules

1. **Start with the minimum** — `kind`, `name`, `status`,
   `created`, a rough Requirements section, and placeholder
   Verification items. This is enough for backlog.
2. **Add assignment when ready** — set `assignee` and `owner`
   when the task moves to `ready`. Leave them empty until then.
3. **Decompose only when needed** — add `## Subtasks` and
   `parent` fields only if the task is too large for a single
   agent pass.
4. **Add output sections at the end** — `## Findings` and
   `## Recommendations` are written by agents during execution,
   not by the task author upfront.

## Examples

### Minimal backlog task

```markdown
---
kind: task
name: 0010-add-login-page
status: backlog
assignee:
owner: user
created: 2026-02-24
---

# Add Login Page

## Requirements

Create a login page with email and password fields. On submit,
call the `/auth/login` endpoint and redirect to the dashboard
on success.

## Verification

- [ ] Login page renders at `/login`
- [ ] Successful login redirects to `/dashboard`
- [ ] Invalid credentials show an error message
```

### Full investigation task

```markdown
---
kind: task
name: 0003-research-obsidian-plugin-api
status: done
assignee: researcher
owner: user
created: 2026-02-21
---

# Research Obsidian Plugin API

## Requirements

Investigate the Obsidian plugin API to understand how Open Station
could integrate with Obsidian as a plugin in the future. Focus on:

- How plugins read and write vault files
- How plugins can add custom views (e.g., a task board)
- How plugins hook into file change events

## Verification

- [x] Research notes cover all three focus areas
- [x] Notes include links to relevant Obsidian documentation
- [x] Findings include a recommendation on feasibility
```

### Task with sub-tasks

#### File structure

```
artifacts/tasks/
├── 0006-adopt-spec-kit-patterns.md   # subtasks: ["[[0007-...]]", "[[0008-...]]"]
├── 0007-add-constitution.md          # parent: "[[0006-adopt-spec-kit-patterns]]"
└── 0008-add-templates.md             # parent: "[[0006-adopt-spec-kit-patterns]]"
```

Sub-tasks are linked via frontmatter wikilinks: `subtasks` on
the parent, `parent` on each child.

#### Parent task (`0006-adopt-spec-kit-patterns.md`)

```markdown
---
kind: task
name: 0006-adopt-spec-kit-patterns
status: backlog
assignee: author
owner: user
subtasks:
  - "[[0007-add-constitution]]"
  - "[[0008-add-templates]]"
created: 2026-02-21
---

# Adopt Spec-Kit Patterns

Implement patterns learned from Spec-Kit research.

## Requirements

Adopt conventions that fit Open Station's zero-dependency
philosophy.

## Subtasks

### HIGH Priority

1. **Add constitution file** — Create `constitution.md` at vault
   root with versioned project principles.

2. **Add templates** — Create `templates/` with structured
   templates for tasks, agents, and research artifacts.

## Verification

- [ ] Constitution file exists and is referenced in manual
- [ ] Templates directory exists with task, agent, and research templates
```

#### Sub-task (`0007-add-constitution.md`)

```markdown
---
kind: task
name: 0007-add-constitution
status: backlog
assignee: author
owner: user
parent: "[[0006-adopt-spec-kit-patterns]]"
created: 2026-02-21
---

# Add Constitution File

## Requirements

Create `constitution.md` at vault root with versioned project
principles.

## Verification

- [ ] Constitution file exists and is referenced in manual
```
