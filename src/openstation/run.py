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
        # Parse aliases (inline YAML list like [pm, manager])
        aliases = []
        alias_raw = fm.get("aliases", "")
        if alias_raw:
            parsed = core.parse_inline_list(alias_raw)
            if parsed is not None:
                aliases = parsed
            elif alias_raw:
                aliases = [alias_raw]
        # Also check multi-line list form
        if not aliases:
            aliases = core.parse_frontmatter_list(text, "aliases")

        agents.append({
            "name": fm.get("name", entry.stem),
            "description": desc,
            "aliases": aliases,
        })
    return agents


def resolve_agent_alias(root, prefix, name):
    """Resolve an agent name or alias to the canonical agent name.

    Returns (canonical_name, error_message). If no alias match is found,
    returns the original name unchanged (so callers can proceed to
    normal not-found handling).
    """
    agents = discover_agents(root, prefix)

    # Check if it's already a canonical name
    for a in agents:
        if a["name"] == name:
            return name, None

    # Check aliases; also detect duplicates
    matches = []
    for a in agents:
        if name in a.get("aliases", []):
            matches.append(a["name"])

    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"Alias '{name}' is ambiguous — matches: {', '.join(matches)}"

    # No match — return original name for downstream not-found handling
    return name, None


def format_agents_table(agents):
    """Format agents as an aligned table."""
    if not agents:
        return ""
    headers = ["Name", "Aliases", "Description"]
    keys = ["name", "aliases", "description"]
    mins = [10, 7, 20]

    def _cell(agent, key):
        val = agent.get(key, "")
        if key == "aliases" and isinstance(val, list):
            return ", ".join(val) if val else ""
        return str(val)

    widths = [max(mins[i], len(headers[i])) for i in range(len(headers))]
    for a in agents:
        for i, k in enumerate(keys):
            widths[i] = max(widths[i], len(_cell(a, k)))

    def fmt_row(values):
        parts = []
        for i, v in enumerate(values):
            parts.append(str(v).ljust(widths[i]))
        return "   ".join(parts)

    lines = [fmt_row(headers)]
    lines.append(fmt_row(["-" * widths[i] for i in range(len(headers))]))
    for a in agents:
        lines.append(fmt_row([_cell(a, k) for k in keys]))
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


def build_command(agent_name, budget, turns, prompt, tools,
                  output_format="json", attached=False,
                  dangerously_skip_permissions=False,
                  worktree=None):
    """Assemble the claude CLI argv."""
    if attached:
        cmd = ["claude"]
        if worktree:
            cmd.extend(["--worktree", worktree])
        cmd.extend(["--agent", agent_name])
        if dangerously_skip_permissions:
            cmd.append("--dangerously-skip-permissions")
        cmd.append("--allowedTools")
        cmd.extend(tools)
        if prompt:
            cmd.extend(["--", prompt])  # -- separates options from positional prompt
        return cmd

    # Detached (autonomous) mode
    cmd = ["claude"]
    if worktree:
        cmd.extend(["--worktree", worktree])
    cmd.extend([
        "-p", prompt,
        "--agent", agent_name,
    ])
    if dangerously_skip_permissions:
        cmd.append("--dangerously-skip-permissions")
    cmd.append("--allowedTools")
    cmd.extend(tools)
    cmd.extend([
        "--max-budget-usd", str(budget),
        "--max-turns", str(turns),
        "--output-format", output_format,
    ])
    if output_format == "stream-json":
        cmd.append("--verbose")
    return cmd


# --- Session ID extraction ----------------------------------------------------

def extract_session_id(line):
    """Extract session_id from a stream-json line. Returns str or None."""
    try:
        obj = json.loads(line)
        if isinstance(obj, dict) and "session_id" in obj:
            return obj["session_id"]
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def _extract_result_text(line):
    """Extract the result text from a stream-json result line. Returns str or None."""
    try:
        obj = json.loads(line)
        if isinstance(obj, dict) and obj.get("type") == "result":
            return obj.get("result", "")
    except (json.JSONDecodeError, TypeError, ValueError):
        pass
    return None


