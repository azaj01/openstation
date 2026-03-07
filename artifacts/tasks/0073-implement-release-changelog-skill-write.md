---
kind: task
name: 0073-implement-release-changelog-skill-write
status: ready
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

## Verification

- [ ] Skill file exists at `skills/release-changelog/SKILL.md`
- [ ] Follows Open Station skill format conventions
- [ ] Covers full workflow: range detection → categorization → draft → review
- [ ] Idempotency documented (existing entry handling)
