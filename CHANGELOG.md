# Changelog

## v0.3.0

Python CLI with read and run commands. Autonomous agent execution
with tiered launch model. New architect and developer agents.

### CLI

- **`openstation` Python CLI** — Single-file CLI (`bin/openstation`)
  with `list`, `show`, and `run` subcommands. Replaces ad-hoc
  shell scripts with a unified entry point.
- **`openstation run`** — Launch agents via `openstation run <agent>`
  (by-agent) or `openstation run --task <id>` (by-task). Supports
  `--tier` (1/2), `--budget`, `--turns`, `--max-tasks`, `--force`,
  `--dry-run`. Uses `os.execvp` for single launches, `subprocess.run`
  for task queues.
- **`openstation list`** — Tabular task listing with `--status` and
  `--agent` filters. Excludes done/failed by default.
- **`openstation show`** — Display full task spec by ID or slug
  with prefix matching.
- **Test suite** — 39 tests covering all CLI subcommands
  (`tests/test_cli.py`).

### Autonomous Execution

- **Tiered launch model** — Tier 1 (interactive with
  `--permission-mode acceptEdits`) and Tier 2 (autonomous with
  budget/turns limits and `--output-format json`).
- **`openstation-run.sh`** — Shell launcher with `--task` mode
  (subtask orchestration), `--force` flag, agent resolution,
  allowed-tools parsing, and live streaming progress.
- **By-task orchestration** — `--task` flag resolves a parent task,
  discovers ready subtasks, and launches agents sequentially with
  `--max-tasks` limit.

### Agents

- **Architect agent** — Design and specification agent for feature
  specs and system architecture.
- **Developer agent** — Python implementation agent for CLI and
  tooling work.

### Specs & Docs

- **Feature spec format** (`docs/feature-spec.md`) — Standardized
  format for feature specifications with problem, architecture,
  components, and design decisions.
- **CLI feature spec** (`artifacts/specs/cli-feature-spec.md`) —
  Spec for the Python CLI design (single-file, zero-dependency).
- **CLI run spec** (`artifacts/specs/cli-run-spec.md`) — Spec for
  the `run` subcommand interface, execution model, and error
  handling.
- **Autonomous execution spec** — Research and design for the
  tiered agent launch model.
- **Subtask conventions** — Codified subtask symlink placement,
  `parent:` field, and status tracking across all docs.

### Commands

- **Updated `/openstation.dispatch`** — Now references
  `openstation run` with tier 1, tier 2, and `--task` launch
  instructions.
- **Updated `/openstation.list`** — Delegates to `openstation list`
  CLI with fallback to manual scan.
- **Updated `/openstation.show`** — Delegates to `openstation show`
  CLI with fallback to manual file read.
- **Updated `/openstation.create`** — Streamlined for CLI
  integration.

### Install

- Updated `install.sh` to install `bin/openstation` CLI.
- Execute skill updated with CLI-aware agent workflows.

### Fix

- Removed stale `.openstation/` directory from source repo.
- Fixed Claude Code hook matcher format (regex string, not object).

## v0.2.1

Unified artifact promotion flow. Agent specs now follow the same
canonical-in-artifacts + symlink-for-discovery pattern as tasks.

### Architecture

- **Agent specs as artifacts** — Agent specs moved from `agents/`
  to `artifacts/agents/` (canonical location). `agents/` now
  contains discovery symlinks (`agents/X.md →
  ../artifacts/agents/X.md`), matching the task symlink pattern.
- **Agent promotion** — `/openstation.done` now promotes agent
  specs by creating discovery symlinks in `agents/` for any
  agent artifacts found in the completed task folder.

### Agents

- **Project manager agent** — New coordination agent for task
  management, agent assignment, artifact oversight, docs
  maintenance, and roadmap planning.

### Docs & Skills

- **Lifecycle** (`docs/lifecycle.md`) — Added agent row to
  routing table, agent promotion section, updated directory
  purposes.
- **Task spec** (`docs/task.spec.md`) — Added canonical path
  guidance for `artifacts:` field and task-folder symlink
  traceability pattern.
- **Execute skill** — Updated vault structure and artifact
  routing with explicit agent/research/specs destinations.

### Install

- `install.sh` writes agents to `artifacts/agents/` and creates
  discovery symlinks in `agents/`.
- Added `artifacts/agents/` to managed directories.
- Updated managed CLAUDE.md section.

### Fix

- Restructured execute skill to directory format for Claude Code
  auto-loading (`skills/openstation-execute/SKILL.md`).

## v0.2.0

Major restructuring of the vault layout, specs, and lifecycle
model. Tasks become first-class artifacts with a symlink-based
architecture.

