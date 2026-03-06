---
kind: research
name: install-vs-init-patterns
agent: researcher
task: "[[0056-research-install-vs-init-patterns]]"
created: 2026-03-05
---

# Install vs Init Patterns in CLI Tools

Research into how established CLI tools separate tool installation
from project initialization, informing the design of
`openstation init`.

---

## 1. Survey of CLI Tools

### 1.1 Git

| Aspect | Details |
|--------|---------|
| **Install** | System package manager (`apt`, `brew`, etc.) puts `git` on PATH |
| **Init** | `git init [directory]` |
| **What init creates** | `.git/` directory with `objects/`, `refs/`, `HEAD`, template hooks |
| **Arguments** | `[directory]` (default: `.`), `--bare`, `--template=<dir>`, `--initial-branch=<name>` |
| **Idempotent?** | **Yes** — running in an existing repo is safe; re-creates templates, does not overwrite `.git/config` or existing refs |
| **Output** | `Initialized empty Git repository in /path/.git/` or `Reinitialised existing Git repository in /path/.git/` |

**Key insight:** Git explicitly distinguishes first-run from re-run
in its output message. Re-init only refreshes templates and is
non-destructive.

### 1.2 npm

| Aspect | Details |
|--------|---------|
| **Install** | `brew install node`, `nvm install`, or OS package manager |
| **Init** | `npm init` (interactive) or `npm init -y` (defaults) |
| **What init creates** | `package.json` in current directory |
| **Arguments** | `-y`/`--yes` (skip prompts), `--scope`, `<initializer>` (delegates to `npx create-<name>`) |
| **Idempotent?** | **Yes** — "strictly additive, keeps any fields and values already set" |
| **Output** | Interactive questionnaire or silent JSON creation with `-y` |

**Key insight:** npm init is additive — it merges with existing
`package.json` rather than overwriting. The `-y` flag enables
fully non-interactive use.

### 1.3 Cargo (Rust)

| Aspect | Details |
|--------|---------|
| **Install** | `rustup` installs the Rust toolchain including `cargo` |
| **Init** | `cargo init [path]` (in existing dir) vs `cargo new <path>` (creates dir) |
| **What init creates** | `Cargo.toml`, `src/main.rs` (or `src/lib.rs` with `--lib`), `.gitignore` |
| **Arguments** | `--lib` (library), `--name <name>`, `--vcs <vcs>`, `--edition <year>` |
| **Idempotent?** | **No** — errors if `Cargo.toml` already exists |
| **Output** | `Created binary (application) package` |

**Key insight:** Cargo distinguishes `init` (existing directory)
from `new` (new directory). Neither is idempotent — they refuse
to overwrite. However, `init` is smart about existing source
files: if `src/main.rs` already exists, it uses it instead of
generating a template.

### 1.4 Terraform

| Aspect | Details |
|--------|---------|
| **Install** | `brew install terraform` or download binary from HashiCorp |
| **Init** | `terraform init` |
| **What init creates** | `.terraform/` directory, downloads providers + modules, configures backend |
| **Arguments** | `-backend-config=<path>`, `-upgrade`, `-reconfigure`, `-migrate-state`, `-input=false` |
| **Idempotent?** | **Yes** — explicitly documented: "safe to run multiple times" |
| **Output** | Verbose progress per provider/module, final `Terraform has been successfully initialized!` |

**Key insight:** Terraform `init` is both project setup AND
dependency installation (providers, modules). It blends
`npm init` + `npm install` semantics. The `-upgrade` flag
makes re-init update locked dependencies.

### 1.5 Poetry (Python)

| Aspect | Details |
|--------|---------|
| **Install** | `pipx install poetry` or `curl` installer |
| **Init** | `poetry init` (interactive) vs `poetry new <path>` (creates dir + project) |
| **What init creates** | `pyproject.toml` in current directory |
| **Arguments** | `--name`, `--description`, `--author`, `--python`, `--dependency`, `--dev-dependency`, `--no-interaction` |
| **Idempotent?** | **No** — errors if `pyproject.toml` already exists |
| **Output** | Interactive questionnaire or silent with `--no-interaction` |

**Key insight:** Like Cargo, Poetry separates `init` (existing
dir) from `new` (new dir). The `--no-interaction` flag enables
scripted use with sensible defaults.

### 1.6 ESLint

| Aspect | Details |
|--------|---------|
| **Install** | `npm install eslint` (local) or `npm install -g eslint` (global) |
| **Init** | `eslint --init` (delegates to `npm init @eslint/config`) |
| **What init creates** | `eslint.config.js` configuration file |
| **Arguments** | `--config <name>` (use shared config) |
| **Idempotent?** | **Yes** — overwrites config file; no harm in re-running |
| **Prerequisite** | Requires `package.json` to exist first |
| **Output** | Interactive wizard with questions about framework, style, etc. |

**Key insight:** ESLint's init is pure configuration generation —
it doesn't touch project structure. Requires the ecosystem
(`package.json`) to already exist.

