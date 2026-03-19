---
kind: spec
name: openstation-only-convention
agent: architect
task: "[[0172-spec-openstation-only-convention]]"
---

# Spec: .openstation-Only Convention

Drop the dual-path convention. All vault files live under
`.openstation/` — one convention, everywhere, including the
source repo.

## Decision Summary

| Decision | Status |
|----------|--------|
| Source repo moves vault dirs under `.openstation/` | **Decided** |
| `find_root` returns `Path` (no prefix tuple) | **Decided** |
| `vault_path()` replaces all `if prefix:` branching | **Decided** |
| Source-repo detection removed entirely | **Decided** |
| `EXIT_SOURCE_GUARD` and init source-guard removed | **Decided** |
| Backward compatibility for installed projects | **Decided** — seamless, no changes needed |

---

## 1. Source Repo Migration Strategy

### What Moves Under `.openstation/`

```
# Before (root-level)              # After (.openstation/)
artifacts/                    →    .openstation/artifacts/
agents/                       →    .openstation/agents/
skills/                       →    .openstation/skills/
commands/                     →    .openstation/commands/
docs/                         →    .openstation/docs/
templates/                    →    .openstation/templates/
settings.json                 →    .openstation/settings.json
```

### What Stays at Root

```
src/                          # Python source code
tests/                        # Test suite
bin/                          # CLI entry point
Makefile                      # Build tooling
pyproject.toml                # Package metadata
install.sh                    # Installer script (no longer a marker)
README.md                     # Project readme
CHANGELOG.md                  # Release changelog
CLAUDE.md                     # Agent instructions
.claude/                      # Claude Code config (symlinks)
hooks/                        # Git hooks (stays — not vault data)
dist/                         # Build artifacts
```

### Source-Guard Removal

The current `_check_dir` detects `agents/ + install.sh` as a
source-repo marker. After migration:

- `agents/` moves to `.openstation/agents/` → the old marker
  pattern no longer exists
- `install.sh` stays at root but is no longer checked
- The `init.py` source-guard check
  (`(cwd / "agents").is_dir() and (cwd / "install.sh").is_file()`)
  is removed — it's no longer meaningful
- `EXIT_SOURCE_GUARD` (exit code 9) is removed from `core.py`

### New Source-Repo Detection

**Removed entirely.** There is no separate source-repo detection.
The source repo is detected the same way as any installed project:
by the presence of `.openstation/`. This is the whole point of
the unification.

---

## 2. New `find_root` Contract

### Current Signature

```python
def find_root(start=None) -> tuple[Path | None, str | None]:
    """Returns (root, prefix) where prefix is '' or '.openstation'."""
```

### New Signature

```python
def find_root(start=None) -> Path | None:
    """Return the project root containing .openstation/, or None.

    Two-step approach (unchanged):
    1. git toplevel — if it has .openstation/, return it (independent vault)
    2. main worktree root — if it has .openstation/, return it (slave mode)
    3. Otherwise return None

    Non-git directories are not supported and return None.
    """
```

### Changes

- Return type: `Path | None` — no more tuple
- Only one marker: `.openstation/` directory
- `_check_dir` simplified to a single check:
  ```python
  def _check_dir(d: Path) -> bool:
      return (d / ".openstation").is_dir()
  ```
- Callers unpack `root = find_root()` instead of
  `root, prefix = find_root()`
- `root is None` check replaces `root is None` (unchanged semantics)

### Worktree Behavior (No Regression)

The two-step resolution is preserved identically:

| Mode | Condition | Result |
|------|-----------|--------|
| **Independent** | Worktree's git toplevel has `.openstation/` | Returns worktree root |
| **Linked** | Worktree lacks `.openstation/`, main repo has it | Returns main repo root |
| **None** | Neither has `.openstation/` | Returns `None` |

The only change: the source-repo marker path (`agents/ + install.sh`)
is no longer checked. Since the source repo will have `.openstation/`,
it's detected via the standard path.

---

## 3. Path Construction

### New Canonical Helper

Add to `core.py`:

```python
def vault_path(root: Path, *parts: str) -> Path:
    """Build a path inside the vault: root / .openstation / parts.

    Examples:
        vault_path(root, "artifacts", "tasks")
        vault_path(root, "settings.json")
        vault_path(root, "agents", "researcher.md")
    """
    return root / ".openstation" / Path(*parts) if parts else root / ".openstation"
```

### Replacement of `tasks_dir_path`

```python
# Before
def tasks_dir_path(root, prefix):
    if prefix:
        return Path(root) / prefix / "artifacts" / "tasks"
    return Path(root) / "artifacts" / "tasks"

# After
def tasks_dir_path(root):
    return vault_path(root, "artifacts", "tasks")
```

### Every `if prefix:` Pattern Replaced

