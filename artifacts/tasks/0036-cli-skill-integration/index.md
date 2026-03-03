---
kind: task
name: 0036-cli-skill-integration
status: done
agent: author
owner: manual
created: 2026-03-03
---

# Integrate OpenStation CLI in Execute Skill & Commands

## Requirements

Update the `openstation-execute` skill and slash commands to use
the `openstation` CLI tool instead of raw file operations for
task management.

### Part A: Execute Skill (done)

Update `skills/openstation-execute/SKILL.md`:

1. **Task discovery** — replace the manual "scan `tasks/current/`"
   instructions in § On Startup with `openstation list --status ready
   --agent <name>` as the primary discovery method. Keep the manual
   scan as a fallback if the CLI is unavailable.

2. **Task inspection** — reference `openstation show <task>` as the
   way to load full task context, alongside the existing "read
   `index.md`" approach.

3. **Task completion** — the skill already references
   `/openstation.done`. No changes needed here.

4. **Sub-task creation** — the skill already references
   `/openstation.create`. No changes needed here.

5. **CLI availability note** — add a brief note that the CLI is
   available as `openstation` and agents should prefer it for
   discovery and inspection, falling back to direct file reads
   when the CLI is not installed.

### Part B: Slash Commands (new)

Update slash commands in `commands/` to delegate to the CLI
instead of instructing agents to scan directories and parse YAML
manually:

6. **`openstation.list.md`** — replace the "scan each status
   bucket" procedure with `openstation list` (passing through
   any filter arguments). Fall back to manual scan if CLI
   unavailable.

7. **`openstation.show.md`** — replace the "locate task folder
   across all buckets" procedure with `openstation show <task>`.
   Fall back to manual file reads if CLI unavailable.

## Findings

### Part A (execute skill — prior session)

Updated `skills/openstation-execute/SKILL.md` with three changes:

1. **New § CLI Tool section** — documents `openstation list`
   and `openstation show`, fallback paths for source/installed repos,
   and an explicit note that the CLI is read-only.

2. **§ On Startup step 4** — `openstation list --status ready --agent
   <your-name>` is now the primary discovery method, with the manual
   `tasks/current/` scan as fallback.

3. **§ Load Context** — `openstation show <task-name>` is now the
   primary inspection method, with direct `index.md` read as fallback.

### Part B (slash commands)

Updated both slash commands to a two-tier procedure (CLI primary,
manual fallback):

4. **`openstation.list.md`** — restructured procedure into "Primary:
   Use the CLI" and "Fallback: Manual Scan" sections. The primary
   path runs `openstation list` with `$ARGUMENTS` translated to CLI
   flags (`status:X` → `--status X`, `agent:X` → `--agent X`). The
   fallback preserves the original bucket-scanning logic verbatim.

5. **`openstation.show.md`** — restructured procedure into "Primary:
   Use the CLI" and "Fallback: Manual File Reads" sections. The
   primary path runs `openstation show <task>` passing `$ARGUMENTS`
   directly. The fallback preserves the original multi-bucket search
   with exact/glob/prefix matching.

## Verification

### Part A (execute skill)
- [x] Skill references `openstation list` for task discovery
- [x] Skill references `openstation show` for task inspection
- [x] Manual file operations retained as fallback

### Part B (slash commands)
- [ ] `openstation.list.md` delegates to `openstation list`
- [ ] `openstation.show.md` delegates to `openstation show`
- [ ] Fallback to manual scan if CLI unavailable
- [ ] No broken references to existing commands or workflows
