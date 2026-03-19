---
kind: spec
name: cli-init-command
agent: architect
task: "[[0057-spec-for-openstation-init-command]]"
created: 2026-03-06
---

# Spec: `openstation init` Command

Technical specification for the `openstation init` CLI subcommand,
which scaffolds an Open Station vault into a target project.

Informed by research in
`artifacts/research/install-vs-init-patterns.md`.

---

## 1. Command Signature

```
openstation init [--local <path>] [--agents <name,...>] [--no-agents] [--dry-run] [--force]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--local <path>` | string | (none) | Copy files from a local Open Station clone instead of downloading from GitHub. Path must exist and contain `docs/lifecycle.md` (validation carried over from install.sh). |
| `--agents <name,...>` | string | (all) | Comma-separated list of agent names to install from `templates/agents/`. E.g., `--agents researcher,author`. If omitted, all templates are installed. Mutually exclusive with `--no-agents`. |
| `--no-agents` | flag | false | Skip installing agent specs entirely. Mutually exclusive with `--agents`. |
| `--dry-run` | flag | false | Print what would be created/modified without writing anything. Prefix each action line with `[would]`. |
| `--force` | flag | false | Overwrite user-owned files too (for reset/repair scenarios). Without this flag, user-owned files are skipped if they exist. |

No positional arguments. Always operates on the current working
directory (like `git init`, `terraform init`).

**Non-interactive.** No prompts, fully deterministic output.
Suitable for scripting and CI.

---

## 2. File Manifest

The init command operates on a fixed manifest of files. These are
the same files currently deployed by `install.sh`.

### 2a. Directories

All created under `.openstation/` in the target project:

```python
DIRS = [
    ".openstation/docs",
    ".openstation/artifacts/tasks",
    ".openstation/artifacts/agents",
    ".openstation/artifacts/research",
    ".openstation/artifacts/specs",
    ".openstation/agents",
    ".openstation/skills",
    ".openstation/commands",
    ".claude",
]
```

Directories that hold user content get `.gitkeep` files:

```python
GITKEEP_DIRS = [
    ".openstation/artifacts/tasks",
    ".openstation/artifacts/agents",
    ".openstation/artifacts/research",
    ".openstation/artifacts/specs",
    ".openstation/agents",
    ".openstation/skills",
    ".openstation/commands",
]
```

### 2b. AS-Owned Files

Always overwritten on re-init (tool-managed, no user edits
expected):

```python
COMMANDS = [
    "commands/openstation.create.md",
    "commands/openstation.dispatch.md",
    "commands/openstation.done.md",
    "commands/openstation.list.md",
    "commands/openstation.ready.md",
    "commands/openstation.reject.md",
    "commands/openstation.show.md",
    "commands/openstation.update.md",
]

SKILLS = [
    "skills/openstation-execute/SKILL.md",
]

DOCS = [
    "docs/lifecycle.md",
    "docs/task.spec.md",
]
```

**Source paths** in the source repo (used with `--local`):

| Manifest entry | Source repo path |
|----------------|-----------------|
| `commands/openstation.create.md` | `commands/openstation.create.md` |
| `skills/openstation-execute/SKILL.md` | `skills/openstation-execute/SKILL.md` |
| `docs/lifecycle.md` | `docs/lifecycle.md` |

**Destination paths** in the target project:

| Manifest entry | Destination |
|----------------|------------|
| `commands/openstation.create.md` | `.openstation/commands/openstation.create.md` |
| `skills/openstation-execute/SKILL.md` | `.openstation/skills/openstation-execute/SKILL.md` |
| `docs/lifecycle.md` | `.openstation/docs/lifecycle.md` |

### 2c. User-Owned Files

Skipped if they already exist (unless `--force`):

```python
# Discover all templates dynamically
AGENT_TEMPLATES = glob("templates/agents/*.md")
```

Source: `templates/agents/<name>.md` in the source repo.
Destination: `.openstation/artifacts/agents/<name>.md`.

During copy, apply simple pattern matching to adapt templates
to the project:

- Extract project name from `CLAUDE.md` (first H1 heading,
  fallback to directory name)
- Replace `"the project"` → `"<project-name>"` in description
  and body