### Architecture

- **Tasks as artifacts** — Task folders now live permanently in
  `artifacts/tasks/` with `index.md` as the canonical file.
  Lifecycle buckets (`tasks/backlog/`, `tasks/current/`,
  `tasks/done/`) contain folder-level symlinks pointing back to
  the canonical location. "Moving" a task between stages means
  deleting the symlink from one bucket and creating it in another.
- **Renamed `task.md` → `index.md`** — The primary file in each
  task folder is now `index.md` (conventional name for a folder's
  main document).
- **Vault restructured** — Flat file layout replaced with
  folder-per-task structure (`NNNN-slug/index.md`). Status buckets
  (`backlog/`, `current/`, `done/`) replace the single `tasks/`
  directory. Artifacts moved to `artifacts/research/` and
  `artifacts/specs/`.

### Specs & Docs

- **Task specification** (`docs/task.spec.md`) — New formal spec
  defining task format, YAML frontmatter schema, naming
  conventions, progressive disclosure stages, and examples.
- **Lifecycle rules** (`docs/lifecycle.md`) — Renamed from
  `workflow.md`. Deduplicated with task spec. Added symlink move
  procedure, artifact routing table, and directory purposes.
- **Execute skill** (`skills/openstation-execute/`) — Merged
  the standalone manual into the skill. Added Record Findings
  step, verification guardrails, and agent ownership rules.

### Commands

- **New commands:**
  - `/openstation.ready` — Promote backlog → ready with
    requirements validation
  - `/openstation.reject` — Reject a task in review → failed
  - `/openstation.show` — Display full task details
- **Updated `/openstation.update`** — No longer handles status
  changes. Only edits metadata fields (agent, owner, parent).
  Status transitions use dedicated commands.
- **Updated `/openstation.create`** — Scans `artifacts/tasks/`
  for next ID. Creates canonical folder + backlog symlink.
- **Updated `/openstation.done`** — Moves symlink instead of
  folder.
- **Removed** speckit commands (analyze, checklist, clarify,
  constitution, implement, plan, specify, tasks, taskstoissues).

### Install

- `install.sh` creates `artifacts/tasks/` directory.
- Installs new commands (ready, reject, show).
- Updated managed CLAUDE.md section with symlink-aware vault
  structure.

### Cleanup

- Removed outdated design artifacts
  (`artifacts/specs/001-open-station/`).
- Removed standalone `docs/manual.md` (merged into execute
  skill).
- Migrated all 10 existing tasks to `artifacts/tasks/` with
  symlinks in their respective buckets.

## v0.1.0

Initial release. Built the core vault structure, agent model,
and task lifecycle from scratch.

### Core

- **Vault structure** — `tasks/`, `agents/`, `skills/`,
  `commands/`, `artifacts/`, `docs/` directory layout with
  YAML frontmatter conventions.
- **Task lifecycle** — `backlog` → `ready` → `in-progress` →
  `review` → `done`/`failed` status machine with folder-move
  semantics.
- **Auto-incrementing IDs** — 4-digit zero-padded task IDs
  (`0001`, `0042`) with kebab-case slugs.
- **Owner/verifier model** — `owner` field (renamed from
  `verifier`) controls who may approve or reject a task.
  Agents cannot self-verify.

### Agents & Skills

- **Researcher agent** — Research-focused agent spec.
- **Author agent** — Structured vault content authoring agent.
- **Execute skill** (`openstation-execute/`) — Agent playbook
  for task discovery, execution, artifact storage, and
  completion.
- **Manual** (`docs/manual.md`) — Standalone agent operating
  guide (later merged into execute skill in v0.2.0).

### Commands

- `/openstation.create` — Create a new task from a description.
- `/openstation.list` — List all tasks with status and filters.
- `/openstation.update` — Update task frontmatter fields
  (including status transitions).
- `/openstation.done` — Mark a task done and archive it. Merged
  the separate promote step into a single command.
- `/openstation.dispatch` — Preview agent details and show
  launch instructions.

### Infrastructure

- **`install.sh`** — Bootstrap script to install Open Station
  into any project. Supports `--local` and `--no-agents` flags.
  Creates directories, installs commands/skills/agents, sets up
  `.claude/` symlinks, and manages a section in `CLAUDE.md`.
- **README** with install instructions, quick start, vault
  structure, architecture diagram, and commands reference.
- **Renamed** from "Agent Station" to "Open Station".

### Design Artifacts (removed in v0.2.0)

- Initial design document, feature spec, implementation plan,
  data model, and research notes in `artifacts/specs/001-open-station/`.
- Spec-Kit integration commands (9 speckit.* commands).
