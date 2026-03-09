---
kind: research
agent: researcher
task: "[[0085-research-install-and-distribution-impact]]"
created: 2026-03-09
---

# Install & Distribution Impact of src/ Refactor

## Recommendation

**Use zipapp** as the primary distribution format, with **pip install**
as a secondary path for advanced users.

Zipapp preserves the current single-file mental model (`openstation`
on PATH), requires no build dependencies beyond stdlib, works
offline, and handles the multi-file package structure transparently.
The build step is one command (`python -m zipapp`), and install.sh
needs only minor changes to point at the `.pyz` output instead of
`bin/openstation`.

---

## Current Model

| Aspect | Detail |
|--------|--------|
| CLI file | `bin/openstation` — 1879 lines, single extensionless Python file |
| Imports | stdlib only (`argparse`, `pathlib`, `json`, `re`, `shutil`, etc.) |
| Shebang | `#!/usr/bin/env python3` |
| Install | `install.sh` clones repo to `~/.local/share/openstation/`, symlinks `bin/openstation` → `~/.local/bin/openstation` |
| Curl fallback | Downloads individual files (bin/openstation, docs, commands, skills, templates) |
| Agent execution | Agents call `openstation` from PATH — must resolve to a working command |

The refactor to `src/openstation/` breaks the single-file assumption.
`bin/openstation` becomes a thin wrapper that imports from the
package, meaning the package must be importable at runtime.

---

## Approaches Compared

### 1. Zipapp (.pyz)

**Mechanism**: `python -m zipapp` bundles a directory into a single
`.pyz` file with an embedded `__main__.py` and optional shebang.
Python can execute zip archives natively (PEP 441). The result is
a single file that behaves like the current `bin/openstation`.

**Build step**:
```bash
python -m zipapp src/openstation \
  -m "openstation.cli:main" \
  -p "/usr/bin/env python3" \
  -o dist/openstation.pyz --compress
```

Or a Makefile/script that copies `src/openstation/` into a staging
dir, adds `__main__.py`, and runs `zipapp.create_archive()`.

| Criterion | Rating | Notes |
|-----------|--------|-------|
| User complexity | **Low** | Same as today — single file on PATH |
| Maintainer complexity | **Low** | One build command, stdlib only |
| install.sh compatibility | **High** | Symlink `.pyz` instead of `bin/openstation` — minimal diff |
| Agent execution | **Works** | `openstation` resolves on PATH identically |
| Offline / air-gapped | **Yes** | Self-contained, no network at runtime |
| Version pinning | **Yes** | `.pyz` is immutable once built; install.sh pins version tag |
| Limitations | No C extensions (not applicable — stdlib only) |

**Confirmed**: zipapp is stdlib (Python 3.5+), no external
dependencies needed for the build step.

### 2. pip install (pyproject.toml + project.scripts)

**Mechanism**: Standard Python packaging. `pyproject.toml` declares
`[project.scripts] openstation = "openstation.cli:main"`. Users run
`pip install openstation` or `pip install -e .` for development.

**pyproject.toml sketch**:
```toml
[project]
name = "openstation"
version = "0.6.1"

[project.scripts]
openstation = "openstation.cli:main"
```

| Criterion | Rating | Notes |
|-----------|--------|-------|
| User complexity | **Medium** | Requires pip, possibly a venv; not all agent environments have pip |
| Maintainer complexity | **Low** | Standard Python packaging |
| install.sh compatibility | **Low** | Fundamentally different model — install.sh would need to run `pip install` |
| Agent execution | **Conditional** | Works if installed into a venv/environment that's on PATH |
| Offline / air-gapped | **No** | Needs pip + network unless pre-downloaded wheel |
| Version pinning | **Yes** | `pip install openstation==0.6.1` |
| Limitations | Assumes pip available; venv management adds friction |

**Likely useful as**: A secondary install path for contributors and
CI, not the primary agent-facing distribution.

### 3. Symlink / PATH Approach

**Mechanism**: Instead of copying files, `install.sh` adds the
source repo's `src/` to `PYTHONPATH` and keeps `bin/openstation` as
the entry point (which imports from the package).

| Criterion | Rating | Notes |
|-----------|--------|-------|
| User complexity | **Low** | Similar to current flow |
| Maintainer complexity | **Low** | No build step |
| install.sh compatibility | **Medium** | Must set `PYTHONPATH` or add `.pth` file |
| Agent execution | **Fragile** | Depends on `PYTHONPATH` being set in agent's shell environment |
| Offline / air-gapped | **Yes** | Local files only |
| Version pinning | **Weak** | Tied to git checkout — no immutable artifact |
| Limitations | `PYTHONPATH` pollution; breaks if repo moves; curl fallback becomes complex (must download entire package tree) |

