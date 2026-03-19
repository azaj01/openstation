---
kind: task
name: 0118-cli-init-install-claude-files
type: feature
status: done
assignee: developer
owner: user
created: 2026-03-12
---

# CLI init — install .claude files to user space

## Requirements

1. Add a `--user` flag to `openstation init` that installs
   `.claude/` discovery files (commands, agents symlinks) to the
   user-level config dir (`~/.claude/`) instead of the
   project-level `.claude/` directory

2. When `--user` is set:
   - Create `~/.claude/commands/` symlinks pointing to the
     vault's commands
   - Create `~/.claude/agents/` symlinks pointing to the
     vault's agent specs
   - Skip project-level `.claude/` creation entirely

3. `--user` is mutually exclusive with the default (project-level)
   behavior — not both at once

4. Respect existing `--dry-run` and `--force` flags when
   operating in user mode

## Verification

- [ ] `openstation init --user` creates symlinks under `~/.claude/`
- [ ] `openstation init --user --dry-run` previews without writing
- [ ] `openstation init` (no flag) behavior unchanged
- [ ] `--user` and default mode are mutually exclusive or clearly scoped
- [ ] Existing init tests still pass
