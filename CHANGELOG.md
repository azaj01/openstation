# Changelog

## v0.13.0

Autonomous task chaining and worktree artifact resolution.
Promotes a task to `ready` and hooks drive it through the
entire lifecycle without human intervention. Linked worktree
agents can now reliably find vault artifacts via the
`OPENSTATION_HOME` environment variable.

### Features

- **Autonomous task chaining hooks** — Four post-transition hooks
  (`auto-start`, `auto-verify`, `auto-accept`, chain-next) enable
  fully autonomous execution. Promote a task to `ready` and it
  runs through `in-progress → review → verified → done`
  automatically. Includes `bin/os-dispatch` orchestrator and
  `autonomous.enabled` setting toggle.
- **`OPENSTATION_HOME` env var** — `openstation run` now sets
  `OPENSTATION_HOME` (absolute path to `.openstation/`) before
  launching agent sessions. Agents use it to resolve vault
  artifacts in all modes — fixes linked worktree agents failing
  to find tasks via relative Search/Glob patterns.

### Skill

- **Execute skill updated** — New `## Environment` section
  documents `OPENSTATION_HOME`. Worktree awareness section
  rewritten to use the env var instead of mode-specific caveats.
  Fallback discovery path uses `$OPENSTATION_HOME/artifacts/tasks/`
  instead of broken relative pattern.

### Internal

- **Run prompt improved** — All launch paths (detached, attached,
  verify, by-agent) include the `OPENSTATION_HOME` value in the
  prompt, replacing the linked-mode-only hint.

## v0.12.0

Suspend and rework flows, the `rejected` status rename, and
worktree-aware agent dispatch. Tasks can now be suspended back
to ready/backlog, verification failures send tasks back to
in-progress for rework, and `failed` is replaced by `rejected`
across the lifecycle.

### Breaking

- **`failed` → `rejected`** — The `failed` status is renamed to
  `rejected` everywhere (lifecycle, CLI, commands, docs). Existing
  tasks with `status: failed` must be updated to `status: rejected`.

### CLI

- **`suspend` subcommand** — `openstation suspend <task>` moves a
  task from `in-progress` back to `ready` (default) or `backlog`.
  Includes `/openstation.suspend` command and skill documentation.
- **`create --body` flag** — `openstation create "<desc>" --body
  "<content>"` sets the task body content inline, skipping the
  default template scaffold.
- **`review → in-progress` transition** — Failed verification now
  sends tasks back to `in-progress` for rework instead of leaving
  them stuck in `review`. The `/openstation.verify` command updated
  to use this transition automatically.

### Lifecycle

- **Rework loop** — `review → in-progress` is now a valid
  transition, enabling iterative verification without manual
  `--force` overrides.
- **Suspend transitions** — `in-progress → ready` and
  `in-progress → backlog` documented and supported via the
  `suspend` subcommand.

### Worktree

- **Worktree integration** — Agent dispatch supports worktree
  execution with proper vault resolution across primary and linked
  worktrees.

### Internal

- **Dynamic init discovery** — `openstation init` now discovers
  docs, skills, and templates dynamically instead of maintaining
  a hardcoded file list.
- **Verification report persistence** — Verification results are
  persisted as a `## Verification Report` section in the task file
  after `/openstation.verify` runs.

## v0.11.0

Unified vault convention — all vault files now live under
`.openstation/` everywhere, including the source repo. Removes the
dual-path detection (root-level vs `.openstation/`) and the `prefix`
parameter that threaded through every module. Also includes worktree
improvements, self-update, and documentation fixes.

### Breaking

- **`.openstation/`-only convention** — The source repo now uses
  `.openstation/` for vault directories (`artifacts/`, `agents/`,
  `skills/`, `commands/`, `docs/`, `templates/`). The old root-level
  layout (`agents/ + install.sh` marker) is no longer detected.
  Installed projects are unaffected (they already use `.openstation/`).
- **`find_root` return type** — Returns `Path | None` instead of
  `(Path, str)` tuple. The `prefix` parameter is removed from all
  ~25 public function signatures across `core.py`, `cli.py`,
  `tasks.py`, `run.py`, `artifacts.py`, and `hooks.py`.
- **Source guard removed** — `openstation init` no longer refuses to
  run inside the source repo. `EXIT_SOURCE_GUARD` (exit code 9)
  removed.

### CLI

- **`vault_path()` helper** — New canonical path builder in `core.py`:
  `vault_path(root, "artifacts", "tasks")` replaces all `if prefix:`
  branching (12 occurrences across 5 modules).
- **`self-update` subcommand** — `openstation self-update` updates
  the local install cache from the remote repository.
- **Worktree CWD fix** — Detached `openstation run` in worktrees now
  correctly uses the original CWD for Claude execution.

### Worktree

- **`find_root` rewrite** — Uses `git rev-parse --show-toplevel` as
  primary resolution with `--git-common-dir` fallback for linked
  worktrees. Replaces the walk-up filesystem scan.
- **Independent vs linked modes** — Documented in `docs/worktrees.md`.
  Worktrees with their own `.openstation/` are independent; those
  without fall back to the main repo's vault.

### Docs

- **`docs/worktrees.md`** — New documentation covering primary and
  linked worktree modes, vault resolution, and agent dispatch.
