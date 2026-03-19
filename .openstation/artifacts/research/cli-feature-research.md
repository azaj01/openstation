# OpenStation CLI — Feature Research

Research artifact for task `0022-cli-feature-research`.

---

## 1. Language Choice: Bash vs Python vs TypeScript (Bun)

### Evaluation Matrix

| Criterion | Bash | Python (stdlib-only) | TypeScript (Bun) |
|-----------|------|---------------------|------------------|
| **YAML parsing** | Fragile — regex/sed on flat `key: value` only | Simple string splitting; handles edge cases cleanly | Manual string splitting; similar to Python |
| **Subcommand dispatch** | Manual `case` statement | `argparse.add_subparsers()` — built-in | `util.parseArgs` — flags only, no subcommand support; manual dispatch needed |
| **Flag parsing** | `getopts` (short only) or manual loop | `argparse` — long/short flags, types, defaults | `util.parseArgs` — boolean/string types, short aliases; no auto-help |
| **Table formatting** | `printf` with manual padding | String formatting, f-strings | Template literals, `padEnd()`/`padStart()` |
| **Symlink resolution** | `readlink -f` (GNU-only, missing on macOS) | `pathlib.Path.resolve()` — cross-platform | `fs.realpathSync()` — cross-platform |
| **Testing** | Needs `bats` or manual harness | `unittest` in stdlib | `bun:test` built-in (Jest-compatible) |
| **Portability** | Any POSIX shell | Requires Python 3.8+ (ubiquitous on dev machines) | Requires Bun runtime (not pre-installed anywhere) |
| **Consistency** | Matches install.sh, openstation-run.sh | New language in the project | New language + new runtime |
| **Maintainability** | Verbose, error-prone string manipulation | Structured data types, clean control flow | Strong typing, clean control flow |
| **Zero dependencies** | ✅ Truly zero | ✅ Stdlib-only, no pip install | ✅ Bun builtins, no npm install (but Bun itself is a dependency) |
| **Type safety** | ❌ None | Optional via type hints + mypy | ✅ Native TypeScript support |
| **Binary compilation** | N/A | N/A (pyinstaller is external) | `bun build --compile` → standalone binary (~40 MB) |

### Existing Codebase Context

The project currently has two bash scripts:
- `install.sh` — bootstraps Open Station into a project (one-time setup)
- `openstation-run.sh` — launches agents with `claude` CLI

Both are "do one thing" scripts with linear flow. The proposed CLI
is qualitatively different: multiple subcommands, flag combinations,
structured data parsing, and formatted output.

### Python vs TypeScript (Bun) — Direct Comparison

| Factor | Python 3.8+ (stdlib) | TypeScript (Bun runtime) |
|--------|---------------------|--------------------------|
| **Subcommand dispatch** | `argparse.add_subparsers()` handles subcommands, flags, auto-generated `--help` — all stdlib | `util.parseArgs` handles flags only; subcommand dispatch requires manual `switch/case` on positional args |
| **Auto-help generation** | ✅ `argparse` generates usage/help text automatically | ❌ Must be hand-written |
| **Runtime availability** | Pre-installed on macOS and most Linux distros | Must be installed separately (`curl -fsSL https://bun.sh/install \| bash`) |
| **Startup speed** | ~30-50 ms | ~5-10 ms (faster V8 startup) |
| **Binary distribution** | Shebang script (`#!/usr/bin/env python3`) — works immediately | `bun build --compile` produces a ~40 MB standalone binary, or requires Bun runtime |
| **Type safety** | Optional (type hints, no enforcement without mypy) | Native TypeScript enforcement at write-time |
| **YAML frontmatter** | `str.split(':', 1)` between `---` markers | Same approach with `string.split(':', 1)` |
| **Path handling** | `pathlib.Path` — ergonomic, cross-platform | `path` + `fs` modules — functional but more verbose |
| **Project fit** | Existing scripts are bash; Python is a common addition for developer tooling | Adds a new runtime dependency to a convention-based system |

**Key tradeoff**: TypeScript/Bun offers better type safety and
faster startup, but at the cost of requiring a non-standard runtime.
Python's `argparse` provides significantly better subcommand support
out of the box — `util.parseArgs` would require reimplementing
subcommand dispatch, help text generation, and argument validation
manually.

For a convention-based system with zero runtime dependencies as a
core principle, requiring Bun installation is a higher barrier than
requiring Python 3.8+ (which ships with the OS on target platforms).

