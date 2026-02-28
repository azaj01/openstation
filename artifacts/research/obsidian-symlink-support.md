---
kind: research
name: obsidian-symlink-support
task: 0012-research-obsidian-symlink-support
created: 2026-02-27
---

# Obsidian Symlink Support

Research into how Obsidian handles symbolic links, with specific
focus on compatibility with Open Station's symlink-based task
lifecycle architecture.

---

## Open Station's Symlink Pattern

Open Station uses directory symlinks for lifecycle buckets:

```
tasks/current/0012-slug → ../../artifacts/tasks/0012-slug/
tasks/done/0009-slug    → ../../artifacts/tasks/0009-slug/
```

These are **intra-vault directory symlinks** — both the symlink
and its target reside inside the same vault.

---

## Obsidian's Native Symlink Behavior

### Timeline

| Version | Change |
|---------|--------|
| Pre-0.11.1 | No symlink support; symlinked dirs invisible |
| 0.11.1 (Feb 2021) | Experimental symlink support added |
| Current (2026) | Symlinks recognized but "strongly not recommended" |

### What Works

- **Directory symlinks to external targets** — symlinks pointing
  outside the vault are followed; files appear in the explorer,
  search, and graph view.
- **File watcher** — changes to files in externally-symlinked
  directories are detected (with caveats on subdirectory depth).
- **Junctions (Windows)** — treated equivalently to symlinks.

### What Does NOT Work

- **Intra-vault symlinks are ignored.** Obsidian silently drops
  any symlink where the target is inside the same vault. This is
  the "disjoint rule": symlink targets must be fully disjoint from
  the vault root and from each other.
- **Symlink loops** — no detection; can crash Obsidian.
- **File-level symlinks** — only directory symlinks are reliably
  supported. Individual file symlinks are inconsistent.
- **File management** — cannot create subdirectories, move files,
  or perform maintenance on symlinked folders through Obsidian's
  file explorer.
- **Symlinks to parent folders** — explicitly blocked.
- **Change detection in deep subdirectories** — file watcher may
  miss changes in nested folders within symlinked directories.

### The Disjoint Rule (Critical for Open Station)

From the official docs:

> Symlink targets must be fully disjoint from the vault root or
> any other symlink targets. Disjoint means one folder does not
> contain another, or vice versa.
>
> Obsidian ignores any symlink to a parent folder of the vault,
> or from one folder in the vault to another folder in the vault.

