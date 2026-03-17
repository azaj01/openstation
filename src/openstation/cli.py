"""Entry point: argparse definition, subcommand routing, and main()."""

import argparse
import os
import sys

from openstation import __version__ as VERSION
from openstation import core
from openstation import tasks
from openstation import run
from openstation import init
from openstation import artifacts
from openstation import hooks


def _command_key(args):
    """Derive the defaults lookup key from parsed args.

    Top-level commands use their name directly (``"show"``,
    ``"list"``).  Nested sub-actions use dot notation
    (``"agents.show"``, ``"artifacts.list"``).
    """
    cmd = args.command
    # Normalize aliases
    if cmd == "ag":
        cmd = "agents"
    elif cmd == "art":
        cmd = "artifacts"

    for attr in ("agents_action", "artifacts_action"):
        action = getattr(args, attr, None)
        if action:
            return f"{cmd}.{action}"
    return cmd


# Boolean flags use store_true (default False).
# String flags use None or "" as their unset sentinel.
_UNSET_SENTINELS = {False, None, ""}


# Map short flags to their argparse attribute names.
_SHORT_TO_ATTR = {
    "j": "json", "v": "vim", "q": "quiet", "a": "attached",
    "w": "worktree", "f": "force",
}


def _explicit_flags(argv=None):
    """Return flag names explicitly passed on the command line.

    Scans *argv* (default: ``sys.argv[1:]``) for ``--flag`` and
    short ``-f`` tokens.  Returns attribute-style names (dashes
    replaced with underscores) so they match argparse attributes.
    """
    tokens = argv if argv is not None else sys.argv[1:]
    flags = set()
    for tok in tokens:
        if tok == "--":
            break
        if tok.startswith("--"):
            name = tok.split("=", 1)[0].lstrip("-").replace("-", "_")
            flags.add(name)
        elif tok.startswith("-") and len(tok) == 2:
            short = tok.lstrip("-")
            flags.add(_SHORT_TO_ATTR.get(short, short))
    return flags


def _apply_cli_defaults(args, settings, argv=None):
    """Merge ``settings.defaults.<command>`` into *args*.

    Only fills in values the user did not explicitly set on the
    command line.  A flag is considered unset when its value is
    ``False``, ``None``, or ``""`` **and** it was not passed in
    ``sys.argv``.  This prevents defaults from overriding flags
    in mutually exclusive groups where the user chose a different
    option.
    """
    defaults = settings.get("defaults", {})
    if not isinstance(defaults, dict):
        return

    key = _command_key(args)
    cmd_defaults = defaults.get(key, {})
    if not isinstance(cmd_defaults, dict):
        return

    explicit = _explicit_flags(argv)

    for flag, value in cmd_defaults.items():
        if flag in explicit:
            continue
        current = getattr(args, flag, _UNSET_SENTINELS)
        if current not in _UNSET_SENTINELS:
            continue
        # For boolean True defaults, skip if the user already
        # explicitly set another boolean flag to True (respects
        # mutually exclusive groups like --json / --vim / --quiet).
        if value is True and any(
            f in explicit and getattr(args, f, False) is True
            for f in vars(args)
        ):
            continue
        setattr(args, flag, value)