### Recommendation: **Python**

**Rationale**: The CLI needs reliable YAML frontmatter parsing,
markdown table formatting, subcommand dispatch with flags, and
cross-platform symlink resolution. All of these are significantly
easier and more maintainable in Python's stdlib than in bash. The
`readlink -f` portability issue alone is a strong signal — Python's
`pathlib.Path.resolve()` handles this correctly on macOS and Linux
without workarounds.

Python wins over TypeScript/Bun on two critical factors:
1. **`argparse` vs `util.parseArgs`** — argparse provides
   subcommands, auto-help, type validation, and defaults with zero
   boilerplate. `util.parseArgs` handles flat flags only, requiring
   ~50 lines of manual subcommand dispatch and help text.
2. **Runtime availability** — Python 3.8+ is pre-installed on macOS
   and most Linux distributions. Bun requires explicit installation,
   contradicting the project's zero-dependency philosophy. The
   `--compile` binary option produces ~40 MB executables — excessive
   for a task listing tool.

TypeScript/Bun would be a reasonable choice if the CLI were a
larger application where type safety and startup performance
justified the runtime dependency. For a two-subcommand tool,
Python's stdlib advantage is decisive.

The existing bash scripts should remain as-is (they're simple and
appropriate for their purpose). The CLI is a different category of
tool.

---

## 2. Survey of Comparable CLI Tools

### Hugo (Go)

- **Pattern**: Hierarchical subcommands — `hugo list`, `hugo new`,
  `hugo server`
- **Dispatch**: Uses cobra library; root command with child commands
- **Config detection**: Walks up from CWD to find `hugo.toml` /
  `config.toml`
- **Relevant takeaway**: Auto-detect project root by walking up
  directories. Hugo's `list` subcommand (`hugo list drafts`,
  `hugo list future`) is a close analog to `openstation list`.

### Jekyll (Ruby)

- **Pattern**: Flat subcommands — `jekyll build`, `jekyll serve`,
  `jekyll new`, `jekyll clean`
- **Dispatch**: `Jekyll::Command` subclass pattern; plugins can
  register new subcommands
- **Config detection**: Looks for `_config.yml` in CWD
- **Relevant takeaway**: Simple subcommand model without nesting.
  Each command is self-contained with its own options.

### Taskfile / Task (Go + Bash variants)

- **Compiled Go variant** (`taskfile.dev`): Embedded shell
  interpreter, YAML task definitions, cross-platform
- **Bash variant** (`github.com/Enrise/Taskfile`): Function-name
  dispatch from a `./Taskfile` script
- **Relevant takeaway**: The bash variant demonstrates that simple
  function dispatch works for small CLIs, but it lacks flag parsing
  and structured output. The Go variant validates that a real CLI
  needs more than shell primitives.

### mise (Rust)

- **Pattern**: `mise run <task>`, `mise install`, etc.
- **Config detection**: Walks up directory tree for `.mise.toml`
  or `.tool-versions`
- **Relevant takeaway**: Multi-file config detection with fallback
  chain. Similar to our need to detect `.openstation/` vs source repo.

### Summary of Patterns

