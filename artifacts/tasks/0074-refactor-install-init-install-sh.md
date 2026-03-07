---
kind: task
name: 0074-refactor-install-init-install-sh
status: done
assignee: developer
owner: user
created: 2026-03-07
---

# Refactor install/init: nvm-style install + local-only init

## Context

Currently `install.sh` downloads just the CLI binary, then
`openstation init` handles both network downloads (from GitHub)
and project scaffolding. This tangles network and local concerns.

Adopt the nvm pattern: the install script handles all network
operations and populates a local cache; `openstation init` is
purely local.

## Requirements

### 1. `install.sh` — network installer (nvm-style)

Rewrite `install.sh` to:

- **Clone** the openstation repo to `~/.local/share/openstation/`
  (prefer `git clone --depth=1`, fall back to curl file-by-file
  if git is unavailable)
- **Symlink or copy** `bin/openstation` to `~/.local/bin/openstation`
- **Detect shell profile** (`.zshrc`, `.bashrc`, `.bash_profile`,
  `.profile`) and append PATH export if `~/.local/bin` is not
  already on PATH
- Support re-running to update (git pull or re-download)
- Wrap everything in `{ ... }` to ensure full download before
  execution (nvm pattern)
- Version-pinned URL: embed the version/tag in the script so
  `curl ... | bash` fetches a known version

Reference: https://raw.githubusercontent.com/nvm-sh/nvm/v0.40.4/install.sh

### 2. `openstation init` — local-only scaffolding

Modify `cmd_init()` in `bin/openstation` to:

- **Always read from `~/.local/share/openstation/`** — never
  download from GitHub
- Remove `INIT_BASE_URL` and all `urllib.request` / curl logic
  from init
- Remove the `--local` flag (the local cache IS the source)
- Keep existing behavior: create `.openstation/` dirs, copy
  commands/skills/docs/agent-templates, create `.claude/`
  symlinks
- Error clearly if `~/.local/share/openstation/` doesn't exist:
  "openstation not installed. Run: curl -fsSL ... | bash"

### 3. Cleanup

- Remove network-download helpers (`_fetch_to`,
  `INIT_BASE_URL`) from `bin/openstation`
- The `--force`, `--dry-run`, `--no-agents`, `--agents` flags
  on init should continue to work as-is

## Verification

- [ ] `curl -fsSL <url>/install.sh | bash` clones repo to `~/.local/share/openstation/`
- [ ] `openstation` binary is available on PATH after install
- [ ] `openstation init` in a fresh project creates `.openstation/` from local cache only (no network)
- [ ] `openstation init` without prior install gives clear error message
- [ ] Re-running `install.sh` updates the local cache (git pull or re-download)
- [ ] `install.sh` works without git (curl fallback)
- [ ] Shell profile is updated with PATH entry (idempotent — no duplicates)
- [ ] `--dry-run`, `--force`, `--no-agents` flags still work on init
- [ ] Source repo guard still prevents running init inside the openstation repo
