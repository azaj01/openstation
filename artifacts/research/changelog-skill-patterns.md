---
kind: research
name: changelog-skill-patterns
agent: researcher
task: "[[0072-research-changelog-skill-patterns-study]]"
created: 2026-03-07
---

# Changelog Skill Patterns

Research into changelog generation patterns for Open Station,
based on the Paperclip `release-changelog` skill and the
existing Open Station release workflow.

---

## 1. Paperclip Skill Analysis

The Paperclip changelog skill
(`skills/release-changelog/SKILL.md`) is a 6-step workflow
designed for a Node.js monorepo with a web API, database
migrations, and a changeset-based release process.

### Workflow Steps

| Step | Action | Open Station? |
|------|--------|---------------|
| 0 | **Idempotency check** — verify if changelog already exists for version | **Keep** |
| 1 | **Determine release range** — find last semver tag, identify commits since | **Keep** |
| 2 | **Gather raw data** — git commits, `.changeset/` files, merged PRs via `gh` | **Simplify** — commits only |
| 3 | **Detect breaking changes** — migrations, removed endpoints, schema changes, `BREAKING:` commits | **Simplify** — conventional commit markers only |
| 4 | **Categorize changes** — Breaking, Highlights, Improvements, Fixes, Internal | **Adapt** — use Open Station categories |
| 5 | **Write changelog** — render markdown from template | **Keep** |
| 6 | **Present for review** — show draft, flag ambiguities, wait for approval | **Keep** |

### Patterns to Keep

1. **Idempotency check** — Before generating, check if the
   version entry already exists in `CHANGELOG.md`. Ask
   whether to regenerate or skip.
2. **Tag-based range detection** — Use `git tag` to find the
   last release and scope the diff.
3. **Conventional commit parsing** — Use `feat:`, `fix:`,
   `docs:`, `refactor:`, `chore:` prefixes as the primary
   categorization signal.
4. **Category-based output** — Group changes under labeled
   sections (H3 headings).
5. **Human review gate** — Always present the draft for
   approval before writing to the file.
6. **Version bump recommendation** — Suggest major/minor/patch
   based on change severity.

### Patterns to Strip

| Paperclip Pattern | Why Strip |
|-------------------|-----------|
| `.changeset/` file scanning | Changeset-based releases (monorepo pattern). Open Station has no changesets. |
| PR metadata via `gh pr list` | Paperclip uses PR descriptions for user-facing language. Open Station commits are already descriptive. |
| Migration detection | No database, no migrations. |
| API endpoint removal scanning | No web API. |
| Schema change detection | No structured schemas to break. |
| `releases/v{version}.md` output | Paperclip writes per-version files. Open Station uses a single `CHANGELOG.md`. |
| Monorepo package scoping | Single Python package, no workspace packages. |
| `cli/package.json` version reading | No `package.json`. Version lives in git tags only. |

---

## 2. Current Open Station CHANGELOG Format

### Structure

The changelog (`CHANGELOG.md`) is a single file with this pattern:

```markdown
# Changelog

## vX.Y.Z

Summary paragraph describing the release theme.

### Category Name

- **Bold feature name** — Description of the change.
- **Another feature** — More detail.

### Another Category

- **Item** — Description.
```

### Categories Used Across Releases

| Category | Releases Used In |
|----------|-----------------|
| Architecture | v0.2.0, v0.4.0 |
| CLI | v0.3.0, v0.4.0 |
| Autonomous Execution | v0.3.0 |
| Agents | v0.2.1, v0.3.0 |
| Specs & Docs | v0.2.0, v0.2.1, v0.3.0, v0.4.0 |
| Commands | v0.2.0, v0.3.0, v0.4.0 |
| Install | v0.2.0, v0.2.1, v0.3.0, v0.4.0 |
| Fix | v0.2.1, v0.3.0 |
| Cleanup | v0.2.0 |
| Core | v0.1.0 |
| Infrastructure | v0.1.0 |

Categories are **domain-specific**, not tied to conventional
commit types. A `feat:` commit about the CLI goes under `### CLI`,
not `### Features`. This is a deliberate editorial choice — the
changelog is grouped by *what changed*, not *how it changed*.

### Entry Format

Each entry follows: `- **Bold name** — Description.`

Multi-sentence descriptions are common. Entries reference file
paths, command names, and spec names when relevant.

### Version Conventions

- Tags: `v0.1.0`, `v0.2.0`, `v0.2.1`, `v0.3.0`, `v0.4.0`
- Semver with `v` prefix
- No pre-release tags observed
- Changelog entry added in the same commit that creates the tag

### Commit Conventions

Conventional commits with these observed prefixes:

| Prefix | Count (v0.1.0–HEAD) | Maps To |
|--------|---------------------|---------|
| `feat:` | 20 | Varies by domain |
| `docs:` | 6 | Specs & Docs |
| `refactor:` | 4 | Varies — may be Internal or domain section |
| `fix:` | 3 | Fix |
| `chore:` | 1 | Internal / omit |

---

## 3. Minimal Git Commands

For a single-package Python project with conventional commits
and semver tags, only three git commands are needed:

### Required

```bash
# 1. Find the latest release tag
git tag --sort=-v:refname | head -1

# 2. List commits since that tag
git log --format="%H %s" <last-tag>..HEAD
```

### Optional (useful context)

```bash
# 3. Files changed (helps assign domain categories)
git diff --stat <last-tag>..HEAD

# 4. Full commit bodies (if summaries aren't enough)
git log --format="%H%n%s%n%b%n---" <last-tag>..HEAD

# 5. Verify tag exists and get its date
git log -1 --format="%ai" <last-tag>
```

### Not Needed

| Command | Why Skip |
|---------|----------|
| `gh pr list` | Commits are self-descriptive; no PR-based workflow |
| `ls .changeset/` | No changeset files |
| `git diff` on migration dirs | No migrations |
| `jq .version package.json` | No package.json; version comes from tag name |

---

## 4. Recommended Skill Workflow

Based on the Paperclip patterns adapted for Open Station:

```
Step 0  Check if CHANGELOG.md already has an entry for target version
Step 1  Find latest git tag (last release)
Step 2  Collect commits: git log <tag>..HEAD
Step 3  Parse conventional commit prefixes
Step 4  Map commits to domain categories (CLI, Agents, Specs & Docs, etc.)
        using file paths + commit content as signals
Step 5  Draft changelog entry with summary paragraph + categorized items
Step 6  Present draft for human review
Step 7  On approval, prepend entry to CHANGELOG.md (after # Changelog)
```

### Category Assignment Heuristic

Since Open Station uses domain categories (not commit-type
categories), the skill needs a mapping layer:

| Signal | Suggested Category |
|--------|-------------------|
| Changes to `bin/openstation`, `tests/` | CLI |
| Changes to `artifacts/agents/` | Agents |
| Changes to `docs/`, `artifacts/specs/` | Specs & Docs |
| Changes to `commands/` | Commands |
| Changes to `skills/` | Skills |
| Changes to `install.sh` | Install |
| `fix:` prefix | Fix |
| `refactor:` prefix (internal) | omit or Internal |
| `chore:` prefix | omit |
| Structural/architectural changes | Architecture |

The skill should present the categorization for review — automated
assignment will be approximate and benefit from human correction.

### What the Skill Should NOT Do

- Never auto-commit or auto-tag (human creates tags)
- Never bump version numbers (version = tag name)
- Never write `releases/` directory (single `CHANGELOG.md`)
- Never scan for changesets, migrations, or API routes
- Never fetch PR metadata

---

## Tags

#research #changelog #skill-patterns #release-workflow
