# Open Station

Task management system for coding AI agents. Convention-first —
markdown specs + skills, minimal dependencies. Adding packages
or modules to existing components is fine; stay minimal.
Do not update CHANGELOG.md unless creating a new release.

## Vault Structure

```
docs/              — Project documentation (lifecycle, task spec, README)
artifacts/         — Canonical artifact storage (source of truth)
  tasks/           —   Task files (canonical location, never move)
  agents/          —   Agent specs (canonical location)
  research/        —   Research outputs
  specs/           —   Specifications & designs
agents/            — Agent discovery (symlinks → artifacts/agents/)
skills/            — Agent skills (operational knowledge, not user-invocable)
commands/          — User-invocable slash commands
```

Note: In target projects, these live under `.openstation/`. In
this source repo they live at the root.

## How Docs Connect

```
                        ┌──────────┐
                        │ CLAUDE.md│
                        └────┬─────┘
                             │
                  references │
             ┌───────────────┤
             ▼               ▼
      ┌────────────┐  ┌───────────┐
      │lifecycle.md │◄─┤task.spec.md│
      └──┬──────┬──┘  └───────────┘
         │      │
         │      └───────────┐
         ▼                  ▼
┌─────────────────────────────┐
│  skills/                    │
│  openstation-execute/       │──► lifecycle.md
└────────────────┬────────────┘    task.spec.md
                 │                 /openstation.create
      skills:    │                 /openstation.done
      execute    │
         ┌───────┴───────┐
         ▼               ▼
  ┌──────────┐    ┌──────────┐
  │researcher│    │  author  │
  └──────────┘    └──────────┘

┌─────────────────────────────────────────┐
│  commands/                               │
│  openstation.create.md  ──► lifecycle.md │
│  openstation.done.md    ──► lifecycle.md │
│  openstation.update.md  ──► lifecycle.md │
│  openstation.list.md                     │
│  openstation.dispatch.md──► agents/      │
└─────────────────────────────────────────┘
```

- **task.spec.md** — the shape (schema, naming, format)
- **lifecycle.md** — the state machine (transitions, ownership, artifacts)
- **storage-query-layer.md** — the storage model (canonical paths, frontmatter associations, queries)
- **execute skill** — the agent playbook (discovery, execution, completion)

## Task Structure

Each task is a single markdown file (`NNNN-slug.md`) stored
in `artifacts/tasks/`. See `docs/storage-query-layer.md` for
the full storage and query model.

## Spec Format

All specs use YAML frontmatter with a `kind` field (`task` or
`agent`) followed by markdown content. Every spec must have at
minimum `kind` and `name` fields.

## Creating a New Task

Use `openstation create "<description>"` or `/openstation.create`
to create tasks — both handle ID assignment and file creation.

For manual creation, see `docs/task.spec.md` for the format.

## CLI

The `openstation` CLI provides scriptable access to the vault:

```
openstation list [--status <s>] [--assignee <name>]
openstation agents
openstation show <task>
openstation create "<description>" [--assignee <a>] [--owner <o>] [--status <s>] [--parent <p>]
openstation status <task> <new-status>
```

## Dispatching an Agent

```bash
claude --agent researcher
```

The agent auto-loads the `openstation-executor` skill (via the
`skills` field in its frontmatter), finds its ready tasks, follows
the manual, and executes.

## Task Lifecycle

Statuses: `backlog` → `ready` → `in-progress` → `review` →
`done`/`failed`. See `docs/lifecycle.md` for transition rules,
ownership model, artifact storage, and promotion routing.

## Discovery

- `.claude/agents` → `agents/` for `--agent` resolution
- `.claude/commands` → `commands/` for slash command discovery
- `skills/` contains agent-only skills (not user-invocable)
- `commands/` contains user-invocable slash commands

## Query Model

Task discovery uses a dual-path approach: the **Obsidian CLI**
as primary query engine (requires Obsidian running) with
**filesystem + grep** as fallback (always available). Obsidian
is an optional dependency — the system is fully functional
without it. See `docs/storage-query-layer.md` Part II for
query patterns.

<!-- openstation:start -->
# Open Station

Task management system for coding AI agents. Convention-first —
markdown specs + skills, minimal dependencies. Adding packages
or modules to existing components is fine; stay minimal.
Do not update CHANGELOG.md unless creating a new release.

## Vault Structure

```
.openstation/
├── docs/              — Project documentation (lifecycle, task spec)
├── artifacts/         — Canonical artifact storage (source of truth)
│   ├── tasks/         —   Task files (canonical location, never move)
│   ├── agents/        —   Agent specs (canonical location)
│   ├── research/      —   Research outputs
│   └── specs/         —   Specifications & designs
├── agents/            — Agent discovery (symlinks → artifacts/agents/)
├── skills/            — Agent skills (not user-invocable)
└── commands/          — User-invocable slash commands
```

## Quick Start

Create a task:  `/openstation.create <description>`
List tasks:     `/openstation.list`
List agents:    `openstation agents`
Update a task:  `/openstation.update <name> field:value`
Run an agent:   `claude --agent <name>`
Complete task:  `/openstation.done <name>`

All relationships (parent/child, task/artifact) are encoded in
YAML frontmatter — no symlinks except `agents/` discovery
symlinks for Claude Code `--agent` resolution. The Obsidian CLI
is an optional query engine; filesystem + grep works everywhere.

See `.openstation/docs/lifecycle.md` for lifecycle rules,
`.openstation/docs/task.spec.md` for task format, and
`.openstation/docs/storage-query-layer.md` for the
storage and query model.
<!-- openstation:end -->
