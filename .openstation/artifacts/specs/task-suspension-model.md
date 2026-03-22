---
kind: spec
name: task-suspension-model
agent: architect
task: "[[0188-research-task-suspension-model-design]]"
---

# Task Suspension Model

Design spec for backward transitions from `in-progress` and the
`/openstation.suspend` command.

---

## 1. New Lifecycle Transitions

Two new transitions are added to `docs/lifecycle.md`:

```
in-progress → ready      (suspend — deprioritize or hand off)
in-progress → backlog    (suspend — park indefinitely)
```

These sit alongside the existing forward transitions from
`in-progress`:

```
in-progress → review     (agent finishes work)
in-progress → rejected   (abandoned mid-effort)
in-progress → ready      (NEW — suspend to ready)
in-progress → backlog    (NEW — suspend to backlog)
```

### Scope Exclusion

No backward transitions from `review`. If work in review needs
to go back, the existing `review → rejected` path applies and
a new task can be created. This is intentionally out of scope
for this iteration.

### Lifecycle Diagram Update

The valid transitions block in `docs/lifecycle.md` gains two
lines:

```
in-progress → ready      (suspend — /openstation.suspend)
in-progress → backlog    (suspend — /openstation.suspend backlog)
```

The status descriptions table is unchanged — `ready` and
`backlog` meanings are not altered by being reachable from
`in-progress`.

---

## 2. `/openstation.suspend` Command Spec

### File

`commands/openstation.suspend.md`

### Input

`$ARGUMENTS` — task name, optional target status, optional
reason.

```
<task-name> [ready|backlog] ["reason text"]
```

- **task-name** — required. Resolved per `docs/task.spec.md`
  § Task Resolution.
- **target status** — optional. `ready` (default) or `backlog`.
  Any other value is an error.
- **reason** — optional. Free text after the target status. If
  the second argument is neither `ready` nor `backlog`, treat
  the entire remainder as the reason (target defaults to `ready`).

Examples:

```
0042                              → ready, no reason
0042 backlog                      → backlog, no reason
0042 ready "blocked on API"       → ready, reason
0042 backlog need more research   → backlog, reason
0042 blocked on API               → ready (default), reason = "blocked on API"
```

### Preconditions

- Task must be in `in-progress`. Refuse with an error if the
  task is in any other status. Message:
  `"error: task <name> is '<status>', can only suspend from in-progress"`

### Procedure

1. **Parse arguments** — extract task name, target status
   (default: `ready`), and optional reason.

2. **Resolve and read task** — per task resolution rules. Verify
   `status: in-progress`.

3. **Prompt: save work** — ask the user:
   ```
   Save uncommitted work to a branch? (y/n)
   ```
   Use the `AskUserQuestion` tool (or equivalent interactive
   prompt mechanism).

4. **If saving work:**

   a. Determine the suspend branch name:
      ```
      suspend/<task-name>
      ```
      Example: `suspend/0042-cli-improvements`

   b. Record the current branch name (to switch back later):
      ```bash
      git rev-parse --abbrev-ref HEAD
      ```

   c. Create and switch to the suspend branch:
      ```bash
      git checkout -b suspend/<task-name>
      ```

   d. Auto-commit task-related changes. Reuse the same pattern
      as `bin/hooks/auto-commit`:
      - Invoke `claude -p` with a prompt instructing the agent
        to read the task file, review the diff, stage related
        files, and create a conventional commit.
      - Commit message format:
        ```
        wip(<task-id>): suspend <task-name>
        ```
      - Scope tools to: `Bash(git:*)`, `Read`, `Glob`, `Grep`
      - If no uncommitted changes exist, skip the commit (the
        branch still gets created as a resume point).

   e. Switch back to the original branch:
      ```bash
      git checkout <original-branch>
      ```

   f. Record the branch name for the task body (step 6).

5. **Transition status** — use the CLI:
   ```bash
   openstation status <task-name> <target-status>
   ```
   This requires the new transitions to be registered in the
   CLI's transition validation table.

   **Manual fallback** — if the CLI is unavailable, edit
   `status: in-progress` → `status: <target>` directly in the
   task frontmatter.

6. **Append `## Suspended` section** — add to the task body:

   ```markdown

   ## Suspended

   **Date:** YYYY-MM-DD
   **Target:** ready|backlog
   **Reason:** <reason text or "—">
   **Branch:** `suspend/<task-name>` (or "—" if work was not saved)
   ```

   If a `## Suspended` section already exists (task suspended
   before), append a new entry below the existing one with a
   horizontal rule separator:

   ```markdown
   ---

   **Date:** YYYY-MM-DD
   **Target:** ready
   **Reason:** blocked on upstream API
   **Branch:** `suspend/0042-cli-improvements`
   ```

