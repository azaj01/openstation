---
kind: spec
name: general-agent-templates
agent: architect
task: "[[0062-spec-for-project-agnostic-agent]]"
---

# General Agent Templates

Spec for making the 5 bundled agent specs project-agnostic so they
work in any project that installs Open Station.

---

## 1. Audit: OS-Specific References by Agent

Every occurrence is tagged with a category letter used in § 2.

### researcher.md

| Location | Text | Category |
|----------|------|----------|
| frontmatter `skills` | `openstation-execute` | C |
| frontmatter `allowed-tools` | `"Bash(openstation *)"` | B |
| Constraints | "Always call `openstation` directly — never `python3 bin/openstation`" | B |

Body text is already generic. **Lowest coupling** of all 5.

### author.md

| Location | Text | Category |
|----------|------|----------|
| frontmatter `description` | "for Open Station vault artifacts" | A |
| frontmatter `skills` | `openstation-execute` | C |
| frontmatter `allowed-tools` | `"Bash(openstation *)"` | B |
| Body intro | "for Open Station" | A |
| Capabilities | "Create task specs with correct frontmatter…" | F |
| Capabilities | "Author skills…", "Update docs and CLAUDE.md…" | F |
| Capabilities | "Maintain cross-references and consistency across vault artifacts" | F |
| Capabilities | "Edit frontmatter fields…" | F |
| Constraints | "Always call `openstation` directly" | B |
| Constraints | "read only the vault" | F |
| Constraints | "Follow vault conventions exactly: kebab-case filenames, YAML frontmatter…" | F |

**Moderate coupling.** The "vault" language is OS-specific, but
the capabilities describe a genuinely generic content-authoring
role — they just happen to use OS vocabulary.

### architect.md

| Location | Text | Category |
|----------|------|----------|
| frontmatter `description` | "for Open Station" | A |
| frontmatter `skills` | `openstation-execute` | C |
| frontmatter `allowed-tools` | `"Bash(openstation *)"` | B |
| Body intro | "for Open Station" | A |
| Constraints | "Always call `openstation` directly" | B |
| Constraints | "Delegate implementation to `author`…" | E |
| Constraints | "Store outputs in `artifacts/specs/`" | D |
| Constraints | "Create research sub-tasks for the `researcher` agent" | E |

**Moderate coupling.** Cross-agent references (E) and vault
paths (D) are the main issues beyond the name.

### developer.md

| Location | Text | Category |
|----------|------|----------|
| frontmatter `description` | "for Open Station" | A |
| frontmatter `skills` | `openstation-execute` | C |
| frontmatter `allowed-tools` | `"Bash(openstation *)"` | B |
| Body intro | "for Open Station" | A |
| Capabilities | "Read a spec from `artifacts/specs/`" | D |
| Constraints | "Always call `openstation` directly" | B |
| Constraints | "create a sub-task for `architect`" | E |
| Constraints | "Task specs, agent specs… belong to the `author` agent" | E |

**Moderate coupling.** Same pattern as architect — name, paths,
cross-agent references.

### project-manager.md

| Location | Text | Category |
|----------|------|----------|
| frontmatter `description` | "for Open Station" | A |
| frontmatter `skills` | `openstation-execute` | C |
| frontmatter `allowed-tools` | `"Bash(openstation *)"` | B |
| Body intro | "for Open Station" | A |
| Capabilities | "Create tasks via `/openstation.create`" | B |
| Capabilities | "Promote tasks to ready via `/openstation.ready`" | B |
| Capabilities | "Write task specs via `/openstation.create`" | B |
| Capabilities | "Assign tasks… `author`… `researcher`" | E |
| Capabilities | "Oversee artifact promotion to `artifacts/research/`, `artifacts/specs/`" | D |
| Capabilities | "Keep `docs/` and `CLAUDE.md` accurate" | D |
| Capabilities | "Maintain the project roadmap (`artifacts/tasks/roadmap.md`)" | D |
| Constraints | "Always call `openstation` directly" | B |
| Constraints | "Follow vault conventions… `docs/lifecycle.md`" | D/F |

**Highest coupling.** 7 distinct CLI/path references, 1
cross-agent reference, plus conventions. This agent's
capabilities are almost entirely expressed in OS terms.

### Category Key

