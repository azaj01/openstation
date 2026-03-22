---
kind: task
name: 0178-persist-verification-report-in-task
type: feature
status: done
assignee: author
owner: user
created: 2026-03-20
---

# Persist Verification Report In Task File

## Requirements

The `/openstation.verify` command produces a rich verification
report (pass/fail table, summary, fix suggestions) but only
displays it in the conversation — it's lost after the session.
Persist this report in the task file so feedback survives across
sessions and agents can see why a previous verification failed.

### 1. Write report into task file

After generating the verification report (step 8 of the verify
command), write it into the task file as a `## Verification Report`
section. Place it immediately **after** `## Verification`.

Content to persist (matches what's already displayed):

```markdown
## Verification Report

*Verified: YYYY-MM-DD*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | <item>    | PASS   | <brief evidence> |
| 2 | <item>    | FAIL   | <what's missing> |

### Summary

<N> passed, <M> failed. <outcome sentence>.

### What Needs Fixing

<only present when items fail — bulleted list of what to fix>
```

### 2. Replace on re-verification

When verifying a task that already has a `## Verification Report`
section, **replace** the entire section (not append). There should
always be exactly one current report.

### 3. Update task spec

Add `## Verification Report` to `docs/task.spec.md`:

- Add to the **Optional Sections** table — written by the
  verifier, not the assignee
- Add to **Canonical Section Order** — position 10, after
  `## Verification`
- Note: this section is machine-written by `/openstation.verify`,
  not authored manually

### 4. Update verify command

Update `.openstation/commands/openstation.verify.md` procedure to
include the file-write step after presenting the report.

## Findings

Updated two files:

- **`commands/openstation.verify.md`** — Added step 9 (persist
  report) between presenting the report (step 8) and the
  pass/fail branching (steps 10–11). The new step writes a
  `## Verification Report` section into the task file with the
  date, pass/fail table, summary, and fix suggestions. It
  explicitly instructs to replace any existing report section.

- **`docs/task.spec.md`** — Added `## Verification Report` to
  the Optional Sections table (noting it's machine-written, not
  manually authored) and to Canonical Section Order as position 10
  after `## Verification`.

## Progress

- 2026-03-20 — Updated `commands/openstation.verify.md` (added
  persist step 9, renumbered 9→10 and 10→11) and
  `docs/task.spec.md` (optional sections table + canonical order
  position 10). Moved to review.

## Verification

- [x] `/openstation.verify` writes a `## Verification Report` section into the task file
- [x] Report contains the date, pass/fail table, summary, and fix suggestions (when applicable)
- [x] Re-running verify on the same task replaces the previous report (not appends)
- [x] `docs/task.spec.md` documents `## Verification Report` in optional sections and canonical order
- [x] `commands/openstation.verify.md` procedure includes the file-write step

## Verification Report

*Verified: 2026-03-20*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | `/openstation.verify` writes a `## Verification Report` section into the task file | PASS | `openstation.verify.md` step 9 (lines 50–76) instructs persisting the report as `## Verification Report` immediately after `## Verification` |
| 2 | Report contains date, pass/fail table, summary, and fix suggestions | PASS | Step 9 format template includes `*Verified: YYYY-MM-DD*`, criterion table, `### Summary`, and `### What Needs Fixing` |
| 3 | Re-running verify replaces previous report (not appends) | PASS | Step 9 explicitly states: "If a `## Verification Report` section already exists, **replace it entirely**" |
| 4 | `docs/task.spec.md` documents `## Verification Report` in optional sections and canonical order | PASS | Optional Sections table (line 292) lists it as machine-written; Canonical Section Order (line 340) places it at position 10 |
| 5 | `commands/openstation.verify.md` procedure includes the file-write step | PASS | Step 9 is the dedicated persist step, inserted between presenting the report (step 8) and pass/fail branching (steps 10–11) |

### Summary

5 passed, 0 failed. All verification criteria met.
