---
kind: task
name: 0228-research-external-data-integration-approaches
type: feature
status: verified
assignee: researcher
owner: user
artifacts:
  - "[[artifacts/research/external-data-integration-approaches]]"
created: 2026-03-24
---

# Research External Data Integration Approaches

## Requirements

1. **Map the integration spectrum** — survey approaches from lightweight to heavy, including:
   - **Notification service** — outbound-only: push task status changes to Slack, email, or webhooks via post-transition hooks (what's possible today vs. what's missing)
   - **Import commands** — inbound-only: `openstation import` that pulls Jira tickets, GitHub Issues, or Slack threads and creates/updates tasks (one-shot, user-triggered)
   - **Bidirectional sync** — two-way mapping between Open Station tasks and external systems (Jira, Linear, GitHub Issues), including conflict resolution and dedup
   - **Agent-as-integration** — a dedicated agent (e.g., an "openclaw"-style orchestrator) that monitors external sources, triages incoming work, and creates/assigns tasks autonomously

2. **For each approach, evaluate:**
   - What changes are needed in Open Station (new CLI commands, new hook types, frontmatter fields like `source:`, new agent capabilities)
   - Authentication and credential management patterns
   - Failure modes and retry semantics
   - How it interacts with the existing lifecycle (hooks, status transitions, ownership)

3. **Identify prior art** — look at how similar tools handle external integrations (Linear's API, Plane's webhooks, Taskwarrior's hooks, n8n/Zapier patterns)

4. **Recommend a sequencing** — which approach delivers value soonest with the least architectural risk, and what foundations (e.g., a `source` frontmatter field, a webhook receiver) should be laid first

## Progress

### 2026-03-24 — researcher

Completed research: surveyed Linear, Plane, Taskwarrior, n8n/Zapier integration patterns. Mapped 4 integration approaches (notification, import, bidirectional sync, agent-as-integration) with concrete evaluations. Produced research artifact at artifacts/research/external-data-integration-approaches.md with 4-phase recommended sequencing.

## Findings

Research artifact: [[artifacts/research/external-data-integration-approaches]]

**Key conclusions:**

1. **Open Station can already do outbound notifications** via
   post-transition hooks + `curl`. No new features needed — just
   documentation (a "Notification Cookbook").

2. **Three foundational changes unlock everything else:**
   - A `source` frontmatter field for external origin tracking
     and dedup
   - Structured JSON payload on hook stdin (following
     Taskwarrior's pattern) so hooks don't need to re-parse
     task files
   - A `TaskCreate` hook event type (already noted as deferred
     in `docs/hooks.md`)

3. **Recommended 4-phase sequencing:**
   - Phase 0 (now): Document notification patterns using existing hooks
   - Phase 1: `source` field + hook payload enhancement + create-time hooks
   - Phase 2: `openstation import` CLI with GitHub/Jira providers
   - Phase 3: Integrator agent for autonomous triage
   - Phase 4 (defer): Bidirectional sync — consider n8n/Zapier
     integration instead of building into core

4. **Prior art surveyed:** Linear (webhooks + HMAC + retry),
   Plane (REST API + webhooks + import-from-competitors),
   Taskwarrior (hook scripts with stdin JSON + syncall community
   tool), n8n/Zapier (workflow automation as external sync layer).

5. **Bidirectional sync should be deferred.** It introduces
   split-brain risk, requires a running process, and conflicts
   with Open Station's zero-dependency philosophy. If needed,
   building an n8n node or Zapier app is a better path.

## Verification

- [x] Research covers all four integration approaches (notification, import, bidirectional sync, agent-as-integration)
- [x] Each approach includes a concrete evaluation (changes needed, auth, failure modes, lifecycle interaction)
- [x] At least three prior-art systems are surveyed
- [x] Findings include a recommended sequencing with rationale
- [x] Output is stored as a research artifact in `artifacts/research/`

## Verification Report

*Verified: 2026-03-24*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Research covers all four integration approaches | PASS | Sections 2a (Notification), 2b (Import), 2c (Bidirectional Sync), 2d (Agent-as-Integration) each have dedicated subsections |
| 2 | Each approach includes concrete evaluation (changes needed, auth, failure modes, lifecycle interaction) | PASS | Every approach has explicit "Changes needed", "Auth patterns", "Failure modes", and "Lifecycle interaction" subsections with tables and specifics |
| 3 | At least three prior-art systems are surveyed | PASS | Four systems surveyed: Linear (3a), Plane (3b), Taskwarrior (3c), n8n/Zapier (3d) — each with key patterns and relevance analysis |
| 4 | Findings include recommended sequencing with rationale | PASS | Section 5 provides 5-phase sequencing (Phase 0–4) with Value/Risk/Effort for each phase plus a summary table in Section 6 |
| 5 | Output is stored as research artifact in `artifacts/research/` | PASS | File exists at `artifacts/research/external-data-integration-approaches.md` with correct frontmatter linking back to the task |

### Summary

5 passed, 0 failed. All verification criteria met.