| Tool | Language | Root Detection | Subcommand Style |
|------|----------|---------------|------------------|
| Hugo | Go | Walk up for config file | Hierarchical |
| Jekyll | Ruby | CWD only | Flat |
| Task | Go/Bash | CWD Taskfile | Flat |
| mise | Rust | Walk up for config | Flat |
| **OpenStation** | **Python** | **Walk up for .openstation/ or agents/** | **Flat** |

---

## 3. Argument Parsing

### Python `argparse` Subcommand Pattern

The standard approach for stdlib-only Python CLIs:

```python
parser = argparse.ArgumentParser(prog='openstation')
subparsers = parser.add_subparsers(dest='command')

# list subcommand
list_parser = subparsers.add_parser('list')
list_parser.add_argument('--status', default=None)
list_parser.add_argument('--agent', default=None)

# show subcommand
show_parser = subparsers.add_parser('show')
show_parser.add_argument('task', help='Task ID or slug')

args = parser.parse_args()
```

### Key Decisions

- **Subparsers `required=True`** (Python 3.7+) — ensures a
  subcommand is provided; prints help otherwise.
- **`set_defaults(func=handler)`** — each subparser stores its
  handler function, allowing clean dispatch via `args.func(args)`.
- **`--status` filter** — accepts `ready`, `in-progress`, `done`,
  `all`, etc. Default behavior: exclude `done`/`failed`.
- **`--agent` filter** — simple string match against frontmatter.

### Edge Cases

- No subcommand provided → print help and exit 1
- Unknown subcommand → argparse handles automatically
- `--status all` → override default done/failed exclusion
- Combined filters → AND logic (`--status ready --agent researcher`)

---

## 4. Symlink Edge Cases

### macOS vs Linux

| Issue | macOS | Linux | Mitigation |
|-------|-------|-------|------------|
| `readlink -f` | ❌ Not available (BSD readlink) | ✅ GNU coreutils | Use Python `pathlib.Path.resolve()` |
| Case sensitivity | Case-insensitive (APFS default) | Case-sensitive (ext4) | Already mitigated: project uses kebab-case |
| `ln -s` relative paths | Works | Works | Use consistent relative targets |

### Relative Symlink Resolution

Open Station symlinks use relative targets:
```
tasks/current/0021-openstation-cli → ../../artifacts/tasks/0021-openstation-cli
```

**Key rule**: Relative symlinks resolve from the symlink's parent
directory, not from CWD.

In Python:
```python
from pathlib import Path

# Resolve symlink to canonical path
link = Path("tasks/current/0021-openstation-cli")
canonical = link.resolve()  # follows symlinks, returns absolute path
```

`Path.resolve()` handles:
- Relative symlink targets
- Chained symlinks (symlink → symlink → real dir)
- `..` components in paths

### Dangerous Patterns to Avoid

- `rm -r symlink/` (trailing slash) — may follow symlink and delete
  target contents on some platforms. Always `rm symlink` without
  trailing slash.
- `os.walk()` follows symlinks by default in Python — use
  `followlinks=False` or stick to `os.listdir()` + manual resolution.

### Broken Symlinks

The CLI should handle broken symlinks gracefully (e.g., a bucket
symlink pointing to a deleted task folder). Use `Path.exists()`
which returns `False` for broken symlinks, while `Path.is_symlink()`
returns `True`.

---

## 5. Integration Detection Strategy

### The Two Environments

| Environment | Structure | Detection Signal |
|-------------|-----------|------------------|
| Source repo | `./tasks/`, `./artifacts/`, `./agents/`, `./install.sh` | `install.sh` exists at root |
| Installed project | `.openstation/tasks/`, `.openstation/artifacts/`, etc. | `.openstation/` directory exists |

### Detection Algorithm

Matches the existing pattern in `openstation-run.sh`
(`find_project_root()`):

```python
def find_project_root(start: Path) -> tuple[Path, str]:
    """Walk up from start to find project root.

    Returns (root_path, prefix) where prefix is:
      - ".openstation" for installed projects
      - "" for the source repo
    """
    current = start.resolve()
    while current != current.parent:
        if (current / ".openstation").is_dir():
            return current, ".openstation"
        if (current / "agents").is_dir() and (current / "install.sh").is_file():
            return current, ""
        current = current.parent
    raise SystemExit("error: not in an Open Station project")
```

### Path Abstraction

Once root and prefix are known, all paths become:
```python
tasks_dir = root / prefix / "artifacts" / "tasks"
```

This single prefix variable eliminates conditional logic throughout
the codebase.

### Precedence

If both `.openstation/` and `agents/` + `install.sh` exist (e.g.,
the source repo after running `install.sh --local .`), prefer
`.openstation/` since that's the canonical installed structure.

---

## Recommendations

1. **Use Python 3.8+ with stdlib only** — `argparse` for CLI,
   `pathlib` for paths, simple string parsing for YAML frontmatter.

2. **Single-file CLI** — `openstation` (or `openstation.py`) as a
   single executable script with `#!/usr/bin/env python3`. No package
   structure needed for two subcommands.

3. **Replicate root detection from openstation-run.sh** — walk up
   directories, detect `.openstation/` vs source repo, set prefix.

4. **Default exclude done/failed** — matches the existing
   `/openstation.list` command behavior. `--status all` overrides.

5. **YAML parsing** — simple `str.split(':', 1)` between `---`
   delimiters. No need for a full YAML parser given the flat
   frontmatter format used by task specs.

6. **Install the CLI** — `install.sh` should copy the script to
   `.openstation/bin/openstation` and optionally add it to PATH
   or create a wrapper script.

## Tags

#openstation #cli #research #python #argparse
