# Changelog

## v0.8.0

Replaces the tier model with attached/detached modes, expands
`agents` into a subcommand group, adds user-level init, a verify
command, and `--dangerously-skip-permissions` passthrough.

### CLI

- **Attached mode** (`--attached` / `-a`) — Replaces `--tier 1`.
  Uses `os.execvp` to replace the process with an interactive
  `claude --agent` session. No log capture, no budget/turns
  limits. Works for both by-agent and by-task runs.
- **Detached mode** (default) — Replaces `--tier 2`. Runs with
  `stream-json` output, captures session ID and logs, enforces
  budget/turns limits. Clear incompatibility checks prevent
  mixing attached-only and detached-only flags.
- **`agents` subcommand group** — `agents` is now a subcommand
  with `list` and `show` actions. `agents list` replaces the
  bare `agents` command (still works as default). `agents show
  <name>` prints the full agent spec with `--json` and `--vim`
  output modes. `ag` alias available for brevity.
- **`init --user`** — Installs `.claude/` discovery files
  (commands, agents, skills) to `~/.claude/` via absolute
  symlinks to the local install cache. Enables Open Station
  commands in any project without per-project init.
- **`/openstation.verify`** — New slash command for structured
  task verification. Reads the `## Verification` section,
  gathers evidence for each criterion, and presents a pass/fail
  report before transitioning to done.
- **`--dangerously-skip-permissions`** (`-dsp`) — New flag on
  `run` that passes through to `claude` for fully autonomous
  execution without permission prompts.
- **CLI reference doc** (`docs/cli.md`) — Comprehensive CLI
  reference covering all commands, flags, examples, and exit
  codes.
- **Removed `/openstation.dispatch`** — Replaced by
  `openstation run --attached`.

### Agents

- **DevRel agent** — New agent spec for developer relations
  content: tweets, blog posts, README sections, and community
  engagement copy. Template added to `templates/agents/`.

### Research & Specs

- **Attached mode research** — Analysis of Claude Code's
  `--agent` flag behavior, permission models, and UX
  implications for interactive vs autonomous execution.
- **Worktree integration research** — Investigation of git
  worktree support for parallel agent execution across
  isolated working directories.
- **Agents subcommand expansion spec** — Design for the
  `agents list` / `agents show` subcommand structure.
- **Assignee-reviewer feedback loop spec** — Design for
  backward status transitions enabling agents to request
  clarification from task owners.
- **Branch-based task scoping spec** — Design for associating
  tasks with git branches for parallel development workflows.

### Fix

- Restored tasks, specs, and content lost in prior rebase.
- Restored devrel agent lost in prior rebase.

## v0.7.0

Refactors CLI into an installable Python package, adds session ID
capture to `openstation run`, and extends `list`/`show` with
editor integration.

### CLI

- **`src/openstation/` package** — Extracted CLI from single-file
  `bin/openstation` into a proper Python package with modules:
  `core.py`, `tasks.py`, `run.py`, `init.py`, `cli.py`. Supports
  `python -m openstation` and `pyproject.toml` entry point.
- **Session ID capture** — `openstation run` now uses
  `--output-format stream-json` to capture the Claude session ID.
  Prints the session ID after execution and shows a
  `claude --resume <id>` command for every run. Logs saved as
  `.jsonl` files in `artifacts/logs/`.
- **Result text output** — `openstation run` prints the agent's
  final result text to stderr after execution, restoring operator
  visibility lost in the format switch.
- **`list --vim`** — Opens filtered task files in `$EDITOR` (vim
  by default). Mutually exclusive with `--json` and `--quiet`.
- **`show --vim`** — Opens a single task file in `$EDITOR`.
- **Short flags** — Added `-j` for `--json`, `-v` for `--vim`,
  `-q` for `--quiet` across `list`, `show`, and `run` subcommands.
- **`type` field** — Tasks now carry a `type` frontmatter field
  (`feature`, `research`, `spec`, `implementation`, `documentation`).
  `list --type` filters by type; defaults to `feature` for
  untyped tasks.

### Run UX

- **Structured output** — Run output uses visual hierarchy:
  timestamped headers, step counters, detail lines, and
  color-coded success/failure indicators.
- **Progress reporting** — Intermediate steps (agent resolution,
  tool parsing, launch command) are now visible during execution.
- **Resume instructions** — Every run prints
  `claude --resume <session-id>` at the end. Summary block shows
  remaining tasks and exact re-run command on partial completion.

### Docs

- **README rewrite** — Features-first layout, competitor
  comparison, flow diagram, agents table.

## v0.6.0

Switches to an nvm-style installation model — the installer clones
the full repo locally and `openstation init` copies from that cache
instead of downloading files from GitHub.

### Install

- **nvm-style installer** — `install.sh` now clones the repo to
  `~/.local/share/openstation/` (or `$OPENSTATION_DIR`), symlinks
  the CLI binary to `~/.local/bin/openstation`, and auto-configures
  PATH in the user's shell profile. Falls back to curl-based
  download when git is unavailable.
- **Local-cache init** — `openstation init` reads files from the
  local install cache instead of fetching from GitHub. Removes the
  `--local` flag; uses `OPENSTATION_DIR` environment variable for
  source resolution.
- **`.version` file** — CLI version is now read from a `.version`
  file at the repo root, replacing the previous `git describe`
  approach for reliable version reporting in installed copies.

