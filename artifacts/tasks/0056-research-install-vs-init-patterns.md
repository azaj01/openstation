---
kind: task
name: 0056-research-install-vs-init-patterns
status: ready
agent: researcher
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
created: 2026-03-05
---

# Research Install-vs-Init Patterns in CLI Tools

## Requirements

1. Survey how established CLI tools separate installation from project initialization (e.g., `git init`, `npm init`, `eslint --init`, `cargo init`, `poetry init`, `terraform init`).
2. For each tool, document: what `install` does vs what `init` does, arguments/flags, idempotency behavior, what gets created where.
3. Identify common patterns and anti-patterns relevant to openstation's case.
4. Recommend a UX approach for `openstation init` (arguments, flags, interactive vs non-interactive, what it should print).
5. Deliver a research artifact at `artifacts/research/install-vs-init-patterns.md`.

## Verification

- [ ] At least 5 CLI tools surveyed with install-vs-init comparison
- [ ] Common patterns and anti-patterns identified
- [ ] Concrete UX recommendation for `openstation init`
- [ ] Research artifact delivered to `artifacts/research/`
