"""Agent operations and run orchestration."""

import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from openstation import core
from openstation import tasks

DEFAULT_TIER = 2
DEFAULT_BUDGET = 5
DEFAULT_TURNS = 50
DEFAULT_MAX_TASKS = 1


# --- Agent operations ---------------------------------------------------------

def discover_agents(root, prefix):
    """Scan artifacts/agents/*.md and return agent dicts."""
    if prefix:
        agents_dir = Path(root) / prefix / "artifacts" / "agents"
    else:
        agents_dir = Path(root) / "artifacts" / "agents"
    agents = []
    if not agents_dir.is_dir():
        return agents
    for entry in sorted(agents_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".md":
            continue
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = core.parse_frontmatter(text)
        if fm.get("kind") != "agent":
            continue
        desc = fm.get("description", "")
        if desc in (">-", ">", "|", "|-"):
            desc = core.parse_multiline_value(text, "description")
        agents.append({
            "name": fm.get("name", entry.stem),
            "description": desc,
        })
    return agents


def format_agents_table(agents):
    """Format agents as an aligned table."""
    if not agents:
        return ""
    headers = ["Name", "Description"]
    keys = ["name", "description"]
    mins = [10, 20]

    widths = [max(mins[i], len(headers[i])) for i in range(len(headers))]
    for a in agents:
        for i, k in enumerate(keys):
            widths[i] = max(widths[i], len(str(a.get(k, ""))))

    def fmt_row(values):
        parts = []
        for i, v in enumerate(values):
            parts.append(str(v).ljust(widths[i]))
        return "   ".join(parts)

    lines = [fmt_row(headers)]
    lines.append(fmt_row(["-" * widths[i] for i in range(len(headers))]))
    for a in agents:
        lines.append(fmt_row([a.get(k, "") for k in keys]))
    return "\n".join(lines)


def find_agent_spec(root, prefix, agent_name):
    """Locate an agent's markdown spec file. Returns Path or None."""
    candidates = []
    if prefix:
        candidates.append(Path(root) / prefix / "agents" / f"{agent_name}.md")
    candidates.append(Path(root) / "agents" / f"{agent_name}.md")
    for p in candidates:
        if p.exists():
            return p
    return None


def parse_allowed_tools(spec_path):
    """Extract the allowed-tools list from an agent spec's frontmatter."""
    tools = []
    in_list = False
    try:
        text = Path(spec_path).read_text(encoding="utf-8")
    except OSError:
        return tools

    for line in text.splitlines():
        if in_list and line.strip() == "---":
            break
        if line.startswith("allowed-tools:"):
            in_list = True
            continue
        if in_list:
            if not re.match(r"^\s*-\s+", line):
                break
            value = re.sub(r"^\s*-\s+", "", line)
            value = value.strip().strip("\"'")
            tools.append(value)
    return tools


def build_command(agent_name, tier, budget, turns, prompt, tools, output_format="json"):
    """Assemble the claude CLI argv for the given tier."""
    if tier == 1:
        return [
            "claude",
            "--agent", agent_name,
            "--permission-mode", "acceptEdits",
        ]
    cmd = [
        "claude",
        "-p", prompt,
        "--agent", agent_name,
        "--allowedTools",
    ]
    cmd.extend(tools)
    cmd.extend([
        "--max-budget-usd", str(budget),
        "--max-turns", str(turns),
        "--output-format", output_format,
    ])
    return cmd


# --- Execution ----------------------------------------------------------------

def run_single_task(root, prefix, task_spec, task_name, tier, budget, turns, dry_run,
                    json_output=False):
    """Execute one task: resolve agent, build command, launch. Returns the exit code."""
    task_spec = Path(task_spec)

    try:
        text = task_spec.read_text(encoding="utf-8")
    except OSError:
        core.err(f"Task spec missing: {task_spec}")
        return core.EXIT_USAGE
    fm = core.parse_frontmatter(text)
    agent = fm.get("assignee", "")
    if not agent:
        core.err(f"No agent assigned to task: {task_name}")
        return core.EXIT_USAGE

    core.detail("agent", agent)

    agent_spec = find_agent_spec(root, prefix, agent)
    if agent_spec is None:
        core.err(f"Agent spec not found: {agent}")
        core.err("  hint: check agents/ directory for available agent specs")
        return core.EXIT_NOT_FOUND

    tools = parse_allowed_tools(agent_spec)
    if not tools:
        core.err(f"No allowed-tools found in agent spec: {agent_spec}")
        core.err("  hint: add an 'allowed-tools:' list to the agent's frontmatter")
        return core.EXIT_USAGE

    prompt = (
        f"Execute task {task_name}. Read its spec at "
        f"artifacts/tasks/{task_name}.md and work through "
        f"the requirements."
    )
    cmd = build_command(agent, tier, budget, turns, prompt, tools)

    if dry_run:
        if json_output:
            print(json.dumps({
                "command": cmd,
                "task": task_name,
                "agent": agent,
            }, indent=2))
        else:
            print(core.shlex_join(cmd))
        return core.EXIT_OK

    core.hint(f"Launching {core.shlex_join(cmd[:4])}...")

    log_dir = root / prefix / "artifacts" / "logs" if prefix else root / "artifacts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{task_name}.json"
    with open(log_file, "w") as f:
        result = subprocess.run(cmd, cwd=str(root), stdout=f)
    core.detail("log", str(log_file.relative_to(root)))
    return result.returncode if result.returncode == 0 else core.EXIT_AGENT_ERROR


def _exec_or_run(root, prefix, tasks_dir, task_name, agent_name_override, tier, budget, turns,
                  dry_run, json_output=False):
    """Execute a single task, using execvp when possible (no queue to iterate)."""
    tasks_dir = Path(tasks_dir)
    spec = tasks_dir / f"{task_name}.md"

    try:
        text = spec.read_text(encoding="utf-8")
    except OSError:
        core.err(f"Task spec missing: {spec}")
        return core.EXIT_USAGE
    fm = core.parse_frontmatter(text)
    agent = fm.get("assignee", "")
    if not agent:
        core.err(f"No agent assigned to task: {task_name}")
        return core.EXIT_USAGE

    agent_spec = find_agent_spec(root, prefix, agent)
    if agent_spec is None:
        core.err(f"Agent spec not found: {agent}")
        core.err("  hint: check agents/ directory for available agent specs")
        return core.EXIT_NOT_FOUND

    tools = parse_allowed_tools(agent_spec)
    if not tools:
        core.err(f"No allowed-tools found in agent spec: {agent_spec}")
        core.err("  hint: add an 'allowed-tools:' list to the agent's frontmatter")
        return core.EXIT_USAGE

    prompt = (
        f"Execute task {task_name}. Read its spec at "
        f"artifacts/tasks/{task_name}.md and work through "
        f"the requirements."
    )
    cmd = build_command(agent, tier, budget, turns, prompt, tools, output_format="text")

    if dry_run:
        if json_output:
            print(json.dumps({
                "command": cmd,
                "task": task_name,
                "agent": agent,
            }, indent=2))
        else:
            print(core.shlex_join(cmd))
        return core.EXIT_OK

    core.header(f"openstation run --task {task_name}")
    core.detail("Task", task_name)
    core.detail("Agent", agent)
    core.detail("Tier", str(tier))
    print(file=sys.stderr)
    core.hint(f"Launching {core.shlex_join(cmd[:4])}...")

    os.chdir(str(root))
    os.execvp(cmd[0], cmd)
    return core.EXIT_OK  # unreachable


# --- Command handlers ---------------------------------------------------------

def cmd_agents(args, root, prefix):
    """Handle the agents subcommand."""
    agents = discover_agents(root, prefix)
    agents.sort(key=lambda a: a["name"])
    output = format_agents_table(agents)
    if output:
        print(output)


def cmd_run(args, root, prefix):
    """Handle the run subcommand."""
    core.set_quiet(getattr(args, "quiet", False))
    core.set_run_start(time.time())

    agent_name = args.agent
    task_ref = args.task

    if agent_name and not task_ref and re.match(r'^\d', agent_name):
        task_ref = agent_name
        agent_name = None

    if agent_name and task_ref:
        core.err("Specify either an agent name or --task, not both")
        return core.EXIT_USAGE
    if not agent_name and not task_ref:
        core.err("Agent name or --task is required")
        return core.EXIT_USAGE

    if not shutil.which("claude"):
        core.err("claude CLI not found on $PATH")
        core.err("  hint: install Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code")
        return core.EXIT_NO_CLAUDE

    tier = args.tier
    budget = args.budget
    turns = args.turns
    dry_run = args.dry_run
    force = args.force
    max_tasks = args.max_tasks
    json_output = getattr(args, "json", False)

    if task_ref:
        # --- BY-TASK MODE ---
        task_name, error, code = tasks.resolve_task(root, prefix, task_ref)
        if error:
            core.err(error)
            return code

        tdir = core.tasks_dir_path(root, prefix)
        spec = tdir / f"{task_name}.md"

        if not force:
            ok, status = tasks.assert_task_ready(spec, task_name)
            if not ok:
                core.err(f"Task {task_name} has status '{status}' (expected 'ready')")
                core.err(f"  hint: current status is '{status}'; use --force to override")
                return core.EXIT_TASK_NOT_READY

        core.header(f"openstation run --task {task_name}")
        core.info(f"Task collection: {task_name}")

        subtasks = tasks.find_ready_subtasks(tdir, task_name, force=force)

        if subtasks:
            core.info(f"Found {len(subtasks)} ready subtask(s)")
            completed = 0
            failed_count = 0
            remaining = len(subtasks)
            rc = core.EXIT_OK

            for sub_spec, sub_name in subtasks:
                if completed >= max_tasks:
                    break
                run_total = min(len(subtasks), max_tasks)
                core.step(completed + 1, run_total, sub_name)
                start = time.time()
                rc = run_single_task(root, prefix, sub_spec, sub_name, tier, budget, turns,
                                     dry_run, json_output=json_output)
                elapsed = time.time() - start
                if rc == core.EXIT_OK:
                    core.success(f"Done (exit 0, {core.format_duration(elapsed)})")
                    completed += 1
                    remaining -= 1
                else:
                    core.failure(f"Failed (exit {rc}, {core.format_duration(elapsed)})")
                    failed_count += 1
                    break

            next_sub = None
            if remaining > 0:
                executed_count = completed + failed_count
                if executed_count < len(subtasks):
                    next_sub = subtasks[executed_count][1]

            core.summary_block(
                completed=completed,
                failed=failed_count,
                pending=remaining,
                resume_cmd=f"openstation run --task {task_name}",
                next_task=next_sub,
            )
            return core.EXIT_OK if completed > 0 else core.EXIT_AGENT_ERROR
        else:
            core.info("No subtasks found, executing task directly")
            return _exec_or_run(root, prefix, tdir, task_name, agent_name, tier, budget, turns,
                                dry_run, json_output=json_output)
    else:
        # --- BY-AGENT MODE ---
        agent_spec = find_agent_spec(root, prefix, agent_name)
        if agent_spec is None:
            core.err(f"Agent spec not found: {agent_name}")
            core.err("  hint: check agents/ directory for available agent specs")
            return core.EXIT_NOT_FOUND

        tools = parse_allowed_tools(agent_spec)
        if not tools:
            core.err(f"No allowed-tools found in agent spec: {agent_spec}")
            core.err("  hint: add an 'allowed-tools:' list to the agent's frontmatter")
            return core.EXIT_USAGE

        prompt = "Execute your ready tasks."
        cmd = build_command(agent_name, tier, budget, turns, prompt, tools, output_format="text")

        if dry_run:
            if json_output:
                print(json.dumps({
                    "command": cmd,
                    "agent": agent_name,
                }, indent=2))
            else:
                print(core.shlex_join(cmd))
            return core.EXIT_OK

        core.header(f"openstation run {agent_name}")
        core.detail("Agent", agent_name)
        print(file=sys.stderr)
        core.hint(f"Launching {core.shlex_join(cmd[:4])}...")

        os.chdir(str(root))
        os.execvp(cmd[0], cmd)
        return core.EXIT_OK  # unreachable