| Cat | Description | Count across all agents |
|-----|-------------|------------------------|
| A | Hardcoded "Open Station" in name/description/body | 8 |
| B | OS CLI references (`openstation`, `/openstation.*`) | 11 |
| C | `skills: - openstation-execute` in frontmatter | 5 |
| D | Vault path references (`artifacts/specs/`, `docs/`) | 7 |
| E | Cross-agent name references (`author`, `researcher`) | 5 |
| F | OS-specific conventions (frontmatter, kebab-case, etc.) | 7 |

---

## 2. Boundary: Agent Spec vs Skill

### Principle

The agent spec defines **who the agent is** — its role,
capabilities, constraints, and tool surface. It should read as
a job description that makes sense in any project.

The `openstation-execute` skill defines **how to operate within
the task system** — discovery, status transitions, artifact
routing, vault paths, CLI usage, and lifecycle rules.

### Boundary Table

| Concern | Belongs in Agent Spec | Belongs in Skill |
|---------|----------------------|------------------|
| Role identity ("You are a researcher") | ✓ | |
| Generic capabilities ("Search codebases and the web") | ✓ | |
| Behavioral constraints ("Design, never implement") | ✓ | |
| Tool list and allowed-tools (generic portion) | ✓ | |
| Cross-agent delegation patterns | ✓ (generic) | ✓ (specific names) |
| Task discovery and pickup | | ✓ |
| Status transitions (ready → in-progress → review) | | ✓ |
| Vault paths (`artifacts/specs/`, `artifacts/tasks/`) | | ✓ |
| CLI usage (`openstation list`, `openstation status`) | | ✓ |
| Slash commands (`/openstation.create`) | | ✓ |
| Artifact routing and provenance | | ✓ |
| Lifecycle rules and guardrails | | ✓ |
| Conventions (frontmatter schema, kebab-case) | | ✓ |
| `skills: - openstation-execute` (frontmatter) | ✓ (injected) | |
| `"Bash(openstation *)"` (allowed-tools) | ✓ (injected) | |

### Gray Zone: Injected Fields

Two frontmatter entries are OS-specific but must live in the
agent spec file because Claude Code reads them from there:

1. **`skills: - openstation-execute`** — tells Claude Code to
   load the OS execution skill. Without it, the agent doesn't
   know how to find or execute tasks.
2. **`"Bash(openstation *)"` in `allowed-tools`** — grants CLI
   access without permission prompts.

These are **installer-managed fields** — the `install.sh` script
(or a future `openstation init`) writes them into the agent spec
at install time. The template should document them separately
from the agent's own role-based tool permissions.

### Decision

Agent specs are rewritten to be project-agnostic. All OS-specific
operational knowledge comes from:

1. The `openstation-execute` skill (loaded at runtime via the
   `skills` frontmatter field)
2. The `CLAUDE.md` managed section (vault structure, quick-start)
3. Installer-injected frontmatter fields (`skills`, OS-specific
   `allowed-tools` entries)

---

## 3. Template Structure

### Frontmatter

```yaml
---
kind: agent
name: <agent-name>
description: >-
  <1-line role description. No project name. Describes the
  agent's function generically.>
model: <model-name>
skills:
  - openstation-execute          # ← injected by installer
tools: <comma-separated tool list>
allowed-tools:
  # --- Role-based (part of template) ---
  - Read
  - Glob
  - Grep
  # ... agent-specific tools ...
  # --- Task-system (injected by installer) ---
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
---
```

**Rules for frontmatter:**

- `description` must not mention any project name.
- `skills` is injected by the installer. The template includes
  it with a comment marking it as installer-managed.
- `allowed-tools` is split into two groups with a comment
  separator: role-based permissions (part of the template) and
  task-system permissions (injected by installer).

### Body

```markdown
# <Agent Name>

<1-2 sentence role statement. Describes WHO the agent is and
WHAT its job is. No project name. Uses "the project" or
"this project" if a project reference is needed.>

## Capabilities

- <Capability — generic skill expressed in domain terms>
- <Capability — what this role CAN do>
- ...

## Constraints

- <Constraint — behavioral boundary>
- <Constraint — what this role MUST NOT do>
- ...
```

**Sections are exactly three:** H1 title, Capabilities, Constraints.
No other sections (Technical Expertise on developer is fine as
an optional domain-specific section).

### Language Patterns

