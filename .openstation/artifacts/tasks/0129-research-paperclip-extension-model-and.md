---
kind: task
name: 0129-research-paperclip-extension-model-and
type: research
status: done
assignee: researcher
owner: user
parent: "[[0125-compare-open-station-with-paperclip]]"
artifacts:
  - "[[artifacts/research/paperclip-extension-model-and-workflows]]"
created: 2026-03-13
---

# Research Paperclip Extension Model And Custom Workflows

## Requirements

1. Deep-dive into Paperclip's extension/plugin model — how third-party or custom capabilities are registered, discovered, and loaded.
2. Analyze Paperclip's custom workflow system — how workflows are defined, composed, triggered, and what primitives are available (conditions, loops, branching, error handling).
3. Document the developer experience for extending Paperclip: what files to create, what APIs to use, how extensions are tested.
4. Assess applicability to Open Station — which patterns (if any) could inform a skill/command extension model or workflow composition layer.
5. Produce a research artifact in `artifacts/research/` with architecture diagrams (textual), code examples, and an applicability assessment.

## Findings

Paperclip's extensibility rests on two pillars: **adapters** (TypeScript packages bridging the orchestration layer to agent runtimes) and **skills** (markdown instruction files with routing descriptions, loaded lazily at runtime). There is no formal plugin system — it's roadmap only. Crucially, Paperclip explicitly declares itself "not a workflow builder" — no DSL, no conditionals, no loops. Workflows emerge from agent behavior guided by skills and the heartbeat scheduling model.

**Extension model:** 7 built-in adapters (Claude, Codex, Gemini, OpenCode, OpenClaw, Process, HTTP), each with a triple-module architecture (server/UI/CLI) and manual registration in three type-keyed registries. Creating a custom adapter requires ~6 steps across TypeScript modules.

**Skill system:** Markdown `SKILL.md` files with frontmatter routing descriptions. Three-stage lazy loading: metadata exposure → relevance evaluation → full content load. Injected via temp directories with symlinks (never polluting the agent's working directory).

**Workflow system:** No formal workflow engine. "Workflows" are emergent from heartbeat triggers (timer/assignment/demand/automation), task-based agent coordination (checkout/delegate/block/release), and approval gates.

**Key takeaway for Open Station:** The most transferable pattern is skill routing via description-as-decision-logic — writing skill descriptions as "use when X; don't use when Y" to enable lazy loading as the skill library grows. Open Station's existing skill model is already comparable; the main enhancement would be adding routing descriptions for conditional loading.

See [[artifacts/research/paperclip-extension-model-and-workflows]] for the full analysis with architecture diagrams and applicability assessment.

## Verification

- [ ] Paperclip extension model documented (registration, discovery, loading, API surface)
- [ ] Custom workflow system documented (definition format, primitives, triggers)
- [ ] Developer experience for extending Paperclip described with concrete examples
- [ ] Applicability assessment for Open Station included
- [ ] Artifact saved to `artifacts/research/`
