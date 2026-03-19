---
kind: dashboard
name: agents-dashboard
---

# Agents

> All agent specs from `artifacts/agents/`. Each agent is
> available via `claude --agent <name>`.

```dataview
TABLE WITHOUT ID
  link(file.path, name) AS "Agent",
  description AS "Description",
  model AS "Model"
FROM "artifacts/agents"
WHERE kind = "agent"
SORT name ASC
```
