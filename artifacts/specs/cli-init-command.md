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
openstation init [--local <path>] [--no-agents] [--dry-run] [--force]
```

| Flag | Type | Default | Description |
|------|------|---------|-------------|
| `--local <path>` | string | (none) | Copy files from a local Open Station clone instead of downloading from GitHub. Path must exist and contain `docs/lifecycle.md` (validation carried over from install.sh). |
| `--no-agents` | flag | false | Skip installing example agent specs (`researcher.md`, `author.md`). |
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
    ".openstation/hooks",
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

HOOKS = [
    "hooks/validate-write-path.sh",
    "hooks/block-destructive-git.sh",
]

LAUNCHER = "openstation-run.sh"
```

**Source paths** in the source repo (used with `--local`):

| Manifest entry | Source repo path |
|----------------|-----------------|
| `commands/openstation.create.md` | `commands/openstation.create.md` |
| `skills/openstation-execute/SKILL.md` | `skills/openstation-execute/SKILL.md` |
| `docs/lifecycle.md` | `docs/lifecycle.md` |
| `hooks/validate-write-path.sh` | `hooks/validate-write-path.sh` |
| `openstation-run.sh` | `openstation-run.sh` |

**Destination paths** in the target project:

| Manifest entry | Destination |
|----------------|------------|
| `commands/openstation.create.md` | `.openstation/commands/openstation.create.md` |
| `skills/openstation-execute/SKILL.md` | `.openstation/skills/openstation-execute/SKILL.md` |
| `docs/lifecycle.md` | `.openstation/docs/lifecycle.md` |
| `hooks/validate-write-path.sh` | `.openstation/hooks/validate-write-path.sh` |
| `openstation-run.sh` | `.openstation/openstation-run.sh` |

### 2c. User-Owned Files

Skipped if they already exist (unless `--force`):

```python
AGENTS = [
    "artifacts/agents/researcher.md",
    "artifacts/agents/author.md",
]
```

Source: `artifacts/agents/researcher.md` in the source repo.
Destination: `.openstation/artifacts/agents/researcher.md`.

### 2d. Managed Files

Files where Open Station owns a section but the user owns the rest:

| File | Strategy |
|------|----------|
| `CLAUDE.md` | Marker-based section replacement (§ 5a) |
| `.claude/settings.json` | JSON key merge (§ 5b) |

---

## 3. File Ownership Model

Every file touched by `openstation init` falls into one of three
categories:

| Category | First run | Re-run (no --force) | Re-run (--force) |
|----------|-----------|---------------------|------------------|
| **AS-owned** | Create | Overwrite | Overwrite |
| **User-owned** | Create | Skip (preserve) | Overwrite |
| **Managed** | Create/inject | Update managed portion only | Overwrite entire file |

### Classification

| Category | Files |
|----------|-------|
| **AS-owned** | commands/\*, skills/\*, docs/\*, hooks/\*, openstation-run.sh, .claude/ symlinks |
| **User-owned** | artifacts/agents/\*.md (example agent specs) |
| **Managed** | CLAUDE.md, .claude/settings.json |

### Rationale

- **AS-owned** files are distributed by Open Station and should
  always match the installed version. Users should not edit these.
  Overwriting on re-init ensures updates propagate after upgrades.
- **User-owned** files are seeded as examples but belong to the
  user. Overwriting would destroy customizations.
- **Managed** files are shared — Open Station maintains a specific
  section/key while preserving user content elsewhere.

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

For each file in COMMANDS, SKILLS, DOCS, HOOKS, and LAUNCHER:

1. Fetch from source (local copy or HTTP download).
2. Write to destination, overwriting any existing file.
3. For hook scripts and launcher: `chmod +x`.

Output: `✓ .openstation/commands/openstation.create.md`

### Step 5: Install Example Agents

Skip entirely if `--no-agents` is set.

For each file in AGENTS:

1. Check if destination exists.
2. If exists and no `--force`: skip. Output: `⊘ .openstation/artifacts/agents/researcher.md (exists, skipped)`
3. If not exists or `--force`: fetch and write.

After writing/skipping each agent spec, create its discovery
symlink in `.openstation/agents/`:

```python
# Always recreate symlinks (they're AS-owned)
link = ".openstation/agents/researcher.md"
target = "../artifacts/agents/researcher.md"
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

### Step 7: Configure .claude/settings.json (Managed)

Merge Open Station hook entries into `.claude/settings.json`.

**Hook entries to ensure:**

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": { "tools": ["Write", "Edit"] },
        "hooks": [{ "type": "command", "command": "bash .openstation/hooks/validate-write-path.sh" }]
      },
      {
        "matcher": { "tools": ["Bash"] },
        "hooks": [{ "type": "command", "command": "bash .openstation/hooks/block-destructive-git.sh" }]
      }
    ]
  }
}
```

**Merge strategy:**

1. If file doesn't exist: create it with the hook entries.
2. If file exists: parse JSON, ensure `hooks.PreToolUse`
   contains our entries (deduplicate by `hooks[0].command`
   value), write back.
3. Use Python `json` module (stdlib). No jq dependency.

The current install.sh has a jq path and a fallback path. The
Python implementation uses `json.loads` / `json.dumps` and needs
no external tool.

Output: `✓ Merged hook config into .claude/settings.json`

### Step 8: Update CLAUDE.md (Managed)

Inject or replace the managed section in `CLAUDE.md`.

**Markers:**

```
<!-- openstation:start -->
...managed content...
<!-- openstation:end -->
```

