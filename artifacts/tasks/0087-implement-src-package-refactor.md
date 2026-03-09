---
kind: task
name: 0087-implement-src-package-refactor
status: done
assignee: developer
owner: user
parent: "[[0084-refactor-cli-into-src-package]]"
created: 2026-03-09
---

# Implement src/ package refactor

Execute the module split spec from task 0086, extracting
`bin/openstation` into `src/openstation/` modules.

## Dependencies

- 0085 (research — install impact) — done
- 0086 (spec — module split design) — must be done first

## Requirements

- Read the spec at `artifacts/specs/src-package-module-split.md`
  (produced by task 0086)
- Create `src/openstation/` package with modules as specified
- Move functions from `bin/openstation` into their assigned modules
- Reduce `bin/openstation` to a thin entry-point wrapper
- Update `tests/test_cli.py` per the spec's test migration strategy
- Apply the distribution approach from task 0085's research
  (zipapp + pyproject.toml)
- Ensure no circular imports

## Verification

- [ ] `src/openstation/` package exists with modules per spec
- [ ] `bin/openstation` is a thin wrapper (~5 lines)
- [ ] All existing tests pass
- [ ] `openstation` CLI works identically from user perspective
- [ ] No circular imports
- [ ] Distribution mechanism works (zipapp or as specified)