7. **Clear assignee** (optional consideration) — the spec does
   NOT clear the assignee on suspend. The task retains its
   assignee so the same agent can pick it up when re-promoted.
   This matches the existing `ready → backlog` transition
   behavior where assignee is preserved.

8. **Confirm** — print: task name, target status, branch
   (if created), and reason (if provided).

### Error Cases

| Condition | Message |
|-----------|---------|
| No arguments | `"usage: /openstation.suspend <task> [ready\|backlog] [reason]"` |
| Task not found | Standard resolution error per task.spec.md |
| Not in-progress | `"error: task <name> is '<status>', can only suspend from in-progress"` |
| Invalid target | `"error: target must be 'ready' or 'backlog', got '<value>'"` |
| Git branch exists | `"warning: branch suspend/<name> already exists, skipping branch creation"` |

---

## 3. CLI `openstation suspend` Subcommand

### Synopsis

```
openstation suspend TASK [TARGET] [REASON...]
```

### Arguments

| Argument | Required | Default | Description |
|----------|----------|---------|-------------|
| `TASK` | yes | — | Task ID, slug, or full name |
| `TARGET` | no | `ready` | Target status: `ready` or `backlog` |
| `REASON` | no | — | Free-text reason (remaining args joined) |

### Behavior

The CLI subcommand handles only the **status transition and
task body update** (steps 1–2, 5–6, 8 from the command spec
above). It does NOT handle the git branch/commit workflow —
that is the responsibility of the `/openstation.suspend` slash
command, which orchestrates the full flow including the user
prompt and auto-commit.

Specifically, `openstation suspend` does:

1. Resolve and validate the task (must be `in-progress`)
2. Accept an optional `--branch` flag to record in the
   `## Suspended` section
3. Transition status to the target
4. Append the `## Suspended` section to the task body
5. Print confirmation

### Flags

| Flag | Description |
|------|-------------|
| `--branch NAME` | Branch name to record in the Suspended section (set by the slash command after creating the branch) |

### Exit Codes

Uses existing exit codes:

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Usage error (bad arguments) |
| 3 | Task not found |
| 6 | Invalid transition (task not in `in-progress`) |

### Examples

```bash
openstation suspend 0042                         # → ready, no reason
openstation suspend 0042 backlog                 # → backlog, no reason
openstation suspend 0042 ready "blocked on API"  # → ready, with reason
openstation suspend 0042 --branch suspend/0042-cli-improvements  # with branch ref
```

### Implementation Notes

The transition validation table in `src/openstation/core.py`
(or wherever transitions are defined) must add:

```python
"in-progress": ["review", "rejected", "ready", "backlog"],
```

This is the only change needed in the transition engine. The
`suspend` subcommand is a thin wrapper around the existing
`cmd_status()` logic plus the `## Suspended` section append.

Hooks: The standard `StatusTransition` hooks fire on
`in-progress→ready` and `in-progress→backlog` transitions.
No special hook handling is needed — existing hook
infrastructure covers this.

---

## 4. Work Preservation Flow

### Branch Naming

```
suspend/<task-name>
```

Examples:
- `suspend/0042-cli-improvements`
- `suspend/0188-research-task-suspension-model-design`

### Auto-Commit Reuse

The `/openstation.suspend` command reuses the same pattern as
`bin/hooks/auto-commit` — invoking `claude -p` with a scoped
prompt and restricted tool set. The key differences:

| Aspect | `auto-commit` (on done) | Suspend save |
|--------|-------------------------|-------------|
| Trigger | Post-hook on `*→done` | User says "yes" to save prompt |
| Branch | Current branch | New `suspend/<task>` branch |
| Commit prefix | `chore(<id>):` | `wip(<id>):` |
| Scope | Stage task-related files | Stage task-related files |
| Tool set | `Bash(git:*), Read, Glob, Grep` | Same |

The suspend command can either:
- **Option A:** Call `bin/hooks/auto-commit` directly after
  switching to the suspend branch (reuse the script as-is,
  since the env vars are the same). The commit message format
  would need an override mechanism.
- **Option B:** Inline the same `claude -p` invocation pattern
  with a modified prompt (preferred — gives control over the
  `wip()` prefix and suspend-specific context).

**Recommendation:** Option B — inline the pattern. The auto-commit
script is designed for the done-transition context (its prompt
says "completed task"). A suspend-specific prompt gives better
commit messages.

### Switch-Back

After creating the branch and committing, the command switches
back to the original branch:

```bash
git checkout <original-branch>
```

The suspend branch is left in place — it serves as a named
reference point for resuming work. It is NOT deleted or merged.

### Edge Cases

| Scenario | Behavior |
|----------|----------|
| No uncommitted changes | Branch is still created (as a resume reference), but no commit is made |
| User says "no" to save | No branch created, no commit. Status still transitions. |
| Suspend branch already exists | Print warning, skip branch creation. Still transition status. Record existing branch name in `## Suspended`. |
| Detached HEAD | Record `HEAD` hash instead of branch name for switch-back |
| Dirty worktree with conflicts | Let git report the error — do not suppress |

