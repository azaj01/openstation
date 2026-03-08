---
kind: task
name: 0073-implement-release-changelog-skill-write
status: done
assignee: author
owner: user
parent: "[[0071-release-changelog-skill-automate-changelog]]"
created: 2026-03-07
---

# Implement Release Changelog Skill

## Requirements

1. Write `skills/release-changelog/SKILL.md` based on research
   from [[0072-research-changelog-skill-patterns-study]].
2. Adapt the Paperclip reference for Open Station: single-package
   Python project, conventional commits, no changesets/migrations.
3. Include: idempotency check, git range detection, commit
   categorization, changelog template, human review step.
4. Follow the existing skill format (see `skills/openstation-execute/SKILL.md`
   for conventions).

## Findings

Skill delivered at `skills/release-changelog/SKILL.md`. 7-step
workflow adapted from Paperclip patterns per the research in
[[0072-research-changelog-skill-patterns-study]]:

1. **Idempotency check** (Step 0) — `grep` for existing version
   entry before generating; prompts to regenerate or skip.
2. **Range detection** (Step 1) — `git tag --sort=-v:refname`
   to find the last tag; handles first-release edge case.
3. **Commit collection** (Step 2) — `git log` subjects +
   per-commit file lists for category assignment.
4. **Categorization** (Step 3) — Two-pass: parse conventional
   commit prefix, then map to domain categories (CLI, Agents,
   Specs & Docs, Commands, Skills, Install, Fix, Architecture)
   using file-path signals.
5. **Draft entry** (Step 4) — Follows the established format:
   H2 version, summary paragraph, H3 categories, bold-name
   em-dash entries.
6. **Version recommendation** (Step 5) — Suggests major/minor/patch
   based on change severity when version isn't specified.
7. **Human review gate** (Step 6) — Presents draft with flagged
   ambiguities; writes to `CHANGELOG.md` only after approval.

Stripped all Paperclip-specific patterns (changesets, migrations,
API routes, PR metadata, monorepo scoping, per-version files).

## Verification

- [ ] Skill file exists at `skills/release-changelog/SKILL.md`
- [ ] Follows Open Station skill format conventions
- [ ] Covers full workflow: range detection → categorization → draft → review
- [ ] Idempotency documented (existing entry handling)