| Module | Current Pattern | New Pattern |
|--------|----------------|-------------|
| `core.py: tasks_dir_path` | `if prefix: root/prefix/artifacts/tasks` | `vault_path(root, "artifacts", "tasks")` |
| `tasks.py: discover_tasks` | `root/prefix/artifacts/tasks if prefix else root/artifacts/tasks` | `vault_path(root, "artifacts", "tasks")` |
| `tasks.py: resolve_task` | Same pattern | `vault_path(root, "artifacts", "tasks")` |
| `tasks.py: cmd_show` | Same pattern | `vault_path(root, "artifacts", "tasks")` |
| `run.py: discover_agents` | `if prefix: root/prefix/artifacts/agents` | `vault_path(root, "artifacts", "agents")` |
| `run.py: find_agent_spec` | `if prefix: root/prefix/agents/...` + fallback `root/agents/...` | `vault_path(root, "agents", f"{name}.md")` |
| `run.py: _find_agent_artifact` | `if prefix: root/prefix/artifacts/agents/...` | `vault_path(root, "artifacts", "agents", f"{name}.md")` |
| `run.py: run_single_task` | `root/prefix/artifacts/logs if prefix` | `vault_path(root, "artifacts", "logs")` |
| `run.py: _exec_or_run` | Same log_dir pattern | `vault_path(root, "artifacts", "logs")` |
| `run.py: cmd_run` (verify) | Same log_dir pattern | `vault_path(root, "artifacts", "logs")` |
| `artifacts.py: _artifacts_base` | `if prefix: root/prefix/artifacts` | `vault_path(root, "artifacts")` |
| `hooks.py: _settings_path` | `root/prefix/settings.json if prefix` | `vault_path(root, "settings.json")` |

### Prompt Path References

In `run.py`, the task path used in prompts changes:

```python
# Before
task_path = str(spec) if worktree else f"artifacts/tasks/{task_name}.md"

# After — always relative to .openstation/
task_path = str(spec) if worktree else f".openstation/artifacts/tasks/{task_name}.md"
```

---

## 4. Migration Checklist

Every file that changes, with what changes:

### Python Source (`src/openstation/`)

