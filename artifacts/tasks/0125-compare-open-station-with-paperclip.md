---
kind: task
name: 0125-compare-open-station-with-paperclip
type: research
status: done
assignee: researcher
owner: user
artifacts:
  - "[[artifacts/research/open-station-vs-paperclip]]"
created: 2026-03-13
subtasks:
  - "[[0129-research-paperclip-extension-model-and]]"
---

# Compare Open Station With Paperclip Offering

## Requirements

1. Analyze Paperclip's architecture, features, and design philosophy from their GitHub repo (https://github.com/paperclipai/paperclip) — README, docs, source code, and any examples.
2. Catalog Paperclip's core capabilities: task management model, agent coordination, workflow primitives, storage/state, and extensibility points.
3. Catalog Open Station's equivalent capabilities for direct comparison.
4. Identify key differentiators — where each system is stronger, weaker, or takes a fundamentally different approach.
5. Surface features or patterns in Paperclip that Open Station could adopt or learn from, and vice versa.
6. Produce a structured comparison artifact in `artifacts/research/` with side-by-side tables and a summary of strategic takeaways.

## Findings

Paperclip (22k+ GitHub stars, MIT, TypeScript) is a full-stack orchestration platform for multi-agent "companies" — PostgreSQL-backed, React UI, REST API, heartbeat scheduling. Open Station is a convention-first task vault — markdown files, zero dependencies, git-native state.

**Key differences:**
- **Scope:** Paperclip targets autonomous multi-agent organizations with org charts, budgets, and governance. Open Station targets solo developers coordinating AI coding agents.
- **Infrastructure:** Paperclip requires Node 20+, PostgreSQL, Docker. Open Station requires only Python and markdown files.
- **Agent model:** Paperclip is runtime-agnostic (7 adapters) with hierarchical delegation. Open Station is Claude-Code-only with flat, independent agents.
- **Storage:** Paperclip uses PostgreSQL with Drizzle ORM. Open Station uses filesystem with YAML frontmatter — git-native and zero-migration.

**Top opportunities for Open Station:**
1. Agent scheduling (lightweight heartbeat/watch mode)
2. Inter-agent task delegation (agents creating tasks for other agents)
3. Cost/token visibility (frontmatter fields after sessions)
4. Priority field for task ordering

**Open Station's distinct strengths** Paperclip lacks: artifact routing with provenance, git-native diffable state, zero-dependency setup, and the verification lifecycle (owner/assignee separation).

See [[artifacts/research/open-station-vs-paperclip]] for the full comparison with side-by-side tables and strategic takeaways.

## Verification

- [ ] Paperclip repo has been thoroughly reviewed (README, docs, source structure, key modules)
- [ ] Comparison covers: architecture, task model, agent model, storage, extensibility, UX/DX
- [ ] Side-by-side table included with clear dimensions
- [ ] Strategic takeaways section identifies actionable insights for Open Station
- [ ] Artifact saved to `artifacts/research/`
