---
kind: research
name: external-data-integration-approaches
agent: researcher
task: "[[0228-research-external-data-integration-approaches]]"
created: 2026-03-24
---

# External Data Integration Approaches

Research into how Open Station can integrate with external systems
(Jira, GitHub Issues, Linear, Slack, etc.) — from lightweight
notifications to full bidirectional sync.

---

## 1. Integration Spectrum

Four approaches ordered from lightweight to heavy:

| # | Approach | Direction | Trigger | Complexity |
|---|----------|-----------|---------|------------|
| 1 | Notification service | Outbound only | Post-transition hooks | Low |
| 2 | Import commands | Inbound only | User-triggered CLI | Low–Medium |
| 3 | Bidirectional sync | Both | Event-driven or polling | High |
| 4 | Agent-as-integration | Both | Autonomous agent | Medium–High |

---

## 2. Approach Details

### 2a. Notification Service (Outbound-Only)

Push task status changes to external channels (Slack, email,
webhooks) when lifecycle transitions occur.

#### What exists today

Open Station already has a post-transition hook system
(`settings.json` → `hooks.StatusTransition`) that runs shell
commands with `OS_TASK_NAME`, `OS_OLD_STATUS`, `OS_NEW_STATUS`,
`OS_TASK_FILE`, and `OS_VAULT_ROOT` environment variables. This
is sufficient to implement outbound notifications today:

```json
{
  "matcher": "*->done",
  "command": "curl -X POST $SLACK_WEBHOOK_URL -d '{\"text\": \"Task '$OS_TASK_NAME' completed\"}'",
  "phase": "post"
}
```

#### What's missing

| Gap | Description |
|-----|-------------|
| **No structured payload** | Hooks get env vars, not a JSON payload with full task frontmatter. A notification hook must re-read the task file to get title, assignee, type, etc. |
| **No webhook receiver format** | No standard outbound webhook payload schema. Each hook script reinvents the format. |
| **No retry/queue** | Post-hooks are fire-and-forget. A Slack API timeout means a lost notification. |
| **No create-time hooks** | Hooks only fire on `openstation status` transitions, not on `openstation create`. Creating a task doesn't trigger notifications. |
| **No templating** | No built-in way to format notification messages from task fields. |

#### Changes needed

1. **`--payload` flag or structured env** — Extend hooks to
   optionally pass a JSON payload (full frontmatter + transition
   metadata) via stdin or a temp file, so notification scripts
   don't need to re-parse the task file.
2. **Create-time hooks** — Add a `TaskCreate` hook event type
   alongside the existing `StatusTransition`. Already noted as
   deferred work in `docs/hooks.md`.
3. **Notification templates** — Optional: a `notifications`
   section in `settings.json` with Slack/email/webhook targets
   and message templates using task field interpolation.

#### Auth patterns

- Slack: Webhook URL stored in env var or `.env` file
- Email: SMTP credentials in env or a sendmail-compatible binary
- Generic webhooks: Bearer token or HMAC signing secret in env

#### Failure modes

- Network timeout → notification lost (no retry in current hooks)
- Invalid webhook URL → hook fails silently (post-hook failure
  is warning-only)
- Mitigation: Add optional retry with exponential backoff to
  post-hooks, or delegate to a lightweight queue (`at` command,
  temp file + cron)

#### Lifecycle interaction

Integrates cleanly — post-hooks are already designed for this
purpose. No changes to the state machine. Create-time hooks
would be additive.

---

### 2b. Import Commands (Inbound-Only)

One-shot, user-triggered commands that pull items from external
systems and create/update Open Station tasks.

#### Design

```bash
openstation import jira PROJ-123          # single issue
openstation import jira --project PROJ --status "To Do"  # bulk
openstation import github owner/repo#42   # GitHub issue
openstation import linear LIN-123         # Linear issue
```

Each import:
1. Fetches the external item via its API
2. Maps fields to Open Station frontmatter (title → H1,
   description → Requirements, labels → type, assignee → assignee)