| File | Changes |
|------|---------|
| `core.py` | Remove `_check_dir` dual-marker logic → single `.openstation/` check. Change `find_root` return type from `(Path, str)` to `Path \| None`. Remove `prefix` param from `tasks_dir_path`. Add `vault_path()` helper. Remove `EXIT_SOURCE_GUARD`. |
| `cli.py` | Change `find_root()` unpacking from `root, prefix = ...` to `root = ...`. Remove `prefix` from all `cmd_*` dispatch calls. Update `load_settings` call (drop prefix). Remove `prefix` from `run.cmd_agents_list`, `run.cmd_agents_show`, `artifacts.cmd_*`, `tasks.cmd_*`, `run.cmd_run`. |
| `tasks.py` | Remove `prefix` parameter from: `discover_tasks`, `resolve_task`, `cmd_list`, `cmd_show`, `cmd_create`, `cmd_status`. Replace all inline path construction with `core.vault_path()` or `core.tasks_dir_path()`. |
| `run.py` | Remove `prefix` parameter from: `discover_agents`, `resolve_agent_alias`, `find_agent_spec`, `_find_agent_artifact`, `_agent_not_found`, `cmd_agents_list`, `cmd_agents_show`, `cmd_run`, `run_single_task`, `_exec_or_run`. Replace all inline path construction. Update prompt path references. |
| `artifacts.py` | Remove `prefix` parameter from: `_artifacts_base`, `discover_artifacts`, `resolve_artifact`, `cmd_artifacts_list`, `cmd_artifacts_show`. Replace `_artifacts_base` body with `vault_path`. |
| `hooks.py` | Remove `prefix` parameter from: `_settings_path`, `load_settings`, `load_hooks`, `run_matched`. Replace path construction. |
| `init.py` | Remove source-guard check (`agents/ + install.sh` at CWD). No other changes — init still creates `.openstation/` in target projects. The `OPENSTATION_HOME` cache structure is unchanged (it's the install cache, not a vault). |

### Tests (`tests/`)

| File | Changes |
|------|---------|
| `test_find_root.py` | Remove `source_repo_dir` fixture. Remove `test_finds_source_repo`, `test_source_repo_from_worktree`, `test_worktree_with_source_markers_returns_worktree`. Change all assertions from `(root, prefix)` tuple to single `root` value. Remove all `assert prefix == ...` lines. |
| `test_cli.py` | Update `make_source_vault` helper → use `.openstation/` layout. Update `make_agent_spec` to place specs under `.openstation/`. Update `make_task` to use `.openstation/artifacts/tasks/`. Update `make_installed_vault` — may merge with `make_source_vault` since there's only one layout now. |
| `test_hooks.py` | Update `vault` fixture — currently creates source-repo layout (`agents/ + install.sh`). Change to `.openstation/` layout. Update all `load_hooks(vault, "")` calls to `load_hooks(vault)`. Remove `test_installed_project_prefix` (the distinction no longer exists) or update it to test the single layout. |
| `test_agents_subcommand.py` | Update fixture layouts from source-repo to `.openstation/`. Remove `prefix` from function calls. |
| `test_artifacts_subcommand.py` | Same as above. |
| `test_cli_defaults.py` | Update `load_settings` call signature (drop prefix). |
| `test_auto_commit_hook.py` | Update if it references vault layout. |

### Documentation

| File | Changes |
|------|---------|
| `CLAUDE.md` | Update vault structure section — remove dual-path description. All paths now use `.openstation/` prefix. Remove source-repo vs target-project distinction. |
| `docs/worktrees.md` | Remove "Markers checked" table showing `agents/ + install.sh`. Only `.openstation/` marker remains. Update mode descriptions. |
| `docs/cli.md` | Update if it references the prefix concept or exit codes (remove `EXIT_SOURCE_GUARD`). |
| `docs/storage-query-layer.md` | Update path examples if they show root-level `artifacts/`. |
| `skills/openstation-execute/SKILL.md` | Update vault structure diagram if it shows root-level paths. |
| `commands/*.md` | Update any path references that assume root-level vault dirs. |

### Repo Structure (Physical Migration)

| Action | Detail |
|--------|--------|
| `mkdir .openstation` | Create the directory |
| `git mv artifacts .openstation/artifacts` | Move artifacts |
| `git mv agents .openstation/agents` | Move agents (symlink dir) |
| `git mv skills .openstation/skills` | Move skills |
| `git mv commands .openstation/commands` | Move commands |
| `git mv docs .openstation/docs` | Move docs |
| `git mv templates .openstation/templates` | Move templates |
| `git mv settings.json .openstation/settings.json` | Move settings |
| Update `.claude/` symlinks | Point to `.openstation/` (already do via init) |
| Update `agents/*.md` symlinks | Relative paths still correct after move |

---

## 5. Backward Compatibility

### Installed Projects (`.openstation/` already exists)

**Seamless — no changes needed.** These projects already use the
`.openstation/` convention. The only difference is that `find_root`
no longer returns a prefix string, but the paths it constructs are
identical:

```python
# Before: root / ".openstation" / "artifacts" / "tasks"
# After:  vault_path(root, "artifacts", "tasks")  →  root / ".openstation" / "artifacts" / "tasks"
```

Users don't need to run any migration. `openstation init` continues
to work as-is for re-initialization.

### `openstation init` Changes

Minimal:

- Remove the source-guard check (the `agents/ + install.sh`
  detection in `cmd_init`). `init` can now be run inside the
  source repo — but it's a no-op since `.openstation/` already
  exists.
- All other init logic is unchanged — it already creates
  `.openstation/` structure.

### Version Compatibility

Users on older CLI versions (pre-migration) who pull the repo
changes will see the new layout. Since their CLI still has
dual-path detection, `find_root` will find `.openstation/` and
work correctly with `prefix=".openstation"`. The old CLI is
forward-compatible with the new layout.

Users who update both CLI and repo simultaneously experience no
disruption.

---

## 6. Worktree Behavior (No Regression)

### Before

```
find_root():
  1. git toplevel → _check_dir → (root, "") or (root, ".openstation")
  2. main worktree root → _check_dir → (root, "") or (root, ".openstation")
  3. (None, None)
```

### After

```
find_root():
  1. git toplevel → has .openstation/? → root
  2. main worktree root → has .openstation/? → root
  3. None
```

The two-step resolution is structurally identical. The only
removed path is the `agents/ + install.sh` marker check, which
no longer applies after the repo migration.

### Worktree Test Matrix

| Scenario | Before | After |
|----------|--------|-------|
| Main repo with `.openstation/` | `(root, ".openstation")` | `root` |
| Main repo with `agents/ + install.sh` | `(root, "")` | N/A — layout migrated |
| Linked worktree, main has `.openstation/` | `(main_root, ".openstation")` | `main_root` |
| Independent worktree with `.openstation/` | `(wt_root, ".openstation")` | `wt_root` |
| No markers | `(None, None)` | `None` |

---

## Implementation Notes

### Function Signature Changes (Summary)

Total functions losing `prefix` parameter: **~25**

The change is mechanical: remove `prefix` from the signature,
replace `root / prefix / ...` or `if prefix:` branching with
`vault_path(root, ...)`.

### Risk Assessment

- **Low risk**: The change is mechanical and well-tested.
  Every `if prefix:` branch collapses to the always-true case
  (since the source repo now uses `.openstation/` too).
- **Test coverage**: Existing tests cover all paths. Source-repo
  test cases are removed (not applicable). All `.openstation/`
  test cases remain.
- **Rollback**: If needed, the physical file move can be reversed
  with `git mv .openstation/* ./`. The code change is a clean
  revert.
