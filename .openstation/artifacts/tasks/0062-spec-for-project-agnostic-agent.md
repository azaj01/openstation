---
kind: task
name: 0062-spec-for-project-agnostic-agent
status: done
assignee: architect
owner: user
parent: "[[0061-generalize-agent-templates-for-any]]"
artifacts:
  - "[[artifacts/specs/general-agent-templates]]"
created: 2026-03-06
---

# Spec for Project-Agnostic Agent Templates

## Requirements

1. Audit all 5 current agent specs (researcher, author, architect, developer, project-manager) and catalogue every "Open Station"-specific reference.
2. Define the boundary: what belongs in the agent spec (generic role identity, capabilities, constraints) vs what belongs in the `openstation-execute` skill (task protocol, vault paths, CLI usage).
3. Specify a template structure for general agent specs — which sections are required, what language patterns to use, how to reference the task system without naming it.
4. Address the `project-manager` agent specifically — it's the most OS-coupled (references roadmap.md, specific agent names, `/openstation.create`). Define how to make it general or whether it should be excluded from `init` installs.
5. Define how `allowed-tools` and `Bash(openstation *)` should be handled — these are OS-specific but functionally necessary.
6. Deliver spec at `artifacts/specs/general-agent-templates.md`.

## Findings

Spec delivered at `artifacts/specs/general-agent-templates.md`. Key results:

**Audit.** Catalogued 43 OS-specific references across 6 categories:
hardcoded name (8), CLI references (11), skill field (5), vault
paths (7), cross-agent names (5), conventions (7). Researcher has
the lowest coupling (3 items, all in frontmatter). Project-manager
has the highest (15+ items spread across capabilities and constraints).

**Boundary.** Agent spec = role identity (who, capabilities,
constraints, tool surface). Skill = operational protocol (discovery,
transitions, routing, CLI, conventions). Two gray-zone fields
(`skills` and OS `allowed-tools` entries) must live in the agent
spec file but are installer-managed.

**Template.** Three body sections: H1 title, Capabilities,
Constraints. Language patterns table maps OS-specific phrases to
generic equivalents (e.g., "Open Station vault" → "the project").
Before/after examples provided for researcher and architect.

**Project-manager.** Generalizable but its capabilities become
more abstract than other agents. Decided: generalize it.
Recommended: keep it out of the default install (current behavior).

**allowed-tools.** Two-tier structure with comment separator:
role-based permissions (template-owned) above, task-system
permissions (installer-injected) below. Three entries are common
to all agents: `Bash(openstation *)`, `Bash(ls *)`, `Bash(readlink *)`.

**Migration checklist** included in § 6 of the spec for the
implementing agent (task 0063).

## Verification

- [ ] All 5 agents audited with OS-specific references catalogued
- [ ] Clear boundary defined between agent spec vs skill responsibilities
- [ ] Template structure specified with concrete examples
- [ ] project-manager case addressed explicitly
- [ ] Spec artifact delivered to `artifacts/specs/`
