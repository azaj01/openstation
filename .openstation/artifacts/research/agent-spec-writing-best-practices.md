---
kind: research
name: agent-spec-writing-best-practices
agent: researcher
task: "[[0066-research-best-practices-for-writing]]"
created: 2026-03-06
---

# Best Practices for Writing Efficient, Minimal Agent Specs

Research into how to write agent specs (system prompts defining
agent identity and behavior) that maximize signal-to-noise ratio.
Scoped to agent spec authoring — not skills, commands, or general
prompting.

---

## 1. Assume Intelligence — Only Add What the Model Lacks

**Rationale:** Claude already knows how to code, reason, and
follow instructions. Every token explaining what the model already
knows wastes context and dilutes the instructions that actually
matter. Anthropic's own guidance: "Only add context Claude doesn't
already have."

**Before (verbose):**

```markdown
## Capabilities

- You can read files from the filesystem using the Read tool
- You can search for text patterns using the Grep tool
- You can write files to the filesystem using the Write tool
- You can execute shell commands using the Bash tool
- You have the ability to analyze code and find bugs
- You can refactor code to improve readability
```

**After (minimal):**

```markdown
## Capabilities

- Read specs from `artifacts/specs/` and implement end-to-end
- Write Python source, tests, and project scaffolding
- Debug failing tests systematically
```

The "after" version names *what the agent does with its tools in
this role*, not generic tool descriptions the model already
understands.

---

## 2. Define Role Through Boundaries, Not Abilities

**Rationale:** Constraints are higher-signal than capabilities.
The model can infer what it *can* do; it cannot infer what it
*should not* do. Well-defined boundaries prevent scope creep and
reduce correction loops.

**Before (capability-focused):**

```markdown
You are an agent that can write code, run tests, fix bugs,
write documentation, create task specs, and review pull requests.
```

**After (boundary-focused):**

```markdown
You implement designs — you do not make architectural decisions.
You never author vault artifacts — delegate to `author` via
sub-task. If a spec is ambiguous, create a sub-task for
`architect` rather than guessing.
```

The "after" version tells the agent where its role stops, which
is far harder for the model to infer on its own.

---

## 3. Use the "Onboarding New Employee" Mental Model

**Rationale:** Anthropic recommends: "Think of Claude as a
brilliant but new employee who lacks context on your norms and
workflows." This mental model clarifies what to include (project
conventions, workflows, domain terms) and what to skip (general
knowledge, obvious tool usage).

**Test:** Would a senior developer need this sentence on their
first day? If yes, include it. If they'd already know it, cut it.

**Before:**

```markdown
Python is a programming language. Use it to write code. Tests
verify that code works correctly. Run them with pytest.
```

**After:**

```markdown
- Primary language: Python — type hints, standard library first
- Test framework: pytest — fixtures, parametrize, `conftest.py`
```

---

## 4. Constraints Over Preferences — Use Imperative Language

**Rationale:** Soft language ("try to," "consider," "prefer to")
gives the model permission to ignore instructions. Hard
constraints ("never," "always," "must") produce reliable behavior.
Research shows models treat hedged instructions as optional.

**Before (soft):**

```markdown
- Try to keep commits small and focused
- Consider running tests before finishing
- You might want to check the spec first
```

**After (imperative):**

```markdown
- Keep commits focused and atomic — one logical change per commit
- Run tests before marking work complete — every implementation
  must pass `pytest`
- Follow the spec — if ambiguous, create a sub-task to clarify
```

---

## 5. Structure for Scanning, Not Reading

**Rationale:** Agent specs are parsed by models with limited
attention over long contexts. Flat prose buries key rules.
Structured markdown (headings, bullets, code blocks) lets the
model locate and weight instructions reliably. Anthropic: "Using
headings, lists, code blocks helps both human maintainers and
the AI model parse and prioritize."

**Recommended structure for an agent spec:**

```markdown
# Agent Name              ← identity (1-2 sentences)

## Capabilities           ← what this agent does (3-7 bullets)

## Constraints            ← hard rules and boundaries (3-7 bullets)
```

Additional sections only when they earn their token cost:

- `## Technical Expertise` — when domain specifics are needed
- `## Workflow` — when execution order is critical and
  non-obvious

Avoid: `## Background`, `## Philosophy`, `## Notes`, or any
section that provides context the model already has.

---

## 6. One Sentence Per Concept — Eliminate Redundancy

**Rationale:** Instruction-following quality degrades as
instruction count rises. Research indicates frontier models
reliably follow ~150-200 instructions; performance decays
linearly beyond that. Every redundant instruction accelerates
this decay.

**Before (redundant):**

```markdown
- Never modify task specs — task specs belong to the author
- Do not edit files in artifacts/tasks/ — these are owned by
  the author agent
- Task specifications should only be changed by the author
```

**After (single statement):**

```markdown
- Never author vault artifacts — delegate to `author` via
  sub-task
```

**Rule of thumb:** If two bullets could be collapsed into one
without losing information, collapse them.

---

## 7. Provide Escape Hatches, Not Exhaustive Rules

**Rationale:** Exhaustive if-else rules in prompts are brittle
and inflate token count. A general principle plus an escape hatch
covers more cases in fewer tokens. Anthropic's context
engineering guide warns: "Avoid overly complex, brittle if-else
logic hardcoded into prompts."

