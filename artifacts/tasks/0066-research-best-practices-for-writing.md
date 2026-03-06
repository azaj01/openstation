---
kind: task
name: 0066-research-best-practices-for-writing
status: review
assignee: researcher
owner: user
artifacts:
  - "[[artifacts/research/agent-spec-writing-best-practices]]"
created: 2026-03-06
---

# Research Best Practices For Writing Efficient, Minimal Agent Specs

## Requirements

1. Research best practices for prompting coding AI agents — scoped to **agent spec** authoring (not skills or commands)
2. Focus on writing **efficient, minimal instructions** — maximize signal-to-noise, avoid verbosity
3. Deliverable: structured list of best practices in `artifacts/research/`
4. Each practice must be actionable and applicable to improving the `author` agent spec

## Findings

Produced 12 concrete best practices for writing efficient, minimal
agent specs. See `artifacts/research/agent-spec-writing-best-practices.md`
for the full deliverable.

**Key themes:**

1. **Assume intelligence** — cut generic explanations the model
   already knows (biggest token savings: 50-70%)
2. **Define boundaries, not abilities** — constraints are
   higher-signal than capability lists
3. **One sentence per concept** — redundancy degrades instruction
   following linearly
4. **Separate identity from protocol** — keep specs at ~30-60
   lines of body; push workflows into skills
5. **Test then cut** — iterative refinement beats speculative
   upfront writing

**Applicability to `author` agent spec:** The current author spec
(~56 lines body) is already well-structured and reasonably
minimal. Main improvement opportunities: the Capabilities section
could be tightened (some bullets describe generic abilities), and
constraints could use stronger imperative language in places.

## Recommendations

1. Apply practices #1 and #6 to all agent specs during the next
   editing pass — cut generic tool descriptions and collapse
   redundant bullets
2. Use the "new employee test" (#3) as a gating question when
   writing new specs: would a senior developer need this sentence?
3. Adopt the iterative process (#12) as standard: minimal spec →
   run → fix failures → cut successes

## Verification

- [ ] Research output exists in `artifacts/research/` as a markdown file
- [ ] Contains at least 8 concrete, actionable best practices
- [ ] Each practice includes a brief rationale and a before/after or example snippet
- [ ] Practices are scoped to agent specs (not general prompting)
- [ ] Emphasizes minimalism and instruction efficiency