3. Creates a task via `openstation create` (or updates if a
   `source` field already links to that external ID)
4. Sets a `source` frontmatter field for dedup:
   `source: "jira:PROJ-123"` or `source: "github:owner/repo#42"`

#### Changes needed

| Change | Scope |
|--------|-------|
| **`openstation import` command** | New CLI subcommand with provider subcommands |
| **`source` frontmatter field** | New optional field in task spec for external origin tracking |
| **Provider adapters** | Per-provider modules: field mapping, API client, auth |
| **Dedup logic** | On import, check if a task with matching `source` exists; update instead of create |

#### Auth patterns

| Provider | Auth method |
|----------|-------------|
| Jira | API token + email (Basic auth) or OAuth 2.0, stored in env `JIRA_TOKEN` |
| GitHub | `gh` CLI auth (already configured per CLAUDE.md), or `GITHUB_TOKEN` env |
| Linear | API key or OAuth 2.0, stored in `LINEAR_API_KEY` env |
| Slack | Bot token for reading threads, `SLACK_BOT_TOKEN` env |

Credential storage: Environment variables or a `.openstation/credentials.json`
(gitignored). No secrets in task files or settings.json.

#### Failure modes

- API rate limits → retry with backoff, report partial import
- Network failure → abort with clear error, no partial state
- Field mapping mismatch → use sensible defaults, log warnings
- Duplicate detection failure → worst case: duplicate task
  (recoverable via manual merge)

#### Lifecycle interaction

- Imported tasks start as `backlog` (default) or `ready` if
  `--status ready` is passed
- The `source` field is read-only metadata — it doesn't affect
  transitions
- No changes to the state machine

---

### 2c. Bidirectional Sync

Two-way mapping between Open Station tasks and external system
items. Changes in either system propagate to the other.

#### Design

Sync requires:
1. **Identity mapping** — `source: "jira:PROJ-123"` on the
   Open Station side; a custom field or label on the external
   side pointing back
2. **Change detection** — file watcher (fswatch/inotify) on
   `artifacts/tasks/` for local changes; webhooks or polling
   for remote changes
3. **Conflict resolution** — last-write-wins, or manual
   resolution for concurrent edits
4. **Field mapping** — bidirectional map between frontmatter
   fields and external fields

#### Architecture options

| Option | Mechanism | Pros | Cons |
|--------|-----------|------|------|
| **Webhook listener** | HTTP server receiving events from Jira/Linear/GitHub | Real-time, event-driven | Requires a running process, public endpoint |
| **Polling daemon** | Periodic `openstation sync` via cron | No public endpoint needed | Latency, API rate limits |
| **Git-based** | Commit-triggered CI pipeline that syncs on push | Works with existing git workflow | Latency, complex merge logic |

#### Changes needed

| Change | Scope | Risk |
|--------|-------|------|
| **`openstation sync` command** | New CLI subcommand | Medium |
| **Sync daemon / webhook receiver** | New long-running process | High — architecture shift |
| **`source` field + `sync` metadata** | `source`, `synced_at`, `sync_version` fields | Low |
| **Conflict resolution strategy** | Policy in settings.json | Medium |
| **Field mapping config** | Per-provider mapping in settings.json | Medium |
| **Webhook endpoint** | HTTP server for inbound events | High — security, availability |

#### Auth patterns

