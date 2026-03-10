---
kind: task
name: 0093-rewrite-openstation-create-command-to
type: implementation
status: review
assignee: author
owner: user
created: 2026-03-10
---

# Streamline openstation.create interview to 2 rounds max

The current `/openstation.create` interview takes 6 round-trips (type, requirements, verification, agent, decomposition, status). Rewrite to present a complete draft upfront and iterate only if needed.

## Requirements

1. **Round 1 — Draft spec**: From the user's description, auto-infer and present a complete draft in one message:
   - Type (inferred from keywords in description)
   - Requirements (expanded from description)
   - Verification criteria (derived from requirements)
   - Agent & owner suggestion (based on type, using `openstation agents`)
   - Status recommendation (ready vs backlog)
   - Decomposition suggestion (only if requirements clearly span multiple domains)

   End with: "Approve, or tell me what to change."

2. **Round 2 — Iterate only if needed**: If the user approves, create immediately. If they request changes, apply them and present the updated draft. Repeat until approved, then create.

3. **Preserve all creation mechanics**: The CLI creation step, sub-task handling, manual fallback, and file editing steps remain unchanged — only the interview flow changes.

4. **Keep decomposition lightweight**: Only propose sub-tasks when requirements clearly warrant it. Don't ask about decomposition as a separate step.

## Context

- File to rewrite: `commands/openstation.create.md`
- Current interview steps to consolidate: (a) type, (b) requirements, (c) verification, (d) agent/owner, (e) decomposition, (f) ready status

## Verification

- [ ] `commands/openstation.create.md` uses a 2-round interview structure
- [ ] Round 1 presents a complete draft spec (type, requirements, verification, agent, owner, status) in one message
- [ ] Round 2 only triggers if user requests changes
- [ ] Decomposition is suggested inline only when warranted, not as a separate step
- [ ] CLI creation steps (step 3 onward in current spec) are preserved
- [ ] The command still calls `openstation agents` to inform agent suggestion
