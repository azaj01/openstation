---
kind: research
name: worktree-merge-back-workflow
agent: researcher
task: "[[0138-research-worktree-merge-back-workflow]]"
created: 2026-03-15
---

# Worktree Merge-Back Workflow

Research into how worktree branch changes should reach main after
an agent finishes work. Covers Claude's cleanup behavior, external
tool patterns, and integration options for Open Station.

---

## 1. Claude Worktree Cleanup Behavior

### 1.1 Intended Behavior

| Condition | Behavior |
|-----------|----------|
| No changes made | Worktree and branch auto-removed on session end |
| Uncommitted changes exist | Claude prompts: keep or remove |
| Commits exist (intended) | Claude should prompt: keep or remove |

### 1.2 Attached vs Detached

| Mode | Cleanup |
|------|---------|
| **Attached** (interactive terminal) | Claude prompts on exit — user chooses keep/remove |
| **Detached** (subprocess, `--tmux`) | No interactive prompt available. Cleanup behavior is undefined — worktree and branch may persist. |
| **VS Code extension** | No cleanup at all. Worktrees accumulate in `.claude/worktrees/` and must be manually removed ([Issue #31488](https://github.com/anthropics/claude-code/issues/31488)). |

### 1.3 Known Bugs (as of March 2026)

| Issue | Impact | Status |
|-------|--------|--------|
| [#27753](https://github.com/anthropics/claude-code/issues/27753) — Worktree auto-deleted despite committed work | Cleanup checks for uncommitted changes only, not diverged branches. Worktree removed even when commits exist on the branch. | Open (stale) |
| [#28422](https://github.com/anthropics/claude-code/issues/28422) — Branch persists after "remove worktree" | Warning says branch will be deleted, but it actually persists. This is standard `git worktree remove` behavior — git does not auto-delete branches. | Open |
| [#26725](https://github.com/anthropics/claude-code/issues/26725) — Stale worktrees never cleaned up | Old worktrees from weeks ago persist across sessions. | Open |

### 1.4 Practical Implication

**After a Claude worktree session ends, the branch typically
survives** (due to #28422) even if the worktree directory is
removed. This is actually helpful for merge-back workflows — the
commits are on a named branch that can be merged or PR'd.

However, for **detached mode** (Open Station's default autonomous
mode), there is no interactive cleanup prompt. The worktree and
branch simply persist until manually handled. This is the gap
Open Station needs to fill.

---

## 2. External Tool Merge-Back Patterns

### 2.1 Worktrunk (`wt merge`)

**Workflow:** Squash + rebase + merge + cleanup in one command.

```bash
wt merge main
```

**Steps performed automatically:**

1. Stage and commit any uncommitted changes (LLM-generated message)
2. Squash all worktree commits into one
3. Rebase onto target branch
4. Fast-forward merge into target
5. Switch back to main worktree
6. Remove worktree directory and branch in background

**Hook support:** `pre-merge` and `post-merge` hooks run before
and after the merge step. If `pre-merge` fails, merge aborts.

**Key design choice:** Opinionated — always squash-merges.
Clean history but loses individual commit granularity.

### 2.2 Workmux (`workmux merge`)

**Workflow:** Merge + full lifecycle cleanup.

```bash
workmux merge <handle>
```

**Steps performed automatically:**

1. Run `pre_merge` hook (if configured — e.g., `just check`)
2. Merge branch into target using configured strategy
3. Delete worktree directory
4. Delete local + tracking branches
5. Close associated tmux window

**Merge strategies** (configurable via `merge_strategy`):
- `merge` (default)
- `rebase`
- `squash`

**PR-alternative workflow:** For teams using PRs, workmux offers
a split path:
1. Push branch, create PR via `gh pr create`
2. Merge PR on GitHub
3. Run `workmux remove` (cleanup only, no local merge)

This separation of "merge" and "cleanup" is a useful pattern.

### 2.3 Comparison

| Aspect | Worktrunk | Workmux |
|--------|-----------|---------|
| Merge strategy | Squash only | Configurable (merge/rebase/squash) |
| Pre-merge validation | Hook support | Hook support (`pre_merge`) |
| Cleanup scope | Worktree + branch | Worktree + branch + tmux window |
| PR workflow | Not built-in | Explicit `remove` (cleanup-only) path |
| Conflict handling | Rebase may fail → manual resolution | Merge may fail → manual resolution |
| LLM integration | Auto-generates commit messages | None |

---

## 3. `gh pr create --head worktree-<name>` as Post-Session Step

### 3.1 Mechanics

After an agent session ends with commits on a worktree branch:

```bash
# Push the worktree branch to remote
git push -u origin worktree-<name>

# Create PR targeting main
gh pr create --base main --head worktree-<name> \
  --title "Task 0042: Add auth endpoint" \
  --body "Automated PR from agent session"
```

### 3.2 Idempotency

Check if PR already exists before creating:

```bash
existing=$(gh pr list --head "worktree-<name>" --json number -q '.[0].number')
if [ -z "$existing" ]; then
  gh pr create --base main --head "worktree-<name>" ...
else
  echo "PR #$existing already exists"
fi
```

### 3.3 Information Available for PR Body

Open Station has rich context to populate the PR:

| Source | Available Data |
|--------|---------------|
| Task frontmatter | Name, type, assignee, parent |
| `## Findings` section | Summary of what was done |
| `## Verification` checklist | What to check during review |
| Git log | Commit messages and diff stats |
| Agent log (`artifacts/logs/`) | Full session transcript |

This makes automated PR creation significantly more useful than
generic worktree PRs — the PR body can include task context.

### 3.4 Feasibility

**Confirmed feasible.** `gh pr create` works with any branch name.
The `worktree-<name>` convention from Claude, or a custom
`task/<id>-<slug>` naming scheme, both work as `--head` values.

**Prerequisite:** The branch must be pushed to the remote first.
This is a separate step that must happen before PR creation.

---

## 4. Integration Options for Open Station

### Option A: `--auto-pr` Flag on `openstation run`

Add a flag that automatically creates a PR after the agent session:

```bash
openstation run --task 0042 --worktree --auto-pr --attached
```

**Post-session steps** (after Claude exits):

1. Check if worktree branch has commits diverging from base
2. Push branch to remote
3. Create PR with task-derived title and body
4. Optionally clean up local worktree

**Pros:**
- Single command, zero manual steps
- PR body populated from task metadata
- Natural extension of `openstation run`

**Cons:**
- Couples run and merge-back into one command
- Only works when session ends normally (not on crash/kill)
- In attached mode, runs after user regains terminal
- In detached mode, harder to orchestrate (need post-process hook)

**Implementation complexity:** Medium. Requires post-session hook
in `run.py` that detects the worktree branch, pushes, and creates
PR. Must handle: no changes, push failures, existing PRs.

### Option B: `--merge` Flag on `openstation run`

Similar to `--auto-pr` but merges locally instead of creating a PR:

```bash
openstation run --task 0042 --worktree --merge --attached
```

**Post-session steps:**

1. Check out main branch
2. Merge worktree branch (fast-forward or squash)
3. Clean up worktree and branch

**Pros:**
- Fastest path to main — no PR review delay
- Good for solo developer / trusted agent workflows

**Cons:**
- Bypasses code review
- Merge conflicts require manual intervention
- Risky for autonomous (detached) agents

**Implementation complexity:** Medium-high. Must handle merge
conflicts gracefully, which is hard to do non-interactively.

### Option C: Separate `openstation merge` Command

A dedicated command for merge-back, decoupled from `openstation run`:

```bash
# After session ends, user decides how to merge
openstation merge 0042           # merge worktree branch for task 0042
openstation merge 0042 --pr      # create PR instead of local merge
openstation merge 0042 --squash  # squash merge
openstation merge 0042 --cleanup # just remove worktree, no merge
```

**Resolution logic:** Find the worktree branch for a task via:
- Task's `branch` field (if set)
- Convention: `worktree-<task-name>` (Claude default)
- Scan `git worktree list` for task-name matches

**Pros:**
- Clean separation of concerns (run ≠ merge)
- User chooses merge strategy after seeing results
- Works regardless of how the session ended
- Handles the `workmux remove` pattern (cleanup-only)
- Can be run days after the session

**Cons:**
- Extra manual step
- User must remember to merge

**Implementation complexity:** Medium. Standalone command, no
coupling to the run lifecycle.

### Option D: Hybrid — `--auto-pr` + `openstation merge`

Combine Options A and C:

- `openstation run --worktree --auto-pr` for the common
  "fire-and-forget with PR review" workflow
- `openstation merge` for manual control, cleanup, or
  when `--auto-pr` wasn't used

This mirrors workmux's split: automated path (merge) + manual
path (remove).

### Recommendation

**Option D (hybrid) is the strongest approach**, implemented in
two phases:

1. **Phase 1:** `openstation merge <task>` command with `--pr`,
   `--squash`, `--cleanup` flags. This is immediately useful
   regardless of how sessions are launched.

2. **Phase 2:** `--auto-pr` flag on `openstation run` that
   calls `openstation merge --pr` as a post-session step. Sugar
   on top of the existing command.

---

## 5. Conflict Scenarios

### 5.1 Multiple Worktree Branches Touching Same Files

| Scenario | Risk | Mitigation |
|----------|------|------------|
| Two agents edit different files | None | Merges cleanly |
| Two agents edit same file, different sections | Low | Git auto-merge usually handles this |
| Two agents edit same file, same lines | **High** | Merge conflict — requires manual resolution |
| Two agents edit shared config/schema files | **Medium** | Common with `CLAUDE.md`, frontmatter, shared types |
| Sequential merge (A merges first, B merges second) | Medium | B must rebase/resolve after A lands |

### 5.2 Open Station-Specific Conflict Risks

Tasks share the `artifacts/` directory:

| Shared Resource | Conflict Likelihood |
|-----------------|-------------------|
| `artifacts/tasks/*.md` (own task) | None — each agent edits its own task file |
| `artifacts/tasks/*.md` (parent task) | **Medium** — subtask agents may update parent's `subtasks` list |
| `artifacts/research/*.md` | Low — different output files |
| `CLAUDE.md` | **Medium** — agents updating docs section |
| `docs/*.md` | Low–Medium — if agents update shared docs |

### 5.3 Conflict Resolution Strategies

**For automated (`--auto-pr`) workflows:**
- Create the PR regardless — GitHub shows conflicts clearly
- Mark PR as needing manual resolution
- This is the safest approach: conflicts are visible, not silent

**For local merge (`openstation merge`):**
- Attempt merge; if conflicts, report them and abort
- User resolves manually, then re-runs

**For parallel agent sessions:**
- Merge branches sequentially, not in parallel
- Use `--squash` to keep one commit per task (simpler rebases)
- Consider a merge ordering based on task completion time

### 5.4 Recommendation

The **PR-based workflow is inherently safer** for conflict handling:
conflicts are visible in the PR diff, CI can validate, and human
review catches issues. Local merge should be an opt-in for
experienced users.

---

## 6. Milestone Placement

### Analysis

| Factor | Assessment |
|--------|------------|
| Dependency on M1 (pass-through) | Yes — needs `--worktree` on `openstation run` |
| Dependency on M2 (branch scoping) | Partial — `branch` field helps `openstation merge` find the right branch, but convention-based resolution works without it |
| Dependency on M3 (agent awareness) | No |
| Standalone viability | Yes — `openstation merge` works with any worktree branch |
| Complexity | Medium — new command, `gh` integration, branch detection |
| User value | High — currently a fully manual multi-step process |

### Recommendation

**Standalone addition after M1, parallel to M2.**

- `openstation merge` does not require branch-scoping to work.
  It can resolve branches by convention (`worktree-<task-name>`)
  or by scanning `git worktree list`.
- It benefits from the `branch` field (M2) but doesn't block on it.
- It's independently useful and addresses a real gap: after
  `openstation run --worktree`, there's no guided path to get
  changes back to main.

**Suggested sequencing:**

```
M1 (pass-through)  ← done/in-progress
     │
     ├── openstation merge command (new, parallel to M2)
     │
M2 (branch scoping)
     │
     ├── --auto-pr on openstation run (after merge command exists)
     │
M3 (agent awareness)
```

Create as a new subtask under 0122, targeted after M1 lands.

---

## Sources

- [Claude Code: Common Workflows — Worktrees](https://code.claude.com/docs/en/common-workflows)
- [Claude Code Issue #27753 — Worktree auto-deleted on exit when work committed](https://github.com/anthropics/claude-code/issues/27753)
- [Claude Code Issue #28422 — Branch persists after worktree removal](https://github.com/anthropics/claude-code/issues/28422)
- [Claude Code Issue #26725 — Stale worktrees never cleaned up](https://github.com/anthropics/claude-code/issues/26725)
- [Claude Code Issue #31488 — VS Code: no worktree cleanup](https://github.com/anthropics/claude-code/issues/31488)
- [Worktrunk](https://worktrunk.dev/) — [GitHub](https://github.com/max-sixty/worktrunk)
- [Workmux](https://github.com/raine/workmux)
- [GitHub CLI `gh pr create` manual](https://cli.github.com/manual/gh_pr_create)
- Prior research: `artifacts/research/worktree-integration.md`
- Prior spec: `artifacts/specs/worktree-pass-through.md`
- Prior spec: `artifacts/specs/branch-based-task-scoping.md`
