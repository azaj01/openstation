---
kind: research
name: paperclip-extension-model-and-workflows
agent: researcher
task: "[[0129-research-paperclip-extension-model-and]]"
created: 2026-03-13
---

# Paperclip Extension Model and Custom Workflows

## Executive Summary

Paperclip's extensibility is built on two primary mechanisms:
**adapters** (runtime bridges to agent execution environments) and
**skills** (markdown instruction files injected at runtime). There is
no formal plugin system yet — it's on the roadmap. Paperclip
explicitly states it is "not a workflow builder" — there are no
drag-and-drop pipelines, conditional branching, loops, or workflow
composition primitives. Instead, workflows emerge from agent behavior
guided by skills and the heartbeat execution model.

For Open Station, the most transferable patterns are: (1) the
adapter's triple-module architecture (server/UI/CLI), (2) the
skill routing model (frontmatter descriptions as decision logic),
and (3) the ClipHub marketplace concept for shareable blueprints.
Open Station's existing skill system is already comparable to
Paperclip's — the main gap is runtime discovery and lazy loading.

---

## 1. Extension Model: Adapters

### Architecture

Adapters are the primary extension point. Each adapter bridges
Paperclip's orchestration layer to a specific agent runtime.

```
                    ┌─────────────────┐
                    │  Heartbeat      │
                    │  Scheduler      │
                    └────────┬────────┘
                             │ triggers
                    ┌────────▼────────┐
                    │  Adapter        │
                    │  Registry       │
                    └────────┬────────┘
                             │ dispatches
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ claude   │  │ codex    │  │ http     │
        │ _local   │  │ _local   │  │          │
        └──────────┘  └──────────┘  └──────────┘
              │              │              │
              ▼              ▼              ▼
        Claude Code    Codex CLI     Webhook POST
```

### Built-in Adapters (7)

| Adapter | Runtime | Use Case |
|---------|---------|----------|
| `claude_local` | Claude Code CLI | Local coding agents with session persistence |
| `codex_local` | Codex CLI | Alternative local coding agent |
| `gemini_local` | Gemini CLI | Google's agent runtime |
| `opencode_local` | OpenCode CLI | Open-source coding agent |
| `openclaw` | OpenClaw | Paperclip's own agent runtime |
| `process` | Shell subprocess | Arbitrary scripts, custom loops |
| `http` | Webhook POST | External/cloud agent services |

### Triple-Module Architecture

Every adapter is a package with three independent modules:

```
packages/adapters/<name>/
├── src/
│   ├── index.ts          # Shared metadata (dependency-free)
│   │   - type:           # Unique snake_case identifier
│   │   - label:          # Human-readable display name
│   │   - models:         # Supported model list
│   │   - agentConfigurationDoc:  # Routing logic for LLM selection
│   │
│   ├── server/           # Execution logic
│   │   ├── execute.ts    # Core: spawn runtime, capture output
│   │   └── test.ts       # Environment diagnostics
│   │
│   ├── ui/               # React components
│   │   ├── parse.ts      # Stdout → transcript entries
│   │   └── config.tsx    # Configuration form
│   │
│   └── cli/              # Terminal formatting
│       └── format.ts     # Streaming output for watch mode
```

Each module is tree-shakeable via separate export points
(`.`, `./server`, `./ui`, `./cli`).

### Registration

Adapters register in three separate registries — one per consumer:

```typescript
// server/src/adapters/registry.ts
export const serverAdapters: Record<string, ServerAdapterModule> = {
  claude_local: claudeLocalServer,
  my_adapter: myAdapterServer,  // ← add here
};

// ui/src/adapters/registry.ts
export const uiAdapters: Record<string, UIAdapterModule> = { ... };

// cli/src/adapters/registry.ts
export const cliAdapters: Record<string, CLIAdapterModule> = { ... };
```

Registration is manual — no auto-discovery. Each registry is a
type-keyed map.

### The `execute()` Contract

The server module's `execute()` function is the critical interface:

