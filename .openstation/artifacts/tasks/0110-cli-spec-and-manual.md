---
kind: task
name: 0110-cli-spec-and-manual
type: documentation
status: done
assignee: author
owner: user
created: 2026-03-11
---

# CLI Spec and Manual

## Requirements

1. Create `docs/cli.md` — a single document that serves as both the CLI specification and user manual.
2. Cover every subcommand: `list`, `show`, `create`, `status`, `run`, `agents`, `init`, and global flags (`--version`).
3. For each command, document: synopsis (usage line), description, flags/options with defaults, examples, and exit codes where relevant.
4. Keep it concise — reference-style, not tutorial-style. One section per command, scannable.
5. Document the exit code table (0–9) in a dedicated section.
6. Include a "Quick Reference" table at the top mapping command → one-line description.
7. Source all information from the actual CLI code (`src/openstation/cli.py` and handler modules) — don't invent flags or behavior.

## Verification

- [ ] `docs/cli.md` exists
- [ ] Every subcommand (`list`, `show`, `create`, `status`, `run`, `agents`, `init`) has a section
- [ ] Each section includes synopsis, flags, and at least one example
- [ ] Exit codes table is present and matches `core.py` constants
- [ ] Quick reference table at the top
- [ ] No invented flags or behavior — all content matches actual CLI
