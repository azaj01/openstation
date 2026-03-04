---
kind: spec
name: storage-query-layer
---

# Storage & Query Layer

Retrospective specification documenting Open Station's storage
model and query patterns as they exist today. This is the
authoritative reference for how tasks, artifacts, and agents are
stored on the filesystem and how they are discovered.

For lifecycle rules (status transitions, ownership, verification)
see `docs/lifecycle.md`. For task field schema and naming see
`docs/task.spec.md`.

---

## Part I — Storage Layer

### 1. Canonical Storage Model

All persistent data lives under `artifacts/`, which is the single
source of truth. Each artifact type has a dedicated subdirectory:

```
artifacts/
├── tasks/       — Task folders (one per task, never moved)
├── agents/      — Agent spec files (canonical location)
├── research/    — Research outputs (from researcher agent)
└── specs/       — Specifications and designs
```

**Immutability rule:** Once a folder or file is created in
`artifacts/`, it stays at that path permanently. Nothing in
`artifacts/` is ever moved or renamed — only its contents are
updated in place.

Tasks are folders (not files). Each task folder contains at
minimum an `index.md` with YAML frontmatter:

```
artifacts/tasks/0010-add-login-page/
└── index.md
```

All other artifact types are single files stored directly in
their category directory:

```
artifacts/agents/researcher.md
artifacts/research/obsidian-plugin-api.md
artifacts/specs/storage-query-layer.md
```

### 2. Symlink Graph

Open Station uses three kinds of symlinks, each serving a
distinct purpose:

#### 2a. Sub-task Symlinks (parent → child)

Symlinks inside a parent task folder that point to sibling
task folders in `artifacts/tasks/`. They establish the
parent-child relationship:

```
artifacts/tasks/0006-adopt-spec-kit-patterns/
├── index.md
├── 0007-add-constitution → ../0007-add-constitution
└── 0008-add-templates    → ../0008-add-templates
```

Sub-tasks are discovered only through their parent folder.

#### 2b. Discovery Symlinks (agent resolution)

Symlinks in `agents/` that point to canonical specs in
`artifacts/agents/`. They make agents available via
`claude --agent <name>`:

```
agents/researcher.md → ../artifacts/agents/researcher.md
```

Discovery symlinks are created by `/openstation.done` after
task verification — never during task execution.

#### 2c. Traceability Symlinks (task → artifact)

Symlinks inside a task folder that point back to the canonical
artifact the task produced. They record which task created which
artifact:

```
artifacts/tasks/0011-add-pm-agent/
├── index.md
└── project-manager.md → ../../agents/project-manager.md
```

These are created by agents during execution alongside storing
the canonical file.

### 3. Artifact Routing

During task execution, agents store artifacts in the appropriate
`artifacts/<category>/` directory. The routing table:

| Artifact Type        | Destination              |
|----------------------|--------------------------|
| Task creation        | `artifacts/tasks/`       |
| Researcher output    | `artifacts/research/`    |
| Agent spec           | `artifacts/agents/`      |
| Other agent output   | `artifacts/specs/`       |

Agents also record produced artifacts in the task's frontmatter
`artifacts` list using canonical paths:

```yaml
artifacts:
  - artifacts/agents/project-manager.md
  - artifacts/research/obsidian-plugin-api.md
```

### 4. Sub-task Storage

Sub-tasks are full tasks with their own canonical folder in
`artifacts/tasks/`, linked to a parent rather than standing
alone. They differ from top-level tasks in two ways:

1. **Parent field.** The sub-task's frontmatter sets
   `parent: <parent-task-name>`.
2. **Parent symlink.** The parent task folder contains a symlink
   to the sub-task folder (see § 2a).

#### Creating a sub-task

1. Create canonical folder: `artifacts/tasks/MMMM-sub-slug/`
   with `index.md`.
2. Set `parent: <parent-task-name>` in sub-task frontmatter.
3. Create symlink inside parent folder:
   `artifacts/tasks/NNNN-parent/MMMM-sub → ../MMMM-sub`
4. Add an entry to the parent's `## Subtasks` body section.

#### Blocking rule

All sub-tasks must reach `done` before the parent can proceed
to `review`.

#### Status tracking

