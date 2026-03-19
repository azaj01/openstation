---
kind: task
name: 0085-research-install-and-distribution-impact
status: done
assignee: researcher
owner: user
parent: "[[0084-refactor-cli-into-src-package]]"
artifacts:
  - "[[artifacts/research/src-refactor-install-impact]]"
created: 2026-03-09
---

# Research install and distribution impact of src refactor

The CLI is currently a single extensionless file (`bin/openstation`)
that `install.sh` copies into target projects. Moving to a
`src/openstation/` package changes the distribution model.
Research the options and their trade-offs.

## Context

- Current install: `install.sh` copies `bin/openstation` to
  `.openstation/bin/openstation` in target projects
- The file is self-contained — no imports outside stdlib
- Target projects add `.openstation/bin` to PATH or alias it
- Some users may `pip install` in the future

## Requirements

Research and compare approaches for distributing a multi-file
Python CLI package to target projects:

1. **Single-file bundle** — build step that concatenates
   `src/` modules into one file for install (like current model).
   Pros/cons, tooling (zipapp, stickytape, pyinstaller lite).

2. **pip install** — `pyproject.toml` with `[project.scripts]`
   entry point. Pros/cons for our use case (agent-driven
   projects, no venv assumption).

3. **Symlink/PATH approach** — install.sh adds the source repo's
   `bin/` to PATH instead of copying. Pros/cons.

4. **Git submodule / subtree** — target project includes
   open-station as a submodule. Pros/cons.

5. **zipapp** — `python -m zipapp` to create a single `.pyz`
   file. Pros/cons.

For each option, evaluate:
- Complexity for end users
- Complexity for maintainers
- Compatibility with current `install.sh` flow
- Impact on agent execution (agents run `openstation` from PATH)
- Offline / air-gapped use
- Version pinning

## Artifact

Output: `artifacts/research/src-refactor-install-impact.md`

## Findings

Five distribution approaches were compared across six evaluation
criteria (user complexity, maintainer complexity, install.sh
compatibility, agent execution, offline use, version pinning).

**Recommendation: Zipapp** as primary distribution format.
- stdlib-only build step (`python -m zipapp`), no external deps
- Produces a single file — preserves current install.sh model
- Transparent to agents (same `openstation` on PATH)
- CI builds the zipapp per release; curl fallback downloads it

**Secondary: pip install** via `pyproject.toml` for contributors
and development (`pip install -e .`).

**Rejected**: git submodule (poor UX, fragile for agents),
single-file bundle/stickytape (unmaintained, fragile import
rewriting), symlink/PATH (PYTHONPATH fragility, breaks curl
fallback).

See [[artifacts/research/src-refactor-install-impact]] for the
full comparison matrix and implementation sketch.

## Verification

- [ ] At least 4 distribution approaches compared
- [ ] Each has clear pros/cons
- [ ] Agent execution impact addressed
- [ ] Concrete recommendation with rationale
- [ ] Artifact written to `artifacts/research/`