**Problem**: The current curl fallback downloads individual files.
With a package, it would need to download every module file and
reconstruct the directory structure — fragile and verbose.

### 4. Git Submodule / Subtree

**Mechanism**: Target project includes open-station as a git
submodule. `bin/openstation` entry point imports from the submodule's
`src/`.

| Criterion | Rating | Notes |
|-----------|--------|-------|
| User complexity | **High** | Submodules are notoriously confusing; `git clone --recurse-submodules` |
| Maintainer complexity | **Medium** | Must manage submodule references |
| install.sh compatibility | **None** | Completely different model |
| Agent execution | **Fragile** | Same PYTHONPATH issues as #3, plus submodule must be initialized |
| Offline / air-gapped | **No** | Initial clone needs network |
| Version pinning | **Yes** | Submodule pins to a commit |
| Limitations | Submodule UX is poor; agents can't reliably manage submodules |

**Not recommended**: Adds significant user friction with no
compensating benefit over zipapp or pip.

### 5. Single-File Bundle (stickytape / custom concatenation)

**Mechanism**: A build step that concatenates all `src/` modules
back into a single Python file, rewriting imports. Tools:
stickytape, or a custom script.

| Criterion | Rating | Notes |
|-----------|--------|-------|
| User complexity | **Low** | Identical to current model — single file |
| Maintainer complexity | **High** | Import rewriting is fragile; stickytape is unmaintained |
| install.sh compatibility | **High** | Drop-in replacement for current file |
| Agent execution | **Works** | Same as today |
| Offline / air-gapped | **Yes** | Self-contained |
| Version pinning | **Yes** | Immutable output file |
| Limitations | Fragile concatenation; no `__file__` reliability; stickytape can't handle dynamic imports; defeats purpose of src/ refactor for debugging |

**Confirmed**: stickytape has not been actively maintained.
Custom concatenation scripts are brittle and hard to debug when
they break.

**Not recommended**: Undermines the goal of the refactor (clean
module boundaries) by collapsing everything back at build time.
Debugging production issues would require mapping back to the
bundle.

---

## Summary Matrix

| Approach | User | Maintainer | install.sh | Agent | Offline | Version Pin |
|----------|------|------------|------------|-------|---------|-------------|
| **Zipapp** | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ | ★★★ |
| **pip install** | ★★☆ | ★★★ | ★☆☆ | ★★☆ | ★☆☆ | ★★★ |
| **Symlink/PATH** | ★★★ | ★★★ | ★★☆ | ★★☆ | ★★★ | ★★☆ |
| **Git submodule** | ★☆☆ | ★★☆ | ☆☆☆ | ★☆☆ | ★☆☆ | ★★★ |
| **Single-file bundle** | ★★★ | ★☆☆ | ★★★ | ★★★ | ★★★ | ★★★ |

---

## Recommended Strategy

### Primary: Zipapp

1. Add a `Makefile` or `scripts/build.sh` that runs:
   ```bash
   python -m zipapp src/openstation \
     -m "openstation.cli:main" \
     -p "/usr/bin/env python3" \
     -o dist/openstation --compress
   ```
   (Output without `.pyz` extension to preserve `openstation` name.)

2. Update `install.sh` to:
   - Git clone path: symlink `dist/openstation` → `~/.local/bin/openstation`
   - Curl fallback: download the pre-built `openstation` binary from
     GitHub releases (single file, same as today)

3. CI builds the zipapp on each release and attaches it to the
   GitHub release as a downloadable asset.

4. `bin/openstation` remains as a **development** entry point (thin
   wrapper that imports from `src/`) — used when running from a
   git checkout. The zipapp is the **distribution** artifact.

### Secondary: pip install

5. Add `pyproject.toml` with `[project.scripts]` for contributors
   and CI environments that prefer `pip install -e .` for
   development.

### Agent Execution Impact

**No change from agent perspective.** Agents call `openstation`
from PATH. Whether that resolves to a zipapp or a symlink to
`bin/openstation` is transparent — the CLI interface is identical.

The only risk is if an agent tries to read `__file__` to locate
sibling files — but the CLI already uses `Path(__file__).resolve()`
only to find `.version`, which would need to be embedded in the
package (e.g., `openstation/__version__.py` or baked into the
zipapp's `__main__.py`). This is a minor adjustment.

---

## Sources

- [Python zipapp docs](https://docs.python.org/3/library/zipapp.html)
- [Real Python — Python's zipapp](https://realpython.com/python-zipapp/)
- [Shiv documentation](https://shiv.readthedocs.io/)
- [Stickytape — GitHub](https://github.com/mwilliamson/stickytape)
- [Writing pyproject.toml — Python Packaging Guide](https://packaging.python.org/en/latest/guides/writing-pyproject-toml/)
- [PEP 441 — Improving Python ZIP Application Support](https://peps.python.org/pep-0441/)