| Instead of… | Write… |
|-------------|--------|
| "for Open Station" | _(omit — role stands alone)_ |
| "Open Station vault" | "the project" or "this project" |
| "vault artifacts" | "project artifacts" |
| "`artifacts/specs/`" | "where the task system directs" or "the designated output location" |
| "Create tasks via `/openstation.create`" | "Create and triage tasks" |
| "Delegate to `author`" | "Delegate to the content-authoring agent" |
| "Create a sub-task for `researcher`" | "Create a research sub-task" |
| "Always call `openstation` directly" | _(remove — this is a CLI usage detail that belongs in the skill)_ |
| "Follow vault conventions: kebab-case…" | "Follow project conventions as defined by the task system" |
| "`docs/lifecycle.md`" | _(remove — the skill provides these references)_ |

### Concrete Examples

#### researcher (before)

```markdown
# Researcher

You are a research agent. Your job is to gather, analyze, and
synthesize information to support decision-making.

## Constraints

- Always call `openstation` directly — never `python3 bin/openstation`
- Present findings with evidence, not opinion
```

#### researcher (after)

```markdown
# Researcher

You are a research agent. Your job is to gather, analyze, and
synthesize information to support decision-making.

## Constraints

- Present findings with evidence, not opinion
```

The `openstation` CLI constraint is removed — it's covered by
the `openstation-execute` skill which all agents load.

#### architect (before)

```markdown
You are the technical architect for Open Station. Your job is to
make high-level technical decisions before implementation begins…

## Constraints

- Always call `openstation` directly — never `python3 bin/openstation`
- **Design, never implement.** …Delegate implementation to
  `author` (for vault artifacts) or other agents via task creation.
- Store outputs in `artifacts/specs/` unless the task spec
  directs otherwise.
- …Create research sub-tasks for the `researcher` agent…
```

#### architect (after)

```markdown
You are a technical architect. Your job is to make high-level
technical decisions before implementation begins…

## Constraints

- **Design, never implement.** …Delegate implementation to the
  appropriate agent via task creation.
- Store outputs where the task spec directs.
- …Create research sub-tasks when information is insufficient…
```

---

## 4. The project-manager Case

### Problem

The PM agent is the most OS-coupled. Its capabilities are
expressed almost entirely as OS operations — specific slash
commands, specific agent names, specific vault paths, and a
specific roadmap file. Stripping all of this leaves a hollow
shell: "You coordinate work."

### Analysis

The PM's identity is fundamentally tied to the task system.
Unlike researcher (generic skill: "research things") or
developer (generic skill: "write code"), the PM's skill IS
operating the task system. There is no useful PM without it.

### Decision: Generalize, but flag as system-coupled

**Decided.** The PM spec should be generalized like the others,
but its capabilities will naturally be more abstract:

```markdown
# Project Manager

You are a project coordinator. Your job is to manage the
project's task backlog: create and triage tasks, assign them
to agents, monitor progress, and maintain project documentation.

## Capabilities

- Create tasks and manage the backlog
- Promote tasks when requirements are clear and an agent is assigned
- Monitor in-progress work and flag stalled tasks
- Define task requirements and verification criteria
- Assign tasks to the best-suited agent based on task type
- Review completed work when designated as the verifier
- Break down large goals into sequenced, actionable tasks
- Keep project documentation accurate and up-to-date
- Identify documentation gaps and create tasks to fill them

## Constraints

- **Coordinate, never implement.** You create and manage tasks,
  assign agents, and review output. You do not research topics
  or produce non-task artifacts yourself.
- Delegate work to the appropriate agent when it falls outside
  your coordination role.
- Respect the ownership model — only verify tasks where you are
  the designated verifier.
- Never skip verification steps.
- When prioritizing, prefer tasks that unblock other work.
```

All OS-specific coordination details (which slash commands to
use, which vault paths exist, which specific agents are available)
come from the `openstation-execute` skill and `CLAUDE.md`.

### Recommendation: Keep PM out of default install

**Recommended.** The current `install.sh` already ships only
`researcher.md` and `author.md`. The PM should remain excluded
from the default agent set for two reasons:

1. Most projects start small — researcher + author covers the
   common case of "research something, then write something."
2. The PM's value scales with project complexity. Installing it
   by default in a fresh project with zero tasks adds noise.

The PM template should remain available in the repo as a
reference and can be added via `--with-pm` or manual copy.

The architect and developer agents are in a similar position —
they are not installed by default. The installer's `AGENTS`
array determines which are bundled. This spec does not change
that array; it only ensures all 5 templates are project-agnostic
when installed.

---