**Impact:** Open Station's `tasks/current/0012-slug →
../../artifacts/tasks/0012-slug` pattern creates symlinks where
both source and target are inside the vault. Obsidian will ignore
these entirely. The `tasks/` bucket directories will appear empty
in Obsidian's file explorer.

---

## Solutions Evaluated

### Solution 1: Do Nothing (Use artifacts/ Directly)

**Approach:** Accept that Obsidian ignores intra-vault symlinks.
Users browse `artifacts/tasks/` directly instead of `tasks/current/`.

| Aspect | Assessment |
|--------|------------|
| Reliability | **High** — no hacks, no plugins |
| Platform | All |
| Maintenance | None |
| UX Impact | Users lose the lifecycle-bucketed view in Obsidian; must navigate to `artifacts/tasks/` and rely on frontmatter `status` field to determine lifecycle stage |

**Verdict:** Works but defeats the purpose of the bucket
directories for visual organization.

### Solution 2: Obsidian Bookmarks / Starred Searches

**Approach:** Use Obsidian's built-in Bookmarks (formerly Starred)
or a Dataview query to create virtual "views" of tasks by status.

Example Dataview query:

```dataview
TABLE status, agent, created
FROM "artifacts/tasks"
WHERE status = "in-progress"
SORT created ASC
```

| Aspect | Assessment |
|--------|------------|
| Reliability | **High** — uses native Obsidian features |
| Platform | All (Dataview plugin needed for queries) |
| Maintenance | Low — queries are self-updating |
| UX Impact | Good — provides filterable task views without relying on symlinks |

**Verdict:** Best pure-Obsidian approach. Requires the Dataview
community plugin but provides richer views than folder browsing.

### Solution 3: Community Plugin — Symlink Creator

**Plugin:** [pteridin/obsidian_symlink_plugin](https://github.com/pteridin/obsidian_symlink_plugin)

**Approach:** Plugin that creates symlinks from within Obsidian.

| Aspect | Assessment |
|--------|------------|
| Reliability | **Low** — early development, explicit "may not work" warning |
| Platform | macOS, Linux, Windows |
| Maintenance | Minimal; v0.1.3 (Oct 2024) |
| UX Impact | Creates symlinks but doesn't address the disjoint rule — Obsidian still ignores intra-vault symlink targets |

**Verdict:** Does not solve the core problem. This plugin helps
*create* symlinks but cannot override Obsidian's disjoint rule
for *following* them.

### Solution 4: Community Plugin — Symlink Refresher

**Plugin:** [chrisdmacrae/symlinks-obsidian](https://github.com/chrisdmacrae/symlinks-obsidian) (archived)

**Approach:** Refreshes symlinks on vault open so Obsidian
recognizes them.

| Aspect | Assessment |
|--------|------------|
| Reliability | **Very Low** — archived Jan 2023, not maintained |
| Platform | All (JavaScript-based) |
| Maintenance | None — abandoned |
| UX Impact | Was designed for external symlinks; unlikely to bypass the disjoint rule |

**Verdict:** Dead project. Not viable.

### Solution 5: Hardlinks Instead of Symlinks

**Approach:** Replace directory symlinks with hardlinks to
`index.md` files.

| Aspect | Assessment |
|--------|------------|
| Reliability | **Low** — macOS/Linux do not support directory hardlinks; only file hardlinks work |
| Platform | Partial — file hardlinks work on macOS/Linux but not directories |
| Maintenance | High — must maintain hardlinks for every file in a task folder, not just the directory |
| UX Impact | Breaks Open Station's directory-based convention; hardlinked files appear as independent files (no folder structure in buckets) |

**Verdict:** Impractical. Open Station tasks are directories
containing `index.md`; hardlinks cannot replicate directory
structures.

### Solution 6: Filesystem Bind Mounts

**Approach:** Use OS-level bind mounts to mirror `artifacts/tasks/`
into bucket directories.

| Aspect | Assessment |
|--------|------------|
| Reliability | **Medium** — works at OS level, Obsidian sees real directories |
| Platform | **Linux only** — macOS has no native bind mount equivalent; would require FUSE/macFUSE |
| Maintenance | High — requires root/sudo, survives only until reboot unless added to fstab |
| UX Impact | Obsidian sees real files, but this is heavy machinery for a lightweight system |

**Verdict:** Not viable for macOS-focused workflow. Overkill for
the problem.

### Solution 7: Reverse the Architecture

**Approach:** Make `tasks/current/` etc. contain the real files,
and have `artifacts/tasks/` contain symlinks (or just be an index).

| Aspect | Assessment |
|--------|------------|
| Reliability | **High** — no symlinks needed for Obsidian to browse |
| Platform | All |
| Maintenance | Requires rearchitecting Open Station's canonical storage |
| UX Impact | Obsidian can browse task buckets natively |

**Verdict:** Would require significant changes to Open Station's
core convention. The "artifacts never move" guarantee would need
to be replaced with "bucket files are canonical, artifacts/ is
derived."

---

## Platform Compatibility Summary (macOS Focus)

| Feature | macOS | Linux | Windows |
|---------|-------|-------|---------|
| External dir symlinks in vault | ✅ | ✅ | ✅ (junctions) |
| Intra-vault dir symlinks | ❌ Ignored | ❌ Ignored | ❌ Ignored |
| File symlinks | ⚠️ Inconsistent | ⚠️ Inconsistent | ⚠️ Inconsistent |
| Hardlinks (files) | ✅ Works | ✅ Works | ✅ Works |
| Hardlinks (dirs) | ❌ Not supported | ❌ Not supported | ❌ Not supported |
| Bind mounts | ❌ No native support | ✅ Native | ❌ No native |

---

## Recommendations

### Primary: Dataview Queries (Solution 2)

Use Obsidian's Dataview plugin to create virtual task board views.
This sidesteps the symlink problem entirely by querying frontmatter
metadata directly from `artifacts/tasks/`.

**Why:** High reliability, zero maintenance on the symlink layer,
works on all platforms, and provides richer filtering (by status,
agent, date) than folder browsing ever could.

**Implementation:** Add a `tasks-dashboard.md` note to the vault
with Dataview queries for each lifecycle stage. Users see a unified
task board without depending on symlinks.

### Fallback: Browse artifacts/ Directly (Solution 1)

If Dataview is not desired, users can navigate `artifacts/tasks/`
and rely on the `status` field in each `index.md` frontmatter.
This is zero-setup but less ergonomic.

### Not Recommended

- Community plugins for symlinks — they don't solve the intra-vault
  disjoint rule, which is the actual blocker.
- Filesystem workarounds (bind mounts, hardlinks) — too fragile
  and platform-specific for a "zero runtime dependencies" system.
- Architecture reversal — too disruptive; Open Station's "artifacts
  never move" convention is a core design strength.

---

## Sources

- [Obsidian Help: Symbolic links and junctions](https://help.obsidian.md/Files+and+folders/Symbolic+links+and+junctions)
- [Obsidian Forum: Symbolic links feature request](https://forum.obsidian.md/t/symbolic-links-symlinks-folder-links/1058)
- [Obsidian Forum: Allow symlinks within vault](https://forum.obsidian.md/t/request-allow-for-symlinks-within-vault-as-a-user-option/43962)
- [Obsidian Forum: Safe symlinks discussion](https://forum.obsidian.md/t/obsidian-safe-symlinks/100873)
- [pjeby/obsidian-symlinks (archived)](https://github.com/pjeby/obsidian-symlinks)
- [chrisdmacrae/symlinks-obsidian (archived)](https://github.com/chrisdmacrae/symlinks-obsidian)
- [pteridin/obsidian_symlink_plugin](https://github.com/pteridin/obsidian_symlink_plugin)
- [SSP.sh: Add external folders via symlink](https://www.ssp.sh/brain/add-external-folders-git-blog-book-to-my-obsidian-vault-via-symlink/)
