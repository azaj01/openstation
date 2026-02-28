---
kind: task
name: 0014-add-architect-agent
status: done
agent: author
owner: manual
artifacts:
  - artifacts/agents/architect.md
created: 2026-02-27
---

# Add Architect Agent

## Requirements

Create a new agent spec at `artifacts/agents/architect.md` that
defines an architect role for Open Station. This agent handles
high-level technical decisions before implementation begins.

### Core responsibilities

1. **Write technical specs** -- Produce architecture documents,
   design specs, and RFC-style proposals. Define system boundaries,
   data flows, and component contracts.

2. **Choose technology stacks** -- Evaluate and select languages,
   frameworks, libraries, and infrastructure. Document trade-offs
   and rationale for each choice.

3. **Design system architecture** -- Define module structure,
   API surfaces, integration patterns, and deployment topology.
   Ensure designs are implementable by other agents.

4. **Set technical standards** -- Establish coding conventions,
   testing strategies, CI/CD patterns, and quality gates.
   Document these as specs or skills for other agents to follow.

5. **Review technical feasibility** -- Evaluate proposed tasks
   and features for technical viability. Flag risks, dependencies,
   and complexity before work begins.

### Agent spec requirements

- Frontmatter with `kind: agent`, `name: architect`,
  `description`, `model`, `skills` list
- Identity section describing the architect role and
  decision authority
- Clear boundaries: the architect designs but does not
  implement. Implementation is delegated to `author` or
  other agents via task specs.
- Skills: reference `openstation-execute`

### Integration

- Launchable via `claude --agent architect`
- Symlink from `agents/architect.md` to
  `artifacts/agents/architect.md`
- Symlink from `.claude/agents/architect.md` to
  `agents/architect.md`

## Verification

- [ ] `artifacts/agents/architect.md` exists with valid frontmatter
- [ ] `agents/architect.md` symlink resolves correctly
- [ ] `.claude/agents/architect.md` symlink resolves correctly
- [ ] Agent spec defines spec-writing, tech-stack, architecture,
      and standards responsibilities
- [ ] Agent delegates implementation -- does not self-implement
- [ ] Agent can be invoked via `claude --agent architect`
