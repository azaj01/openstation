---
kind: task
name: 0102-add-devrel-agent
type: documentation
status: done
assignee: author
owner: user
artifacts:
  - "[[artifacts/agents/devrel]]"
created: 2026-03-10
---

# Add devrel agent

Create a new `devrel` agent responsible for developer relations output.

## Requirements

1. **Agent spec** — create `artifacts/agents/devrel.md` with frontmatter (`kind: agent`, `name: devrel`, `skills` list) and a system prompt defining the agent's role and constraints
2. **Scope** — the devrel agent handles:
   - Writing articles and blog posts about Open Station
   - Creating proof-of-concept demos and tutorials
   - Social media content (announcements, threads, tips)
   - User onboarding guides and getting-started material
3. **Discovery symlink** — add `agents/devrel.md → artifacts/agents/devrel.md` so `claude --agent devrel` works
4. **Skills** — include `openstation-execute` skill (same as other agents) so it can pick up tasks from the vault
5. **Constraints** — define what the agent should and shouldn't do (e.g., writes external-facing content, doesn't modify core code or internal docs)

## Verification

- [x] `artifacts/agents/devrel.md` exists with valid agent frontmatter
- [x] Agent description covers articles, PoCs, social media, and onboarding
- [x] Discovery symlink at `agents/devrel.md` works
- [x] `openstation agents` lists the devrel agent
- [x] Agent includes `openstation-execute` skill
