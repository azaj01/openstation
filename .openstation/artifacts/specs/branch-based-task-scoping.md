---
kind: spec
name: branch-based-task-scoping
agent: architect
task: "[[0094-spec-branch-based-task-scoping]]"
---

# Branch-Based Task Scoping

Design for scoping tasks to git branches so that agents working
in worktrees only pick up tasks relevant to their branch.

---

## 1. `branch` Frontmatter Field

### Schema

```yaml
branch: feature/add-auth   # Optional. Scopes task to this branch.
```

| Property | Value |
|----------|-------|
| Type | string |
| Required | no |
| Default | empty (global task) |
| Mutability | editable via `openstation update` |

### Semantics

- **Set** — the task is scoped to that branch. Only visible when
  the current branch matches.
- **Unset / empty** — the task is **global**. Visible from every
  branch, including the main worktree.

The value is a bare branch name (e.g., `feature/add-auth`), not
a ref path. No `refs/heads/` prefix.

### Placement in Frontmatter

After `owner`, before `parent` — grouping identity fields
together:

```yaml
---
kind: task
name: 0110-add-auth-endpoint
status: ready
assignee: developer
owner: user
branch: feature/add-auth
parent: "[[0100-add-auth]]"
created: 2026-03-10
---
```

---

## 2. Filtering Logic

### Rule

**Default: show all tasks.** Branch filtering is opt-in.

When `--branch <name>` is passed, a task is **visible** when:

```
task.branch is empty  OR  task.branch == <name>
```

When `--branch auto` is passed, `<name>` is detected via
`git branch --show-current`.

When no `--branch` flag is given, **all tasks are shown**
regardless of their `branch` field.

| Command | Default (no flag) | With `--branch` |
|---------|-------------------|-----------------|
| `openstation list` | Show all tasks | Filter to matching + global |
| `openstation run` | Pick up any ready task | Only matching + global ready tasks |
| `openstation show` | Always works | N/A (no flag) |

### Implementation Notes

- `discover_tasks()` in `core.py` gains an optional `branch`
  parameter. When `None` (default), no filtering. When set,
  tasks are filtered by the visibility rule above.
- `--branch <name>` on `list` and `run` passes the value to
  `discover_tasks()`.
- `--branch auto` detects current branch via
  `git branch --show-current`. If detached HEAD or git
  unavailable, skips filtering and warns to stderr.

### Fallback Query (filesystem)

```bash
# Find tasks scoped to branch "feature/add-auth" + global tasks
grep -rL 'branch:' artifacts/tasks/*.md  # global (no branch field)
grep -rl 'branch: feature/add-auth' artifacts/tasks/*.md  # scoped
```

### Obsidian CLI Query

```bash
obsidian search vault="open-station" \
  query='[kind: task] [status: ready] [branch: feature/add-auth]' \
  format=json
```

Global tasks (no `branch` field) require a separate query or
post-filtering since Obsidian property search cannot express
"field is absent".

---

## 3. CLI Interface

### `openstation create`

New flag: `--branch <name>`

```
openstation create "Add auth endpoint" --branch feature/add-auth
```

| Behavior | Detail |
|----------|--------|
| Explicit `--branch` | Sets `branch:` in frontmatter |
| No `--branch` flag | No `branch:` field written (global task) |
| `--branch auto` | Uses current branch from `git branch --show-current`. If detached HEAD or git unavailable, omits the field and warns to stderr. |

**Decided:** No auto-setting by default. Creating a global task
(no branch) is the safe default — it matches current behavior
and avoids surprise scoping. Users opt in with `--branch` or
`--branch auto`.

**Rationale:** Auto-setting would break the common case where
tasks are created on `main` and should be visible everywhere.
Requiring explicit opt-in keeps the feature additive.

### `openstation list`

New flag:

```
--branch <name>    Filter to tasks scoped to <name> + global tasks
--branch auto      Auto-detect current branch and filter
```

Default behavior (no flag): show all tasks (no branch filtering).

### `openstation run`

Same `--branch` flag as `list`. Default: run any ready task
regardless of branch.

### `openstation update`

The `branch` field is editable via the existing update command:

```
openstation update 0110-add-auth-endpoint branch:feature/add-auth
openstation update 0110-add-auth-endpoint branch:       # clear it (make global)
```

No new command needed.

---

## 4. Edge Cases

### Detached HEAD

Only relevant when `--branch auto` is used.
`git branch --show-current` returns an empty string.

**Behavior:** Skip filtering, show all tasks. Warn to stderr:

```
warning: detached HEAD — branch filtering skipped
```

