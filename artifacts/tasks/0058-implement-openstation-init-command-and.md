---
kind: task
name: 0058-implement-openstation-init-command-and
status: ready
assignee: developer
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-05
---

# Implement `openstation init` Command and Refactor install.sh

## Context

The init spec (§2c) references `artifacts/agents/` as the agent
source. Task 0063 created project-agnostic templates in
`templates/agents/` — init must source from there instead.
Additionally, all 5 agent templates should be installed by default
(not just researcher + author).

References:
- Init spec: `artifacts/specs/cli-init-command.md` (from [[0057-spec-for-openstation-init-command]])
- Agent templates: `templates/agents/` (from [[0063-rewrite-agent-specs-as-general]])
- Template authoring guidelines: `artifacts/specs/general-agent-templates.md`

## Requirements

1. Implement `openstation init` per the spec from [[0057-spec-for-openstation-init-command]], with the following overrides:
   - **Agent source**: use `templates/agents/` instead of `artifacts/agents/` (the spec predates task 0063)
   - **Default agent set**: install all 5 templates (researcher, author, architect, developer, project-manager), not just researcher + author
2. Move scaffold logic out of `install.sh` into the new `init` command (directory creation, file downloads/copies, symlinks, CLAUDE.md injection, settings.json merge).
3. Refactor `install.sh` to only install the `openstation` binary/CLI on PATH — optionally call `openstation init` at the end, or instruct the user to run it.
4. `openstation init` must be idempotent: safe to re-run without data loss.
5. Add tests for the `init` command (directory creation, idempotency, flag handling).
6. Ensure existing `install.sh --local` and `--no-agents` flags are preserved or mapped to `init` flags.

## Verification

- [ ] `openstation init` creates correct `.openstation/` structure in a clean dir
- [ ] `openstation init` is idempotent (second run doesn't break anything)
- [ ] `install.sh` only installs the binary, no longer scaffolds
- [ ] `--local` and `--no-agents` functionality preserved
- [ ] Agent specs sourced from `templates/agents/`, not `artifacts/agents/`
- [ ] All 5 agent templates installed by default
- [ ] Tests pass for the new `init` command
- [ ] Existing tests still pass
