---
kind: task
name: 0067-research-agent-driven-template-customization
status: done
assignee: researcher
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
artifacts:
  - "[[artifacts/research/agent-driven-template-customization]]"
created: 2026-03-06
---

# Research Agent-Driven Template Customization

## Requirements

1. Research how the author agent could read a generic template
   (`templates/agents/`) + project context (CLAUDE.md, vault
   structure, existing agents) and produce a project-specific
   agent in `artifacts/agents/`
2. Define "project context" concretely — what inputs does the
   agent need to transform a template into a project agent?
3. Evaluate the trigger mechanism — command
   (`/openstation.customize`), skill, post-init task, or built
   into init itself
4. Address the bootstrap problem — the author agent is itself
   created from a template; how does it customize itself?
5. Research how GitHub's spec-kit repo handles this:
   https://github.com/github/spec-kit — how does it turn
   templates into project-specific specs/agents?
6. Deliverable: structured research in `artifacts/research/`

## Findings

Research artifact: `artifacts/research/agent-driven-template-customization.md`

**Key findings:**

1. **Project context** is concrete and small: CLAUDE.md (project
   name, conventions, stack), vault structure (canonical paths),
   peer agent names, and optionally tech stack signals from
   package files. The author agent extracts these and applies
   6 categories of transformation (project name insertion, agent
   cross-refs, path specificity, conventions, tool specificity,
   comment cleanup).

2. **Trigger mechanism**: Recommend `/openstation.customize` as a
   dedicated post-init command. Evaluated 4 options — a command
   gives the best balance of user control, discoverability,
   idempotency, and low complexity. Init can print a hint to
   run it.

3. **Bootstrap problem** is less severe than it appears. The
   author agent's generic template is fully functional — it
   defines the role completely. Project-specific customization
   adds context but doesn't change capability. One-pass
   self-customization (author customizes all agents including
   itself) works because the instructions come from the
   skill/command, not from the agent's own spec.

4. **Spec-kit pattern**: Treats templates as "prompts that
   constrain LLM output" rather than string-substitution targets.
   Open Station should follow this model — the author reads a
   template as structural guide and produces a new file informed
   by project context, not find-and-replace.

## Recommendations

1. Implement `/openstation.customize` as a slash command that
   invokes the author agent with gathered project context.
2. `openstation init` should copy generic templates as-is
   (agents work immediately) and print a hint about customize.
3. The customize command should support selective customization
   (`/openstation.customize researcher`) for adding new agents.
4. Re-running customize overwrites `artifacts/agents/` —
   document this clearly so users know to edit after the last
   customize run.

## Verification

- [ ] Research defines concrete inputs (template + project context)
- [ ] At least 2 trigger mechanisms evaluated with trade-offs
- [ ] Bootstrap problem addressed
- [ ] Deliverable in `artifacts/research/`
