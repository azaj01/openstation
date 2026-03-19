---
kind: task
name: 0056-research-install-vs-init-patterns
status: done
assignee: researcher
owner: user
parent: "[[0055-cli-init-command-separate-project]]"
artifacts:
  - "[[artifacts/research/install-vs-init-patterns]]"
created: 2026-03-05
---

# Research Install-vs-Init Patterns in CLI Tools

## Requirements

1. Survey how established CLI tools separate installation from project initialization (e.g., `git init`, `npm init`, `eslint --init`, `cargo init`, `poetry init`, `terraform init`).
2. For each tool, document: what `install` does vs what `init` does, arguments/flags, idempotency behavior, what gets created where.
3. Identify common patterns and anti-patterns relevant to openstation's case.
4. Recommend a UX approach for `openstation init` (arguments, flags, interactive vs non-interactive, what it should print).
5. Deliver a research artifact at `artifacts/research/install-vs-init-patterns.md`.

## Findings

Surveyed 8 CLI tools: git, npm, cargo, terraform, poetry, eslint,
go modules, and husky. Full details in
`artifacts/research/install-vs-init-patterns.md`.

**Key patterns discovered:**

1. **Universal install/init separation** — every mature tool
   separates "get the binary" from "set up a project." This is
   the right direction for openstation.

2. **Idempotency spectrum** — git and terraform are fully
   idempotent (safe to re-run), cargo/poetry/go refuse on
   conflict, eslint overwrites silently. Git/terraform model
   is best for openstation.

3. **File ownership model** — tools like git distinguish
   "tool-owned" files (refresh on re-init) from "user-owned"
   files (never overwrite). openstation's install.sh already
   implements this correctly.

4. **Non-interactive for simple init** — tools with few decisions
   (git, terraform, go) are non-interactive. openstation init
   needs no prompts since all decisions are convention-based.

## Recommendations

1. **Command:** `openstation init [--local <path>] [--no-agents] [--dry-run] [--force]`
2. **Non-interactive** — no prompts, deterministic output
3. **Fully idempotent** — AS-owned files overwritten, user-owned
   files skipped, CLAUDE.md marker-based section replaced, settings
   merged
4. **Add `--dry-run`** — not found in any surveyed tool; valuable
   for openstation since it modifies existing files (CLAUDE.md,
   settings.json)
5. **install.sh becomes thin wrapper** — downloads CLI binary,
   then runs `openstation init`
6. **Existing install.sh behavior is correct** — the refactor is
   structural (bash → Python CLI), not behavioral

## Verification

- [ ] At least 5 CLI tools surveyed with install-vs-init comparison
- [ ] Common patterns and anti-patterns identified
- [ ] Concrete UX recommendation for `openstation init`
- [ ] Research artifact delivered to `artifacts/research/`
