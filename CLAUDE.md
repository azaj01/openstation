# Open Station

Task management system for coding AI agents. Convention-first —
markdown specs + skills, minimal dependencies. Adding packages
or modules to existing components is fine; stay minimal.

## Vault Structure

```
docs/              — Project documentation (lifecycle, task spec, README)
tasks/             — Lifecycle buckets (contain symlinks, not real folders)
  backlog/         —   Not yet ready for agents
  current/         —   Active work (ready → in-progress → review)
  done/            —   Completed tasks
artifacts/         — Canonical artifact storage (source of truth)
  tasks/           —   Task folders (canonical location, never move)
  agents/          —   Agent specs (canonical location)
  research/        —   Research outputs
  specs/           —   Specifications & designs
agents/            — Agent discovery (symlinks → artifacts/agents/)
skills/            — Agent skills (operational knowledge, not user-invocable)
commands/          — User-invocable slash commands
```

Note: `install.sh` places these under `.openstation/` in target
projects. In this source repo they live at the root.

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
- **storage-query-layer.md** — the storage model (canonical paths, symlinks, queries)
- **execute skill** — the agent playbook (discovery, execution, completion)

## Task Structure

Each task is a folder with an `index.md` inside, stored
canonically in `artifacts/tasks/`. Lifecycle buckets contain
symlinks to these folders. See
`artifacts/specs/storage-query-layer.md` for the full storage
and query model.

## Spec Format

All specs use YAML frontmatter with a `kind` field (`task` or
`agent`) followed by markdown content. Every spec must have at
minimum `kind` and `name` fields.

## Creating a New Task

Use `/openstation.create` to create tasks interactively — it
handles ID assignment, folder creation, and symlink placement.

For manual creation, see `docs/task.spec.md` for the format
and `artifacts/specs/storage-query-layer.md` § 3 for symlink
placement.

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

<!-- openstation:start -->
# Open Station

Task management system for coding AI agents. Convention-first —
markdown specs + skills, minimal dependencies. Adding packages
or modules to existing components is fine; stay minimal.

## Vault Structure

```
.openstation/
├── docs/              — Project documentation (lifecycle, task spec)
├── tasks/             — Lifecycle buckets (contain symlinks)
│   ├── backlog/       —   Not yet ready for agents
│   ├── current/       —   Active work (ready → in-progress → review)
│   └── done/          —   Completed tasks
├── artifacts/         — Canonical artifact storage (source of truth)
│   ├── tasks/         —   Task folders (canonical location, never move)
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
Update a task:  `/openstation.update <name> field:value`
Run an agent:   `claude --agent <name>`
Complete task:  `/openstation.done <name>`

See `.openstation/docs/lifecycle.md` for lifecycle rules,
`.openstation/docs/task.spec.md` for task format, and
`.openstation/artifacts/specs/storage-query-layer.md` for the
storage and query model.
<!-- openstation:end -->