### 1.7 Go Modules

| Aspect | Details |
|--------|---------|
| **Install** | OS package manager or `go.dev/dl` installer |
| **Init** | `go mod init <module-path>` |
| **What init creates** | `go.mod` file with `module` and `go` directives |
| **Arguments** | `<module-path>` (required — e.g., `github.com/user/project`) |
| **Idempotent?** | **No** — fails if `go.mod` already exists |
| **Output** | Silent on success |

**Key insight:** Go requires a positional argument (module path)
making initialization explicit about project identity. Not
idempotent — strict one-time initialization.

### 1.8 Husky

| Aspect | Details |
|--------|---------|
| **Install** | `npm install husky --save-dev` |
| **Init** | `npx husky init` |
| **What init creates** | `.husky/` directory with `pre-commit` script; updates `prepare` script in `package.json` |
| **Arguments** | Minimal — no flags |
| **Idempotent?** | **Mostly** — re-creates `.husky/` and updates `package.json` |
| **Output** | Minimal feedback |

**Key insight:** Husky init is a good parallel for openstation —
it creates a hidden directory with hook scripts and modifies an
existing config file (`package.json`), similar to how
`openstation init` needs to create `.openstation/` and modify
`CLAUDE.md` + `.claude/settings.json`.

---

## 2. Common Patterns

### 2.1 Install vs Init Separation

Every mature tool separates these concerns:

| Phase | Responsibility | Who runs it |
|-------|---------------|-------------|
| **Install** | Put the binary/CLI on PATH | Once per machine (user or admin) |
| **Init** | Set up a project directory for use with the tool | Once per project (developer) |

This is universal across git, npm, cargo, terraform, poetry,
go, and husky. The install mechanism varies (package manager,
curl script, installer), but `init` is always a subcommand of
the tool itself.

### 2.2 Idempotency Spectrum

| Behavior | Tools | Approach |
|----------|-------|----------|
| **Fully idempotent** | git, terraform, npm | Safe to re-run; skip/merge existing state |
| **Refuse on conflict** | cargo, poetry, go | Error if manifest already exists |
| **Overwrite silently** | eslint | Regenerates config without checking |

The most user-friendly tools are **fully idempotent** with
clear messaging about what changed vs what was skipped.

### 2.3 Interactive vs Non-Interactive

| Mode | Tools | Flag |
|------|-------|------|
| **Interactive by default** | npm, poetry, eslint | Ask questions |
| **Non-interactive flag** | npm (`-y`), poetry (`--no-interaction`) | Skip prompts, use defaults |
| **Non-interactive only** | git, terraform, go, cargo | No prompts, deterministic |

Tools with simple initialization (few decisions) skip
interactivity entirely. Tools that need user input offer
both modes.

### 2.4 File Ownership Model

Several tools distinguish between files they own and files
the user owns:

| Category | Behavior on re-init | Examples |
|----------|-------------------|----------|
| **Tool-owned** | Overwrite/refresh | git templates, terraform providers, npm scripts |
| **User-owned** | Skip/merge, never overwrite | git config, npm package.json fields, cargo source files |

This pattern is directly relevant to openstation's split
between AS-owned files (commands, skills, docs, hooks) and
user-owned files (agent specs, tasks, CLAUDE.md user content).

### 2.5 Output Conventions

| Pattern | Examples |
|---------|----------|
| **Per-action status lines** | terraform (`Downloading...`, `Installing...`) |
| **Checkmark/skip indicators** | Many tools use ✓ for created, ⊘ for skipped |
| **Summary with next steps** | npm, git, terraform print "what to do next" |
| **Distinguish first-init from re-init** | git prints different messages |

---

## 3. Anti-Patterns

### 3.1 Monolithic Install Scripts