Each sub-task tracks its own status in its `index.md`
frontmatter, following the same transitions as any task.

### 5. Install-time Layout

When installed into a target project via `install.sh`, the entire
vault is placed under `.openstation/`:

```
target-project/
├── .openstation/
│   ├── docs/                    — lifecycle.md, task.spec.md
│   ├── artifacts/
│   │   ├── tasks/
│   │   ├── agents/
│   │   ├── research/
│   │   └── specs/
│   ├── agents/                  — Discovery symlinks → artifacts/agents/
│   ├── skills/                  — Agent skills (openstation-execute)
│   ├── commands/                — Slash commands
│   └── hooks/                   — Pre-tool-use hooks
├── .claude/
│   ├── commands → ../.openstation/commands
│   ├── agents  → ../.openstation/agents
│   ├── skills  → ../.openstation/skills
│   └── settings.json            — Hook configuration
└── CLAUDE.md                    — Contains managed openstation section
```

**Claude Code integration** is achieved through three directory
symlinks in `.claude/` that point into `.openstation/`:

| `.claude/` entry  | Target                          | Purpose                  |
|-------------------|---------------------------------|--------------------------|
| `commands/`       | `../.openstation/commands`      | Slash command discovery   |
| `agents/`         | `../.openstation/agents`        | `--agent` resolution     |
| `skills/`         | `../.openstation/skills`        | Skill loading            |

The installer also:

- Places `.gitkeep` files in empty content directories.
- Deploys pre-tool-use hooks (`validate-write-path.sh`,
  `block-destructive-git.sh`) and registers them in
  `.claude/settings.json`.
- Injects a managed `<!-- openstation:start -->` …
  `<!-- openstation:end -->` section into `CLAUDE.md`.
- Copies example agent specs to `artifacts/agents/` (skippable
  with `--no-agents`) and creates their discovery symlinks.

### 6. Design Rationale

**Canonical paths are stable.** Task folders in `artifacts/tasks/`
never move or rename. Any reference to
`artifacts/tasks/NNNN-slug/` remains valid across all lifecycle
stages. Traceability symlinks and `artifacts` field entries never
go stale.

**Flat `artifacts/tasks/` over nested.** All task folders are
siblings under `artifacts/tasks/` rather than nested by status
or parent. This keeps:

- Task IDs globally unique and easily scannable (`ls artifacts/tasks/`).
- Sub-task symlinks simple (relative `../MMMM-slug` targets).
- No deep nesting that obscures the task list.

**Convention over database.** The filesystem *is* the database.
Markdown files with YAML frontmatter are both human-readable and
machine-parseable. This means:

- Zero runtime dependencies — no database server, no ORM, no
  migrations.
- Git-native — all state is versioned, diffable, and mergeable.
- Agent-friendly — LLM agents can read and write tasks with
  standard file tools (Read, Write, Edit, Glob, Grep).
- Portable — `install.sh` bootstraps the full system from a
  single script.

**Frontmatter as single source of truth.** Task lifecycle state
lives exclusively in the `status` frontmatter field — there is
no secondary representation to keep in sync. This eliminates
state-split bugs where one source says `ready` and another says
`in-progress`.

**Dual-path query model.** The Obsidian CLI
(`/Applications/Obsidian.app/Contents/MacOS/obsidian`) provides
fast structured property queries when Obsidian is running. The
filesystem + `grep` fallback covers headless and CI environments.
This layered approach offers:

- Fast interactive queries via `obsidian search` with
  `[property: value]` syntax and JSON output.
- Reliable fallback when Obsidian is not running — `grep` across
  `artifacts/tasks/*/index.md` achieves the same results.
- No hard dependency on Obsidian — the system is fully functional
  with filesystem queries alone.

---

## Part II — Query Layer

All query patterns support two execution paths: the **Obsidian
CLI** (primary, requires Obsidian running) and **filesystem**
(fallback, always available). The `openstation` CLI wraps both
paths with automatic fallback.

### 7. Find Tasks by Status

**Primary (Obsidian CLI):**

```bash
obsidian search vault="open-station" query='[kind: task] [status: ready]' format=json
```

**Fallback (filesystem):**

```bash
grep -rl 'status: ready' artifacts/tasks/*/index.md
```