Same as import (§ 2b), plus:
- Webhook receiver needs its own auth (HMAC signature
  verification, like Linear's `Linear-Signature` header)
- OAuth refresh token management for long-running sync

#### Failure modes

- **Split-brain** — concurrent edits on both sides →
  last-write-wins or manual resolution
- **Webhook delivery failure** — events lost if receiver is
  down → need dead letter queue or polling fallback
- **Schema drift** — external system adds/removes fields →
  mapping breaks silently
- **Partial sync** — network failure mid-batch → inconsistent
  state across systems
- **Clock skew** — `synced_at` timestamps diverge → stale
  conflict resolution

#### Lifecycle interaction

- External status changes must map to valid Open Station
  transitions. Jira's "In Progress" → `in-progress`, "Done" →
  `done`. Invalid mappings must be rejected or queued.
- Hooks would fire on sync-induced transitions (may cause
  infinite loops if notifications trigger sync which triggers
  notifications). Need a `sync: true` flag to suppress
  re-entrant hooks.
- Ownership model is strained: who is the `owner` when an
  external user marks something done?

---

### 2d. Agent-as-Integration

A dedicated agent that monitors external sources, triages
incoming work, and creates/assigns tasks autonomously.

#### Design

An agent spec (e.g., `integrator` or `triage-agent`) that:
1. Polls or watches external sources (Slack channels, Jira
   boards, GitHub issue labels, email inboxes)
2. Evaluates incoming items against criteria (labels, keywords,
   assignee patterns)
3. Creates Open Station tasks via `openstation create`
4. Optionally assigns agents and sets initial status
5. Posts acknowledgments back to the source

```yaml
# artifacts/agents/integrator.md
---
kind: agent
name: integrator
description: Monitors external sources and triages incoming work
model: claude-sonnet-4-20250514
skills:
  - openstation-execute
---
```

This agent would run periodically via `openstation run integrator`
(cron or manual) or continuously in a long-running session.

#### Changes needed

| Change | Scope | Risk |
|--------|-------|------|
| **Integrator agent spec** | New agent in `artifacts/agents/` | Low |
| **`source` frontmatter field** | Same as import (§ 2b) | Low |
| **Source config in settings.json** | `integrations` section defining sources, credentials, filters | Medium |
| **Polling/watch infrastructure** | Agent needs tools to query APIs (WebFetch, or dedicated MCP tools) | Low — already available |
| **Dedup logic** | Same as import — check `source` field before creating | Low |

#### Auth patterns

Same as import. The agent's session inherits environment
variables. MCP servers (e.g., `mcp__github`) provide
authenticated access to some sources without manual token
management.

#### Failure modes

- Agent session timeout → incomplete triage, resumed on next run
- API rate limits → agent backs off, resumes in next session
- Misclassification → agent creates tasks with wrong type/assignee
  → human reviews in backlog
- Duplicate creation → mitigated by `source` field dedup
- Runaway creation → agent floods vault with tasks → needs a
  rate limit or daily cap in config

#### Lifecycle interaction

- Agent creates tasks as `backlog` or `ready` depending on
  confidence and config
- Existing lifecycle is preserved — agent uses standard CLI
  commands
- Owner is `user` by default (human reviews agent-created tasks)
- The integrator agent itself follows the execute skill like
  any other agent

---

## 3. Prior Art Survey

### 3a. Linear

**Model:** API-first with webhooks. Linear provides a GraphQL
API and webhook system for every data change event.

**Key patterns:**
- Webhooks are org-level, scoped to teams or all public teams
- Payloads include `action` (create/update/remove), full entity
  data, and `updatedFrom` for diffs
- HMAC-SHA256 signature verification on `Linear-Signature` header
- Retry: 3 attempts with exponential backoff (1m, 1h, 6h)
- Endpoints auto-disabled after persistent failures
- OAuth 2.0 with refresh tokens (mandatory for new apps as of
  Oct 2025)

**Relevance to Open Station:**
- The `updatedFrom` pattern (shipping previous values) is useful
  for change detection without full diff
- Auto-disabling failing endpoints prevents silent data loss
- Retry with exponential backoff is the standard pattern

### 3b. Plane

**Model:** Open-source, self-hosted with REST API + webhooks.

**Key patterns:**
- REST API with OAuth 2.0 and HMAC-signed webhooks
- Typed SDKs (Node.js, Python) for integration development
- GitHub/GitLab/Slack/Sentry integrations built-in
- Import from Jira, Linear, Asana, ClickUp, Monday
- Community Edition (AGPL-3.0) includes full API + webhooks
- MCP server available for AI agent integration

**Relevance to Open Station:**
- Plane's import-from-competitors pattern validates the import
  command approach (§ 2b)
- MCP server for AI agents is directly applicable — Open Station
  could expose an MCP server for task operations
- Self-hosted model aligns with Open Station's zero-dependency
  philosophy

### 3c. Taskwarrior

**Model:** Local-first with hook scripts and sync protocol.

**Key patterns:**
- Four hook events: `on-launch`, `on-add`, `on-modify`, `on-exit`
- Hooks receive JSON task data on stdin, emit modified JSON on
  stdout
- Hook scripts are executables in `~/.task/hooks/` named by
  event (e.g., `on-add-notify.sh`)
- Exit code 0 = success, non-zero = abort the operation
- Sync via TaskChampion protocol (multi-replica, not
  bidirectional with external systems)
- Community `syncall` tool enables bidirectional sync with
  Google Tasks, Notion, CalDAV

**Relevance to Open Station:**
- Open Station's hook system is already similar to Taskwarrior's
  (shell commands, env vars, exit code semantics)
- Taskwarrior's stdin JSON approach is more ergonomic than env
  vars for complex payloads — worth adopting
- The `on-add` event type maps directly to the missing
  create-time hooks
- Community-built sync tools (syncall) show that bidirectional
  sync is best left to dedicated tools, not the core system

### 3d. n8n / Zapier

**Model:** Workflow automation platforms connecting arbitrary
services via triggers and actions.

**Key patterns:**
- Trigger → Action pipeline with visual builder
- Webhooks as universal trigger (n8n: free; Zapier: premium)
- HTTP Request nodes for arbitrary API calls
- Built-in auth management (OAuth, API keys, tokens)
- Error handling: retry policies, dead letter queues, alerts
- Self-hosted option (n8n) aligns with local-first philosophy

**Relevance to Open Station:**
- n8n/Zapier validate the "outbound webhook → external action"
  pattern without building it into the core
- Open Station could be an n8n/Zapier target by exposing a
  standard outbound webhook payload from post-hooks
- The alternative: Open Station as a n8n node/Zapier app
  (requires a running API endpoint)

---

## 4. Cross-Cutting Concerns

### 4a. The `source` Field

Every approach beyond pure notification needs a way to track
external origin. Proposed addition to task frontmatter:

```yaml
source: "jira:PROJ-123"          # provider:identifier format
source: "github:owner/repo#42"
source: "linear:LIN-abc123"
source: "slack:C0123456789/1234567890.123456"  # channel/message_ts
```

This field enables:
- Dedup on import (don't create duplicate tasks)
- Backlink to external system (clickable in Obsidian with a
  plugin or custom URI scheme)
- Sync identity mapping (which external item maps to which task)

**Spec change:** Add `source` as an optional string field in
`docs/task.spec.md`. No impact on existing tasks.

### 4b. Credential Management

| Pattern | Pros | Cons |
|---------|------|------|
| **Environment variables** | Simple, standard, no file to gitignore | Scattered, hard to audit |
| **`.openstation/credentials.json`** (gitignored) | Centralized, inspectable | Another file to manage, risk of accidental commit |
| **System keychain** | Most secure | Platform-specific, hard to script |
| **MCP server auth** | Delegated, per-provider | Requires MCP infrastructure |

**Recommendation:** Start with environment variables (simplest,
works with existing hooks). Add `credentials.json` support later
if needed. Never store credentials in `settings.json` or task
files.

### 4c. Hook Payload Enhancement

The biggest low-cost improvement: make hooks receive structured
task data without re-parsing the file.

**Option A — JSON on stdin:**
```json
{
  "task": { "name": "0042-...", "status": "done", "assignee": "dev", ... },
  "transition": { "old": "review", "new": "done" },
  "vault_root": "/path/to/project"
}
```

**Option B — JSON file path in env:**
```
OS_PAYLOAD=/tmp/openstation-hook-xxxx.json
```

Option A follows Taskwarrior's pattern and is more ergonomic.

---

## 5. Recommended Sequencing

### Phase 0: Foundation (no new features needed)

Use what exists today. Post-hooks can already send notifications
via `curl`. Document a "Notification Cookbook" showing patterns
for Slack, email, and generic webhooks using current hooks.

**Value:** Immediate. Users can integrate today.
**Risk:** None.
**Effort:** Documentation only.

### Phase 1: `source` Field + Hook Payload Enhancement

1. Add `source` as an optional frontmatter field in task spec
2. Enhance hooks to pass JSON payload on stdin (Option A)
3. Add `TaskCreate` hook event type

**Value:** Enables dedup-safe imports and richer notifications.
Foundation for everything that follows.
**Risk:** Low — additive changes, no breaking changes.
**Effort:** Small (1 spec update, 1 hooks enhancement, 1 new
event type).

### Phase 2: Import Commands

1. `openstation import` CLI subcommand
2. GitHub provider (leverages existing `gh` CLI auth)
3. Jira provider
4. Linear provider (optional, if demand exists)

**Value:** Users can pull work from external systems into
Open Station. Solves the "I have Jira tickets but want to
work in Open Station" use case.
**Risk:** Low–Medium — provider APIs may change, but adapters
are isolated modules.
**Effort:** Medium (new CLI subcommand + per-provider adapters).

### Phase 3: Agent-as-Integration

1. `integrator` agent spec
2. Configuration schema for sources and filters
3. Dedup logic using `source` field (built in Phase 1)

**Value:** Autonomous triage of incoming work. Powerful for
teams that receive work from multiple channels.
**Risk:** Medium — agent behavior needs guardrails (rate limits,
human review for backlog items).
**Effort:** Medium (agent spec + config schema; most tooling
already exists via MCP servers and `openstation create`).

### Phase 4: Bidirectional Sync (deferred)

1. `openstation sync` command
2. Webhook receiver or polling daemon
3. Conflict resolution strategy
4. Per-provider field mapping

**Value:** Full two-way integration. The holy grail but also
the most complex.
**Risk:** High — split-brain, re-entrant hooks, schema drift,
operational burden of a running process.
**Effort:** Large. Consider whether n8n/Zapier integration is
a better path (Open Station as a webhook source + n8n handles
the sync logic).

**Recommendation:** Defer Phase 4 until Phases 1–3 prove
demand exists. If bidirectional sync is needed, evaluate
building an n8n node or Zapier app instead of baking sync
into the core. This keeps Open Station's zero-dependency
philosophy intact.

---

## 6. Summary

| Approach | Feasibility | Value | Recommended Phase |
|----------|-------------|-------|-------------------|
| Notification service | Already possible (hooks) | High | 0 (now) |
| Hook payload enhancement | Easy addition | High | 1 |
| `source` field | Trivial spec change | High | 1 |
| Create-time hooks | Moderate addition | Medium | 1 |
| Import commands | Moderate new work | High | 2 |
| Agent-as-integration | Moderate new work | Medium–High | 3 |
| Bidirectional sync | Complex new work | Medium | 4 (defer) |

The key insight: Open Station's existing hook system already
provides the foundation for outbound integrations. The highest
ROI next steps are small, additive changes (structured payload,
`source` field, create-time hooks) that unlock import and
agent-based integration without architectural changes.

---

## Sources

- [Linear API & Webhooks](https://linear.app/docs/api-and-webhooks)
- [Linear Webhooks Developer Docs](https://linear.app/developers/webhooks)
- [Plane Open Source](https://plane.so/open-source)
- [Plane Developer Docs](https://developers.plane.so/)
- [Taskwarrior Hooks v1](https://taskwarrior.org/docs/hooks/)
- [Taskwarrior Hooks v2](https://taskwarrior.org/docs/hooks2/)
- [syncall — Bidirectional Taskwarrior Sync](https://github.com/bergercookie/syncall)
- [n8n vs Zapier](https://n8n.io/vs/zapier/)