- Strip template comment markers (`# --- Role-based ---`,
  `# --- Task-system ---`) from `allowed-tools`

---

## 3. File Ownership Model

Every file touched by `openstation init` falls into one of two
categories:

| Category | First run | Re-run (no --force) | Re-run (--force) |
|----------|-----------|---------------------|------------------|
| **AS-owned** | Create | Overwrite | Overwrite |
| **User-owned** | Create | Skip (preserve) | Overwrite |

### Classification

| Category | Files |
|----------|-------|
| **AS-owned** | commands/\*, skills/\*, docs/\*, .claude/ symlinks |
| **User-owned** | artifacts/agents/\*.md (example agent specs) |

### Rationale

- **AS-owned** files are distributed by Open Station and should
  always match the installed version. Users should not edit these.
  Overwriting on re-init ensures updates propagate after upgrades.
- **User-owned** files are seeded as examples but belong to the
  user. Overwriting would destroy customizations.

---

## 4. Operations (Execution Order)

The init command performs these steps in order. Each step is
a discrete operation with its own output section.

### Step 1: Source Repo Guard

```python
if is_source_repo(cwd):
    err("Cannot init inside the Open Station source repo.")
    sys.exit(EXIT_SOURCE_GUARD)
```

Detection: directory contains both `agents/` and `install.sh`
at the project root (same heuristic as current install.sh and
`find_root()`).

### Step 2: Validate Prerequisites

| Check | Behavior |
|-------|----------|
| `--local <path>` provided | Path must exist, must be a directory, must contain `docs/lifecycle.md`. Error if not. |
| `--local` not provided | `urllib.request` is used (stdlib, no curl dependency). No extra check needed. |
| Git repo check | Warn if not in a git repo, but proceed. (Same as current install.sh.) |

### Step 3: Create Directories

Create each directory in the DIRS list. Use `os.makedirs(exist_ok=True)`.
Place `.gitkeep` in GITKEEP_DIRS directories.

Output per directory:
- Created: `✓ .openstation/docs/`
- Exists: (silent — directories are never reported as skipped)

### Step 4: Install AS-Owned Files

For each file in COMMANDS, SKILLS, and DOCS:

1. Fetch from source (local copy or HTTP download).
2. Write to destination, overwriting any existing file.

Output: `✓ .openstation/commands/openstation.create.md`

### Step 5: Install Agent Templates

Skip entirely if `--no-agents` is set.

For each file in AGENT_TEMPLATES (discovered via glob):

1. Check if destination exists.
2. If exists and no `--force`: skip. Output: `⊘ .openstation/artifacts/agents/researcher.md (exists, skipped)`
3. If not exists or `--force`: fetch template, apply pattern
   matching (project name substitution, strip comment markers),
   write to destination.

After writing/skipping each agent spec, create its discovery
symlink in `.openstation/agents/`:

```python
# Always recreate symlinks (they're AS-owned)
link = f".openstation/agents/{name}.md"
target = f"../artifacts/agents/{name}.md"
# Remove existing (symlink or file), then create
os.symlink(target, link)
```

Output: `✓ .openstation/agents/researcher.md → ../artifacts/agents/researcher.md`

### Step 6: Create .claude/ Symlinks

Three directory symlinks connect `.claude/` to `.openstation/`:

| Link | Target |
|------|--------|
| `.claude/commands` | `../.openstation/commands` |
| `.claude/agents` | `../.openstation/agents` |
| `.claude/skills` | `../.openstation/skills` |

**Symlink strategy** (same as current install.sh):

For each link:
1. If link is a symlink: remove and recreate.
2. If link is a non-empty directory (user has their own
   commands/skills): merge by creating per-file symlinks
   instead of a directory symlink. Warn the user.
3. If link is an empty directory: remove and create directory
   symlink.
4. If link doesn't exist: create directory symlink.

Output:
- Directory symlink: `✓ .claude/commands → ../.openstation/commands`
- Per-file merge: `! .claude/commands/ exists with files — merging`
  followed by per-file `✓ .claude/commands/openstation.create.md → ...`

### Step 7: Summary

Print a final summary with next steps.

**First init:**

