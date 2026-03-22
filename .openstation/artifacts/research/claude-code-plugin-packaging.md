---
kind: research
name: claude-code-plugin-packaging
agent: researcher
task: "[[0174-research-claude-code-plugin-packaging]]"
created: 2026-03-19
---

# Claude Code Plugin Packaging for Open Station

## Recommendation

**Hybrid approach.** Package Open Station's static prompts
(commands, skills, default agent templates) as a Claude Code
plugin for discovery and updates, while keeping `openstation init`
for project-specific setup (directory creation, task storage,
customized agents, CLAUDE.md injection). This gives the best of
both: native plugin UX for installation/updates plus
project-local state ownership.

---

## 1. Plugin Mechanics

### Discovery and Loading

Claude Code discovers plugins through two paths:

- **Marketplace install (persistent):** Plugins installed via
  `/plugin install plugin-name@marketplace-name` are cached at
  `~/.claude/plugins/cache/`. They auto-load on every session.
- **Session-scoped (development):** `claude --plugin-dir ./path`
  loads a plugin for the current session only.

Plugins are enabled/disabled per scope in settings files:

```json
{
  "enabledPlugins": {
    "open-station@marketplace-name": true
  }
}
```

Settings precedence: managed > local > project > user.

A `/reload-plugins` command picks up changes without restarting.

### Coexistence with `.claude/`

**Confirmed: plugins coexist with `.claude/` contents.** The
plugin system uses namespacing to avoid collisions:

| Source | Command name |
|--------|-------------|
| `.claude/commands/foo.md` | `/foo` |
| Plugin `bar` with `commands/foo.md` | `/bar:foo` |

The official docs recommend starting with standalone `.claude/`
for iteration, then migrating to a plugin for sharing. Both can
exist simultaneously.

### Resolution Order

- Plugin commands/skills are namespaced as
  `/plugin-name:component-name`, so they don't collide with
  `.claude/` equivalents.
- `--plugin-dir` (local) overrides marketplace plugins of the
  same name for that session.
- Managed-scope plugins (admin-enforced) cannot be overridden.
- The docs do not specify what happens when two marketplace
  plugins from different marketplaces share the same `name`.

**Implication for Open Station:** If we ship both a plugin AND
keep `.claude/` symlinks, commands would appear twice (e.g.,
`/openstation.create` and `/open-station:openstation.create`).
The hybrid approach must choose one discovery path per component.

---

## 2. Fit with Open Station's Model

### Per-Project Customization

Plugins are read-only from the user's perspective. Plugin files
are cached at `~/.claude/plugins/cache/` and cannot be modified
in place. This is a fundamental mismatch with Open Station's
current model, where `openstation init` copies agent templates
into `.openstation/artifacts/agents/` so projects can customize
them (e.g., adapting agent names, adding project-specific
instructions).

**How other plugins handle this:** They don't — plugins like
feature-dev and hookify ship fixed agents/skills with no
per-project override mechanism. The plugin spec has no layering
or override system.

**Workaround:** Ship generic/default agents via the plugin;
let `openstation init` create customized copies in
`.openstation/` that take precedence through `.claude/agents/`
symlinks. Since `.claude/agents/` resolves before plugin agents
(direct path vs namespaced), local agents win.

### Working Directory Access

Plugin hook scripts and MCP servers run as subprocesses with
access to the project working directory (cwd). The plugin
itself uses `${CLAUDE_PLUGIN_ROOT}` for self-references and
`${CLAUDE_PLUGIN_DATA}` for persistent state.

**Confirmed:** The execute skill's references to
`.openstation/artifacts/tasks/` would work because skills are
prompt text loaded into the conversation — they instruct the
LLM to use filesystem tools, which operate in the project cwd.
Skills don't need filesystem access themselves.

### Hooks

**Confirmed:** Plugins can ship `hooks/hooks.json` with full
lifecycle hook support (22 event types including `SessionStart`).
This could replace the manual `.claude/settings.json` hook
configuration that `openstation init` currently requires.