### Skills

- **Release changelog steps** — Updated release checklist to include
  writing `.version` and updating `OPENSTATION_VERSION` in `install.sh`.

## v0.5.1

Delivers the release-changelog skill and switches CLI versioning
to derive from git tags automatically.

### Skills

- **Release changelog skill** — Delivered `skills/release-changelog/SKILL.md`
  with full workflow: conventional-commit parsing, domain-category mapping,
  version recommendation, and idempotency checks. Completes tasks 0072/0073.

### CLI

- **Git-derived version** — `openstation --version` now reads the version
  from `git describe --tags` instead of a hardcoded string, eliminating
  manual version bumps on release.

## v0.5.0

New `openstation init` command for project setup, flexible task ID
resolution, and a field rename from `agent` to `assignee` across
the vault.

### CLI

- **`openstation init`** — New project setup command replacing the
  monolithic `install.sh`. Creates `.openstation/` directory structure,
  copies agent templates, installs commands and skills, and sets up
  `.claude/` discovery symlinks. Simpler, more focused than the old
  installer.
- **Flexible task ID resolution** — `openstation show`, `status`, and
  other task commands now accept bare numbers (`42`), zero-padded IDs
  (`0042`), or full slugs (`0042-my-task`). Prefix matching finds the
  right file.
- **`--version` flag** — `openstation --version` prints the current
  version.
- **`openstation list --all`** — New `--all` flag shows done/failed
  tasks alongside active ones. Default behavior unchanged (active only).

### Agents

- **Tightened author agent spec** — Applied prompting best practices
  from research task 0066. Clearer constraints, better-structured
  instructions.
- **Agent templates** — Project-agnostic agent templates in
  `templates/agents/` (architect, author, developer, project-manager,
  researcher) for use by `openstation init`.

### Specs & Docs

- **`agent.spec.md`** — New agent specification document defining
  the schema, format, and conventions for agent specs.
- **General agent templates spec** — Design spec for project-agnostic
  agent templates with role-based customization.
- **`init` command spec** — Simplified from the original design,
  removing hooks, CLAUDE.md injection, and deprecated launcher
  references.

### Skills

- **Release changelog skill** — New skill at
  `skills/release-changelog/SKILL.md` for generating changelog entries
  from conventional commits with domain-specific categorization.
  Includes research artifact at
  `artifacts/research/changelog-skill-patterns.md`.

### Architecture

- **`agent` → `assignee` rename** — Task frontmatter field renamed
  from `agent` to `assignee` across all task files, CLI, commands,
  docs, and skills. Better reflects the field's purpose.
- **Removed `openstation-run.sh`** — Deprecated shell launcher removed.
  Agent execution now uses `claude --agent` directly.
- **Simplified `install.sh`** — Reduced from ~450 lines to a minimal
  bootstrap that delegates to `openstation init`.

## v0.4.0

Single-file task storage, CLI write commands, and a new storage &
query layer spec. Eliminates folder-per-task and symlink buckets
in favor of flat `NNNN-slug.md` files in `artifacts/tasks/`.

### Architecture

- **Single-file tasks** — Tasks are now individual markdown files
  (`NNNN-slug.md`) in `artifacts/tasks/`, replacing the
  folder-per-task + `index.md` model. Status lives in YAML
  frontmatter; no more symlink buckets (`tasks/backlog/`,
  `tasks/current/`, `tasks/done/`).
- **Storage & query layer spec** (`docs/storage-query-layer.md`) —
  New spec defining the canonical storage model, frontmatter
  associations (parent/subtask, task/artifact), and dual-path
  query approach (Obsidian CLI primary, filesystem + grep
  fallback).

### CLI

- **`openstation create`** — Create tasks from the command line
  with `--agent`, `--owner`, `--status`, and `--parent` options.
  Handles ID assignment, slug generation, and atomic file creation.
- **`openstation status`** — Change task status via
  `openstation status <task> <new-status>`.
- **`openstation agents`** — List available agents with
  descriptions.
- **`openstation list` active-only default** — Excludes done/failed
  tasks by default (was already documented but now enforced).
- **`openstation run` auto-detect** — Automatically distinguishes
  task IDs from agent names, removing ambiguity in
  `openstation run <arg>`.
- **Test suite expanded** — Tests covering all new write commands
  and updated storage model.

### Specs & Docs

- **Deduplicated docs** — Lifecycle, task spec, and execute skill
  now reference `docs/storage-query-layer.md` as the single source
  of truth for storage rules, eliminating duplicated storage
  guidance.
- **Updated task spec** (`docs/task.spec.md`) — Reflects single-file
  format with inline frontmatter schema.
- **Updated lifecycle** (`docs/lifecycle.md`) — Simplified
  transition rules without symlink move procedures.
- **CLI write commands spec** (`artifacts/specs/cli-write-commands.md`)
  — Design spec for the `create`, `status`, and `agents`
  subcommands.

### Commands

- **Updated `/openstation.create`** — Interview-driven workflow
  that delegates to `openstation create` CLI.
- **Updated `/openstation.done`**, **`/openstation.ready`**,
  **`/openstation.reject`** — Adapted for single-file tasks
  (frontmatter update instead of symlink moves).
- **Updated `/openstation.update`** — Simplified for flat file
  model.

### Install

- Updated `install.sh` for single-file task layout.
- Removed symlink bucket creation from install script.

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
