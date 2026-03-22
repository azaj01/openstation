---
kind: task
name: 0208-spec-hook-based-autonomous-chaining
type: spec
status: done
assignee: architect
owner: user
parent: "[[0204-hook-based-autonomous-task-chaining]]"
artifacts:
  - "[[artifacts/specs/hook-based-autonomous-chaining]]"
created: 2026-03-22
---

# Spec Hook-Based Autonomous Chaining With Tmux Dispatch

## Requirements

Design the hook-based autonomous task chaining system for 0204.
The agent completing a task triggers the next lifecycle step
automatically — the only human touchpoint is promoting to `ready`.

### Input

- Research findings: [[artifacts/research/nested-claude-instance-limitation]]
- Root cause: `CLAUDECODE=1` env var guard, bypassed via tmux `-e "CLAUDECODE="`
- Recommended approach: tmux primary, nohup fallback

### What to design

1. **Shared tmux dispatch helper** — a reusable script/module that
   spawns `openstation run` (or any command) in a named tmux window
   with `CLAUDECODE` cleared. This primitive will also be used by
   0199 (tmux for detached runs) later.
   - Session/window naming convention
   - tmux availability detection
   - nohup fallback when tmux is absent
   - Error handling (tmux server not running, duplicate names)

2. **Three hook scripts to implement** using the dispatch helper:
   - `*→ready` — auto-start: dispatch `openstation run --task`
   - `*→review` — auto-verify: dispatch `openstation run --task --verify`
   - `*→verified` — auto-accept: `openstation status <task> done` (no claude needed, direct CLI call)

3. **Future hook (design only, do not implement):**
   - `*→done` — chain-next: find parent, check for next ready subtask, dispatch it
   - The design must support this hook, but it is out of scope for now.
     Users will promote subtasks to ready manually.

4. **Loop prevention** — hooks triggering transitions that trigger
   hooks. Design a depth guard mechanism:
   - `OS_HOOK_DEPTH` env var incremented on each spawn?
   - Max depth limit?
   - Or: spawned sessions run in clean env so hooks don't re-fire?

5. **`_build_hook_env()` change** — should the hooks engine strip
   `CLAUDECODE` from the env dict? Trade-off: hooks may legitimately
   want to know they're in a Claude session. Recommend an approach.

6. **Updated `settings.json`** — the full hook configuration with
   the three implemented hooks, phases, timeouts, and matchers.

7. **Failure modes and recovery:**
   - Verify rejects (review → in-progress) — does rework re-trigger the chain?
   - Agent crashes mid-task
   - tmux session dies
   - Multiple subtasks promoted to ready simultaneously (concurrency)
   - Task has no assignee or agent spec missing

8. **Opt-in mechanism** — should autonomous chaining be opt-in per
   task (frontmatter flag), per project (settings), or always-on?
   Consider safety for users who don't want auto-execution.

### Constraints

- Hook scripts must be simple bash — no Python dependencies beyond
  what openstation already uses
- The tmux helper should be reusable by 0199 later
- Must work in both source repo and installed project contexts
- Respect existing hook execution model (pre/post, timeout, ordering)

## Progress

### 2026-03-22 — architect
> time: 00:58
> log: [[artifacts/logs/0208-spec-hook-based-autonomous-chaining]]

Designed autonomous chaining spec: tmux dispatch helper, 3 hook scripts, chain-next future design, loop prevention via OS_HOOK_DEPTH, _build_hook_env unchanged, project-level opt-in, 7 failure modes with recovery. Spec at artifacts/specs/hook-based-autonomous-chaining.md.

## Findings

Designed the full autonomous chaining system. Key decisions:

1. **Tmux dispatch helper** (`bin/os-dispatch`): Reusable script
   that spawns commands in named tmux windows with `CLAUDECODE`
   cleared. Falls back to nohup when tmux is unavailable. Uses
   current session (no session creation), caller-provided window
   names with `os-<task>` convention.

2. **Three hook scripts**: auto-start (`*→ready`), auto-verify
   (`*→review`), auto-accept (`*→verified`). All are post-hooks.
   Auto-accept runs inline (no Claude needed); the other two
   dispatch via `os-dispatch`.

