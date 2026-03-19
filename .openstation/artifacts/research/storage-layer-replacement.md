---
kind: research
name: storage-layer-replacement
task: 0044-storage-layer-replacement
created: 2026-03-04
---

# Storage Layer Replacement

Research into whether Open Station's symlink-based storage layer can
be replaced with a simpler frontmatter-query approach.

---

## Current Architecture Summary

### The Four Symlink Types

Open Station uses four kinds of symlinks, each serving a distinct
purpose:

| Type | Example | Purpose |
|------|---------|---------|
| **Bucket** | `tasks/current/0010-slug → ../../artifacts/tasks/0010-slug` | Lifecycle state (which stage a task is in) |
| **Sub-task** | `artifacts/tasks/0006-parent/0007-child → ../0007-child` | Parent-child relationships |
| **Discovery** | `agents/researcher.md → ../artifacts/agents/researcher.md` | Agent resolution for `claude --agent` |
| **Traceability** | `artifacts/tasks/0011-slug/pm.md → ../../agents/pm.md` | Which task produced which artifact |

### What Bucket Symlinks Do Today

Three directories hold bucket symlinks mapped to statuses:

| Bucket | Statuses |
|--------|----------|
| `tasks/backlog/` | `backlog` |
| `tasks/current/` | `ready`, `in-progress`, `review` |
| `tasks/done/` | `done`, `failed` |

Lifecycle transitions move symlinks between buckets. The canonical
task folder in `artifacts/tasks/` never moves.

### Components That Depend on Bucket Symlinks

| Component | How it uses buckets | Could work without them? |
|-----------|-------------------|--------------------------|
| **CLI `discover_tasks()`** | Scans `artifacts/tasks/` directly, not buckets | **Already independent** — `resolve_bucket()` only checks bucket for informational display |
| **CLI `cmd_list`** | Filters by frontmatter `status` field | **Already independent** |
| **Execute skill** | Fallback: scans `tasks/current/`; primary: uses `openstation list` | Primary path already independent; fallback needs update |
| **Dashboard** | Uses Dataview queries on `artifacts/tasks/` frontmatter | **Already independent** |
| **`/openstation.create`** | Creates bucket symlink in `tasks/backlog/` or `tasks/current/` | Only needs frontmatter `status` field |
| **`/openstation.ready`** | Moves symlink `backlog/ → current/` | Only needs frontmatter edit |
| **`/openstation.done`** | Moves symlink `current/ → done/` | Only needs frontmatter edit |
| **`/openstation.reject`** | Moves symlink `current/ → done/` | Only needs frontmatter edit |
| **`/openstation.list`** | Delegates to CLI (fallback scans buckets) | Primary path independent; fallback needs update |
| **Install script** | Creates `tasks/{backlog,current,done}` directories | Would stop creating them |
| **Docs** | `storage-query-layer.md`, `lifecycle.md`, `task.spec.md`, `CLAUDE.md` reference buckets | Need updates |

**Key finding:** The CLI and dashboard already query `artifacts/tasks/`
directly via frontmatter. Bucket symlinks are only actively maintained
by the four lifecycle commands (`create`, `ready`, `done`, `reject`).

---

## Alternative 1: Dataview-Style Queries (Frontmatter-Only)

### Approach

Eliminate bucket symlinks entirely. All task state lives in
frontmatter `status` field. Discovery uses frontmatter queries
on `artifacts/tasks/` — exactly what the dashboard and CLI already
do.

### Feasibility: HIGH

The system is already 90% there:

- **Dashboard** queries `artifacts/tasks/` frontmatter via Dataview
  (ships today, works perfectly).
- **CLI `discover_tasks()`** scans `artifacts/tasks/*/index.md` and
  parses frontmatter (ships today, no bucket dependency).
- **Commands** already edit frontmatter fields during transitions —
  the symlink create/delete operations are an additional step that
  duplicates what the frontmatter already records.

### What Changes

