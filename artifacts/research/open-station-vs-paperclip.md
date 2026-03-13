---
kind: research
name: open-station-vs-paperclip
agent: researcher
task: "[[0125-compare-open-station-with-paperclip]]"
created: 2026-03-13
---

# Open Station vs Paperclip: Comparative Analysis

## Executive Summary

Open Station and Paperclip solve related but fundamentally different
problems. **Open Station** is a convention-first task management
system for individual coding agents — markdown specs, filesystem
storage, zero runtime dependencies. **Paperclip** is a full-stack
orchestration platform for multi-agent "companies" — TypeScript
monorepo, PostgreSQL, React UI, REST API, heartbeat scheduling.

They share the idea that AI agents need structured task systems,
but diverge sharply on scope, complexity, and philosophy.

---

## Side-by-Side Comparison

### Architecture

| Dimension | Open Station | Paperclip |
|-----------|-------------|-----------|
| **Core metaphor** | Vault (markdown files + conventions) | Company (org chart + control plane) |
| **Language** | Python CLI + Markdown specs | TypeScript monorepo (Node.js + React) |
| **Storage** | Filesystem — YAML frontmatter in `.md` files | PostgreSQL (Drizzle ORM) + PGlite for local dev |
| **UI** | None (CLI + Obsidian optional) | React web dashboard (Vite) |
| **API** | CLI only (`openstation` commands) | REST API (Express.js) serving both UI and agents |
| **Dependencies** | Near-zero (Python, markdown files) | Heavy (Node 20+, pnpm, PostgreSQL, Docker) |
| **Installation** | `openstation init` in any project | `npx paperclipai onboard` or Docker Compose |
| **State versioning** | Git-native (all state is diffable markdown) | Database migrations (Drizzle) |
| **Deployment** | Local only (filesystem) | Local → hosted → distributed (progressive) |

### Task Model

| Dimension | Open Station | Paperclip |
|-----------|-------------|-----------|
| **Task unit** | Single markdown file (`NNNN-slug.md`) | Database row ("Issue") with team-prefix IDs (`ENG-123`) |
| **Statuses** | Fixed: `backlog → ready → in-progress → review → done/failed` | Customizable per-team within 6 categories (Triage, Backlog, Unstarted, Started, Completed, Cancelled) |
| **Hierarchy** | `parent`/`subtasks` frontmatter fields | Workspace → Initiative → Project → Milestone → Issue → Sub-issue |
| **Priority** | Not modeled (ordering is implicit) | 5-level scale (0–4) |
| **Relations** | Parent/child only | Parent/child + related, blocks, blocked_by, duplicate |
| **Assignee model** | Single agent (`assignee` field) | Single agent (atomic checkout) |
| **Ownership/verification** | Separate `owner` field — agent or `user` verifies | Board (human) governs; agents report status |
| **Task types** | `feature`, `research`, `spec`, `implementation`, `documentation` | Not typed — issues are generic work items |
| **Estimates/due dates** | Not modeled | Supported (estimates, due dates, timestamps) |
| **Labels/tags** | Not modeled (freeform in markdown body) | First-class with grouping and mutual exclusion |

### Agent Model

| Dimension | Open Station | Paperclip |
|-----------|-------------|-----------|
| **Agent definition** | Markdown spec file with YAML frontmatter | Database entity with adapter config |
| **Agent types** | Named roles (researcher, author, architect, etc.) | Named roles with titles, managers, subordinates |
| **Org structure** | Flat — agents are independent peers | Hierarchical tree — CEO → managers → reports |
| **Execution trigger** | Manual: `openstation run <agent>` or `--agent` flag | Heartbeat scheduler (cron-like) + manual + event-driven |
| **Execution model** | Claude Code session (interactive or detached) | Adapter-mediated (Claude, Codex, Gemini, shell, HTTP) |
| **Agent runtime** | Claude Code only | Runtime-agnostic (7+ adapters) |
| **Inter-agent communication** | None (agents work independently) | Via task system (create/assign/comment on issues) |
| **Budget/cost tracking** | Not modeled | Core feature — per-agent, per-task, per-project budgets with hard limits |
| **Agent status** | Not tracked | active, idle, running, error, paused, terminated |