```
Open Station initialized successfully!

Next steps:
  1. Review .openstation/docs/lifecycle.md
  2. Customize agent specs in .openstation/agents/
  3. Create your first task: /openstation.create <description>
  4. Run an agent: claude --agent <name>
```

**Re-init:**

```
Open Station re-initialized (12 files updated, 2 skipped).
```

Detection: if `.openstation/` existed before init ran, it's a
re-init.

---

## 5. Idempotency Rules

### 5a. Symlinks

Always removed and recreated (ensuring correct target after
moves/upgrades).

### 5b. Directories

Created with `exist_ok=True`. No-op if they already exist.

### 5c. .gitkeep Files

Created only if missing. Never removed.

---

## 6. install.sh Boundary

After the refactor, responsibilities split cleanly:

### install.sh (Thin Wrapper)

**Sole responsibility:** Get the `openstation` CLI binary onto
`$PATH`.

```bash
#!/usr/bin/env bash
set -euo pipefail

# Download or copy the openstation CLI binary
# Then run: openstation init [forwarded flags]
```

**Operations:**

1. Determine installation method:
   - `--local <path>`: copy `bin/openstation` from local clone.
   - Default: download `bin/openstation` from GitHub raw URL.
2. Place binary at a known location (e.g., `~/.local/bin/openstation`
   or a project-local `.openstation/bin/openstation`).
3. Ensure the location is on `$PATH` (or warn if not).
4. Forward remaining flags to `openstation init`:
   ```bash
   openstation init "$@"
   ```

**What install.sh no longer does:**

- Directory creation (→ init)
- File downloads for commands/skills/docs (→ init)
- Symlink creation (→ init)
- Agent spec deployment (→ init)
- Source repo guard (→ init, but install.sh may keep its own
  guard for the binary copy step)

### openstation init (Full Scaffold)

**All scaffold logic.** Everything currently in install.sh
except the binary installation.

### Migration Path

1. Implement `openstation init` as a new subcommand in
   `bin/openstation`.
2. Test `openstation init` independently.
3. Refactor `install.sh` to install the binary and call
   `openstation init`.
4. Verify end-to-end: `curl ... | bash` still works, now going
   through the two-phase path.

---

## 7. Error Handling

| Condition | Behavior | Exit Code |
|-----------|----------|-----------|
| Running inside source repo | Error: "Cannot init inside the Open Station source repo." | 2 |
| `--local` path doesn't exist | Error: "Local path does not exist: <path>" | 1 |
| `--local` path invalid (no `docs/lifecycle.md`) | Error: "Local path does not look like an Open Station repo: <path>" | 1 |
| Not in a git repo | Warning (stderr): "Not inside a git repository. Proceeding anyway." Continue. | — |
| Network error during download | Error: "Failed to download <file>: <reason>" | 1 |
| File write permission denied | Error: "Cannot write to <path>: Permission denied" | 1 |

### Exit Codes

```python
EXIT_OK = 0
EXIT_USAGE = 1            # Bad arguments, download failure, permission error
EXIT_SOURCE_GUARD = 2     # Attempted init inside source repo
```

---

## 8. Output Format

### Standard Output

All output goes to stdout. Errors and warnings go to stderr.

**Section headers:** Plain text, no prefix.
**Status lines:** Indented, with indicator prefix.

| Indicator | Meaning |
|-----------|---------|
| `✓` (green) | Created or updated |
| `⊘` (yellow) | Skipped (exists, user-owned) |
| `!` (yellow) | Warning (non-fatal issue) |
| `✗` (red) | Error (fatal, to stderr) |

### Dry-Run Mode

With `--dry-run`, every action line is prefixed with `[would]`
and nothing is written to disk:

```
  [would] ✓ .openstation/docs/
  [would] ⊘ .openstation/artifacts/agents/researcher.md (exists, would skip)
  [would] ✓ .claude/commands → ../.openstation/commands
```

### First Init vs Re-Init

Detection: check if `.openstation/` exists before the first
`mkdir`.

- First: Banner says "Open Station" and summary says
  "initialized successfully!"
- Re-init: Summary says "re-initialized (N files updated,
  M skipped)."

---

## 9. File Sourcing

### 9a. Local Mode (`--local <path>`)

