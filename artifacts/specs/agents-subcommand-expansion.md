---
kind: spec
name: agents-subcommand-expansion
agent: architect
task: "[[0113-spec-agents-subcommand-expansion]]"
created: 2026-03-12
status: draft
---

# Agents Subcommand Expansion

Expand `openstation agents` from a flat agent-listing command into
a subcommand group with `list`, `show`, and `dispatch` sub-actions.

## Problem

`openstation agents` currently only prints a name/description
table. To inspect an agent's full spec or launch it, users must
know separate commands (`cat agents/<name>.md`, `openstation run
<name>`). Grouping these under `agents` improves discoverability
and consistency with how `list`/`show` work for tasks.

## Architecture

### Command Routing

```
openstation agents [sub-action] [args]

         +------------------+
         | agents parser    |
         | (sub_sub = ...)  |
         +--------+---------+
                  |
     +------------+------------+
     v            v            v
   list         show       dispatch
  (default)   <name>       <name>
```

Bare `openstation agents` (no positional) routes to `list`.
This preserves backward compatibility.

### Data Flow

```
artifacts/agents/*.md
        |
        v
  discover_agents()       -> list of agent dicts
        |
        +-> list: format_agents_table() or JSON -> stdout
        |
        +-> show: read full spec file -> stdout (or JSON/vim)
        |
        +-> dispatch: find_agent_spec() -> execvp claude --agent
```

## Sub-Actions

### `agents list` (default)

```
openstation agents [list] [--json | --quiet]
```

| Flag | Short | Description |
|------|-------|-------------|
| `--json` | `-j` | JSON array of agent objects |
| `--quiet` | `-q` | One agent name per line (pipe-friendly) |

`--json` and `--quiet` are mutually exclusive (same pattern as
`openstation list`). Default output is the existing table format.

Reuses `discover_agents()` and `format_agents_table()`.

**Exit codes**: 0 success (even if no agents found), 1 usage
error, 2 not in project.

### `agents show <name>`

```
openstation agents show <name> [--json | --vim]
```

| Argument/Flag | Required | Description |
|---------------|----------|-------------|
| `name` | yes | Agent name (filename stem in `artifacts/agents/`) |
| `--json` | no | Frontmatter fields + `body` key as JSON object |
| `--vim` | no | Open spec file in vim (reuse `exec_vim()`) |

**Name resolution**: exact match only (`<name>.md` in
`artifacts/agents/`). No prefix or fuzzy matching — agent names
are short and explicit. On not-found, hint with available agents.

**`--json` shape**: all frontmatter fields as top-level keys,
plus a `body` key containing the markdown after the closing `---`.
Needs a `core.extract_body(text)` helper if one doesn't exist.

**Exit codes**: 0 success, 1 usage error, 2 not in project,
3 not found.

### `agents dispatch <name>`

```
openstation agents dispatch <name>
```

Launch an interactive Claude Code session with the named agent.
No output format flags — this replaces the process via `execvp`.

**Behavior**:
1. Resolve agent spec via `find_agent_spec()`
2. Verify spec exists; if not -> exit 3 with hint
3. Verify `claude` is on `$PATH`; if not -> exit 7
4. `execvp` into `claude --agent <name>`

No `--tier`, `--budget`, `--turns` flags — those belong to
`openstation run`. `dispatch` is an interactive shortcut only.

**Exit codes**: 1 usage error, 2 not in project, 3 not found,
7 claude not found.

## Argparse Approach

Use **nested subparsers** — `agents` gets its own
`add_subparsers(dest="agents_action")` with `list`, `show`, and
`dispatch` as sub-commands.

**Backward compatibility**: when `agents_action` is `None` (bare
`openstation agents`), route to `list` with default flags. The
`args` object won't have output-format attributes in this case —
handlers must use `getattr` defensively.

## Implementation Scope

### Files to Modify

| File | Change |
|------|--------|
| `src/openstation/cli.py` | Replace flat `agents` parser with nested subparsers |
| `src/openstation/run.py` | Split `cmd_agents` into three handlers: `cmd_agents_list`, `cmd_agents_show`, `cmd_agents_dispatch` |

### Files to Create

| File | Purpose |
|------|---------|
| `tests/test_agents_subcommand.py` | Tests for all three sub-actions + backward compat |

### New Helper

`core.extract_body(text)` — return the markdown body after the
closing `---` frontmatter delimiter. Add to `core.py` if it
doesn't already exist.

## Design Decisions

### DD-1: Nested subparsers, not positional heuristics

**Alternative**: single positional arg with heuristics (if it
matches an agent name -> show, else -> sub-action keyword).
**Rejected**: an agent named "list" or "show" would collide.
**Trade-off**: more argparse setup, but unambiguous parsing and
proper `--help` per sub-action.

### DD-2: Bare `agents` defaults to `list`

Backward compatibility. Today `openstation agents` lists agents;
it must continue doing so.

### DD-3: `dispatch` has no execution flags

`openstation run` is the full-featured execution path. `dispatch`
is `claude --agent <name>` with agent resolution. Duplicating
flags creates two config paths.

### DD-4: No `--vim` on `list`

`--vim` opens a single file. A list has no single file to open.

## Verification

| Criterion | How to verify |
|-----------|---------------|
| `list` works | `openstation agents list` outputs table |
| `list` is default | `openstation agents` same output as `agents list` |
| `list --json` | Valid JSON array |
| `list --quiet` | One name per line, no header |
| `show <name>` | Prints full agent spec markdown |
| `show --json` | JSON with frontmatter fields + body |
| `show --vim` | Opens file in vim |
| `show` not found | Exit 3, lists available agents |
| `dispatch <name>` | Replaces process with `claude --agent` |
| `dispatch` not found | Exit 3, lists available |
| `dispatch` no claude | Exit 7 with hint |
| Backward compat | `openstation agents` output unchanged |