### Storage & State

| Dimension | Open Station | Paperclip |
|-----------|-------------|-----------|
| **Primary storage** | `artifacts/` directory tree | PostgreSQL tables |
| **State encoding** | YAML frontmatter + markdown body | Database columns |
| **Relationships** | Obsidian wikilinks in frontmatter | Foreign keys |
| **Query engine** | Obsidian CLI (optional) + grep fallback | SQL (via Drizzle ORM) |
| **Artifact storage** | Typed directories (`research/`, `specs/`, `agents/`) | Not managed (agent's domain) |
| **Provenance tracking** | Frontmatter fields (`agent`, `task` wikilinks) | Database relations + activity logs |
| **Version history** | Git (implicit — files are in repo) | Database audit trail |
| **Portability** | Copy the directory | Database export/import |

### Extensibility

| Dimension | Open Station | Paperclip |
|-----------|-------------|-----------|
| **Extension model** | Skills (markdown instructions) + slash commands | Plugin architecture + adapter SDK |
| **Custom workflows** | Add skills or modify lifecycle.md | Custom adapters + event hooks |
| **Agent creation** | Write a markdown spec file | API call or UI form |
| **Integration surface** | Claude Code conventions (.claude/ symlinks) | REST API + webhook adapters |
| **Multi-project** | One vault per project (`.openstation/`) | Multi-company, multi-tenant |

### UX / Developer Experience

| Dimension | Open Station | Paperclip |
|-----------|-------------|-----------|
| **Primary interface** | Terminal (CLI + Claude Code) | Web UI + CLI |
| **Setup time** | Seconds (`openstation init`) | Minutes (database, dependencies, Docker) |
| **Learning curve** | Low — read markdown files, run CLI | Moderate — understand companies, heartbeats, adapters |
| **Visibility** | `openstation list`, read files, Obsidian graph | Dashboard with org chart, task board, cost views |
| **Debugging** | Read task files, git log | Audit trail, conversation tracing, agent logs |
| **Human oversight** | `owner: user` → human verifies in terminal | Board governance with approval gates |

---

## Key Differentiators

### Where Open Station Is Stronger

1. **Zero-dependency simplicity.** Filesystem-as-database means no
   PostgreSQL, no migrations, no Docker required. Any project can
   adopt it in seconds with `openstation init`.

2. **Git-native state.** All task state is diffable, branchable,
   and mergeable. No database backup/restore workflow needed.
   Task changes appear in PRs naturally.

3. **Convention over infrastructure.** Skills and lifecycle rules
   are markdown documents that agents read directly — no API layer
   to maintain or version.

4. **Low cognitive overhead.** A task is a file. An agent is a file.
   Everything is readable with `cat`. No abstractions to learn
   beyond frontmatter fields and status transitions.

5. **Artifact management.** Open Station has first-class routing
   for research outputs, specs, and agent definitions — typed
   directories with provenance tracking. Paperclip explicitly
   declares artifact management out of scope.

6. **Verification model.** The `owner` field and review → done/failed
   flow creates a clean separation between execution (agent) and
   verification (owner). Paperclip relies on Board governance
   which is heavier.

### Where Paperclip Is Stronger

1. **Multi-agent orchestration.** Hierarchical org structures,
   delegation, escalation, and inter-agent task assignment are core
   primitives. Open Station agents are independent peers with no
   coordination model.

2. **Runtime agnosticism.** Seven adapter types (Claude, Codex,
   Gemini, shell, HTTP, etc.) vs Open Station's Claude-Code-only
   execution. Any callable agent can participate.

3. **Scheduling and automation.** Heartbeat system triggers agents
   on schedules, events, or mentions. Open Station requires manual
   `openstation run` invocation.

4. **Cost management.** Per-agent budgets, token tracking, soft
   alerts, and hard ceilings are built in. Open Station has no
   cost visibility.

5. **Rich task metadata.** Priorities, estimates, due dates,
   labels with grouping, custom workflow states, and cross-team
   issue relations provide more sophisticated project management.

6. **Web UI.** Visual dashboards, org charts, and task boards make
   status visible to non-terminal users. Open Station is
   terminal-only (plus optional Obsidian).

7. **Multi-tenancy.** A single Paperclip deployment manages
   multiple isolated "companies." Open Station is one vault
   per project.

### Fundamentally Different Approaches

| Concern | Open Station | Paperclip |
|---------|-------------|-----------|
| **Target user** | Solo developer or small team using Claude Code | Organization running autonomous multi-agent operations |
| **Scale ambition** | Dozens of tasks per project | Enterprise-scale with hundreds of agents and thousands of issues |
| **Agent autonomy** | High — agent reads spec and works independently | Managed — heartbeats control when agents run, budgets control how much |
| **Human role** | Owner verifies completed work | Board governs ongoing operations |
| **Philosophy** | "Convention over infrastructure" | "Company as organizing principle" |

---

## Features Open Station Could Adopt

### High Value

1. **Agent scheduling / heartbeats.** A lightweight cron-like
   trigger (even a simple `openstation watch`) would let agents
   pick up ready tasks automatically instead of requiring manual
   dispatch. Could be as simple as a shell loop.

2. **Inter-agent task assignment.** Allow agents to create and
   assign tasks to other agents during execution. Open Station's
   sub-task model is close but lacks the runtime delegation piece.

3. **Cost/token tracking.** Add optional `cost` or `tokens`
   frontmatter fields to tasks, populated after agent sessions.
   Lightweight — no budget enforcement needed, just visibility.

4. **Priority field.** A simple numeric priority on tasks would
   improve agent task selection beyond "earliest created date."

### Medium Value

5. **Issue relations beyond parent/child.** `blocks` /
   `blocked_by` relations would help agents understand
   dependencies without reading parent context.

6. **Custom workflow states.** Allow projects to define their own
   status categories within the existing lifecycle framework —
   useful for teams with different process needs.

7. **Labels/tags in frontmatter.** A `tags` field (beyond
   freeform markdown) would improve machine-queryable
   categorization.

### Lower Value

8. **Adapter abstraction.** If Open Station ever supports non-Claude
   agents, Paperclip's adapter pattern (server/UI/CLI modules) is
   a clean model.

9. **Web dashboard.** A read-only HTML view generated from task
   files would help non-terminal stakeholders see project status.

## Features Paperclip Could Learn From Open Station

1. **Filesystem-as-database for portability.** Paperclip's PostgreSQL
   dependency makes casual adoption harder. A markdown-file mode
   for small-scale use would lower the barrier.

2. **Artifact routing and provenance.** Paperclip explicitly punts
   on artifact management. Open Station's typed directories with
   provenance fields are a lightweight pattern that could apply.

3. **Git-native state.** Task state in version control enables
   branch-per-feature workflows where tasks travel with the code.
   Database-backed state can't do this without export/import.

4. **Verification lifecycle.** The explicit review → done/failed
   flow with separate owner/assignee roles is cleaner than relying
   on Board approval for everything.

5. **Skills as documentation.** Open Station's skills are just
   markdown files agents read — no SDK, no plugin API. This is
   easier to author and iterate on than Paperclip's SKILL.md +
   adapter approach.

---

## Strategic Takeaways

1. **Open Station occupies a distinct niche.** It serves the
   "solo developer + AI agents" workflow that Paperclip doesn't
   target. The zero-dependency, git-native approach is a genuine
   strength, not a limitation to overcome.

2. **Don't chase Paperclip's scope.** Adding PostgreSQL, a web UI,
   or multi-tenancy would abandon Open Station's core value
   proposition. The right strategy is to deepen convention-based
   strengths.

3. **Scheduling is the biggest gap.** The single most impactful
   feature to borrow is automated agent dispatch. Even a minimal
   `openstation watch --agent researcher` that polls for ready
   tasks would transform the workflow from manual to semi-autonomous.

4. **Cost visibility is cheap to add.** Recording token usage
   in task frontmatter after agent sessions requires minimal
   infrastructure and provides meaningful insights.

5. **Inter-agent coordination is the growth frontier.** If Open
   Station wants to support more complex workflows, the path is
   through task-based agent communication (as Paperclip does),
   not through building infrastructure. Agents creating tasks
   for other agents fits the existing model naturally.

## Tags

#research #comparison #paperclip #open-station #architecture
