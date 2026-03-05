---
name: openstation.dispatch
description: Preview agent details and show launch instructions for executing ready tasks. $ARGUMENTS = agent name. Use when user says "run agent", "start agent", "dispatch agent", or wants to launch an agent on its tasks.
---

# Dispatch Agent

Show agent details and instruct the user how to launch it.

## Input

`$ARGUMENTS` — the agent name.

## Procedure

1. Validate that `agents/<name>.md` exists. If not, report an error
   and list available agents from `agents/`.
2. Read and display the agent spec (name, description, model, skills).
3. Run `openstation list --status ready --agent <name>` to find
   ready tasks assigned to this agent. Display them in a short list.
4. If no ready tasks exist, report: "No ready tasks for agent
   <name>." and stop.
5. Instruct the user to launch the agent using `openstation run`:

   **Tier 2 (fully autonomous, default):**
   ```
   openstation run <name>
   ```

   **Tier 1 (semi-autonomous, interactive):**
   ```
   openstation run <name> --tier 1
   ```

   **Launch by task (resolves agent from task frontmatter):**
   ```
   openstation run --task <id-or-slug>
   ```

   Run `openstation run --help` for all options (--budget,
   --turns, --dry-run, --max-tasks, --force).