- **Verify agent setting** — `settings.json` supports
  `verify.agent` for project-level verification agent defaults.

## v0.10.0

Lifecycle hooks, a `verified` status gate, and the `--verify` flag
for agent-driven task verification. Hooks enable automated actions
on status transitions (e.g., auto-commit on completion), while the
new verified status adds a mandatory review checkpoint before tasks
reach done.

### CLI

- **`--verify` flag** — `openstation run --task <id> --verify`
  launches an agent in verification mode, loading the task's
  `## Verification` section as the prompt. Agent resolution follows
  a 4-level priority chain: `--agent` > task `owner` (skips
  `user`/empty) > `settings.verify.agent` > `project-manager`
  fallback.
- **`verified` status** — New status between `review` and `done`.
  `openstation status <task> verified` transitions review →
  verified. The full chain is now `backlog → ready → in-progress →
  review → verified → done/failed`.
- **`--force` flag for `status`** — `openstation status <task>
  <status> --force` bypasses transition validation, allowing any
  status change.
- **`--editor` flag** — Renamed from `--vim` across `list`, `show`,
  and `agents show`. Opens files in `$EDITOR`.
- **Interactive status picker** — `openstation status <task>`
  without a target status presents an interactive picker showing
  valid transitions.
- **CLI defaults in settings** — `settings.json` now supports
  `defaults.run.attached`, `defaults.run.worktree`, and
  `defaults.run.dsp` keys to set project-level defaults for
  `openstation run`.

### Hooks

- **Lifecycle hooks engine** — Status transitions can trigger hooks
  defined in `settings.json`. Supports `pre` and `post` phases with
  `command` type hooks. Configuration documented in `docs/hooks.md`.
- **Post-transition hooks** — Hooks fire after the status transition
  completes, enabling side effects like notifications or artifact
  generation.
- **Auto-commit hook** — Built-in `auto-commit` hook
  (`bin/hooks/auto-commit`) commits task artifacts when a task
  transitions to `done` or `verified`. Requests user permission
  before committing.

### Commands

- **Updated `done` and `verify`** — `/openstation.done` and
  `/openstation.verify` updated to support the `verified` status
  gate. Verify command now transitions to `verified`; done
  transitions from `verified` to `done`.
- **Updated `create`** — `/openstation.create` updated for future
  hooks integration (task creation support specs added).

### Specs & Docs

- **`verified` status in lifecycle** — `docs/lifecycle.md` and
  `docs/task.spec.md` updated with the new status, transition
  rules, and ownership model.
- **`docs/hooks.md`** — New documentation for lifecycle hooks
  configuration, built-in hooks, and custom hook authoring.
- **`docs/settings.md`** — New settings reference documenting all
  `settings.json` keys including `verify.agent`, CLI defaults, and
  hooks.
- **Architecture section required** — Feature specs now require an
  `## Architecture` section per `docs/task.spec.md`.

### Research

- **Worktree merge-back workflow** — Research into strategies for
  merging agent work from worktree branches back to the parent
  branch (`artifacts/research/worktree-merge-back-workflow.md`).

## v0.9.0

Worktree integration, feedback loops, lifecycle hooks, and a new
`artifacts` CLI subcommand. Agents can now run in isolated
worktrees, communicate progress back to task owners, and the
system gains a spec for hook-based lifecycle automation.

### CLI

- **`artifacts` subcommand** — `artifacts list` and `artifacts show`
  for browsing research, specs, and agent artifacts from the CLI.
  Includes comprehensive test suite.
- **`--worktree` pass-through** — `openstation run --worktree`
  passes through to `claude --worktree`, enabling agent execution
  in isolated git worktrees. Includes alias resolution and CLI
  tests.
- **Agent aliases** — Agents now declare `aliases` in frontmatter
  (e.g. `dev` for `developer`). CLI resolves aliases across `run`,
  `agents show`, and `list --assignee`.

### Commands

- **`/openstation.progress`** — New slash command for recording
  structured progress entries on tasks, with worktree metadata
  support.
- **DRY slash commands** — Centralized task resolution logic
  across `done`, `list`, `ready`, `reject`, `show`, `update`, and
  `verify` commands, reducing duplication.
- **Tightened verification flow** — `done` and `verify` commands
  updated with stricter verification guardrails.

### Specs & Docs

- **Task lifecycle hooks spec** — Design for hook-based automation
  on status transitions (`artifacts/specs/task-lifecycle-hooks.md`).
  Covers configuration schema, execution model, and built-in hooks.
- **Feedback loop spec updates** — Added Progress convention and
  Downstream section to the assignee-reviewer feedback loop spec.
  Implemented changes across lifecycle docs, task spec, and execute
  skill.
- **Worktree pass-through spec** — Design for CLI worktree flag
  forwarding to Claude Code.
- **Storage query layer rewrite** — Rewrote for CLI-first queries,
  removing Obsidian dependency from the primary path.
- **Task spec expanded** — Added scope authority rules, milestone
  examples, and progress entry format with worktree metadata.

### Research

- **Worktree integration** — Research into git worktree support for
  parallel agent execution, including branch scoping and cleanup
  behavior.
- **Paperclip extension model** — Comparative analysis of Open
  Station vs Paperclip's extension model and workflows.

### Agents

- **Aliases added** — All six agent specs now include an `aliases`
  field for shorthand resolution.

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