## 5. allowed-tools and Bash(openstation *) Handling

### Problem

`allowed-tools` is a Claude Code feature that determines which
tools the agent can use without human confirmation. Some entries
are role-specific (a developer needs `"Bash(pytest *)"`) while
others are task-system-specific (`"Bash(openstation *)"`).

### Decision: Two-tier structure with comments

The `allowed-tools` field uses inline comments to separate
the two tiers:

```yaml
allowed-tools:
  # --- Role-based (defined by agent template) ---
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  # --- Task-system (added by openstation) ---
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
```

**Rationale:** Claude Code reads `allowed-tools` from the agent
spec file — there's no mechanism to inject them from a skill.
So both tiers must live in the same file. The comment separation
makes it clear which entries a project can customize (role-based)
vs which the task system needs (system-managed).

### Per-Agent Role-Based Tools

| Agent | Role-based allowed-tools |
|-------|-------------------------|
| researcher | Read, Glob, Grep, Write, Edit, WebSearch, WebFetch |
| author | Read, Glob, Grep, Write, Edit, `Bash(ln *)`, `Bash(mkdir *)` |
| architect | Read, Glob, Grep, Write, Edit |
| developer | Read, Glob, Grep, Write, Edit, `Bash(python *)`, `Bash(python3 *)`, `Bash(pip *)`, `Bash(pytest *)`, `Bash(mkdir *)`, `Bash(chmod *)`, `Bash(pyenv *)` |
| project-manager | Read, Glob, Grep, Write, Edit, `Bash(ln *)`, `Bash(mkdir *)`, `Bash(mv *)`, `Bash(rm *)` |

### Task-System Tools (common to all agents)

```yaml
- "Bash(openstation *)"
- "Bash(ls *)"
- "Bash(readlink *)"
```

These three are required by the `openstation-execute` skill for
task discovery, artifact inspection, and symlink resolution.

### Installer Responsibility

The installer writes the complete `allowed-tools` list into
each agent spec file. It merges the role-based list from the
template with the task-system list. If an agent spec already
exists (skip-if-exists behavior), the installer does not
overwrite — the user owns the file.

---

## 6. Migration Checklist

For the implementing agent (task 0063), apply these changes
to each agent spec:

### All 5 agents

- [ ] Remove "Open Station" from `description` frontmatter field
- [ ] Remove "Open Station" from body intro sentence
- [ ] Remove "Always call `openstation` directly" constraint
- [ ] Add comment separator in `allowed-tools` between role-based
      and task-system entries
- [ ] Verify `skills: - openstation-execute` remains (it's
      injected but must be present)

### author

- [ ] Replace "Open Station vault artifacts" → "project artifacts"
      in description
- [ ] Replace "vault" references with "project" in body
- [ ] Replace convention-specific language with "Follow project
      conventions as defined by the task system"

### architect

- [ ] Replace "Delegate implementation to `author`" →
      "Delegate implementation to the appropriate agent"
- [ ] Replace "`artifacts/specs/`" →
      "where the task spec directs"
- [ ] Replace "for the `researcher` agent" →
      generic phrasing

### developer

- [ ] Replace "`artifacts/specs/`" →
      "the designated spec location"
- [ ] Replace "sub-task for `architect`" →
      "a sub-task to clarify the design"
- [ ] Replace "belong to the `author` agent" →
      "belong to the content-authoring agent"

### project-manager

- [ ] Replace all `/openstation.*` command references with
      generic equivalents ("Create tasks", "Promote tasks")
- [ ] Replace hardcoded agent names in delegation with role
      descriptions
- [ ] Remove `artifacts/tasks/roadmap.md` reference
- [ ] Remove specific vault path references (`docs/`,
      `artifacts/research/`)
- [ ] Replace convention references with generic language

---

## 7. Summary of Decisions

| # | Decision | Status |
|---|----------|--------|
| 1 | Agent specs must not contain project names | Decided |
| 2 | OS CLI constraints move to the skill | Decided |
| 3 | `skills` and OS `allowed-tools` are installer-injected | Decided |
| 4 | Cross-agent references use role descriptions, not names | Decided |
| 5 | Vault paths are removed; skill provides routing | Decided |
| 6 | PM is generalized but stays out of default install | Decided (generalize) / Recommended (exclude from default) |
| 7 | `allowed-tools` uses two-tier structure with comments | Decided |
| 8 | Convention references move to skill or use generic phrasing | Decided |