**Strategy:**

1. If `CLAUDE.md` doesn't exist: create it with the managed
   section only.
2. If `CLAUDE.md` exists and contains markers: replace content
   between markers (inclusive) with the new managed section.
3. If `CLAUDE.md` exists but has no markers: append the managed
   section (preceded by a blank line).

The managed section content is a string constant in the CLI.
It matches the current content in `install.sh`.

When `--force` is set: overwrite the entire CLAUDE.md with just
the managed section (losing any user content). This is the
nuclear option for full reset.

Output:
- Created: `✓ Created CLAUDE.md with Open Station section`
- Updated: `✓ Updated Open Station section in CLAUDE.md`
- Appended: `✓ Appended Open Station section to CLAUDE.md`

### Step 9: Summary

Print a final summary with next steps.

**First init:**

```
Open Station initialized successfully!

Next steps:
  1. Review CLAUDE.md and .openstation/docs/lifecycle.md
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

### 5a. CLAUDE.md Marker-Based Section

The managed section lives between markers:

```
<!-- openstation:start -->
...
<!-- openstation:end -->
```

On re-init, only content between these markers (inclusive) is
replaced. Everything before and after is preserved.

**Edge case:** If a user deletes the markers but keeps some
content, the section is appended again (resulting in a
duplicate). This is acceptable — the markers are the contract.

### 5b. settings.json Merge

Hook entries are deduplicated by the `command` string in
`hooks[0].command`. If an entry with the same command already
exists in `PreToolUse`, it is replaced with the new version
(to pick up any structural changes). Other entries in
`PreToolUse` or other keys in `settings.json` are preserved.

### 5c. Symlinks

Always removed and recreated (ensuring correct target after
moves/upgrades).

### 5d. Directories

Created with `exist_ok=True`. No-op if they already exist.

### 5e. .gitkeep Files

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
- File downloads for commands/skills/docs/hooks (→ init)
- Symlink creation (→ init)
- CLAUDE.md injection (→ init)
- settings.json merge (→ init)
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
| `.claude/settings.json` is malformed JSON | Warning: "Cannot parse .claude/settings.json — creating backup and overwriting." Rename to `.claude/settings.json.bak`, write fresh. | — |

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

### 10b. CLAUDE.md Managed Section

The managed section content should be a module-level string
constant (e.g., `CLAUDEMD_SECTION`). This keeps it readable
and easy to update. It must match the content currently in
install.sh's heredoc.

### 10c. settings.json Merge

Use `json.loads()` / `json.dumps(indent=2)` for reading and
writing. The merge algorithm:

```python
def merge_settings(existing_json: dict) -> dict:
    hooks = existing_json.setdefault("hooks", {})
    pre_tool_use = hooks.setdefault("PreToolUse", [])

    # Our hook entries
    our_hooks = [HOOK_WRITE_EDIT, HOOK_BASH]

    # Remove existing entries with our commands
    our_commands = {h["hooks"][0]["command"] for h in our_hooks}
    pre_tool_use[:] = [
        entry for entry in pre_tool_use
        if entry.get("hooks", [{}])[0].get("command") not in our_commands
    ]

    # Append ours
    pre_tool_use.extend(our_hooks)
    return existing_json
```

### 10d. Fetch Helper

Single function for both modes:

```python
def fetch_file(src_relative: str, dst: str, local_path: str | None) -> None:
    if local_path:
        shutil.copy2(os.path.join(local_path, src_relative), dst)
    else:
        url = f"{BASE_URL}/{src_relative}"
        urllib.request.urlretrieve(url, dst)
```

### 10e. Dry-Run Implementation

Wrap all side-effecting operations in a dry-run check. The
simplest approach: pass a `dry_run: bool` parameter through
all helper functions. When true, print what would happen but
skip the actual `os.makedirs`, `shutil.copy2`, `os.symlink`,
and file writes.

### 10f. Counters for Summary

Track counts during execution:

```python
@dataclass
class InitStats:
    created: int = 0
    updated: int = 0
    skipped: int = 0
```

Increment as actions are performed. Use for the summary message.

### 10g. argparse Registration

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

### 10h. Root Detection Override

The `init` command should NOT call `find_root()` to locate an
existing project. It always operates on the current working
directory. This differs from other subcommands which walk up to
find the project root.

The source repo guard uses its own check (§ 4, Step 1) rather
than `find_root()`.

### 10i. Testing Strategy

Add a `TestInitCommand` class to `tests/test_cli.py` following
the existing test patterns. Key test cases:

1. **First init** — creates full directory structure and files
2. **Re-init** — AS-owned files overwritten, user-owned skipped
3. **Re-init with --force** — user-owned files overwritten
4. **--no-agents** — agent specs not installed
5. **--dry-run** — no files created, output shows `[would]`
6. **Source repo guard** — errors when run in source repo
7. **--local validation** — errors on bad path
8. **CLAUDE.md first create** — managed section only
9. **CLAUDE.md append** — existing file, no markers
10. **CLAUDE.md replace** — existing file, markers present
11. **settings.json merge** — existing settings preserved
12. **settings.json create** — new file from scratch
13. **Symlink re-creation** — stale symlinks corrected
14. **Not a git repo** — warning but succeeds

Use `tempfile.mkdtemp()` for isolated test directories, matching
the existing pattern in `test_cli.py`.

---

## 11. Open Questions

**Decided:**

- Non-interactive, fully idempotent (follows git/terraform model)
- File ownership model (AS-owned / user-owned / managed)
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