The `openstation list --status <s>` CLI command wraps this
dual-path pattern.

### 8. Get Artifacts for a Task

Two complementary methods:

#### Frontmatter `artifacts` field

The task's `index.md` lists canonical paths to produced artifacts:

```yaml
artifacts:
  - artifacts/agents/project-manager.md
  - artifacts/research/obsidian-plugin-api.md
```

#### Traceability symlinks

The task folder contains symlinks to each artifact:

```
artifacts/tasks/0011-add-pm-agent/
├── index.md
└── project-manager.md → ../../agents/project-manager.md
```

To enumerate: list all symlinks in the task folder (excluding
`index.md` and sub-task symlinks which point to sibling
directories, not files).

### 9. Get Sub-tasks of a Parent

Sub-tasks are symlinked inside the parent folder. To enumerate:

```bash
# List sub-task symlinks (they point to sibling directories)
ls -l artifacts/tasks/NNNN-parent-slug/
```

Sub-task symlinks are directory symlinks with relative targets
of the form `../MMMM-sub-slug`. They are distinguishable from
traceability symlinks (which are file symlinks targeting
`../../<category>/<file>`).

To check sub-task statuses, read each sub-task's `index.md`:

```bash
for sub in artifacts/tasks/NNNN-parent/*/index.md; do
  grep 'status:' "$sub"
done
```

### 10. Find Tasks by Agent

**Primary (Obsidian CLI):**

```bash
obsidian search vault="open-station" query='[kind: task] [agent: researcher]' format=json
```

**Fallback (filesystem):**

```bash
grep -rl 'agent: researcher' artifacts/tasks/*/index.md
```

Combined filters (status + agent):

**Primary:**

```bash
obsidian search vault="open-station" query='[kind: task] [status: ready] [agent: researcher]' format=json
```

**Fallback:**

```bash
grep -rl 'status: ready' artifacts/tasks/*/index.md | xargs grep -l 'agent: researcher'
```

The `openstation list --agent <name>` CLI command wraps this.

### 11. Agent Discovery

Agents are discovered through symlinks in the `agents/`
directory. The resolution chain:

```
claude --agent researcher
  → .claude/agents/researcher.md          (Claude Code lookup)
  → ../.openstation/agents/researcher.md  (install-time symlink)
  → ../artifacts/agents/researcher.md     (discovery symlink)
```

In the source repo (no `.openstation/` prefix):

```
claude --agent researcher
  → .claude/agents/researcher.md
  → agents/researcher.md                  (discovery symlink)
  → ../artifacts/agents/researcher.md     (canonical file)
```

Discovery symlinks are created by:

- `install.sh` — for bundled example agents at install time.
- `/openstation.done` — for agents produced by tasks, after
  verification passes (agent promotion).

### 12. Query Patterns Summary

Quick-reference table mapping common queries to operations.
Frontmatter queries use the Obsidian CLI when available,
falling back to `grep` on the filesystem. ¹

| Query                        | Operation                                                       |
|------------------------------|-----------------------------------------------------------------|
| Tasks with status X          | `obsidian search query='[kind: task] [status: X]' format=json` ¹ |
| Tasks assigned to agent A    | `obsidian search query='[kind: task] [agent: A]' format=json` ¹  |
| Status + agent combined      | `obsidian search query='[kind: task] [status: X] [agent: A]' format=json` ¹ |
| Count tasks by status        | Add `total` flag to any search command above ¹                  |
| Tasks with a given parent    | `obsidian search query='[kind: task] [parent: <name>]' format=json` ¹ |
| Artifacts for task T         | Read `artifacts` field in task frontmatter, or `ls` task dir    |
| Sub-tasks of parent P        | `ls artifacts/tasks/P/` (directory symlinks = sub-tasks)        |
| Sub-task statuses            | `grep 'status:' artifacts/tasks/P/*/index.md`                  |
| Resolve agent name           | Follow `agents/<name>.md` → `artifacts/agents/<name>.md`       |
| All known agents             | `ls agents/`                                                    |
| Next available task ID       | `ls artifacts/tasks/ \| sort \| tail -1` then increment        |

¹ Fallback: `grep -rl '<field>: <value>' artifacts/tasks/*/index.md`