def main():
    fmt = argparse.RawDescriptionHelpFormatter

    parser = argparse.ArgumentParser(
        prog="openstation",
        description="CLI for the Open Station task vault.",
        formatter_class=fmt,
    )
    parser.add_argument(
        "--version", action="version", version=f"openstation {VERSION}",
    )
    sub = parser.add_subparsers(dest="command")

    # list
    list_p = sub.add_parser("list", help="List tasks", formatter_class=fmt, epilog="""\
examples:
  openstation list                          # active tasks (ready + in-progress + review)
  openstation list --status all             # all tasks regardless of status
  openstation list --status ready --assignee researcher
  openstation list -q --status ready        # one task name per line (pipe-friendly)
  openstation list --json                   # JSON array of task objects
  openstation list --vim                    # open active tasks in vim
  openstation list --status ready --vim     # open only ready tasks in vim
  openstation list 0042                     # show task 0042 and its subtask tree""")
    list_p.add_argument("filter", nargs="?", default=None,
                        help="Task ID/slug or assignee name (auto-detected)")
    list_p.add_argument("--status", default=None,
                        help="Filter by status: backlog|ready|in-progress|review|done|failed|active|all "
                             "(default: active = ready + in-progress + review)")
    list_p.add_argument("--assignee", default="",
                        help="Filter by assignee (exact match)")
    list_output = list_p.add_mutually_exclusive_group()
    list_output.add_argument("-j", "--json", action="store_true",
                        help="Emit output as a JSON array of task objects")
    list_output.add_argument("-q", "--quiet", action="store_true",
                        help="Emit one task name per line, no header (pipe-friendly)")
    list_output.add_argument("-v", "--vim", action="store_true",
                        help="Open matching task files in vim as a buffer list")
    list_p.add_argument("--type", default=None,
                        help="Filter by type: feature|research|spec|implementation|documentation")

    # agents (with sub-actions: list, show)
    agents_p = sub.add_parser("agents", aliases=["ag"], help="Agent operations", formatter_class=fmt, epilog="""\
examples:
  openstation agents                        # list all agents (default)
  openstation agents list                   # same as bare 'agents'
  openstation agents list --json            # JSON array of agent objects
  openstation agents list --quiet           # one name per line (pipe-friendly)
  openstation agents show researcher        # print full agent spec
  openstation agents show researcher --json # frontmatter + body as JSON
  openstation agents show researcher --vim  # open in editor""")
    agents_sub = agents_p.add_subparsers(dest="agents_action")

    # agents list (also the default when no sub-action given)
    agents_list_p = agents_sub.add_parser("list", help="List agents")
    agents_list_output = agents_list_p.add_mutually_exclusive_group()
    agents_list_output.add_argument("-j", "--json", action="store_true",
                        help="Emit JSON array of agent objects")
    agents_list_output.add_argument("-q", "--quiet", action="store_true",
                        help="One agent name per line (pipe-friendly)")

    # agents show
    agents_show_p = agents_sub.add_parser("show", help="Show agent spec")
    agents_show_p.add_argument("name", help="Agent name")
    agents_show_output = agents_show_p.add_mutually_exclusive_group()
    agents_show_output.add_argument("-j", "--json", action="store_true",
                        help="Emit parsed frontmatter + body as JSON object")
    agents_show_output.add_argument("-v", "--vim", action="store_true",
                        help="Open the agent spec file in editor")

    # artifacts (with sub-actions: list, show)
    artifacts_p = sub.add_parser("artifacts", aliases=["art"], help="Browse non-task artifacts", formatter_class=fmt, epilog="""\
examples:
  openstation artifacts                       # list all non-task artifacts (default)
  openstation artifacts list                  # same as bare 'artifacts'
  openstation artifacts list --kind research  # only research artifacts
  openstation artifacts list --json           # JSON array of artifact objects
  openstation artifacts list --quiet          # one name per line (pipe-friendly)
  openstation artifacts show cli-feature-spec # print full artifact
  openstation artifacts show cli-feature-spec --json  # frontmatter + body as JSON
  openstation artifacts show cli-feature-spec --vim   # open in editor""")
    artifacts_sub = artifacts_p.add_subparsers(dest="artifacts_action")

    # artifacts list (also the default when no sub-action given)
    artifacts_list_p = artifacts_sub.add_parser("list", help="List artifacts")
    artifacts_list_p.add_argument("--kind", default=None,
                        help="Filter by kind: agents, research, specs")
    artifacts_list_output = artifacts_list_p.add_mutually_exclusive_group()
    artifacts_list_output.add_argument("-j", "--json", action="store_true",
                        help="Emit JSON array of artifact objects")
    artifacts_list_output.add_argument("-q", "--quiet", action="store_true",
                        help="One artifact name per line (pipe-friendly)")

    # artifacts show
    artifacts_show_p = artifacts_sub.add_parser("show", help="Show an artifact")
    artifacts_show_p.add_argument("name", help="Artifact name (resolved across research/, specs/, agents/)")
    artifacts_show_output = artifacts_show_p.add_mutually_exclusive_group()
    artifacts_show_output.add_argument("-j", "--json", action="store_true",
                        help="Emit parsed frontmatter + body as JSON object")
    artifacts_show_output.add_argument("-v", "--vim", action="store_true",
                        help="Open the artifact file in editor")

    # show
    show_p = sub.add_parser("show", help="Show a task spec", formatter_class=fmt, epilog="""\
examples:
  openstation show 0042                     # show by numeric ID
  openstation show 42                       # short ID (auto-padded)
  openstation show 0042-cli-improvements    # show by full name
  openstation show cli-improvements         # show by slug
  openstation show 0042 --json              # frontmatter + body as JSON
  openstation show 0042 --vim               # open in vim with markdown support""")
    show_p.add_argument("task", help="Task ID or slug (e.g. 0023, 23, or cli-feature-spec)")
    show_p.add_argument("-j", "--json", action="store_true",
                        help="Emit parsed frontmatter and body as a JSON object")
    show_p.add_argument("-v", "--vim", action="store_true",
                        help="Open the task file in vim (markdown plugins work)")

    # create
    create_p = sub.add_parser("create", help="Create a new task", formatter_class=fmt, epilog="""\
examples:
  openstation create "add login page"
  openstation create "fix auth bug" --assignee developer --status ready
  openstation create "child task" --parent 0042""")
    create_p.add_argument("description", help="Task description (free text)")
    create_p.add_argument("--assignee", default="", help="Agent name to assign")
    create_p.add_argument("--owner", default="user", help="Who verifies (default: user)")
    create_p.add_argument("--status", default=None,
                          help="Initial status: backlog or ready (default: inherit from parent, else backlog)")
    create_p.add_argument("--type", default="feature",
                          help="Task type: feature|research|spec|implementation|documentation (default: feature)")
    create_p.add_argument("--parent", default="",
                          help="Parent task name (wikilink added automatically)")

    # status
    status_p = sub.add_parser("status", help="Change a task's status", formatter_class=fmt, epilog="""\
examples:
  openstation status 0042                   # interactive picker
  openstation status 0042 ready             # backlog → ready
  openstation status 42 in-progress         # short ID works
  openstation status cli-improvements review

valid transitions:
  backlog → ready → in-progress → review → done
                                  review → failed → in-progress""")
    status_p.add_argument("task", help="Task ID or slug")
    status_p.add_argument("new_status", nargs="?", default=None,
                          help="Target status (omit for interactive picker): backlog|ready|in-progress|review|done|failed")
    status_p.add_argument("-f", "--force", action="store_true",
                          help="Bypass transition validation (any status → any status)")

    # run
    run_p = sub.add_parser("run", help="Launch an agent", formatter_class=fmt, epilog="""\
Two modes of operation:

  By-agent:  openstation run <agent>          Execute agent's ready tasks
  By-task:   openstation run --task <id>      Execute a specific task

examples:
  openstation run researcher --attached       # interactive agent session
  openstation run --task 0042 --attached      # interactive task session
  openstation run --task 0042                 # autonomous (detached)
  openstation run --task 0042 --attached --dry-run  # preview attached command
  openstation run researcher --dry-run        # show command without executing
  openstation run --task 42 --dry-run --json  # structured JSON dry-run output
  openstation run --task 42 --verify          # launch verification (agent from task owner)
  openstation run --task 42 --verify --attached  # interactive verification""")
    run_p.add_argument("agent", nargs="?", default=None,
                       help="Agent name or task ID (auto-detected: numeric prefix → task)")
    run_p.add_argument("--task", default=None,
                       help="Task ID or slug (explicit, same as positional)")
    run_p.add_argument("-a", "--attached", action="store_true",
                       help="Interactive mode (replace process, no log capture)")
    run_p.add_argument("--budget", type=float, default=run.DEFAULT_BUDGET,
                       help="Max USD per invocation (detached only, default: 5)")
    run_p.add_argument("--turns", type=int, default=run.DEFAULT_TURNS,
                       help="Max turns per invocation (detached only, default: 50)")
    run_p.add_argument("--max-tasks", type=int, default=run.DEFAULT_MAX_TASKS,
                       help="Max subtasks to execute (detached only, default: 1)")
    run_p.add_argument("--force", action="store_true",
                       help="Skip task status checks")
    run_p.add_argument("--dry-run", action="store_true",
                       help="Print command without executing")
    run_p.add_argument("-q", "--quiet", action="store_true",
                       help="Suppress progress output (detached only)")
    run_p.add_argument("-j", "--json", action="store_true",
                       help="Structured JSON dry-run output (detached only)")
    run_p.add_argument("-w", "--worktree",
                       nargs="?", const=True, default=None, metavar="NAME",
                       help="Run in a Claude worktree (optional name, default: auto-derived)")
    run_p.add_argument("--verify", action="store_true",
                       help="Launch verification: resolve agent from task owner, pre-load /openstation.verify")
    run_p.add_argument("--agent", default=None, dest="verify_agent",
                       help="Override agent for --verify (default: task owner)")
    run_p.add_argument("--dangerously-skip-permissions", "-dsp", action="store_true",
                       default=False,
                       help="Pass --dangerously-skip-permissions to claude")

    # init
    init_p = sub.add_parser("init", help="Initialize Open Station in current directory",
                            formatter_class=fmt, epilog="""\
examples:
  openstation init                          # full init with all agents
  openstation init --agents researcher,author
  openstation init --no-agents
  openstation init --user                   # install to ~/.claude/ instead
  openstation init --dry-run                # preview without writing""")
    agent_grp = init_p.add_mutually_exclusive_group()
    agent_grp.add_argument("--agents", default=None, metavar="NAMES",
                           help="Comma-separated agent names to install (default: all)")
    agent_grp.add_argument("--no-agents", action="store_true",
                           help="Skip installing example agent specs")
    init_p.add_argument("--user", action="store_true",
                        help="Install .claude/ files to ~/.claude/ (user-level)")
    init_p.add_argument("--dry-run", action="store_true",
                        help="Show what would be done without writing")
    init_p.add_argument("--force", action="store_true",
                        help="Overwrite user-owned files too")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return core.EXIT_USAGE

    # init operates on CWD, doesn't need find_root()
    if args.command == "init":
        return init.cmd_init(args) or 0

    root, prefix = core.find_root()
    if root is None:
        core.err("not in an Open Station project")
        core.err("  hint: run from a directory containing .openstation/")
        return core.EXIT_NO_PROJECT

    # Apply CLI defaults from settings (human context only)
    if not os.environ.get("CLAUDECODE"):
        settings = hooks.load_settings(root, prefix)
        _apply_cli_defaults(args, settings)

    if args.command == "list":
        return tasks.cmd_list(args, root, prefix) or 0
    elif args.command in ("agents", "ag"):
        action = getattr(args, "agents_action", None)
        if action is None or action == "list":
            return run.cmd_agents_list(args, root, prefix) or 0
        elif action == "show":
            return run.cmd_agents_show(args, root, prefix)
    elif args.command in ("artifacts", "art"):
        action = getattr(args, "artifacts_action", None)
        if action is None or action == "list":
            return artifacts.cmd_artifacts_list(args, root, prefix) or 0
        elif action == "show":
            return artifacts.cmd_artifacts_show(args, root, prefix)
    elif args.command == "show":
        return tasks.cmd_show(args, root, prefix)
    elif args.command == "create":
        return tasks.cmd_create(args, root, prefix)
    elif args.command == "status":
        return tasks.cmd_status(args, root, prefix)
    elif args.command == "run":
        return run.cmd_run(args, root, prefix)
    return core.EXIT_OK
