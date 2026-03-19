---
kind: task
name: 0138-research-worktree-merge-back-workflow
type: research
status: done
assignee: researcher
owner: user
parent: "[[0122-worktree-integration]]"
artifacts:
  - "[[artifacts/research/worktree-merge-back-workflow]]"
created: 2026-03-15
---

# Research: Worktree Merge-Back Workflow

After an agent finishes work in a worktree, its commits live on
a `worktree-<name>` branch. Open Station currently has no
opinion on how those changes reach main. Research the options.

## Requirements

1. Document Claude's worktree cleanup behavior in detail — what
   happens to the branch after session end, attached vs detached
2. Investigate how worktrunk (`wt merge`) and workmux
   (`workmux merge`) handle the merge-back step
3. Explore `gh pr create --head worktree-<name>` as an automated
   post-session step
4. Evaluate whether `openstation run` should offer a
   `--auto-pr` or `--merge` flag, or if a separate command
   (`openstation merge`) is more appropriate
5. Consider conflict resolution — what happens when multiple
   worktree branches touch the same files
6. Assess whether this belongs in M2 (branch scoping) or as a
   standalone milestone

## Findings

Research artifact: `artifacts/research/worktree-merge-back-workflow.md`

**Key conclusions:**

1. **Claude cleanup is unreliable.** Branches typically survive
   worktree removal (#28422), but cleanup logic has bugs —
   auto-deletes committed work (#27753), stale worktrees accumulate
   (#26725), VS Code never cleans up (#31488). Detached mode has
   no interactive prompt, so worktrees persist indefinitely.

2. **External tools solve this well.** Worktrunk (`wt merge`)
   does squash + rebase + merge + cleanup in one command. Workmux
   offers configurable merge strategies + a split path where you
   can PR first and `remove` later.

3. **`gh pr create --head worktree-<name>` is confirmed feasible**
   and Open Station has rich task context to populate PR bodies
   (findings, verification checklist, agent logs).

4. **Decided: standalone `openstation merge <task>`** with `--pr`,
   `--squash`, `--cleanup` flags. No `--auto-pr` on run, no
   lifecycle hook wiring — hooks are global and would break
   non-worktree tasks. Keep merge-back as an explicit user action.

5. **Conflict risk is real but manageable.** Main risks are parent
   task file edits and shared docs. PR-based workflow is safest —
   conflicts are visible, not silent.

6. **Milestone placement: standalone, parallel to M2.** The merge
   command doesn't require branch-scoping. It resolves branches by
   convention or `git worktree list`. Benefits from M2 but doesn't
   block on it.

## Progress

- 2026-03-15 — researcher: Researched Claude cleanup behavior
  (bugs #27753, #28422, #26725, #31488), worktrunk/workmux merge
  patterns, `gh pr create` feasibility, and four integration
  options. Produced research artifact.

## Observed Pain Points (2026-03-15 session)

Real issues hit during task 0139 worktree execution:

1. **Agent didn't commit** — ran 51 turns, made changes across
   5 files, but never committed. No branch to merge, just dirty
   working tree files.
2. **`git apply` failed** — worktree branched from older commit,
   so diffs couldn't apply to main. Had to `cat` files manually.
3. **CWD drift** — `cd` into worktree for testing broke all
   subsequent `openstation` commands (`find_root()` resolved
   worktree as vault root).
4. **Stale task files** — worktree had old task versions, agent
   read wrong task and went off-track ($1.79 wasted).

### Additional investigation points from these observations

- **Post-run auto-commit** — should `openstation run` instruct
  the agent (via prompt) or use a hook to commit worktree changes
  before session ends?
- **`openstation merge <worktree>`** — new command that handles
  diff/apply/cherry-pick from a worktree branch to main, with
  conflict detection
- **PR-based flow** — auto `gh pr create --head worktree-<name>`
  after detached runs; populate PR body from task findings and
  verification checklist

## Verification

- [ ] Research artifact exists in `artifacts/research/`
- [ ] Claude cleanup behavior documented (attached + detached)
- [ ] worktrunk and workmux merge patterns compared
- [ ] At least two concrete integration options proposed
- [ ] Conflict scenarios identified
- [ ] Milestone placement recommended