| Component | Change Required | Effort |
|-----------|----------------|--------|
| **CLI** | Remove `resolve_bucket()` and `bucket` field from task dicts (informational only) | Trivial — delete ~15 lines |
| **`/openstation.create`** | Remove symlink creation (steps 7–8) | Small — delete symlink steps |
| **`/openstation.ready`** | Remove symlink move (step 8); keep frontmatter edit | Small |
| **`/openstation.done`** | Remove symlink move (step 5); keep frontmatter + promotion | Small |
| **`/openstation.reject`** | Remove symlink move (step 6); keep frontmatter edit | Small |
| **Execute skill** | Change fallback from `tasks/current/` scan to `artifacts/tasks/` scan | Trivial — one line |
| **Install script** | Stop creating `tasks/{backlog,current,done}` dirs and `.gitkeep` files | Small |
| **`storage-query-layer.md`** | Remove §§ 2a, 3; update §§ 8, 13 query patterns | Medium — doc rewrite |
| **`lifecycle.md`** | Remove "Bucket Mapping" section; simplify transitions | Medium — doc rewrite |
| **`task.spec.md`** | Remove bucket references | Small |
| **`CLAUDE.md`** | Update vault structure (remove `tasks/` bucket tree) | Small |
| **Dashboard** | No change | Zero |

### Trade-offs

| Pro | Con |
|-----|-----|
| Eliminates Obsidian incompatibility (no intra-vault symlinks) | Lose `ls tasks/current/` as a quick shell query |
| Single source of truth (frontmatter `status` only) | Must use CLI or `grep` for shell-based discovery |
| No state-split bugs (symlink says one thing, frontmatter says another) | Migration needed for existing vaults |
| Simpler install script | — |
| Fewer git diffs (no symlink create/delete on transitions) | — |
| Three fewer directories to maintain | — |

### Migration Path (Existing Vaults)

1. Update CLI, commands, skill, and docs (all changes above).
2. Bucket symlinks become inert — nothing reads or writes them.
3. Optionally delete `tasks/{backlog,current,done}` directories.
   No data loss (canonical folders are in `artifacts/tasks/`).

### What Survives (Unchanged)

- **Discovery symlinks** (`agents/ → artifacts/agents/`) — still
  required for Claude Code `--agent` resolution chain.
- **Traceability symlinks** (task folder → artifact) — still
  valuable for linking tasks to outputs.
- **Sub-task symlinks** (parent → child) — still needed for
  parent-child discovery within `artifacts/tasks/`.

Only bucket symlinks are eliminated.

---

## Alternative 2: Obsidian CLI

### Landscape

