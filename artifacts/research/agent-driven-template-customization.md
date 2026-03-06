---
kind: research
name: agent-driven-template-customization
agent: researcher
task: "[[0067-research-agent-driven-template-customization]]"
created: 2026-03-06
---

# Agent-Driven Template Customization

How the author agent could transform generic templates into
project-specific agents using project context.

---

## 1. Current State

### Templates vs. Deployed Agents

Open Station ships 5 generic agent templates in `templates/agents/`.
The actual deployed agents in `artifacts/agents/` differ in 6
categories of project-specific changes:

| Category | Template (generic) | Deployed (project-specific) |
|----------|-------------------|---------------------------|
| **Project name** | "Technical architect" | "Technical architect **for Open Station**" |
| **Agent cross-refs** | "the appropriate agent" | "`author`", "`researcher`", "`architect`" |
| **Path specificity** | "where the spec directs" | "`artifacts/specs/`", "`src/`" |
| **Conventions** | "read the project" | "read the vault"; pyenv refs |
| **Tool specificity** | "source files, tests" | "Python source files", "`python3 -m pytest`" |
| **Comment cleanup** | `# --- Role-based ---` markers | markers removed |

### Key Observation

The templates are already well-structured — they have the
right roles, capabilities, and constraints. Customization is
a focused transformation, not a rewrite. Most changes are
string substitutions or targeted refinements to 5–15 lines.

---

## 2. Project Context — Concrete Inputs

For the author agent to transform a template into a
project-specific agent, it needs these inputs:

### Required Inputs

| Input | Source | What It Provides |
|-------|--------|-----------------|
| **Template file** | `templates/agents/<name>.md` | Base agent structure, role, capabilities, constraints |
| **CLAUDE.md** | Project root or `.openstation/` | Project name, conventions, tech stack, directory structure |
| **Vault structure** | `ls` of `.openstation/` dirs | Canonical paths (artifacts/, agents/, skills/) |
| **Existing agents** | `artifacts/agents/*.md` or `templates/agents/*.md` | Agent names for cross-references ("delegate to `author`") |

### Optional Inputs

| Input | Source | What It Provides |
|-------|--------|-----------------|
| **constitution.md** | Vault root (if present) | Project principles that constrain agent behavior |
| **Existing skills** | `skills/` | Available skills the agent can reference |
| **Tech stack signals** | `package.json`, `pyproject.toml`, etc. | Language/framework specificity for developer agent |

### What the Author Agent Does With These Inputs

1. **Extract project name** from CLAUDE.md (first H1 or
   project description)
2. **Extract tech stack** from package manager files or CLAUDE.md
3. **List peer agent names** from existing agents
4. **List canonical paths** from vault structure
5. **Apply transformations**:
   - Insert project name into description and body
   - Replace generic agent references with actual agent names
   - Replace generic path references with actual vault paths
   - Add project-specific conventions (CLI constraint, tech
     stack references)
   - Remove template scaffolding markers (comments)

---

## 3. Trigger Mechanism Evaluation

### Option A: Post-Init Command — `/openstation.customize`

A dedicated slash command the user runs after `openstation init`.

| Aspect | Assessment |
|--------|-----------|
| **User control** | High — user decides when to customize |
| **Discoverability** | Medium — user must know the command exists |
| **Idempotency** | Good — can re-run after changing CLAUDE.md |
| **Complexity** | Low — single command, clear purpose |
| **Flexibility** | High — can customize one agent or all |

**How it works**: User runs `/openstation.customize` (or
`/openstation.customize researcher`). The command loads the
author agent (or instructs the current agent to act as author)
and passes it the template + project context. The author agent
writes the customized spec to `artifacts/agents/`.

### Option B: Built Into `openstation init`

The init command itself runs the author agent to customize
templates during scaffolding.

