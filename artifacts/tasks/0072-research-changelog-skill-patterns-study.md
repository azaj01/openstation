---
kind: task
name: 0072-research-changelog-skill-patterns-study
status: review
assignee: researcher
owner: user
parent: "[[0071-release-changelog-skill-automate-changelog]]"
artifacts:
  - "[[artifacts/research/changelog-skill-patterns]]"
created: 2026-03-07
---

# Research Changelog Skill Patterns

## Requirements

1. Study the Paperclip changelog skill at
   `https://github.com/paperclipai/paperclip/blob/master/skills/release-changelog/SKILL.md`.
   Identify which patterns apply to Open Station and which to strip
   (no migrations, no API routes, no changesets, no monorepo packages).
2. Review the current `CHANGELOG.md` format and release workflow
   in Open Station (tags, version bumps, commit conventions).
3. Identify the minimal set of git commands needed for changelog
   generation in a single-package Python project.
4. Deliver findings as a research artifact at
   `artifacts/research/changelog-skill-patterns.md`.

## Findings

Research artifact delivered at `artifacts/research/changelog-skill-patterns.md`.

**Key conclusions:**

1. **Paperclip patterns** — 6 of 7 steps apply with adaptation.
   Keep: idempotency check, tag-based range, conventional commit
   parsing, categorized output, human review gate, version bump
   recommendation. Strip: changeset scanning, PR metadata, migration
   detection, API endpoint scanning, monorepo package scoping,
   per-version release files.

2. **Open Station format** — Uses domain-specific categories
   (CLI, Agents, Specs & Docs, Commands, Install) rather than
   commit-type categories. Each entry is
   `- **Bold name** — Description`. Summary paragraph precedes
   categorized sections. 5 releases (v0.1.0–v0.4.0), all semver
   with `v` prefix.

3. **Minimal git commands** — Only 2 required:
   `git tag --sort=-v:refname | head -1` and
   `git log --format="%H %s" <tag>..HEAD`. Optional:
   `git diff --stat` for file-path-based category hints.

4. **Category assignment** — The skill should map commits to
   domain categories using file paths as the primary signal
   (changes to `bin/` → CLI, changes to `commands/` → Commands,
   etc.) and present the mapping for human review.

## Verification

- [ ] Research artifact delivered
- [ ] Paperclip patterns analyzed with keep/strip recommendations
- [ ] Current CHANGELOG.md format documented
- [ ] Git commands for Open Station changelog identified
