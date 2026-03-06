---
kind: task
name: 0040-cli-agent-friendly-audit
status: done
assignee: researcher
owner: user
created: 2026-03-04
artifacts:
  - artifacts/research/cli-agent-friendly-audit.md
---

# Audit CLI against agent-friendly best practices

## Requirements

Audit the `openstation` CLI (`bin/openstation`) against agent-friendly
CLI best practices from two sources and produce a gap analysis with
prioritized recommendations.

**Sources:**
1. [Writing CLI Tools That AI Agents Actually Want to Use](https://dev.to/uenyioha/writing-cli-tools-that-ai-agents-actually-want-to-use-39no) — 8 rules for agent-friendly CLIs
2. [CLI-First Skill Design](https://agentic-patterns.com/patterns/cli-first-skill-design/) — patterns for CLI-as-skill integration

**Evaluation criteria** (from source 1):
1. **Structured output** — does the CLI support `--json`? Is stdout clean (messages to stderr)?
2. **Exit codes** — are exit codes meaningful and distinct (not just 0/1)?
3. **Idempotent commands** — are write commands (when they exist) safe to retry?
4. **Self-documenting** — does `--help` provide enough detail for an agent to use each subcommand without external docs?
5. **Composability** — does the CLI support `--quiet`, stdin, filtering, field selection?
6. **Dry-run & confirmation bypass** — do destructive commands support `--dry-run` and `--yes`?
7. **Actionable errors** — do errors include error types, failing input, and recovery suggestions?
8. **Consistent grammar** — is the noun-verb/verb-noun pattern consistent across subcommands?

Additionally, evaluate against patterns from source 2 (CLI-first skill
design) and incorporate any relevant criteria not already covered above.

**Deliverables:**
- A research artifact (`artifacts/research/cli-agent-friendly-audit.md`)
  with per-rule assessment (current state, gap, recommendation)
- Prioritized list of improvements (P0/P1/P2) considering what matters
  most for our agent workflows

## Findings

The CLI has a solid foundation — stderr/stdout separation, 6 distinct
exit codes, `--dry-run` support, and no interactive prompts. Three
critical gaps were identified:

1. **No structured output** (P0) — No `--json` flag on any subcommand.
   Agents must parse human-readable tables, which is fragile. This is
   the single highest-impact improvement and a prerequisite for
   composability and structured error handling.

2. **Sparse `--help` text** (P0) — No usage examples, no exit code
   documentation, no description of `run`'s dual modes. Agents can't
   self-discover capabilities from help alone.

3. **Exit code collisions** (P1) — Codes 2 and 3 are overloaded
   across different error conditions (`EXIT_NO_AGENT=2` collides with
   "not in project"; `EXIT_NO_CLAUDE=3` collides with "task not found"
   in `cmd_show`).

Additional gaps: no `--quiet` mode for piping (P1), no recovery hints
in error messages (P1), no TTY auto-detection (P2).

See `artifacts/research/cli-agent-friendly-audit.md` for the full
per-rule assessment and 11 prioritized improvements.

## Verification

- [x] Research artifact exists at `artifacts/research/cli-agent-friendly-audit.md`
- [x] All 8 rules from source 1 are assessed with current state, gap, and recommendation
- [x] Patterns from source 2 (CLI-first skill design) are evaluated and incorporated
- [x] Improvements are prioritized as P0/P1/P2 with rationale
- [x] Recommendations are specific and actionable (not vague "improve X")