Combining tool installation + project setup in a single script
(what openstation's `install.sh` does today). Problems:
- Can't re-init without re-installing
- Can't install without init
- Hard to version independently

### 3.2 Non-Idempotent Init

Tools that refuse to run twice (cargo, poetry, go) create
friction for:
- CI/CD pipelines that always run init
- Updating tool-owned files after upgrades
- Recovery from partial initialization

### 3.3 Silent Overwrites

Overwriting user files without warning (eslint). Loses
customizations and erodes trust.

### 3.4 Missing Positional Context

Requiring arguments that could be inferred. Go's requirement
for `<module-path>` is justified (no convention to guess it),
but tools like `git init` wisely default to the current
directory.

### 3.5 No Dry-Run Mode

None of the surveyed tools offer `--dry-run` for init. This
is a missed opportunity — especially for tools that modify
existing files (CLAUDE.md, settings.json).

---

## 4. UX Recommendation for `openstation init`

### 4.1 Command Signature

```
openstation init [--local <path>] [--no-agents] [--dry-run] [--force]
```

| Flag | Purpose |
|------|---------|
| `--local <path>` | Copy from local clone instead of downloading (carried over from install.sh) |
| `--no-agents` | Skip installing example agent specs (carried over from install.sh) |
| `--dry-run` | Show what would be created/modified without writing (novel — addresses anti-pattern 3.5) |
| `--force` | Overwrite user-owned files too (for reset scenarios) |

No positional argument needed — always operates on the current
directory (like `git init`, `terraform init`, `npm init`).

### 4.2 Non-Interactive

`openstation init` should be **fully non-interactive** (like
git, terraform). Reasons:
- All decisions are already made by convention (directory
  structure, file locations, owned files)
- There's nothing meaningful to ask the user
- Scriptable by default — no `-y` flag needed

### 4.3 Idempotent by Default

Follow the git/terraform model — fully idempotent:

| File category | First run | Re-run |
|---------------|-----------|--------|
| **Directories** | Create | Skip (already exist) |
| **AS-owned files** (commands, skills, docs, hooks, launcher) | Create | Overwrite (update to latest) |
| **User-owned files** (agent specs) | Create | Skip (preserve customizations) |
| **CLAUDE.md** | Create or append managed section | Replace managed section only (between markers) |
| **`.claude/settings.json`** | Create with hooks | Merge hooks (deduplicate) |
| **Symlinks** | Create | Re-create (ensure correct target) |

This is exactly what install.sh already does — the behavior
just moves into `openstation init`.

### 4.4 Output Format

Follow the existing install.sh conventions (they're good):

```
Open Station

Creating directories...
  ✓ .openstation/docs/
  ✓ .openstation/artifacts/tasks/
  ⊘ .openstation/artifacts/agents/ (exists, skipped)

Installing commands...
  ✓ .openstation/commands/openstation.create.md
  ✓ .openstation/commands/openstation.list.md

Installing skills...
  ✓ .openstation/skills/openstation-execute/SKILL.md

Installing docs...
  ✓ .openstation/docs/lifecycle.md

Installing hooks...
  ✓ .openstation/hooks/validate-write-path.sh

Installing example agents...
  ⊘ .openstation/artifacts/agents/researcher.md (exists, skipped)
  ✓ .openstation/agents/researcher.md → ../artifacts/agents/researcher.md

Creating symlinks...
  ✓ .claude/commands → ../.openstation/commands
  ✓ .claude/agents → ../.openstation/agents

Configuring hooks in .claude/settings.json...
  ✓ Merged hook config into .claude/settings.json

Updating CLAUDE.md...
  ✓ Updated Open Station section in CLAUDE.md

Open Station initialized successfully!

Next steps:
  1. Review CLAUDE.md and .openstation/docs/lifecycle.md
  2. Customize agent specs in .openstation/agents/
  3. Create your first task: /openstation.create <description>
  4. Run an agent: claude --agent <name>
```

Add a distinguishing message for re-init (like git):
- First run: `Open Station initialized successfully!`
- Re-run: `Open Station re-initialized (N files updated).`

### 4.5 Dry-Run Mode

With `--dry-run`, print the same output but prefix actions with
`[would]` and write nothing:

```
  [would] ✓ .openstation/docs/
  [would] ⊘ .openstation/artifacts/agents/ (exists, would skip)
```

### 4.6 Implementation Notes

1. **Move scaffold logic from install.sh into `openstation init`
   subcommand** — the Python CLI already has a subcommand
   structure.
2. **install.sh becomes a thin wrapper:** download/copy the
   `openstation` binary onto PATH, then run `openstation init`.
3. **Source guard:** `openstation init` should detect and refuse
   to run inside the openstation source repo (carry over the
   existing guard from install.sh).
4. **The `--local` flag** lets `openstation init` work offline
   or during development — files are copied from a local clone
   instead of downloaded.

### 4.7 Comparison with Current State

| Aspect | Current (`install.sh`) | Proposed (`openstation init`) |
|--------|----------------------|-------------------------------|
| Invocation | `curl ... \| bash` or `./install.sh` | `openstation init` |
| Prerequisites | curl (for remote), bash | openstation CLI on PATH |
| Idempotent | Yes | Yes (same behavior) |
| Interactive | No | No |
| Scaffold logic | In bash script | In Python CLI |
| Binary install | Mixed into scaffold | Separate (install.sh only) |
| Dry-run | No | Yes (`--dry-run`) |
| Force overwrite | No | Yes (`--force`) |

---

## 5. Summary

The install/init split is a universal pattern across mature
CLI tools. The key design decisions for `openstation init`:

1. **Non-interactive** — no prompts, deterministic output
2. **Idempotent** — safe to re-run, with file-ownership-aware
   skip/overwrite logic (already implemented in install.sh)
3. **Clear output** — per-file status with ✓/⊘ indicators and
   a summary with next steps
4. **Dry-run support** — differentiation from the surveyed tools
5. **Separation of concerns** — install.sh gets the binary,
   `openstation init` sets up the project

The existing install.sh already follows best practices for the
init behavior — the refactor is primarily structural (moving
logic into the CLI) rather than behavioral.
