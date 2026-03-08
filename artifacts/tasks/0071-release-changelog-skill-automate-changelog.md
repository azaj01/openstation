---
kind: task
name: 0071-release-changelog-skill-automate-changelog
status: done
assignee: 
owner: user
created: 2026-03-07
subtasks:
  - "[[0072-research-changelog-skill-patterns-study]]"
  - "[[0073-implement-release-changelog-skill-write]]"
---

# Release Changelog Skill

## Requirements

Create a `skills/release-changelog/SKILL.md` agent skill that
automates changelog generation for Open Station releases.
Adapted from the Paperclip reference (`paperclipai/paperclip`)
but simplified for this project.

1. Skill reads git history since the last release tag, categorizes
   commits, and writes structured markdown to `CHANGELOG.md`.
2. Idempotency — check if version entry exists, ask before
   overwriting.
3. Categories: Breaking Changes, Highlights, Improvements, Fixes.
   Internal changes (refactor, CI, tests) omitted from output.
4. Use conventional commit prefixes (`feat:`, `fix:`, `refactor:`,
   `docs:`, `chore:`, `test:`) for auto-categorization.
5. Present draft for human review before finalizing.
6. Skill is agent-invocable (not a slash command).

Reference: `https://github.com/paperclipai/paperclip/blob/master/skills/release-changelog/SKILL.md`

## Subtasks

- [[0072-research-changelog-skill-patterns-study]] — Research patterns
- [[0073-implement-release-changelog-skill-write]] — Implement skill

## Verification

- [ ] Skill file exists at `skills/release-changelog/SKILL.md`
- [ ] Skill produces correct changelog from git history
- [ ] Idempotency: re-running doesn't silently overwrite
- [ ] Conventional commit categorization works
- [ ] Both subtasks completed