**Before (exhaustive rules):**

```markdown
- If you encounter a missing file, create it
- If you encounter a permission error, report it
- If you encounter a syntax error, fix it
- If you encounter a test failure, debug it
- If you encounter an import error, install the package
```

**After (principle + escape hatch):**

```markdown
- Debug errors systematically — fix what you can, report what
  you can't
```

The model is capable of deciding how to handle specific errors.
The spec just needs to set the expectation of *approach*.

---

## 8. Anchor to Concrete Paths and Commands, Not Abstractions

**Rationale:** Concrete references (file paths, CLI commands,
tool patterns) are unambiguous and verifiable. Abstract
descriptions ("the configuration system," "the relevant
directory") force the model to guess, introducing errors.

**Before (abstract):**

```markdown
Store your output in the appropriate location based on the
type of artifact you're producing.
```

**After (concrete):**

```markdown
- Read specs from `artifacts/specs/`
- Store implementations in `src/` unless the spec directs
  otherwise
- Run tests: `python3 -m pytest`
```

---

## 9. Separate Identity from Protocol

**Rationale:** Agent specs should define *who the agent is* —
its role, capabilities, and constraints. Operational *how-to*
protocols (lifecycle steps, execution playbooks) belong in
skills, not in the spec. Mixing them bloats the spec and
creates maintenance burden when protocols change.

**Pattern:**

- **Agent spec** → identity, capabilities, constraints
  (~30-60 lines of body content)
- **Skills** → step-by-step protocols, loaded on demand

The agent spec's frontmatter `skills:` field references the
protocols the agent should follow. This mirrors Anthropic's
progressive disclosure model: metadata at startup, detail on
demand.

**Anti-pattern:** Embedding a full execution workflow (20+
steps) directly in the agent spec body.

---

## 10. Write for Cacheability — Static Content First

**Rationale:** Anthropic's prompt caching places static content
first and variable content last, cutting costs up to 90%. Agent
specs are the static layer — they should contain stable
instructions that rarely change. Volatile details (current task,
user preferences) arrive later via conversation context.

**Implication for agent specs:**

- Keep the spec stable — avoid embedding task-specific guidance
- Don't include instructions that change per-session ("today
  we're working on X")
- Let skills and task specs carry the variable context

---

## 11. Match Freedom to Fragility

**Rationale:** Not all instructions need the same rigidity.
Anthropic's skill authoring guide recommends calibrating
specificity to the task's fragility. High-stakes or
error-prone operations need exact commands; creative or
judgment-based work needs general direction.

**High freedom** (judgment-based):

```markdown
- Produce structured research summaries with clear
  recommendations
```

**Low freedom** (fragile operation):

```markdown
- Always call `openstation` directly — never
  `python3 bin/openstation`
```

**Guideline:** Use low freedom (exact commands, "never/always")
for operations where mistakes are costly or hard to detect. Use
high freedom (direction, principles) where multiple valid
approaches exist.

---

## 12. Test with Real Tasks, Then Cut

**Rationale:** The most effective specs are built iteratively —
start minimal, observe failures, add only what's needed to fix
them. Anthropic: "Start by testing a minimal prompt with the
best model available, then add instructions based on failure
modes." This prevents speculative instructions that bloat the
spec without improving behavior.

**Process:**

1. Write a 3-section spec: identity sentence, capabilities
   (3-5 bullets), constraints (3-5 bullets)
2. Run the agent on representative tasks
3. When it fails, add the minimum instruction to fix the failure
4. When it succeeds, check whether any instruction can be
   removed without regression
5. Repeat

**Anti-pattern:** Writing a comprehensive 200-line spec before
the agent has ever run.

---

## Summary Table

| # | Practice | Signal | Token Cost |
|---|----------|--------|------------|
| 1 | Assume intelligence | Cut generic explanations | −50-70% |
| 2 | Define boundaries | Constraints > capabilities | Neutral |
| 3 | New-employee mental model | Include only project context | −30-50% |
| 4 | Imperative language | "Never" > "try to" | Neutral |
| 5 | Structured markdown | Headings + bullets | Neutral |
| 6 | One sentence per concept | Eliminate redundancy | −20-40% |
| 7 | Escape hatches | Principles > exhaustive rules | −40-60% |
| 8 | Concrete paths/commands | Unambiguous references | Neutral |
| 9 | Separate identity from protocol | Spec ≠ skill | −30-50% |
| 10 | Write for cacheability | Static content only | Neutral |
| 11 | Match freedom to fragility | Calibrate specificity | Neutral |
| 12 | Test then cut | Iterative refinement | −20-30% |

---

## Sources

- [Anthropic — Skill Authoring Best Practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Anthropic — Prompting Best Practices (Claude 4)](https://platform.claude.com/docs/en/docs/build-with-claude/prompt-engineering/claude-4-best-practices)
- [Anthropic — Effective Context Engineering for AI Agents](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents)
- [Anthropic — Equipping Agents with Skills](https://claude.com/blog/equipping-agents-for-the-real-world-with-agent-skills)
- [HumanLayer — Writing a Good CLAUDE.md](https://www.humanlayer.dev/blog/writing-a-good-claude-md)
- [Builder.io — How to Write a Good CLAUDE.md File](https://www.builder.io/blog/claude-md-guide)