3. **Chain-next** (`*→done`): Documented as future extension with
   algorithm, naming, and constraints. Deferred due to complexity
   (multi-file YAML parsing, subtask ordering).

4. **Loop prevention**: `OS_HOOK_DEPTH` env var, incremented per
   dispatch, max depth 5. Exits 0 (no-op) at limit — doesn't
   block transitions. Depth propagates via tmux `-e` or process
   inheritance.

5. **`_build_hook_env()` unchanged**: CLAUDECODE stripping happens
   in `os-dispatch` only, not in the generic env builder. Trade-off:
   hooks retain ability to detect Claude sessions; dispatch helper
   is the right abstraction boundary.

6. **Opt-in**: Project-level `autonomous.enabled` in settings.json,
   default `false`. Every hook script checks this and no-ops when
   disabled. Clean mid-chain shutdown — disabling stops the next
   hook, current agent finishes normally.

7. **Failure modes**: 7 scenarios covered with recovery paths.
   Key design choice: verify rejection does NOT auto-restart
   (prevents wasteful retry loops — rework needs human attention).

Spec: [[artifacts/specs/hook-based-autonomous-chaining]]

## Verification

- [x] Tmux dispatch helper designed with naming, detection, fallback
- [x] Three hook scripts specified with trigger, action, error handling
- [x] Chain-next hook (`*→done`) documented as future extension
- [x] Loop prevention mechanism designed and justified
- [x] `_build_hook_env()` recommendation made with trade-off analysis
- [x] Full `settings.json` configuration provided
- [x] Failure modes enumerated with recovery behavior for each
- [x] Opt-in mechanism decided and documented
- [x] Spec stored in artifacts/specs/

## Verification Report

*Verified: 2026-03-22*

| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Tmux dispatch helper designed with naming, detection, fallback | PASS | Spec §1: naming convention (§1.3), `tmux info` detection (§1.4), nohup fallback (§1.6), full script (§1.7), error handling table (§1.8) |
| 2 | Three hook scripts specified with trigger, action, error handling | PASS | Spec §2: auto-start (§2.1, `*→ready`), auto-verify (§2.2, `*→review`), auto-accept (§2.3, `*→verified`); each has full bash script with guards, opt-in check, depth guard |
| 3 | Chain-next hook documented as future extension | PASS | Spec §3: algorithm (§3.1), naming (§3.2), design constraints (§3.3), rationale for deferral (§3.4) |
| 4 | Loop prevention mechanism designed and justified | PASS | Spec §4: `OS_HOOK_DEPTH` env var (§4.1), max depth 5 (§4.2), exits 0 at limit (§4.3), clean-env alternative rejected with reasoning (§4.4), propagation table (§4.5) |
| 5 | `_build_hook_env()` recommendation with trade-off analysis | PASS | Spec §5: decision to NOT strip CLAUDECODE (§5.1), trade-off comparison table (§5.2), what changes summary (§5.3) |
| 6 | Full `settings.json` configuration provided | PASS | Spec §6: complete JSON with 3 autonomous hooks + existing hooks, `autonomous.enabled: false`, hook details table (§6.1), ordering rationale (§6.2), interaction chain diagram (§6.3) |
| 7 | Failure modes enumerated with recovery behavior | PASS | Spec §7: 7 scenarios — verify rejects (§7.1), agent crash (§7.2), tmux dies (§7.3), parallel promotion (§7.4), no assignee (§7.5), missing agent spec (§7.6), auto-commit failure (§7.7); each has behavior + recovery |
| 8 | Opt-in mechanism decided and documented | PASS | Spec §8: project-level via `settings.json` (§8.1), scope comparison table (§8.2), implementation pattern (§8.3), safety properties (§8.5) |
| 9 | Spec stored in artifacts/specs/ | PASS | File exists at `artifacts/specs/hook-based-autonomous-chaining.md` with proper frontmatter |

### Summary

9 passed, 0 failed. All verification criteria met — spec is thorough and well-structured.