def _stream_and_capture(cmd, cwd, log_file):
    """Run cmd with stream-json, write stdout to log_file, return (returncode, session_id, result_text)."""
    session_id = None
    result_text = None
    with open(log_file, "w") as f:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, cwd=str(cwd))
        for raw_line in proc.stdout:
            line = raw_line.decode("utf-8", errors="replace")
            f.write(line)
            if session_id is None:
                session_id = extract_session_id(line)
            rt = _extract_result_text(line)
            if rt is not None:
                result_text = rt
        proc.wait()
    rc = proc.returncode if proc.returncode == 0 else core.EXIT_AGENT_ERROR
    return rc, session_id, result_text


# --- Execution ----------------------------------------------------------------

def run_single_task(root, prefix, task_spec, task_name, budget, turns, dry_run,
                    json_output=False, dangerously_skip_permissions=False,
                    worktree=None, exec_cwd=None):
    """Execute one task: resolve agent, build command, launch. Returns (exit_code, session_id)."""
    task_spec = Path(task_spec)

    try:
        text = task_spec.read_text(encoding="utf-8")
    except OSError:
        core.err(f"Task spec missing: {task_spec}")
        return core.EXIT_USAGE, None
    fm = core.parse_frontmatter(text)
    agent = fm.get("assignee", "")
    if not agent:
        core.err(f"No agent assigned to task: {task_name}")
        return core.EXIT_USAGE, None

    core.detail("agent", agent)

    agent_spec = find_agent_spec(root, prefix, agent)
    if agent_spec is None:
        core.err(f"Agent spec not found: {agent}")
        core.err("  hint: check agents/ directory for available agent specs")
        return core.EXIT_NOT_FOUND, None

    tools = parse_allowed_tools(agent_spec)
    if not tools:
        core.err(f"No allowed-tools found in agent spec: {agent_spec}")
        core.err("  hint: add an 'allowed-tools:' list to the agent's frontmatter")
        return core.EXIT_USAGE, None

    task_path = task_spec if worktree else f"artifacts/tasks/{task_name}.md"
    prompt = (
        f"Execute task {task_name}. Read its spec at "
        f"{task_path} and work through "
        f"the requirements."
    )
    if worktree and exec_cwd is not None and exec_cwd.resolve() != root.resolve():
        prompt += (
            f" Artifacts are in the main repo at `{root}`;"
            f" use CLI commands to access them."
        )
    cmd = build_command(agent, budget, turns, prompt, tools, output_format="stream-json",
                        dangerously_skip_permissions=dangerously_skip_permissions,
                        worktree=worktree)

    if dry_run:
        if json_output:
            print(json.dumps({
                "command": cmd,
                "task": task_name,
                "agent": agent,
            }, indent=2))
        else:
            print(core.shlex_join(cmd))
        return core.EXIT_OK, None

    core.hint(f"Launching {core.shlex_join(cmd[:4])}...")

    log_dir = root / prefix / "artifacts" / "logs" if prefix else root / "artifacts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{task_name}.jsonl"

    cwd = exec_cwd if exec_cwd is not None else root
    rc, session_id, result_text = _stream_and_capture(cmd, cwd, log_file)
    core.detail("log", str(log_file.relative_to(root)))
    if session_id:
        core.detail("session", session_id)
    if result_text:
        print(result_text, file=sys.stderr)
    return rc, session_id