```
Input:  Runtime context (agent config, env vars, session state)
Output: Structured result (exit code, stdout, token usage, cost,
        session state for persistence)
```

Key responsibilities:
1. Read typed configuration securely
2. Build environment with `buildPaperclipEnv(agent)` + context vars
3. Render prompt templates (supports `{{variable}}` substitution)
4. Spawn child process or make API call
5. Parse output for usage metrics and session state
6. Handle session errors (clear stale data, retry fresh)

### Session Persistence

Adapters serialize conversation state between heartbeats via a
`sessionCodec` with three operations:

- `serialize()` — execution results → storable parameters
- `deserialize()` — database → typed session state
- `getDisplayId()` — human-readable session identifier

Sessions are working-directory-aware: directory changes trigger
fresh sessions. Failed resume attempts auto-retry with new sessions.

---

## 2. Extension Model: Skills

### Format

Skills are markdown directories with a core `SKILL.md` file:

```
skills/
└── my-skill/
    ├── SKILL.md           # Primary instruction document
    └── references/        # Optional supplementary files
        └── examples.md
```

SKILL.md uses YAML frontmatter:

```yaml
---
name: my-skill
description: >
  Routing description that tells the agent WHEN to use this skill.
  Write as decision logic, not marketing copy.
---

# My Skill

Detailed instructions for the agent...
```

Required frontmatter fields:
- `name` — unique kebab-case identifier
- `description` — routing logic (when to use / when NOT to use)

### Built-in Skills (4)

| Skill | Purpose |
|-------|---------|
| `paperclip` | Core heartbeat protocol — task checkout, status updates, delegation |
| `paperclip-create-agent` | Guide for creating new agents via the API |
| `create-agent-adapter` | Guide for building custom adapter packages |
| `para-memory-files` | Memory file management patterns |

### Runtime Loading (Three-Stage)

1. **Metadata exposure** — Agent receives skill name + description
   in its context (via adapter injection)
2. **Relevance evaluation** — Agent decides if the skill applies to
   current task based on the routing description
3. **Full loading** — Agent retrieves complete SKILL.md content and
   follows instructions

This lazy-loading pattern keeps base prompts minimal — full skill
content loads only when needed.

### Skill Injection by Adapter

Each adapter handles skill injection differently:

| Adapter | Injection Method |
|---------|-----------------|
| `claude_local` | Creates temp directory with skill symlinks, passes via `--add-dir` flag |
| `codex_local` | Uses global skills directory |
| `process` | Skills available via filesystem; agent reads directly |
| `http` | Not applicable (external agent manages own skills) |

**Key principle:** Never pollute the agent's working directory with
Paperclip skills. Use isolated temp directories or global config paths.

---

## 3. Custom Workflow System

### Confirmed: No Formal Workflow Engine

Paperclip explicitly states: **"Not a workflow builder. No
drag-and-drop pipelines."** The documentation and website both
confirm this. There is no:

- Workflow definition language or DSL
- Conditional branching primitives
- Loop constructs
- Visual workflow composer
- Event-driven pipeline system

### How "Workflows" Actually Work

Workflows in Paperclip emerge from three mechanisms:

#### a) Heartbeat Scheduling

Agents wake on triggers, not continuous execution:

| Trigger | Description |
|---------|-------------|
| `timer` | Cron-like intervals (e.g., every 5 minutes) |
| `assignment` | When work is assigned to the agent |
| `on_demand` | Manual button/API invocation |
| `automation` | System-initiated future wakeups |

Concurrent wakeups coalesce to prevent duplicate execution.

#### b) Task-Based Coordination

Agents coordinate through the task system:

- **Checkout** — atomic claim (`POST /issues/{id}/checkout`);
  409 Conflict on race → pick another task
- **Delegation** — create subtasks with `parentId` and
  `assigneeAgentId` for routing to other agents
- **Blocking** — set status to `blocked` with blocker explanation
- **Release** — surrender tasks via `/issues/{id}/release`

#### c) Approval Gates

Governance flows act as workflow control points:

- `hire_agent` — board approval required for new agents
- `approve_ceo_strategy` — CEO strategy requires board sign-off
- Custom approval types via company policy

Agents receive approval results via environment variables
(`PAPERCLIP_APPROVAL_STATUS`) on their next heartbeat.

### Error Handling

Error handling is behavioral, not declarative:

- **409 Conflict** — terminal, never retry (another agent owns it)
- **Blocked tasks** — update status + comment blocker + escalate
  through chain of command
- **Failed runs** — recorded with status, errors, and logs;
  next heartbeat can retry or reassign
- **Session failures** — adapter clears stale session, retries fresh

---

## 4. Developer Experience for Extending Paperclip

### Creating a Custom Adapter (Step-by-Step)

1. **Scaffold the package** at `packages/adapters/<name>/`
2. **Define metadata** in `src/index.ts`:
   - `type`: unique snake_case identifier
   - `label`: display name
   - `models`: supported models
   - `agentConfigurationDoc`: routing logic for LLM selection
3. **Implement server execution** in `src/server/execute.ts`:
   - Build env with `buildPaperclipEnv(agent)`
   - Spawn process or make API call
   - Parse structured output (tokens, cost, session)
4. **Implement environment test** in `src/server/test.ts`:
   - Return diagnostics at error/warning/info levels
5. **Implement UI components** in `src/ui/`:
   - Config form using shared primitives
   - Stdout parser for transcript entries
6. **Implement CLI formatting** in `src/cli/`:
   - Stream formatting with `picocolors`
7. **Register** in three registries (server, UI, CLI)
8. **Verify**: `pnpm -r typecheck && pnpm test:run && pnpm build`

### Creating a Custom Skill

1. Create directory: `skills/<name>/`
2. Write `SKILL.md` with frontmatter (`name`, `description`)
3. Optionally add `references/` for supplementary files
4. Write description as **routing logic** — when to use AND when
   NOT to use
5. Provide concrete API calls and command examples
6. Keep to single concerns per skill

### Testing

- Adapters: `pnpm -r typecheck`, `pnpm test:run`, `pnpm build`
- Skills: manual — run an agent with the skill and verify behavior
- Environment validation: adapter `test.ts` returns structured
  diagnostics

### DX Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Adapter creation | Moderate | 6-step process, 3 registries, TypeScript required |
| Skill creation | Low barrier | Markdown file + frontmatter, no code required |
| Documentation | Good | Dedicated guides, examples, and a skill that teaches adapter creation |
| Testing | Mixed | Adapters have structured testing; skills lack automated verification |
| Discovery | Manual | Registries are hand-edited; no auto-scan |

---

## 5. ClipHub: The Planned Marketplace

ClipHub is Paperclip's planned marketplace for shareable
configurations (not yet implemented — spec stage):

- **Team Blueprints** — Complete org structures (agents, reporting
  chains, governance rules)
- **Agent Blueprints** — Individual agent configurations
- **Skills** — Modular capabilities (free or paid)
- **Governance Templates** — Pre-built approval flows

Revenue model: 90% creator / 10% platform after Stripe processing.

Installation via API calls that create agents, establish reporting
chains, deploy skills, and apply governance policies.

---

## 6. Applicability Assessment for Open Station

### Directly Transferable Patterns

#### a) Skill Routing via Description-as-Decision-Logic

**Paperclip pattern:** Skill frontmatter `description` is written as
routing logic ("use when X; don't use when Y") — not marketing copy.
Agents evaluate descriptions to decide whether to load the full skill.

**Open Station status:** Skills exist but lack standardized routing
descriptions. The `openstation-execute` skill is loaded always, not
conditionally.

**Recommendation:** Add an optional `description` field to skill
frontmatter that serves as routing logic. Agents would scan
descriptions first, then load full content only when relevant.
This keeps base prompts small as the skill library grows.

#### b) Lazy Skill Loading (Three-Stage)

**Paperclip pattern:** Metadata → relevance check → full load.

**Open Station status:** Skills load fully when referenced in agent
specs via the `skills` field. No intermediate evaluation step.

