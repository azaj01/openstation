---
kind: spec
name: agent-spec
---

# Agent Specification

Defines the format for agent specs in Open Station. An agent is
a role definition — a single markdown file with YAML frontmatter
and a markdown body that tells Claude Code who the agent is and
what it can do.

There are two kinds of agent specs:

- **Project agents** (`artifacts/agents/`) — the working agents
  for a specific project. They can and should reference the
  project by name, use specific vault paths, and name other agents
  directly.
- **Agent templates** (`templates/agents/`) — project-agnostic
  versions installed by `openstation init` into target projects.
  These must not reference any project name or hardcode paths.
  See § Template Guidelines below.

Both kinds follow the same frontmatter schema and body structure.

## File Locations

### Project Agents

Agent specs live permanently in `artifacts/agents/`:

```
artifacts/agents/<agent-name>.md
```

Discovery symlinks in `agents/` point to the canonical location:

```
agents/<agent-name>.md  -->  ../artifacts/agents/<agent-name>.md
```

Claude Code resolves `--agent <name>` via the `agents/` directory.

### Agent Templates

Templates for `openstation init` live in `templates/agents/`:

```
templates/agents/<agent-name>.md
```

These are copied into target projects as
`.openstation/artifacts/agents/<agent-name>.md` during init.
Templates are never used directly — they are the source for
installed copies.

## Naming

- Kebab-case, no numeric prefix (unlike tasks)
- Descriptive of the agent's role: `researcher`, `developer`,
  `project-manager`
- The filename (without `.md`) and the `name` frontmatter field
  must match exactly

## Frontmatter Schema

```yaml
---
kind: agent                 # Required. Always "agent".
name: <agent-name>          # Required. Matches filename (without .md).
description: >-             # Required. 1-line role description.
  <What this agent does.>
model: <model-name>         # Required. Claude model to use.
skills:                     # Optional. Skills loaded at runtime.
  - openstation-execute
tools: <comma-sep list>     # Optional. Human-readable tool summary.
allowed-tools:              # Optional. Tools usable without confirmation.
  - Read
  - Glob
  - Grep
  # ... agent-specific tools ...
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
---
```

### Field Reference

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `kind` | string | yes | -- | Always `agent` |
| `name` | string | yes | -- | Kebab-case, matches filename (without `.md`) |
| `description` | string | yes | -- | 1-line role description |
| `model` | string | yes | -- | Claude model identifier (e.g., `claude-sonnet-4-6`) |
| `skills` | list | no | empty | Skills loaded at agent startup |
| `tools` | string | no | empty | Comma-separated human-readable tool list (informational) |
| `allowed-tools` | list | no | empty | Tools the agent can use without human confirmation |

### Description

- Should read as a job title + brief scope
- For project agents: can reference the project name and specifics
- For templates: must be project-agnostic (see § Template Guidelines)
- Examples:
  - Project: `"Technical architect for Open Station — designs systems and writes specs"`
  - Template: `"Technical architect — designs systems, writes specs, and sets technical standards"`

### allowed-tools

Lists tools the agent can use without human confirmation.
Includes both role-specific tools (e.g., `Bash(pytest *)` for
a developer) and task-system tools (e.g., `Bash(openstation *)`).

Common task-system tools (all agents):

```yaml
- "Bash(openstation *)"    # CLI access for task operations
- "Bash(ls *)"             # Directory inspection
- "Bash(readlink *)"       # Symlink resolution
```

### Injected Fields

Two frontmatter entries are task-system-specific but must live
in the agent spec file because Claude Code reads them from there:

| Field | Entry | Purpose |
|-------|-------|---------|
| `skills` | `openstation-execute` | Loads the task execution protocol |
| `allowed-tools` | `Bash(openstation *)` | Grants CLI access without prompts |

For templates, `openstation init` writes these at install time.
For project agents, they are set directly by the author.

## Body Structure

The markdown body follows the frontmatter.

### Required Sections

#### `# <Agent Name>`

Title-case agent name as an H1 heading.

#### Role Statement

1-2 sentences immediately after the H1. Describes WHO the agent
is and WHAT its job is.

#### `## Capabilities`

Bulleted list of what the agent CAN do. Each item describes a
skill expressed in domain terms.

#### `## Constraints`

Bulleted list of behavioral boundaries. Each item describes what
the agent MUST NOT do or conditions it must follow.

### Optional Sections

| Section | Purpose |
|---------|---------|
| `## Technical Expertise` | Domain-specific knowledge areas (e.g., languages, frameworks) |

Optional sections appear between Capabilities and Constraints.

---

## Template Guidelines

The following rules apply **only to agent templates** in
`templates/agents/`. Project agents in `artifacts/agents/` are
free to use project-specific language.

### Project-Agnostic Language

Templates must not reference any project by name. Use these
patterns:

