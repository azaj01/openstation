---
kind: task
name: 0174-research-claude-code-plugin-packaging
status: done
type: research
assignee: researcher
owner: project-manager
created: 2026-03-19
artifacts:
  - "[[artifacts/research/claude-code-plugin-packaging]]"
---

# Research: Package Open Station as a Claude Code Plugin

## Context

Claude Code now has an official plugin system
(`anthropics/claude-code/plugins/`). A plugin is a directory
containing `.claude-plugin/plugin.json` metadata plus optional
`commands/`, `agents/`, `skills/`, `hooks/`, and `.mcp.json`.

Open Station currently installs via `openstation init`, which
copies commands/skills/docs into `.openstation/` and creates
symlinks under `.claude/` for discovery. The question is whether
wrapping our prompts (agents, skills, commands) as a Claude Code
plugin would be a better delivery mechanism.

## Research Questions

### 1. Plugin mechanics

- How does Claude Code discover and load plugins? (settings.json
  config? marketplace install? local path?)
- Can a plugin coexist with existing `.claude/` directory
  contents (commands, agents, skills from other sources)?
- What is the plugin resolution order when the same command or
  agent name exists in both a plugin and `.claude/`?

### 2. Fit with Open Station's model

- Agents/skills/commands would be read-only from the plugin.
  Open Station currently copies agent templates so projects can
  customize them. How would per-project customization work in a
  plugin model? Can plugins support overrides?
- The execute skill references vault-local paths
  (`.openstation/artifacts/tasks/`). Does a plugin have access
  to the project working directory?
- Can a plugin ship hooks (e.g., SessionStart) that inject the
  CLAUDE.md managed section?

### 3. Pros and cons analysis

Evaluate these dimensions:

| Dimension | Current (init + copy/symlink) | Plugin |
|-----------|-------------------------------|--------|
| Installation UX | `openstation init` | `claude plugin install` or settings.json |
| Update story | `openstation init` re-copies | Plugin version bump, auto-update? |
| Per-project customization | Edit copied files freely | Overrides? Layering? |
| Self-contained projects | Yes, `.openstation/` has everything | Depends on plugin runtime |
| Offline support | Full | Does plugin need network? |
| Discoverability | Symlinks in `.claude/` | Native plugin registry |
| Hooks integration | Manual `.claude/settings.json` | Plugin-native hooks |
| MCP server bundling | Separate config | `.mcp.json` in plugin |
| Version pinning | Git tag in install cache | Plugin version in metadata |
| Team sharing | Commit `.openstation/` | Commit plugin reference |

### 4. Migration path

- Could we ship a plugin that only provides the *static*
  prompts (commands, skills, default agents) while `init` still
  handles the *project-specific* setup (directories, task
  storage, customized agents)?
- Is a hybrid approach viable: plugin for discovery, init for
  state?

### 5. Reference plugins to study

- `feature-dev` — has commands + agents, similar structure
- `hookify` — has commands + agents + skills + hooks, most
  complete example
- `plugin-dev` — meta-plugin for building plugins, documents
  best practices

## Deliverable

A research note in `artifacts/research/` covering all five
sections above, with a clear recommendation: adopt plugin
packaging, stay with current init, or hybrid approach.

## Findings

**Recommendation: Hybrid approach** — plugin for static prompts
(commands, skills, hooks), `openstation init` for project state
(directories, customized agents, task storage).

Key findings:

1. **Plugin mechanics are well-suited** — Claude Code plugins
   support commands, agents, skills, hooks, and MCP servers.
   Discovery is native via marketplace UI and `/plugin install`.
   Plugins coexist with `.claude/` contents through namespacing.

2. **No per-project override mechanism exists** — Plugins are
   read-only (cached at `~/.claude/plugins/cache/`). This is the
   critical gap: Open Station copies agent templates so projects
   can customize them. No plugin supports overrides or layering.

3. **Hybrid is viable** — Plugin ships commands + skills + hooks
   (auto-updated, zero config). Init creates project directories
   and customized agents. Local `.claude/agents/` symlinks take
   precedence over plugin agents for customized agents.

4. **Hooks are a clear win** — Plugin-native `hooks/hooks.json`
   replaces manual `.claude/settings.json` editing. SessionStart
   hook can inject the CLAUDE.md managed section automatically.

5. **Command naming needs thought** — Plugin namespacing creates
   `/open-station:openstation.create` (redundant). Options:
   rename commands to drop prefix, or accept the redundancy.

Three reference plugins analyzed (hookify, feature-dev,
plugin-dev). Hookify is the closest architectural match.
Full analysis in
[[artifacts/research/claude-code-plugin-packaging]].

## Progress

- 2026-03-19: Researched Claude Code plugin system — studied
  official docs, three reference plugins (hookify, feature-dev,
  plugin-dev), and Open Station's init.py. Produced research
  note with hybrid recommendation.

## Verification

- [ ] All five research questions answered with evidence
- [ ] Pros/cons table filled in with concrete findings
- [ ] At least two reference plugins analyzed in detail
- [ ] Clear recommendation with rationale
- [ ] Research note stored in `artifacts/research/`