| Aspect | Assessment |
|--------|-----------|
| **User control** | Low — happens automatically |
| **Discoverability** | High — no extra step needed |
| **Idempotency** | Problematic — re-running init shouldn't overwrite user-edited agents |
| **Complexity** | High — init becomes agent-dependent; needs Claude API or agent invocation |
| **Flexibility** | Low — all-or-nothing during init |

**Problem**: `openstation init` is a Python CLI command. Invoking
an LLM agent from within it requires either: (a) Claude API
calls baked into the CLI, or (b) shelling out to
`claude --agent author`. Both add significant complexity and
a hard dependency on Claude being available at init time.

### Option C: Skill-Based — Agent Self-Customization

A skill (`customize-agents`) that any agent can invoke, or that
the author agent runs as part of its first task.

| Aspect | Assessment |
|--------|-----------|
| **User control** | Medium — triggered by task assignment |
| **Discoverability** | Low — hidden in skill system |
| **Idempotency** | Good — skill can check existing agents |
| **Complexity** | Medium — skill definition + context gathering |
| **Flexibility** | High — skill can be invoked from any context |

**How it works**: Create a task "Customize agent templates for
this project" assigned to the author agent. The author reads the
skill, gathers context, and writes customized agents.

### Option D: Post-Init Task Auto-Creation

`openstation init` creates a backlog task "Customize agents for
[project]" assigned to the author agent. User promotes it when
ready.

| Aspect | Assessment |
|--------|-----------|
| **User control** | High — user promotes the task |
| **Discoverability** | High — appears in task list |
| **Idempotency** | Good — task is one-shot |
| **Complexity** | Low — init just creates a task file |
| **Flexibility** | High — user can edit task before promoting |

**How it works**: `openstation init` writes a task file to
`artifacts/tasks/` as part of scaffolding. The task contains
requirements and context for the author agent. When the user
is ready (CLAUDE.md written, project conventions established),
they promote the task and dispatch the author agent.

### Recommendation

**Option A (`/openstation.customize`) as primary, with Option D
as enhancement.**

Rationale:
- A command is the most natural UX for a one-time operation
- It separates concerns cleanly (init = structure, customize =
  content)
- It can be re-run if CLAUDE.md changes
- Option D (auto-created task) provides discoverability — init
  can print "Run `/openstation.customize` or promote task
  NNNN-customize-agents to personalize agents for your project"

---

## 4. The Bootstrap Problem

**Problem**: The author agent is itself created from a template.
How does it customize itself?

### Analysis

The author agent needs to exist (even generically) to customize
other agents. But if it hasn't been customized, it lacks
project-specific context in its own spec.

### Solutions Evaluated

**A. Two-Pass Approach**
1. Init installs generic author from template
2. Author customizes all other agents first
3. Author then customizes its own spec last

*Problem*: The author is operating with a generic spec while
doing project-specific work. It works — the template is
functional — but the output quality may be lower for the
author's own spec since it can't reference itself as an example.

**B. Self-Customization in One Pass**
The author customizes all agents including itself in a single
pass. It reads the template, gathers project context, and
writes all specs including its own.

*This works*. The author doesn't need a customized spec to
produce customized specs — it needs the customization
**instructions** (from the skill/command) and the **context**
(CLAUDE.md, vault structure). The template provides sufficient
role definition for the author to operate.

**C. Init Handles Author Specially**
`openstation init` does basic string substitution on the author
template (project name only), and the author agent handles the
rest.

*Unnecessary complexity.* Option B is simpler and sufficient.

### Recommendation

**Option B: Self-Customization in One Pass.**

The bootstrap problem is less severe than it appears. The
author agent's template already defines its role completely:
"craft clear, precise instructions that agents can follow
reliably." Project-specific customization adds context (project
name, peer agents, paths) but doesn't change the fundamental
capability. The skill/command provides all the instructions
the generic author needs to produce project-specific output.

---

## 5. Spec-Kit Patterns — Lessons for Open Station