**Recommendation:** As skill count grows, consider a two-phase
approach: agent specs list available skills by name, the executor
reads descriptions to decide which to fully load. Not needed yet
(Open Station has ~10 skills), but good to design for.

#### c) Skill-as-Extension-Guide

**Paperclip pattern:** The `create-agent-adapter` skill IS the
extension documentation — an agent reads it to learn how to build
adapters. Skills bootstrap new skills.

**Open Station status:** The `skill-creator` command serves a
similar role but is a user-invocable command, not an agent skill.

**Recommendation:** Consider adding an agent-consumable skill for
creating new skills/commands — enabling agents to extend the system
autonomously.

### Partially Transferable Patterns

#### d) Adapter Triple-Module Pattern

**Paperclip pattern:** Server/UI/CLI separation with independent
registries per consumer.

**Open Station relevance:** Low for now. Open Station has one
execution environment (Claude Code). But if multi-runtime support
ever comes, this is the model to follow: each runtime gets a
package with separate execution, display, and terminal modules.

**Recommendation:** No action needed now. Note as reference
architecture if Open Station adds non-Claude agent support.

#### e) ClipHub Marketplace Concept

**Paperclip pattern:** Shareable agent configurations, skills, and
governance templates via a marketplace.

**Open Station relevance:** Medium. Open Station's skills and agent
specs are already portable markdown files. A "skill library" or
"agent template gallery" would be natural — just a git repo or
directory of shareable specs.

**Recommendation:** Consider a `templates/` directory or a
community repo for shareable agent specs and skills. No marketplace
infrastructure needed — git is the distribution mechanism.

### Not Transferable

#### f) Heartbeat Scheduling System

**Paperclip pattern:** Cron-like timer triggers, assignment triggers,
coalesced wakeups.

**Open Station status:** The parent research
([[artifacts/research/open-station-vs-paperclip]]) already
identified scheduling as the biggest gap and recommended a
lightweight `openstation watch`.

**Why not directly transferable:** Paperclip's heartbeat system is
deeply coupled to its PostgreSQL state, adapter registry, and REST
API. The concept (poll for ready tasks, dispatch agents) transfers,
but the implementation is completely different.

#### g) Approval Gate System

**Paperclip pattern:** Typed approval flows (`hire_agent`,
`approve_ceo_strategy`) with env var notification.

**Open Station status:** The `owner: user` verification model serves
a similar purpose but is simpler and sufficient for the current
scope.

**Why not transferable:** Approval gates solve a multi-agent
governance problem that Open Station doesn't have (flat agent
model, human owner verification).

#### h) REST API Extension Surface

**Paperclip pattern:** Agents extend behavior by calling API
endpoints during heartbeats.

**Open Station status:** CLI-based, no API server.

**Why not transferable:** Adding a REST API would violate Open
Station's zero-dependency philosophy. The CLI + filesystem model
is the correct extension surface for this system.

---

## Summary Table

| Paperclip Extension | Mechanism | Open Station Equivalent | Gap |
|---------------------|-----------|------------------------|-----|
| Adapter SDK | TypeScript packages with server/UI/CLI modules | None (Claude-only) | Large, but intentional |
| Skill system | Markdown SKILL.md with routing descriptions | Skills + commands (markdown) | Small — add routing descriptions |
| Skill injection | Temp dir with symlinks + `--add-dir` | Agent spec `skills` field + executor | Comparable |
| Adapter registry | Manual type-keyed maps (3 registries) | `agents/` symlinks | Comparable |
| Plugin system | Roadmap only | Not planned | N/A |
| Workflow engine | None ("not a workflow builder") | None | Parity |
| ClipHub marketplace | Spec stage (not built) | Not planned | Low priority |
| Heartbeat scheduling | Timer/assignment/demand triggers | Manual `openstation run` | Already identified |
| Approval gates | Typed approvals with env var callbacks | `owner` verification | Sufficient for scope |

## Tags

#research #paperclip #extensions #adapters #skills #workflows #open-station
