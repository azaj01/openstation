---
kind: task
name: 0069-add-version-flag-to-openstation
status: done
assignee: developer
owner: user
created: 2026-03-07
---

# Add --version flag to openstation CLI

## Requirements

- Add a `--version` flag to the `openstation` CLI so `openstation --version` prints the current version
- Version string sourced from a single `VERSION` constant near the top of `bin/openstation`
- Output format: `openstation <version>` (e.g., `openstation 0.4.0`)
- Use argparse's built-in `version` action

## Verification

- [ ] `openstation --version` prints the version string and exits 0
- [ ] Version is defined as a single constant near the top of `bin/openstation`
- [ ] Existing commands still work (relevant pytest tests pass)