---

## 5. Task Body: `## Suspended` Section Format

### Placement

The `## Suspended` section appears in the optional sections
zone, between `## Progress` and `## Findings` (or before
`## Verification` if no Findings yet exists). Canonical order
update:

1. `# Title`
2. `## Context`
3. `## Requirements`
4. `## Subtasks`
5. `## Progress`
6. **`## Suspended`** (new)
7. `## Findings`
8. `## Downstream`
9. `## Recommendations`
10. `## Verification`
11. `## Verification Report`

### Format

Single suspension:

```markdown
## Suspended

**Date:** 2026-03-21
**Target:** ready
**Reason:** blocked on upstream API
**Branch:** `suspend/0042-cli-improvements`
```

Multiple suspensions (task suspended, resumed, suspended again):

```markdown
## Suspended

**Date:** 2026-03-15
**Target:** ready
**Reason:** waiting for spec review
**Branch:** `suspend/0042-cli-improvements`

---

**Date:** 2026-03-21
**Target:** backlog
**Reason:** deprioritized for Q2
**Branch:** —
```

### Field Reference

| Field | Required | Description |
|-------|----------|-------------|
| **Date** | yes | ISO 8601 date (YYYY-MM-DD) |
| **Target** | yes | Target status: `ready` or `backlog` |
| **Reason** | yes | Reason text, or `—` if none provided |
| **Branch** | yes | Branch name (backtick-wrapped), or `—` if work was not saved |

---

## 6. Agent Discovery of Prior Work

When an agent picks up a previously-suspended task (task moves
back to `in-progress` from `ready`), it discovers prior work
through existing mechanisms:

### Discovery Path

1. **`## Suspended` section** — the agent reads the task file
   and finds the branch reference and suspension reason. This
   tells the agent:
   - Why the task was suspended
   - Where to find prior work (`suspend/<task-name>` branch)

2. **`## Progress` section** — any progress entries from the
   previous session remain in the task body. These give the
   agent context on what was already done.

3. **Branch diff** — the agent can inspect prior work:
   ```bash
   git log suspend/<task-name>
   git diff main...suspend/<task-name>
   ```

### No Special Tooling Needed

The `openstation-execute` skill already instructs agents to
read the full task file on startup (§ "Load Context"). The
`## Suspended` section is naturally discovered during this
read. No changes to the execute skill are required beyond
documenting that `## Suspended` may exist and what it means.

### Recommended Execute Skill Addition

Add a note to the "Load Context" step in
`skills/openstation-execute/`:

> If the task has a `## Suspended` section, read the branch
> reference and check out prior work if needed. Use
> `git diff main...suspend/<task-name>` to understand what
> was done before. The suspension reason provides context on
> why work was paused.

---

## 7. Compatibility Analysis

### No Conflicts with Existing Transitions

The two new transitions do not conflict with any existing
transition:

| Existing from `in-progress` | New | Conflict? |
|-----------------------------|-----|-----------|
| `in-progress → review` | — | No |
| `in-progress → rejected` | — | No |
| — | `in-progress → ready` | No (ready is not a current target from in-progress) |
| — | `in-progress → backlog` | No (backlog is not a current target from in-progress) |

### Hook Compatibility

Existing hooks use matcher patterns like `in-progress→review`
or `*→done`. The new transitions (`in-progress→ready`,
`in-progress→backlog`) will only match:
- Hooks with `in-progress→ready` or `in-progress→backlog`
  matchers (none exist today)
- Hooks with `in-progress→*` matchers (none configured by
  default)
- Hooks with `*→ready` or `*→backlog` matchers (none exist
  today)
- Catch-all `*→*` hooks (would match, as expected)

No unintended hook firing.

### Parent Auto-Promotion

The parent auto-promotion rules in `docs/lifecycle.md` promote
parents forward, never backward. A sub-task going from
`in-progress → ready` does not trigger backward movement on
the parent. The parent stays at its current status.

This is correct behavior — if one sub-task is suspended, other
sub-tasks may still be in-progress.

---

## 8. Files to Create or Modify

### New Files

| File | Type | Description |
|------|------|-------------|
| `commands/openstation.suspend.md` | command | Slash command spec |

### Modified Files

| File | Change |
|------|--------|
| `docs/lifecycle.md` | Add two transitions, add suspend to guardrails |
| `docs/task.spec.md` | Add `## Suspended` to canonical section order |
| `docs/cli.md` | Add `suspend` subcommand reference |
| `src/openstation/core.py` | Add `ready` and `backlog` to valid targets from `in-progress` |
| `src/openstation/tasks.py` | Add `cmd_suspend()` function |
| `skills/openstation-execute/` | Add note about `## Suspended` section discovery |
