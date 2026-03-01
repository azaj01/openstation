---
kind: task
name: 0025-add-developer-agent
status: done
agent: author
owner: user
created: 2026-03-01
---

# Add Developer Agent

## Requirements

Spec and add a `developer` agent to Open Station responsible for
implementing technical specs produced by the architect. The agent
turns design documents into working code.

### Agent Profile

1. Create `artifacts/agents/developer.md` with proper `kind: agent`
   frontmatter, including `skills: [openstation-execute]`.
2. The agent's system prompt must establish it as a hands-on
   implementer — it writes application code, tests, configs, and
   build files. It does **not** make architectural decisions or
   author vault artifacts (those belong to `architect` and `author`).

### Technical Expertise

The developer agent must be profiled with expertise in:

- **TypeScript** — primary implementation language
- **Bash** — scripting, automation, CI/CD pipelines
- **Bun.js** — preferred runtime over Node.js; use Bun APIs,
  `bun test`, `bun build`, and `bunx` where applicable

### Capabilities (minimum)

- Read a spec from `artifacts/specs/` and implement it
- Write TypeScript source files, tests, and configs
- Run builds and tests via Bash (`bun test`, `bun build`, etc.)
- Create and maintain `package.json`, `tsconfig.json`, and
  related project scaffolding
- Use Bun-native APIs (e.g., `Bun.serve`, `Bun.file`,
  `Bun.write`) when available instead of Node equivalents

### Constraints (minimum)

- Never make design decisions — follow the spec; if the spec is
  ambiguous, create a sub-task for `architect` to clarify
- Never author vault artifacts (task specs, agent specs, skills,
  docs) — delegate to `author`
- Prefer Bun.js runtime and tooling over Node.js unless the spec
  explicitly requires Node
- Run tests before marking work complete

### Discovery

3. Create the discovery symlink:
   `agents/developer.md -> ../artifacts/agents/developer.md`
4. Add `developer` to `.claude/agents/` if a symlink mapping is
   needed there for `--agent developer` resolution.

## Verification

- [ ] `artifacts/agents/developer.md` exists with valid `kind: agent` frontmatter
- [ ] Agent description clearly states implementation responsibility
- [ ] System prompt establishes TypeScript + Bash expertise and Bun.js preference
- [ ] Capabilities section covers spec reading, coding, testing, and scaffolding
- [ ] Constraints prevent design decisions and vault authoring
- [ ] `skills` includes `openstation-execute`
- [ ] Discovery symlink `agents/developer.md` points to canonical location
- [ ] Agent can be launched with `claude --agent developer`
