---
kind: task
name: 0075-cli-agent-friendly-improvements-json
status: done
assignee: developer
owner: user
created: 2026-03-08
---

# CLI Agent-Friendly Improvements

Implement P0 and P1 improvements from the CLI agent-friendly audit
(task 0040, artifact `artifacts/research/cli-agent-friendly-audit.md`).

## Requirements

### P0 — Structured Output
1. **`--json` flag on `list`** — emit a JSON array of task objects
   (keys: `id`, `name`, `status`, `assignee`, `owner`). Keep the
   human-readable table as the default.
2. **`--json` flag on `show`** — emit parsed frontmatter as a JSON
   object with an additional `body` field containing the markdown body.

### P0 — Self-Documenting Help
3. **Enrich `--help` with examples** — add `epilog` text to each
   subparser with 2–3 concrete usage examples. Use
   `RawDescriptionHelpFormatter` to preserve formatting.
4. **Expand filter docs** — `list --help` should list valid status
   values; `run --help` should describe both modes (by-agent vs
   by-task).

### P1 — Exit Codes
5. **Fix exit code collisions** — add `EXIT_NOT_FOUND` and
   `EXIT_AMBIGUOUS` constants. Renumber so each code maps to exactly
   one error condition. Replace all bare integer returns with named
   constants.

### P1 — Actionable Errors
6. **Add recovery hints** to common errors:
   - task not found → `run 'openstation list' to see available tasks`
   - agent spec not found → `check agents/ directory`
   - not in an Open Station project → `run from a directory containing .openstation/`
   - task not ready → `current status is '{status}'; use --force to override`

### P1 — Composability
7. **`--quiet` / `-q` on `list`** — emit one task name per line,
   no header. Enables piping to `xargs`.
8. **`--dry-run --json` on `run`** — emit structured JSON
   (`{"command": [...], "task": "...", "agent": "..."}`).

## Reference

- Audit artifact: `artifacts/research/cli-agent-friendly-audit.md`
- CLI source: `bin/openstation`

## Verification

- [ ] `openstation list --json` emits a valid JSON array of task objects
- [ ] `openstation show <task> --json` emits valid JSON (frontmatter fields + body)
- [ ] `--help` on each subcommand includes usage examples
- [ ] `list --help` shows valid status values; `run --help` describes both modes
- [ ] Exit codes use named constants everywhere — no bare integer returns
- [ ] No exit code collisions (each code maps to one error condition)
- [ ] Common errors include recovery hints (task not found, agent missing, not ready, not in project)
- [ ] `openstation list -q` emits one task name per line, no header
- [ ] `run --dry-run --json` emits structured JSON output