An **official Obsidian CLI** ships with Obsidian 1.12+ (docs:
https://help.obsidian.md/cli). The binary is at
`/Applications/Obsidian.app/Contents/MacOS/obsidian` and provides
80+ commands covering file management, property operations, search,
plugin management, and vault administration.

**Prerequisite:** Obsidian must be running (the CLI communicates
with the running app instance). This is the main architectural
constraint.

### Key Capabilities (Tested)

#### Frontmatter Property Queries

The CLI supports `[property: value]` search syntax with AND
combination:

```bash
# Find all tasks with status=ready
obsidian search vault="open-station" query='[kind: task] [status: ready]' format=json
# → ["artifacts/tasks/0035-cli-agent-session/index.md"]

# Complex AND: kind + status + agent
obsidian search vault="open-station" query='[kind: task] [status: review] [agent: researcher]' format=json
# → ["artifacts/tasks/0044-storage-layer-replacement/index.md"]

# Count done tasks
obsidian search vault="open-station" query='[kind: task] [status: done]' total
# → {"total":32}

# Path-scoped queries
obsidian search vault="open-station" query='[kind: task] [status: backlog]' path="artifacts/tasks" format=json
# → [7 backlog tasks]
```

This directly replaces `discover_tasks()` frontmatter parsing.

#### Property Read/Write

```bash
# Read a property
obsidian property:read vault="open-station" name="status" path="artifacts/tasks/0044/index.md"
# → review

# Set a property (lifecycle transition)
obsidian property:set vault="open-station" name="status" value="in-progress" path="artifacts/tasks/0044/index.md"

# List all properties with types and counts
obsidian properties vault="open-station" format=json
# → [{name:"status", type:"text", count:44}, ...]
```

This can handle lifecycle transitions without custom YAML parsing.

#### File Operations

```bash
# List files in a folder
obsidian files vault="open-station" folder="artifacts/tasks"

# Read file contents
obsidian read vault="open-station" path="artifacts/tasks/0044/index.md"

# Create a file with content
obsidian create vault="open-station" path="artifacts/tasks/0045-new/index.md" content="---\nkind: task\n---"

# Append/prepend content
obsidian append vault="open-station" path="..." content="## Findings\n..."
```

#### Vault & File Metadata

```bash
# List vaults with paths
obsidian vaults verbose
# → open-station   /Users/.../open-station

# File info (size, dates)
obsidian file vault="open-station" path="artifacts/tasks/0044/index.md"

# Outgoing links and backlinks
obsidian links vault="open-station" path="..."
obsidian backlinks vault="open-station" path="..."
```

#### Task Checkboxes (Not Our Task Concept)

The `tasks` command manages markdown checkbox items (`- [ ]`),
not Open Station task specs. It lists/toggles checkboxes by file
and line number — useful for verification checklists but not for
task lifecycle.

### Feasibility: MEDIUM-HIGH (as a CLI replacement)

**What it can replace:**

| Current CLI Function | Obsidian CLI Equivalent | Notes |
|---------------------|------------------------|-------|
| `discover_tasks()` — scan + parse frontmatter | `search query='[kind: task] [status: X]'` | Full AND queries, JSON output, path scoping |
| `cmd_list` — filter by status/agent | `search query='[kind: task] [status: X] [agent: Y]'` | Matches current filter capability |
| `cmd_show` — read task details | `read path=...` + `property:read` | Equivalent |
| Frontmatter editing (transitions) | `property:set name=status value=...` | No YAML parsing needed |
| `resolve_bucket()` — informational | Eliminated (no buckets) | N/A |

**What it cannot replace (lifecycle logic stays custom):**

- Status transition validation (e.g., `backlog → ready` is valid,
  `backlog → done` is not)
- Artifact promotion routing (moving outputs to canonical folders)
- Sub-task relationship management
- The `run` subcommand (agent dispatch orchestration)
- Verification checklist enforcement

**Critical constraint:** Requires Obsidian running. This means:
- Works for interactive development (Obsidian is typically open)
- Does NOT work in CI, headless servers, or when Obsidian is closed
- A fallback to direct filesystem + grep is needed for robustness

### Feasibility: HIGH (as a complement)

The Obsidian CLI is strongest as the **primary query engine** with
filesystem fallback:

```
┌─────────────────────────┐
│  openstation CLI        │
│  (lifecycle logic,      │
│   validation, dispatch) │
├─────────────────────────┤
│  Query layer            │
│  ┌───────────────────┐  │
│  │ obsidian search   │◄─── Primary: fast, structured queries
│  │ obsidian property │    │
│  └───────┬───────────┘  │
│          │ fallback      │
│  ┌───────▼───────────┐  │
│  │ filesystem + grep │◄─── Fallback: when Obsidian not running
│  └───────────────────┘  │
└─────────────────────────┘
```

**Additional complement capabilities:**
- `obsidian open` — open task in Obsidian from terminal
- `obsidian backlinks` — find tasks referencing an artifact
- `obsidian tags` — tag-based discovery across vault
- `obsidian search:context` — grep-like search with context
- `obsidian tasks` — manage verification checklists

---

## Recommendation: REPLACE Bucket Symlinks + ADOPT Obsidian CLI

**Replace** bucket symlinks with a frontmatter-only approach.
**Adopt** the Obsidian CLI as the primary query engine with
filesystem fallback. Keep discovery, traceability, and sub-task
symlinks.

### Rationale

1. **The system is already there.** The CLI and dashboard query
   frontmatter directly. Bucket symlinks are maintained by commands
   but never read by the primary query paths.

2. **Bucket symlinks are pure overhead.** They duplicate information
   already in frontmatter (`status` field), create a state-split
   risk (symlink in wrong bucket vs frontmatter says different
   status), and add complexity to every lifecycle command.

3. **Obsidian compatibility.** Removing intra-vault symlinks
   eliminates the "disjoint rule" problem documented in
   `artifacts/research/obsidian-symlink-support.md`. The dashboard
   already proves the Dataview approach works.

4. **Obsidian CLI fills the query gap.** The official CLI provides
   frontmatter property queries (`[kind: task] [status: ready]`),
   property read/write, and structured JSON output — exactly the
   primitives our custom CLI reimplements with Python YAML parsing.
   Using it as the primary query layer eliminates ~100 lines of
   custom discovery/parsing code.

5. **Graceful degradation.** The Obsidian CLI requires the app to
   be running, so the filesystem+grep fallback must remain for
   headless/CI use. This dual-path is a net positive: fast
   structured queries when Obsidian is open, reliable fallback
   otherwise.

### Required Changes (If Replacement Proceeds)

#### Phase 1 — Core (all must ship together)

1. **CLI (`bin/openstation`)** — Replace `discover_tasks()` with
   Obsidian CLI calls (`obsidian search`, `obsidian property:read`).
   Keep filesystem scanning as fallback when Obsidian isn't running.
   Remove `resolve_bucket()` and bucket-related code.

2. **Commands** — Remove symlink create/move/delete steps from
   `/openstation.create` (steps 7–8), `/openstation.ready` (step 8),
   `/openstation.done` (step 5), `/openstation.reject` (step 6).
   Keep all frontmatter edits and agent promotion logic. Consider
   using `obsidian property:set` for frontmatter edits.

3. **Execute skill** — Update fallback discovery from
   `tasks/current/` to `artifacts/tasks/` with frontmatter filter.
   Primary path can use `obsidian search query='[kind: task]
   [status: ready] [agent: $AGENT]'` for faster task discovery.

4. **Install script** — Remove `tasks/{backlog,current,done}`
   directory creation and `.gitkeep` files. Keep `artifacts/`
   directories. Update CLAUDE.md managed section to remove bucket
   references.

#### Phase 2 — Documentation

5. **`storage-query-layer.md`** — Remove §§ 2a (bucket symlinks),
   3 (lifecycle bucket mapping). Update §§ 8, 13 (query patterns)
   to show Obsidian CLI queries as primary, filesystem as fallback.
   Update § 6 (install layout).

6. **`lifecycle.md`** — Remove "Bucket Mapping" section. Simplify
   transition descriptions to frontmatter-only edits.

7. **`task.spec.md`** — Remove references to bucket symlinks in
   "File Location" section.

8. **`CLAUDE.md`** — Update vault structure diagram (remove
   `tasks/` bucket tree). Document Obsidian CLI dependency as
   optional (enhances performance, not required).

#### Phase 3 — Cleanup (optional, non-breaking)

9. Remove `tasks/{backlog,current,done}` directories and their
   symlinks from existing vaults. No data loss — canonical data
   is in `artifacts/tasks/`.

### Obsidian CLI Command Reference (for Open Station)

Key commands that map to Open Station operations:

| Operation | Command |
|-----------|---------|
| List tasks by status | `obsidian search query='[kind: task] [status: ready]' format=json` |
| List tasks by agent | `obsidian search query='[kind: task] [agent: researcher]' format=json` |
| Combined filter | `obsidian search query='[kind: task] [status: ready] [agent: researcher]' format=json` |
| Count tasks | `obsidian search query='[kind: task] [status: done]' total` |
| Read task status | `obsidian property:read name=status path=artifacts/tasks/0044/index.md` |
| Set task status | `obsidian property:set name=status value=in-progress path=...` |
| Read task content | `obsidian read path=artifacts/tasks/0044/index.md` |
| Create task file | `obsidian create path=... content="---\nkind: task\n..."` |
| List all properties | `obsidian properties format=json` |
| Open in Obsidian | `obsidian open path=artifacts/tasks/0044/index.md` |
| Find backlinks | `obsidian backlinks path=...` |

---

## Tags

#research #storage #symlinks #obsidian #architecture #cli