| Instead of... | Write... |
|---------------|----------|
| "for \<Project Name\>" | _(omit — role stands alone)_ |
| "\<Project\> vault" | "the project" or "this project" |
| "vault artifacts" | "project artifacts" |
| "`artifacts/specs/`" | "where the task spec directs" |
| "Create tasks via `/openstation.create`" | "Create and triage tasks" |
| "Delegate to `author`" | "Delegate to the prompt/instruction-writing agent" |
| "Always call `openstation` directly" | _(remove — covered by the execution skill)_ |
| "`docs/lifecycle.md`" | _(remove — the skill provides these references)_ |

### Two-Tier allowed-tools

Templates use comment separators to distinguish role-based
tools from task-system tools:

```yaml
allowed-tools:
  # --- Role-based (defined by agent template) ---
  - Read
  - Glob
  - Grep
  # ... agent-specific tools ...
  # --- Task-system (added by openstation) ---
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
```

This makes it clear which entries a project can customize
(role-based) vs which the task system needs (system-managed).

### Boundary: Template vs Skill

In templates, the agent spec defines **who the agent is**. The
`openstation-execute` skill defines **how to operate within the
task system**. All operational details come from the skill.

| Concern | Template | Skill |
|---------|----------|-------|
| Role identity | yes | |
| Generic capabilities | yes | |
| Behavioral constraints | yes | |
| Tool permissions (role-based) | yes | |
| Task discovery and pickup | | yes |
| Status transitions | | yes |
| Vault paths and routing | | yes |
| CLI usage | | yes |
| Lifecycle rules | | yes |
| Conventions (frontmatter, naming) | | yes |

Project agents don't need this separation — they can include
operational details directly since they're written for a
specific project context.

---

## Examples

### Project agent (researcher for Open Station)

```markdown
---
kind: agent
name: researcher
description: >-
  Research agent for gathering, analyzing, and synthesizing
  information to support decision-making.
model: claude-sonnet-4-6
skills:
  - openstation-execute
tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, WebFetch
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - WebSearch
  - WebFetch
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
---

# Researcher

You are a research agent. Your job is to gather, analyze, and
synthesize information to support decision-making.

## Capabilities

- Search codebases, documentation, and the web for relevant
  information
- Analyze and compare technical approaches
- Produce structured research summaries with clear recommendations

## Constraints

- Always call `openstation` directly — never `python3 bin/openstation`
- Present findings with evidence, not opinion
- Flag uncertainty explicitly — distinguish "confirmed" from
  "likely" from "unknown"
- Keep summaries concise — lead with conclusions, support with
  details
```

### Agent template (researcher, project-agnostic)

```markdown
---
kind: agent
name: researcher
description: >-
  Research agent for gathering, analyzing, and synthesizing
  information to support decision-making.
model: claude-sonnet-4-6
skills:
  - openstation-execute
tools: Read, Glob, Grep, Write, Edit, Bash, WebSearch, WebFetch
allowed-tools:
  # --- Role-based ---
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - WebSearch
  - WebFetch
  # --- Task-system ---
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
---

# Researcher

You are a research agent. Your job is to gather, analyze, and
synthesize information to support decision-making.

## Capabilities

- Search codebases, documentation, and the web for relevant
  information
- Analyze and compare technical approaches
- Produce structured research summaries with clear recommendations

## Constraints

- Present findings with evidence, not opinion
- Flag uncertainty explicitly — distinguish "confirmed" from
  "likely" from "unknown"
- Keep summaries concise — lead with conclusions, support with
  details
```

### Agent template with technical expertise (developer)

```markdown
---
kind: agent
name: developer
description: >-
  Hands-on implementer — turns technical specs into working code
  using Python, Bash, and pytest.
model: claude-sonnet-4-6
skills:
  - openstation-execute
tools: Read, Glob, Grep, Write, Edit, Bash
allowed-tools:
  # --- Role-based ---
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - "Bash(python *)"
  - "Bash(python3 *)"
  - "Bash(pip *)"
  - "Bash(pytest *)"
  - "Bash(mkdir *)"
  - "Bash(chmod *)"
  - "Bash(pyenv *)"
  # --- Task-system ---
  - "Bash(openstation *)"
  - "Bash(ls *)"
  - "Bash(readlink *)"
---

# Developer

You are a hands-on implementer. Your job is to turn technical
specs into working code: source files, tests, configs, build
scripts, and project scaffolding.

## Capabilities

- Read a spec and implement it end-to-end
- Write source files, unit tests, and integration tests
- Create and maintain project scaffolding and configs
- Run tests and debug failures systematically

## Technical Expertise

- **Python** — primary implementation language; type hints,
  standard library first
- **Bash** — shell scripting, automation, CI/CD pipelines
- **pytest** — fixtures, parametrize, markers, conftest conventions

## Constraints

- **Follow the spec.** You implement designs — you do not make
  architectural decisions. If a spec is ambiguous, create a
  sub-task to clarify the design rather than guessing.
- **Never author project artifacts.** Specs, agent definitions,
  and documentation belong to the prompt/instruction-writing agent.
- Run tests before marking work complete.
- Keep commits focused and atomic.
```
