---
kind: task
name: 0012-research-obsidian-symlink-support
status: done
assignee: researcher
owner: manual
artifacts:
  - artifacts/research/obsidian-symlink-support.md
created: 2026-02-27
---

# Research Obsidian Symlink Support

## Requirements

- Investigate why Obsidian does not follow symlinks by default
  and document the exact limitations (files vs directories,
  platform differences).
- Research all known solutions to enable symlink support in
  Obsidian, including:
  - Built-in settings or hidden/experimental flags
  - Community plugins that add symlink resolution
  - Filesystem-level workarounds (e.g., bind mounts, hardlinks)
  - Obsidian configuration file edits
- Evaluate each solution for reliability, platform compatibility
  (macOS focus), and maintenance burden.
- Recommend the best approach for the Open Station vault, which
  relies heavily on symlinks for task lifecycle buckets.
- Store findings as a research artifact in `artifacts/research/`.

## Findings

Open Station's symlink architecture is **fundamentally incompatible**
with Obsidian's symlink handling due to the "disjoint rule":
Obsidian silently ignores any symlink whose target is inside the
same vault. Since Open Station's bucket symlinks
(`tasks/current/0012-slug → ../../artifacts/tasks/0012-slug`) are
intra-vault by definition, Obsidian will show the `tasks/` bucket
directories as empty.

Seven solutions were evaluated (see
`artifacts/research/obsidian-symlink-support.md`). Key findings:

- **No built-in setting** exists to override the disjoint rule.
- **Community plugins** (Symlink Creator, Symlink Refresher) help
  create symlinks but cannot force Obsidian to follow intra-vault
  targets.
- **Filesystem workarounds** (hardlinks, bind mounts) are either
  impractical on macOS or too heavy for a zero-dependency system.

## Recommendations

1. **Use Dataview queries** to create virtual task board views
   from `artifacts/tasks/` frontmatter. This is reliable,
   cross-platform, and provides richer filtering than folder
   browsing.
2. **Browse `artifacts/tasks/` directly** as a zero-plugin
   fallback — the `status` field in frontmatter indicates
   lifecycle stage.
3. **Do not** pursue plugin-based or filesystem-level symlink
   workarounds — they don't solve the core disjoint rule issue.

## Verification

- [ ] Research artifact exists in `artifacts/research/` with
      findings on Obsidian symlink behavior
- [ ] At least two distinct solutions are documented with
      pros/cons
- [ ] A clear recommendation is provided for the Open Station
      use case
- [ ] Platform compatibility (macOS at minimum) is addressed