def _exec_or_run(root, prefix, tasks_dir, task_name, agent_name_override, budget, turns,
                  dry_run, json_output=False, attached=False,
                  dangerously_skip_permissions=False,
                  worktree=None, exec_cwd=None):
    """Execute a single task with stream-json capture."""
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

    task_path = str(spec) if worktree else f"artifacts/tasks/{task_name}.md"
    prompt = (
        f"Execute task {task_name}. Read its spec at "
        f"{task_path} and work through "
        f"the requirements."
    )
    if worktree and exec_cwd is not None and Path(exec_cwd).resolve() != root.resolve():
        prompt += (
            f" Artifacts are in the main repo at `{root}`;"
            f" use CLI commands to access them."
        )

    if attached:
        cmd = build_command(agent, budget, turns, prompt, tools, attached=True,
                            dangerously_skip_permissions=dangerously_skip_permissions,
                            worktree=worktree)
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
        core.header(f"openstation run --task {task_name} --attached")
        core.detail("Task", task_name)
        core.detail("Agent", agent)
        core.detail("Mode", "attached")
        os.execvp(cmd[0], cmd)
        return core.EXIT_OK  # unreachable

    cmd = build_command(agent, budget, turns, prompt, tools, output_format="stream-json",
                        dangerously_skip_permissions=dangerously_skip_permissions,
                        worktree=worktree)

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
    core.detail("Mode", "detached")
    print(file=sys.stderr)
    core.hint(f"Launching {core.shlex_join(cmd[:4])}...")

    log_dir = root / prefix / "artifacts" / "logs" if prefix else root / "artifacts" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"{task_name}.jsonl"

    cwd = exec_cwd if exec_cwd is not None else root
    os.chdir(str(cwd))
    rc, session_id, result_text = _stream_and_capture(cmd, cwd, log_file)

    if result_text:
        print(result_text, file=sys.stderr)
    print(file=sys.stderr)
    core.detail("log", str(log_file.relative_to(root)))
    if session_id:
        core.detail("session", session_id)
    core.tips_block(session_id=session_id, task_name=task_name)

    return rc


# --- Command handlers ---------------------------------------------------------

def cmd_agents_list(args, root, prefix):
    """Handle 'agents list' (and bare 'agents')."""
    agents = discover_agents(root, prefix)
    agents.sort(key=lambda a: a["name"])

    if getattr(args, "json", False):
        print(json.dumps(agents, indent=2))
    elif getattr(args, "quiet", False):
        for a in agents:
            print(a["name"])
    else:
        output = format_agents_table(agents)
        if output:
            print(output)


def _find_agent_artifact(root, prefix, name):
    """Locate an agent spec in artifacts/agents/. Returns Path or None."""
    if prefix:
        p = Path(root) / prefix / "artifacts" / "agents" / f"{name}.md"
    else:
        p = Path(root) / "artifacts" / "agents" / f"{name}.md"
    return p if p.is_file() else None


def _agent_not_found(name, root, prefix):
    """Print not-found error with available agents hint. Returns exit code."""
    core.err(f"Agent not found: {name}")
    agents = discover_agents(root, prefix)
    if agents:
        parts = []
        for a in sorted(agents, key=lambda a: a["name"]):
            aliases = a.get("aliases", [])
            if aliases:
                parts.append(f"{a['name']} ({', '.join(aliases)})")
            else:
                parts.append(a["name"])
        core.err(f"  available: {', '.join(parts)}")
    return core.EXIT_NOT_FOUND


def cmd_agents_show(args, root, prefix):
    """Handle 'agents show <name>'."""
    name, alias_err = resolve_agent_alias(root, prefix, args.name)
    if alias_err:
        core.err(alias_err)
        return core.EXIT_USAGE
    spec_path = _find_agent_artifact(root, prefix, name)
    if spec_path is None:
        return _agent_not_found(name, root, prefix)

    text = spec_path.read_text(encoding="utf-8")

    if getattr(args, "editor", False):
        editor = os.environ.get("EDITOR", "vim")
        os.execvp(editor, [editor, str(spec_path)])
        return core.EXIT_OK  # unreachable

    if getattr(args, "json", False):
        fm = core.parse_frontmatter_for_json(text)
        fm["body"] = core.extract_body(text)
        print(json.dumps(fm, indent=2))
    else:
        print(text)
    return core.EXIT_OK