Example from hookify:
```json
{
  "hooks": {
    "PreToolUse": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ${CLAUDE_PLUGIN_ROOT}/hooks/handler.py",
        "timeout": 10
      }]
    }]
  }
}
```

A plugin `SessionStart` hook could inject the CLAUDE.md managed
section without requiring `openstation init` to modify
`.claude/settings.json`.

---

## 3. Pros and Cons Analysis

| Dimension | Current (init + copy/symlink) | Plugin | Hybrid |
|-----------|-------------------------------|--------|--------|
| **Installation UX** | `openstation init` (requires prior `install.sh`) | `/plugin install` or `claude plugin install` — native, familiar | Plugin for prompts + `openstation init` for project setup |
| **Update story** | `openstation init` re-copies (manual) | Version bump in marketplace triggers auto-update or manual `/plugin update` | Plugin auto-updates prompts; `openstation init` for project state |
| **Per-project customization** | Edit copied files freely in `.openstation/` | Not supported — plugins are read-only | Plugin ships defaults; init copies customizable agents |
| **Self-contained projects** | Yes — `.openstation/` has everything, works offline | No — depends on plugin cache at `~/.claude/plugins/` | Partial — project state is local, prompts need plugin installed |
| **Offline support** | Full — all files are local | Full once installed — cached locally at `~/.claude/plugins/cache/` | Full once both plugin + init are done |
| **Discoverability** | Symlinks in `.claude/` (invisible to users unfamiliar with the project) | Native plugin registry, `/plugin` UI, marketplace browsing | Best of both — discoverable via marketplace + local state |
| **Hooks integration** | Manual `.claude/settings.json` editing or SessionStart hook in settings | Plugin-native `hooks/hooks.json` — cleaner, no settings.json editing | Plugin ships hooks natively |
| **MCP server bundling** | Separate config | `.mcp.json` in plugin — auto-configured | Plugin ships MCP if needed |
| **Version pinning** | Git tag in install cache | Semver in `plugin.json`, tracked in `installed_plugins.json` with git SHA | Plugin versioned; init tracks compatibility |
| **Team sharing** | Commit `.openstation/` to repo | Add marketplace + `enabledPlugins` to `.claude/settings.json` | Both — plugin ref in settings + `.openstation/` in repo |
| **New project setup** | `install.sh` + `openstation init` (2 steps) | `claude plugin install open-station` (1 step for prompts) | 1 step for prompts + `openstation init` for project state |
| **Existing `.claude/` conflict** | Symlink merging logic (complex, fragile) | Namespaced — no conflicts | Eliminates symlink complexity for commands/skills |

---

## 4. Migration Path

### Viable Hybrid Model

**Plugin provides (read-only, auto-updated):**
- Commands (`/open-station:openstation.create`, etc.)
- Skills (`openstation-execute`)
- Default agent templates (as reference, not for direct use)
- Hooks (`SessionStart` for CLAUDE.md injection)
- Optionally: MCP server for the CLI

**`openstation init` provides (project-local, customizable):**
- `.openstation/` directory structure
- `artifacts/tasks/`, `artifacts/agents/`, etc.
- Customized agent copies in `.openstation/artifacts/agents/`
- `.openstation/docs/` (lifecycle, task spec)
- Discovery symlinks for customized agents only
  (`.claude/agents/` -> `.openstation/agents/`)

### Migration Steps

1. Create `.claude-plugin/plugin.json` in the Open Station repo
2. Move commands to plugin `commands/` layout
3. Move skills to plugin `skills/` layout
4. Create `hooks/hooks.json` for SessionStart injection
5. Publish to a marketplace (own repo or official)
6. Update `openstation init` to:
   - Skip command/skill copying (plugin handles these)
   - Keep directory creation and agent template installation
   - Remove `.claude/commands` and `.claude/skills` symlink logic
   - Keep `.claude/agents` symlinks (for customized agents)

### Naming Consideration

Plugin namespacing means commands become
`/open-station:openstation.create` — the double "openstation"
is redundant. Options:
- Name the plugin `os` -> `/os:openstation.create` (conflicts
  with "operating system")