### Branch Rename

If a branch is renamed, tasks scoped to the old name won't match
`--branch auto` on the new name. Manual update required:

```bash
openstation update <task> branch:new-name
```

### Task Created Before Branch Exists

Valid. The `branch` field is just a string — no validation
against existing branches.

### Multiple Tasks on Same Branch

Fully supported. Multiple tasks can share the same `branch`
value. This is the expected pattern — a feature branch may have
several tasks (or a parent + sub-tasks all scoped to it).

### No Git Available

Only relevant when `--branch auto` is used. If `git` is not
installed or CWD is not a git repo, same as detached HEAD —
skip filtering, warn to stderr.

### Sub-tasks and Branch Scoping

Sub-tasks inherit no branch scoping from their parent. Each task
independently declares its `branch` (or omits it).

**Recommended pattern:** When decomposing a branch-scoped task
into sub-tasks, set the same `branch` on each sub-task. The
`--branch auto` flag on `create` makes this ergonomic:

```bash
openstation create "Sub-task A" --parent 0110-add-auth --branch auto
```

---

## 5. Concurrency

### Question: Is a Lock Mechanism Needed?

**Decision: No. Status-based protection is sufficient.**

### Analysis

The concern: two agents running simultaneously on the same
branch could pick up the same task.

Current protection:

1. **`status: in-progress`** — Once an agent picks up a task and
   transitions it to `in-progress`, other agents skip it (they
   only look for `status: ready`).
2. **Atomic file writes** — Frontmatter updates use
   `open(path, 'w')` which is atomic on most filesystems for
   single-file writes.

Race window: Between an agent reading a task as `ready` and
writing `in-progress`, another agent could also read it as
`ready`. This window is typically < 100ms.

### Why No Lock File

| Factor | Assessment |
|--------|------------|
| Race window size | Sub-second. Agent startup takes seconds. |
| Practical likelihood | Low. Two agents on same branch is uncommon. `openstation run` dispatches one agent at a time. |
| Lock complexity | File locks, stale lock cleanup, timeout handling — significant complexity for a rare edge case. |
| Recovery cost | If double-pickup occurs, one agent finds conflicting changes and the task goes to `review` with merge issues — recoverable. |

**Recommendation:** If concurrency becomes a real problem, add
an advisory lock in a future iteration. The lock design would be:

```
artifacts/tasks/.locks/NNNN-slug.lock
```

containing agent name and PID, with a 10-minute staleness
threshold. But this is **not needed now**.

---

## 6. Schema Changes

### `docs/task.spec.md`

Add `branch` to the frontmatter schema table:

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| `branch` | string | no | empty | Branch name this task is scoped to. When empty, task is global. |

Add `branch` to the frontmatter block example between `owner`
and `parent`.

### `docs/storage-query-layer.md`

Add a new query pattern section (§ 14) for branch-scoped queries:

- **Find tasks for current branch:** Filter by `branch: <name>`
  plus tasks with no `branch` field (global).
- **Filesystem fallback:** `grep -rl` for scoped +
  `grep -rL` for global.
- **Obsidian CLI:** Property query `[branch: <name>]` for scoped;
  post-filter for global.

Update the Query Patterns Summary table (§ 13) with a new row.

### `docs/lifecycle.md`

No changes needed. Branch scoping is a filtering/discovery
concern, not a lifecycle concern. Status transitions, ownership,
and verification rules are unaffected by which branch a task
belongs to.

### `CLAUDE.md`

Add a "Worktree Support" section documenting:

- Shared vault across worktrees (`.openstation/` in main worktree)
- Branch-scoped tasks via `branch` frontmatter field
- Opt-in filtering via `--branch` flag on `list` and `run`

---

## 7. Summary of Decisions

| Decision | Status | Rationale |
|----------|--------|-----------|
| `branch` field is optional string | Decided | Backward-compatible; global tasks are the default |
| No auto-set on create | Decided | Avoids surprise scoping; opt-in via `--branch` |
| **Show all tasks by default** | Decided | No surprise filtering; `--branch` is opt-in |
| `--branch auto` uses current git branch | Decided | Ergonomic shorthand for worktree workflows |
| Detached HEAD + `--branch auto` → skip filter | Decided | Safe fallback; warn user |
| No branch rename migration | Decided | Low frequency; manual update is acceptable |
| Sub-tasks don't inherit branch | Decided | Explicit > implicit; `--branch auto` covers the ergonomic case |
| No lock mechanism | Decided | Status-based is sufficient; lock adds complexity for a rare race |
| `show` ignores branch filter | Decided | Explicit lookups should always work |