Files are copied from the local clone using `shutil.copy2`.
The source path is constructed as `<local_path>/<manifest_entry>`.

Example: `--local /home/user/openstation` →
`/home/user/openstation/commands/openstation.create.md` →
`.openstation/commands/openstation.create.md`

### 9b. Remote Mode (default)

Files are downloaded from GitHub using `urllib.request.urlopen`.
The URL pattern matches the current install.sh:

```python
BASE_URL = f"https://raw.githubusercontent.com/{REPO_OWNER}/{REPO_NAME}/{BRANCH}"
url = f"{BASE_URL}/{manifest_entry}"
```

Constants:

```python
REPO_OWNER = "leonprou"
REPO_NAME = "openstation"
BRANCH = "main"
```

No curl dependency — Python's stdlib `urllib.request` replaces
the bash `curl -fsSL` calls.

---

## 10. Implementation Notes

### 10a. Location in Codebase

Add `cmd_init()` function and `init` subparser to
`bin/openstation`. The existing subcommand pattern
(`cmd_list`, `cmd_show`, `cmd_create`, etc.) is followed.

### 10b. Fetch Helper

Single function for both modes:

```python
def fetch_file(src_relative: str, dst: str, local_path: str | None) -> None:
    if local_path:
        shutil.copy2(os.path.join(local_path, src_relative), dst)
    else:
        url = f"{BASE_URL}/{src_relative}"
        urllib.request.urlretrieve(url, dst)
```

### 10c. Dry-Run Implementation

Wrap all side-effecting operations in a dry-run check. The
simplest approach: pass a `dry_run: bool` parameter through
all helper functions. When true, print what would happen but
skip the actual `os.makedirs`, `shutil.copy2`, `os.symlink`,
and file writes.

### 10d. Counters for Summary

Track counts during execution:

```python
@dataclass
class InitStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
```

Increment as actions are performed. Use for the summary message.

### 10e. argparse Registration

```python
init_p = sub.add_parser("init", help="Initialize Open Station in current directory")
init_p.add_argument("--local", default=None, metavar="PATH",
                     help="Copy files from a local Open Station clone")
init_p.add_argument("--no-agents", action="store_true",
                     help="Skip installing example agent specs")
init_p.add_argument("--dry-run", action="store_true",
                     help="Show what would be done without writing")
init_p.add_argument("--force", action="store_true",
                     help="Overwrite user-owned files too")
```

### 10f. Root Detection Override

The `init` command should NOT call `find_root()` to locate an
existing project. It always operates on the current working
directory. This differs from other subcommands which walk up to
find the project root.

The source repo guard uses its own check (§ 4, Step 1) rather
than `find_root()`.

### 10g. Testing Strategy

Add a `TestInitCommand` class to `tests/test_cli.py` following
the existing test patterns. Key test cases:

1. **First init** — creates full directory structure and files
2. **Re-init** — AS-owned files overwritten, user-owned skipped
3. **Re-init with --force** — user-owned files overwritten
4. **--no-agents** — agent specs not installed
5. **--dry-run** — no files created, output shows `[would]`
6. **Source repo guard** — errors when run in source repo
7. **--local validation** — errors on bad path
8. **Symlink re-creation** — stale symlinks corrected
9. **Not a git repo** — warning but succeeds

Use `tempfile.mkdtemp()` for isolated test directories, matching
the existing pattern in `test_cli.py`.

---

## 11. Open Questions

**Decided:**

- Non-interactive, fully idempotent (follows git/terraform model)
- File ownership model (AS-owned / user-owned)
- `urllib.request` for downloads (stdlib, no curl)
- Single-file CLI (`bin/openstation`)
- Same flags as install.sh plus `--dry-run` and `--force`

**Recommended (needs validation during implementation):**

- Binary installation location: `~/.local/bin/openstation` is a
  reasonable default for install.sh, but the exact location
  depends on how the binary is distributed. May need a
  `--prefix` flag on install.sh. Not in scope for this spec —
  only the `init` subcommand is spec'd here.

- Future: when proper Python packaging is adopted (pyproject.toml,
  pip install), the AS-owned files could be bundled as package
  data via `importlib.resources`. This would eliminate the
  download step entirely for installed packages. Not needed now.
