---
kind: task
name: 0022-cli-feature-research
status: done
assignee: researcher
owner: manual
parent: "[[0021-openstation-cli]]"
created: 2026-03-01
---

# CLI Feature Research

## Requirements

Research design decisions for the OpenStation CLI tool:

1. **Language choice** — evaluate bash vs Python (stdlib-only) vs
   TypeScript/Bun for maintainability, portability, and testability.
   Include a direct comparison of Python and TypeScript (Bun runtime).
2. **CLI patterns** — survey how similar convention-based tools
   (e.g., Hugo, Jekyll, Taskfile) structure their CLIs
3. **Argument parsing** — identify idiomatic approaches for the
   chosen language (argparse, getopts, subcommand dispatch)
4. **Symlink management** — document edge cases around
   cross-platform symlink creation and resolution
5. **Integration points** — how the CLI detects whether it's
   running in the source repo vs an `.openstation/`-installed project

## Findings

Full research in `artifacts/research/cli-feature-research.md`.

### Language Choice

**Recommend Python 3.8+ (stdlib-only)** over bash and TypeScript/Bun.

**Python vs Bash** — Python wins on `argparse` subcommand dispatch,
`pathlib` cross-platform symlinks, and `unittest` testing. Bash
scripts are appropriate for linear "do one thing" purposes; the CLI
is a different category of tool.

**Python vs TypeScript/Bun** — evaluated Bun's `util.parseArgs`,
built-in TypeScript support, and `bun build --compile` binary
compilation. Python wins on two critical factors:
- `argparse` provides subcommands, auto-help, type validation out of
  the box. `util.parseArgs` handles flat flags only — subcommand
  dispatch, help text, and validation would need ~50 lines of manual
  code.
- Python 3.8+ ships pre-installed on macOS/Linux. Bun requires
  explicit installation, contradicting the zero-dependency principle.
  Compiled binaries are ~40 MB — excessive for a task listing tool.

TypeScript/Bun would be reasonable for a larger CLI where type safety
and startup performance justify the runtime dependency. For two
subcommands, Python's stdlib advantage is decisive.

### CLI Tool Survey

Surveyed 4 tools: Hugo, Jekyll, Taskfile, mise. Key patterns:

- All use flat subcommand dispatch (not nested)
- Root detection via walking up directory tree (Hugo, mise) is the
  dominant pattern — matches existing `openstation-run.sh`
- Config auto-detection with environment prefix is standard

### Argument Parsing

Python `argparse.add_subparsers()` with `set_defaults(func=handler)`
is the standard zero-dependency pattern. Handles `list --status ready
--agent researcher` and `show <task>` cleanly.

### Symlink Edge Cases

- macOS lacks `readlink -f` — Python `pathlib` resolves this
- Relative symlinks resolve from the symlink's parent, not CWD
- Broken symlinks: `Path.exists()` returns False, `Path.is_symlink()`
  returns True — must handle gracefully
- Never `rm -r symlink/` (trailing slash) — may follow symlink

### Integration Detection

Walk up from CWD; check for `.openstation/` (installed) or
`agents/` + `install.sh` (source repo). Set prefix accordingly.
All paths become `root / prefix / "artifacts" / "tasks"`.

## Recommendations

1. Single-file Python script (`openstation` with `#!/usr/bin/env python3`)
2. Replicate root detection from `openstation-run.sh`
3. Default exclude done/failed; `--status all` overrides
4. Simple `str.split(':', 1)` YAML parsing between `---` delimiters
5. Install via `install.sh` to `.openstation/bin/openstation`

## Verification

- [ ] Language recommendation with pros/cons (must include Python vs TypeScript/Bun comparison)
- [ ] Survey of at least 3 comparable CLI tools
- [ ] Documented symlink edge cases
- [ ] Integration detection strategy documented