- Rename commands to drop the prefix -> `/open-station:create`,
  `/open-station:list` (breaking change for existing users)
- Accept the redundancy (least disruptive)

---

## 5. Reference Plugin Analysis

### hookify (most complete example)

**Structure:**
```
hookify/
├── .claude-plugin/plugin.json
├── agents/           # 1 agent
├── commands/         # 3 commands (hookify, list, configure)
├── core/             # Python core logic
├── hooks/hooks.json  # PreToolUse, PostToolUse, Stop, UserPromptSubmit
├── matchers/         # Hook matcher patterns
├── skills/           # 1 skill (writing-rules)
└── utils/            # Shared utilities
```

**Key patterns:**
- Uses `${CLAUDE_PLUGIN_ROOT}` in hooks.json for portable paths
- Python scripts in `hooks/` run as subprocesses with project cwd
- Commands reference plugin internals via relative paths
- Skills follow the `skills/name/SKILL.md` convention
- No MCP servers — pure prompt + hook architecture

**Relevance to Open Station:** Hookify's architecture is the
closest match. It ships commands, skills, hooks, and an agent —
the same components Open Station needs. The key difference is
hookify has no project-local state, confirming that the
customization gap is real and requires the hybrid approach.

### feature-dev (commands + agents)

**Structure:**
```
feature-dev/
├── .claude-plugin/plugin.json
├── agents/           # 3 agents (code-explorer, code-architect, code-reviewer)
├── commands/         # 1 command (feature-dev)
└── README.md
```

**Key patterns:**
- Minimal plugin — only commands and agents, no skills or hooks
- Agents are specialized subagents launched by the main command
- No per-project customization — same agents everywhere
- 119,000+ installs — most popular official plugin

**Relevance to Open Station:** Demonstrates that agent-heavy
plugins work well when agents are generic (code review, architecture).
Open Station's agents are project-customized, which is why
feature-dev's pattern doesn't directly apply.

### plugin-dev (meta-plugin)

**Structure:**
```
plugin-dev/
├── .claude-plugin/plugin.json
├── agents/           # Plugin development agents
├── commands/         # create-plugin command (8-phase workflow)
├── skills/           # 7 skills covering plugin development
└── README.md
```

**Key patterns:**
- Heavy use of skills for domain knowledge
- Multi-phase guided workflow in the main command
- Skills document best practices and reference material
- ~21,000 words of documentation embedded in skills

**Relevance to Open Station:** Shows that skills-heavy plugins
are viable. Open Station's execute skill (~300 lines) fits
comfortably within this pattern.

---

## Confidence Levels

| Finding | Confidence |
|---------|-----------|
| Plugins coexist with `.claude/` | **Confirmed** — documented, tested by reference plugins |
| Plugin commands are namespaced | **Confirmed** — documented, observed in installed plugins |
| Hooks work in plugins | **Confirmed** — hookify demonstrates all major event types |
| Skills work in plugins | **Confirmed** — hookify and plugin-dev ship skills |
| No per-project override mechanism | **Confirmed** — no docs mention it, no plugins implement it |
| Hybrid approach is viable | **Likely** — follows documented patterns, but untested for Open Station specifically |
| Auto-update works reliably | **Likely** — documented, but depends on marketplace configuration |
| Command naming redundancy | **Confirmed** — namespacing is mandatory for plugin commands |

---

## Sources

- [Plugins reference — Claude Code Docs](https://code.claude.com/docs/en/plugins-reference)
- [Create plugins — Claude Code Docs](https://code.claude.com/docs/en/plugins)
- [Discover and install plugins — Claude Code Docs](https://code.claude.com/docs/en/discover-plugins)
- [anthropics/claude-plugins-official (GitHub)](https://github.com/anthropics/claude-plugins-official)
- hookify plugin source: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/hookify/`
- feature-dev plugin source: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/feature-dev/`
- plugin-dev plugin source: `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/plugin-dev/`
- Open Station `src/openstation/init.py` — current init implementation