def cmd_run(args, root, prefix):
    """Handle the run subcommand."""
    exec_cwd = Path.cwd()
    core.set_quiet(getattr(args, "quiet", False))
    core.set_run_start(time.time())

    agent_name = args.agent
    task_ref = args.task

    if agent_name and not task_ref and re.match(r'^\d', agent_name):
        task_ref = agent_name
        agent_name = None

    verify = getattr(args, "verify", False)

    if agent_name and task_ref and not verify:
        core.err("Specify either an agent name or --task, not both")
        return core.EXIT_USAGE
    if not agent_name and not task_ref:
        core.err("Agent name or --task is required")
        return core.EXIT_USAGE

    if not shutil.which("claude"):
        core.err("claude CLI not found on $PATH")
        core.err("  hint: install Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code")
        return core.EXIT_NO_CLAUDE

    attached = getattr(args, "attached", False)
    budget = args.budget
    turns = args.turns
    dry_run = args.dry_run
    force = args.force
    max_tasks = args.max_tasks
    json_output = getattr(args, "json", False)
    skip_perms = getattr(args, "dangerously_skip_permissions", False)
    worktree = getattr(args, "worktree", None)

    # --- --verify mode ---
    if verify:
        if not task_ref:
            core.err("--verify requires --task")
            return core.EXIT_USAGE

        task_name, error, code = tasks.resolve_task(root, prefix, task_ref)
        if error:
            core.err(error)
            return code

        tdir = core.tasks_dir_path(root, prefix)
        spec = tdir / f"{task_name}.md"

        try:
            text = spec.read_text(encoding="utf-8")
        except OSError:
            core.err(f"Task spec missing: {spec}")
            return core.EXIT_USAGE
        fm = core.parse_frontmatter(text)
        task_status = fm.get("status", "")
        if task_status != "review":
            core.err(f"Task {task_name} has status '{task_status}' (expected 'review')")
            return core.EXIT_TASK_NOT_READY

        # Agent resolution (highest to lowest priority):
        #   1. --agent CLI argument
        #   2. Task owner field (skip if "user" or empty)
        #   3. settings.verify.agent (project-level default)
        #   4. Hardcoded fallback: project-manager
        explicit_agent = getattr(args, "verify_agent", None)
        if explicit_agent:
            verify_agent = explicit_agent
        elif agent_name:
            verify_agent = agent_name
        else:
            task_owner = fm.get("owner", "")
            if task_owner and task_owner != "user":
                verify_agent = task_owner
            else:
                from openstation import hooks
                settings = hooks.load_settings(root, prefix)
                verify_cfg = settings.get("verify", {})
                if isinstance(verify_cfg, dict) and verify_cfg.get("agent"):
                    verify_agent = verify_cfg["agent"]
                else:
                    verify_agent = "project-manager"

        verify_agent, alias_err = resolve_agent_alias(root, prefix, verify_agent)
        if alias_err:
            core.err(alias_err)
            return core.EXIT_USAGE

        agent_spec = find_agent_spec(root, prefix, verify_agent)
        if agent_spec is None:
            core.err(f"Agent spec not found: {verify_agent}")
            core.err("  hint: check agents/ directory for available agent specs")
            return core.EXIT_NOT_FOUND

        tools = parse_allowed_tools(agent_spec)
        if not tools:
            core.err(f"No allowed-tools found in agent spec: {agent_spec}")
            core.err("  hint: add an 'allowed-tools:' list to the agent's frontmatter")
            return core.EXIT_USAGE

        if worktree is True:
            worktree = task_name

        prompt = f"/openstation.verify {task_name}"
        cmd = build_command(verify_agent, budget, turns, prompt, tools,
                            attached=attached,
                            dangerously_skip_permissions=skip_perms,
                            worktree=worktree)

        if dry_run:
            if json_output:
                print(json.dumps({
                    "command": cmd,
                    "task": task_name,
                    "agent": verify_agent,
                    "mode": "verify",
                }, indent=2))
            else:
                print(core.shlex_join(cmd))
            return core.EXIT_OK

        core.header(f"openstation run --task {task_name} --verify")
        core.detail("Task", task_name)
        core.detail("Agent", verify_agent)
        core.detail("Mode", "verify")
        if attached:
            os.execvp(cmd[0], cmd)
            return core.EXIT_OK  # unreachable

        # Detached verify
        log_dir = root / prefix / "artifacts" / "logs" if prefix else root / "artifacts" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / f"{task_name}.jsonl"
        os.chdir(str(exec_cwd))
        rc, session_id, result_text = _stream_and_capture(cmd, exec_cwd, log_file)
        if result_text:
            print(result_text, file=sys.stderr)
        core.detail("log", str(log_file.relative_to(root)))
        if session_id:
            core.detail("session", session_id)
        core.tips_block(session_id=session_id, task_name=task_name)
        return rc

    # --- Attached mode incompatibility checks ---
    if attached:
        if json_output:
            core.err("JSON output not supported in attached mode")
            return core.EXIT_USAGE
        if getattr(args, "quiet", False):
            core.err("Quiet mode not supported in attached mode")
            return core.EXIT_USAGE
        if args.budget != DEFAULT_BUDGET:
            core.warn("--budget is ignored in attached mode")
        if args.turns != DEFAULT_TURNS:
            core.warn("--turns is ignored in attached mode")
        if args.max_tasks != DEFAULT_MAX_TASKS:
            core.warn("--max-tasks is ignored in attached mode")

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

        # Derive worktree name when --worktree given without a value
        if worktree is True:
            worktree = task_name

        core.header(f"openstation run --task {task_name}")
        core.info(f"Task collection: {task_name}")

        subtasks = tasks.find_ready_subtasks(tdir, task_name, force=force)

        if attached and subtasks:
            core.err(
                f"Attached mode requires a single task. "
                f"This task has {len(subtasks)} ready subtask(s). "
                f"Use --task <subtask-id> to target one."
            )
            return core.EXIT_USAGE

        if subtasks:
            core.info(f"Found {len(subtasks)} ready subtask(s)")
            completed = 0
            failed_count = 0
            remaining = len(subtasks)
            rc = core.EXIT_OK
            last_session_id = None

            for sub_spec, sub_name in subtasks:
                if completed >= max_tasks:
                    break
                run_total = min(len(subtasks), max_tasks)
                core.step(completed + 1, run_total, sub_name)
                start = time.time()
                rc, sid = run_single_task(root, prefix, sub_spec, sub_name, budget, turns,
                                          dry_run, json_output=json_output,
                                          dangerously_skip_permissions=skip_perms,
                                          worktree=worktree, exec_cwd=exec_cwd)
                elapsed = time.time() - start
                if sid:
                    last_session_id = sid
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
                session_id=last_session_id,
                task_name=task_name,
            )
            return core.EXIT_OK if completed > 0 else core.EXIT_AGENT_ERROR
        else:
            core.info("No subtasks found, executing task directly")
            return _exec_or_run(root, prefix, tdir, task_name, agent_name, budget, turns,
                                dry_run, json_output=json_output, attached=attached,
                                dangerously_skip_permissions=skip_perms,
                                worktree=worktree, exec_cwd=exec_cwd)
    else:
        # --- BY-AGENT MODE ---
        # Resolve alias to canonical agent name
        agent_name, alias_err = resolve_agent_alias(root, prefix, agent_name)
        if alias_err:
            core.err(alias_err)
            return core.EXIT_USAGE

        # Derive worktree name when --worktree given without a value
        if worktree is True:
            worktree = agent_name

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

        if attached:
            cmd = build_command(agent_name, budget, turns, None, tools, attached=True,
                                dangerously_skip_permissions=skip_perms,
                                worktree=worktree)
            if dry_run:
                if json_output:
                    print(json.dumps({
                        "command": cmd,
                        "agent": agent_name,
                    }, indent=2))
                else:
                    print(core.shlex_join(cmd))
                return core.EXIT_OK
            core.header(f"openstation run {agent_name} --attached")
            core.detail("Agent", agent_name)
            core.detail("Mode", "attached")
            os.chdir(str(exec_cwd))
            os.execvp(cmd[0], cmd)
            return core.EXIT_OK  # unreachable

        prompt = "Execute your ready tasks."
        cmd = build_command(agent_name, budget, turns, prompt, tools, output_format="text",
                            dangerously_skip_permissions=skip_perms,
                            worktree=worktree)

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

        os.chdir(str(exec_cwd))
        os.execvp(cmd[0], cmd)
        return core.EXIT_OK  # unreachable