### How Spec-Kit Handles Templates

GitHub's [spec-kit](https://github.com/github/spec-kit) uses a
**two-layer template system**:

1. **Static templates** — markdown files with `[PLACEHOLDER]`
   brackets (e.g., `[PROJECT NAME]`, `[DATE]`,
   `[EXTRACTED FROM ALL PLAN.MD FILES]`). These are copied and
   filled during `specify init`.

2. **LLM-driven generation** — slash commands
   (`/speckit.constitution`, `/speckit.specify`, `/speckit.plan`)
   invoke an LLM to generate project-specific artifacts from
   templates + project context. Templates act as "sophisticated
   prompts that constrain the LLM's output."

3. **Agent selection at init** — the `--ai` flag selects which
   AI agent's command files to install (Claude, Copilot, Gemini,
   etc.), determining the slash command implementations.

4. **Extension system** — community extensions add capabilities
   via a catalog mechanism (`catalog.json`), allowing
   project-specific customization beyond the base templates.

### Key Insight

Spec-kit treats templates as **prompts for LLM generation**, not
as files to string-substitute. The template shapes the LLM's
output rather than being directly modified. This is the right
model for Open Station: the author agent reads a template as
a **starting point and structural guide**, then produces a
project-specific artifact informed by project context.

### What Open Station Should Adopt

| Spec-Kit Pattern | Open Station Adaptation |
|-----------------|------------------------|
| Slash commands generate project-specific artifacts | `/openstation.customize` invokes author to produce project agents |
| Templates are LLM prompts, not string-substitution targets | Author reads template + context, writes new file (not find-and-replace) |
| `--ai` flag selects agent implementations | N/A — Open Station is Claude-native |
| Constitution constrains all generation | CLAUDE.md serves this role |
| Extensions for customization | Future: custom agent templates in project |

### What Open Station Should NOT Adopt

- **Spec-kit's complexity** — 17+ agent integrations, extension
  catalogs, environment variables. Open Station is convention-first
  and minimal.
- **Placeholder string substitution** — `[PROJECT NAME]` style
  placeholders are brittle. LLM-driven generation is more robust
  and produces natural-sounding text.

---

## 6. Proposed Workflow

```
openstation init
  │
  ├── Creates .openstation/ structure
  ├── Copies generic templates → artifacts/agents/
  ├── Sets up symlinks, commands, skills
  └── Prints: "Agents installed from templates.
       Run /openstation.customize to personalize
       them for your project."

User writes CLAUDE.md, sets up project...

/openstation.customize
  │
  ├── Gathers project context:
  │   ├── CLAUDE.md (project name, conventions, stack)
  │   ├── Vault structure (canonical paths)
  │   ├── Agent list (peer names)
  │   └── Tech stack signals (package files)
  │
  ├── For each agent in artifacts/agents/:
  │   ├── Reads corresponding template
  │   ├── Reads project context
  │   └── Author agent writes customized spec
  │
  └── Output: project-specific agents in artifacts/agents/
```

### Idempotency

`/openstation.customize` can be re-run safely:
- It reads templates (immutable source) + current context
- It overwrites `artifacts/agents/` (generated output)
- User edits to agents would be lost on re-run — document this
  clearly. If users want custom modifications, they should edit
  after the last customize run.

---

## 7. Open Questions

1. **Should customize be selective?** E.g.,
   `/openstation.customize researcher` to customize one agent.
   *Likely yes* — useful when adding a new agent template later.

2. **Should init copy templates as-is or not at all?** Currently
   init copies templates to `artifacts/agents/`. Alternative:
   init only creates symlinks, and customize materializes them.
   *Recommend: copy as-is* — agents should work immediately,
   even if generic.

3. **What about custom agent templates?** Projects may want
   agents beyond the 5 defaults. The customize command could
   support `templates/agents/` in the project directory.
   *Future work* — not needed for initial implementation.
