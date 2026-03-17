"""Task discovery, listing, showing, creating, status transitions, and formatting."""

import datetime
import errno
import json
import os
import re
import sys
from pathlib import Path

from openstation import core

MAX_CREATE_RETRIES = 5
SUBTASK_PREFIX = "  └─"  # kept for backward compat; see _indent_prefix() for depth-aware version


# --- Discovery ----------------------------------------------------------------

def discover_tasks(root, prefix):
    """Scan artifacts/tasks/*.md and return task dicts."""
    tasks_dir = Path(root) / prefix / "artifacts" / "tasks" if prefix else Path(root) / "artifacts" / "tasks"
    tasks = []
    if not tasks_dir.is_dir():
        return tasks
    for entry in sorted(tasks_dir.iterdir()):
        if not entry.is_file() or entry.suffix != ".md":
            continue
        try:
            text = entry.read_text(encoding="utf-8")
        except OSError:
            continue
        fm = core.parse_frontmatter(text)
        if fm.get("kind") != "task":
            continue
        task_name = entry.stem
        parent_raw = fm.get("parent", "")
        parent = core.strip_wikilink(parent_raw) if parent_raw else ""
        tasks.append({
            "id": task_name.split("-", 1)[0],
            "name": task_name,
            "type": fm.get("type", "feature"),
            "status": fm.get("status", ""),
            "assignee": fm.get("assignee", ""),
            "owner": fm.get("owner", ""),
            "parent": parent,
        })
    return tasks


def resolve_task(root, prefix, query):
    """Resolve a task query to a task name. Returns (name, error_msg, exit_code).

    Resolution priority (first match wins):
    1. Exact match (full name)
    2. Zero-padded ID prefix match (e.g. "0058" or "58" → "0058-slug")
    3. Slug match (e.g. "implement-foo" matches "0058-implement-foo")
    """
    tasks_dir = Path(root) / prefix / "artifacts" / "tasks" if prefix else Path(root) / "artifacts" / "tasks"
    if not tasks_dir.is_dir():
        return None, "artifacts/tasks directory not found", 3

    entries = sorted(e.stem for e in tasks_dir.iterdir() if e.is_file() and e.suffix == ".md")

    # 1. Exact match
    if query in entries:
        return query, None, core.EXIT_OK

    # 2. Zero-padded ID prefix match
    padded = query.zfill(4) if query.isdigit() else query
    matches = [e for e in entries if e.startswith(padded)]
    if len(matches) == 1:
        return matches[0], None, core.EXIT_OK
    if len(matches) > 1:
        match_list = "\n".join(f"  {m}" for m in matches)
        return None, f"ambiguous task '{query}', matches:\n{match_list}", core.EXIT_AMBIGUOUS

    # 3. Slug match
    slug_matches = [e for e in entries if "-" in e and e.split("-", 1)[1] == query]
    if not slug_matches:
        slug_matches = [e for e in entries if "-" in e and e.split("-", 1)[1].startswith(query)]
    if len(slug_matches) == 1:
        return slug_matches[0], None, core.EXIT_OK
    if len(slug_matches) > 1:
        match_list = "\n".join(f"  {m}" for m in slug_matches)
        return None, f"ambiguous task '{query}', matches:\n{match_list}", core.EXIT_AMBIGUOUS

    return None, f"task not found: {query}\n  hint: run 'openstation list' to see available tasks", core.EXIT_NOT_FOUND


def find_ready_subtasks(tasks_dir, task_name, force=False):
    """Read the subtasks field from a task's frontmatter and return ready ones.

    Returns a list of (subtask_path, subtask_name) tuples.
    When force=True, returns all subtasks regardless of status.
    """
    tasks_dir = Path(tasks_dir)
    spec = tasks_dir / f"{task_name}.md"
    results = []
    try:
        text = spec.read_text(encoding="utf-8")
    except OSError:
        return results

    subtask_names = core.parse_frontmatter_list(text, "subtasks")
    for sub_name in subtask_names:
        sub_spec = tasks_dir / f"{sub_name}.md"
        if not sub_spec.is_file():
            continue
        if force:
            results.append((sub_spec, sub_name))
        else:
            try:
                sub_text = sub_spec.read_text(encoding="utf-8")
            except OSError:
                continue
            fm = core.parse_frontmatter(sub_text)
            if fm.get("status") == "ready":
                results.append((sub_spec, sub_name))
    return results


def assert_task_ready(spec_path, task_name):
    """Validate that a task's status is 'ready'. Returns (ok, status)."""
    try:
        text = Path(spec_path).read_text(encoding="utf-8")
    except OSError:
        return False, "missing"
    fm = core.parse_frontmatter(text)
    status = fm.get("status", "")
    return status == "ready", status


# --- Formatting ---------------------------------------------------------------

def group_tasks_for_display(tasks):
    """Order tasks so subtasks appear grouped under their parent.

    Returns a list of (task_dict, depth) tuples where depth is an
    integer: 0 for top-level, 1 for direct children, 2 for
    grandchildren, etc.
    """
    by_name = {t["name"]: t for t in tasks}
    children = {}
    for t in tasks:
        parent = t.get("parent", "")
        if parent and parent in by_name:
            children.setdefault(parent, []).append(t)

    top_level = [t for t in tasks
                 if not t.get("parent", "") or t["parent"] not in by_name]
    top_level.sort(key=lambda t: t["id"])

    def collect_descendants(name, depth):
        kids = children.get(name, [])
        kids.sort(key=lambda c: c["id"])
        result = []
        for child in kids:
            result.append((child, depth))
            result.extend(collect_descendants(child["name"], depth + 1))
        return result

    result = []
    for t in top_level:
        result.append((t, 0))
        result.extend(collect_descendants(t["name"], 1))
    return result


def _indent_prefix(depth):
    """Build a tree-drawing prefix for the given nesting depth.

    depth 0 → ""  (top-level)
    depth 1 → "  └─ "
    depth 2 → "    └─ "
    depth N → "  " * N + "└─ "
    """
    if depth <= 0:
        return ""
    return "  " * depth + "└─ "


def format_table(rows):
    """Format task rows as an aligned table."""
    if not rows:
        return ""
    headers = ["ID", "Name", "Status", "Assignee", "Owner"]
    keys = ["id", "name", "status", "assignee", "owner"]
    mins = [4, 10, 7, 8, 5]

    widths = [max(mins[i], len(headers[i])) for i in range(len(headers))]
    for t, depth in rows:
        for i, k in enumerate(keys):
            val = str(t.get(k, ""))
            if depth > 0 and k == "name":
                val = _indent_prefix(depth) + val
            widths[i] = max(widths[i], len(val))

    def fmt_row(values):
        parts = []
        for i, v in enumerate(values):
            parts.append(str(v).ljust(widths[i]))
        return "   ".join(parts)

    lines = [fmt_row(headers)]
    lines.append(fmt_row(["-" * widths[i] for i in range(len(headers))]))
    for t, depth in rows:
        values = []
        for i, k in enumerate(keys):
            val = t.get(k, "")
            if depth > 0 and k == "name":
                val = _indent_prefix(depth) + val
            values.append(val)
        lines.append(fmt_row(values))
    return "\n".join(lines)


def collect_task_tree(tasks, root_name):
    """Return the task named *root_name* and all its descendants."""
    by_name = {t["name"]: t for t in tasks}
    children_map = {}
    for t in tasks:
        parent = t.get("parent", "")
        if parent:
            children_map.setdefault(parent, []).append(t)

    root_task = by_name.get(root_name)
    if not root_task:
        return []

    result = []
    queue = [root_task]
    while queue:
        task = queue.pop(0)
        result.append(task)
        queue.extend(children_map.get(task["name"], []))
    return result


def pull_in_subtasks(filtered_tasks, all_tasks):
    """Include all descendants of *filtered_tasks* from *all_tasks*."""
    children_map = {}
    for t in all_tasks:
        parent = t.get("parent", "")
        if parent:
            children_map.setdefault(parent, []).append(t)

    result_names = {t["name"] for t in filtered_tasks}
    result = list(filtered_tasks)

    def add_descendants(name):
        for child in children_map.get(name, []):
            if child["name"] not in result_names:
                result_names.add(child["name"])
                result.append(child)
                add_descendants(child["name"])

    for t in list(filtered_tasks):
        add_descendants(t["name"])

    return result


# --- Lifecycle ----------------------------------------------------------------

def validate_transition(current, target):
    """Check if (current, target) is a valid lifecycle transition."""
    return (current, target) in core.VALID_TRANSITIONS


def allowed_from(status):
    """Return the set of statuses reachable from the given status."""
    return {t for (s, t) in core.VALID_TRANSITIONS if s == status}


def auto_promote_parent(tasks_dir, task_name, child_new_status):
    """If this task has a parent, ensure the parent's status is high enough.

    Returns a message string if promotion happened, or None.
    """
    spec = tasks_dir / f"{task_name}.md"
    try:
        text = spec.read_text(encoding="utf-8")
    except OSError:
        return None

    fm = core.parse_frontmatter(text)
    parent_raw = fm.get("parent", "")
    if not parent_raw:
        return None

    parent_name = core.strip_wikilink(parent_raw)
    parent_spec = tasks_dir / f"{parent_name}.md"
    if not parent_spec.is_file():
        return None

    try:
        parent_text = parent_spec.read_text(encoding="utf-8")
    except OSError:
        return None

    parent_fm = core.parse_frontmatter(parent_text)
    parent_status = parent_fm.get("status", "")
    min_status = core._MIN_PARENT_STATUS.get(child_new_status)
    if not min_status:
        return None

    parent_rank = core._STATUS_RANK.get(parent_status, 0)
    min_rank = core._STATUS_RANK.get(min_status, 0)

    if parent_rank >= min_rank:
        return None

    current = parent_status
    while core._STATUS_RANK.get(current, 0) < min_rank:
        targets = allowed_from(current)
        next_step = None
        for t in targets:
            if core._STATUS_RANK.get(t, 0) > core._STATUS_RANK.get(current, 0) and core._STATUS_RANK.get(t, 0) <= min_rank:
                if next_step is None or core._STATUS_RANK.get(t, 0) < core._STATUS_RANK.get(next_step, 0):
                    next_step = t
        if not next_step:
            break
        update_frontmatter(parent_spec, current, next_step)
        current = next_step

    if current != parent_status:
        return f"{parent_name}: {parent_status} → {current} (auto-promoted)"
    return None


def update_frontmatter(file_path, old_status, new_status):
    """Replace the status field in a task file's frontmatter."""
    text = file_path.read_text(encoding="utf-8")
    updated = text.replace(
        f"status: {old_status}",
        f"status: {new_status}",
        1,
    )
    file_path.write_text(updated, encoding="utf-8")


def append_frontmatter_list(file_path, key, value):
    """Append a value to a YAML list field in frontmatter."""
    text = file_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    new_item = f'  - "{value}"\n'

    fm_start = None
    fm_end = None
    for i, line in enumerate(lines):
        if line.strip() == "---":
            if fm_start is None:
                fm_start = i
            else:
                fm_end = i
                break

    if fm_start is None or fm_end is None:
        raise ValueError(f"No frontmatter found in {file_path}")

    field_line = None
    last_list_item = None
    for i in range(fm_start + 1, fm_end):
        if lines[i].startswith(f"{key}:"):
            field_line = i
        elif field_line is not None and re.match(r"^\s+-\s+", lines[i]):
            last_list_item = i
        elif field_line is not None and not re.match(r"^\s+-\s+", lines[i]):
            break

    if field_line is not None and last_list_item is not None:
        lines.insert(last_list_item + 1, new_item)
    elif field_line is not None:
        lines.insert(field_line + 1, new_item)
    else:
        lines.insert(fm_end, f"{key}:\n")
        lines.insert(fm_end + 1, new_item)

    file_path.write_text("".join(lines), encoding="utf-8")


# --- Write helpers ------------------------------------------------------------

def next_task_id(tasks_dir):
    """Scan tasks_dir for the highest numeric prefix and return next ID (zero-padded)."""
    max_id = 0
    for entry in tasks_dir.iterdir():
        if entry.suffix != ".md":
            continue
        match = re.match(r"^(\d+)-", entry.name)
        if match:
            max_id = max(max_id, int(match.group(1)))
    return f"{max_id + 1:04d}"


def create_task_file(tasks_dir, slug, content):
    """Create a task file with the next available ID using atomic creation.

    Returns the created Path, or raises RuntimeError.
    """
    for attempt in range(MAX_CREATE_RETRIES):
        tid = next_task_id(tasks_dir)
        filename = f"{tid}-{slug}.md"
        filepath = tasks_dir / filename
        try:
            fd = os.open(
                str(filepath),
                os.O_CREAT | os.O_EXCL | os.O_WRONLY,
                0o644,
            )
            with os.fdopen(fd, "w") as f:
                f.write(content)
            return filepath
        except OSError as e:
            if e.errno == errno.EEXIST:
                continue
            raise
    raise RuntimeError(
        f"Failed to create task after {MAX_CREATE_RETRIES} retries"
    )


# --- Command handlers ---------------------------------------------------------

def cmd_list(args, root, prefix):
    """Handle the list subcommand."""
    all_tasks = discover_tasks(root, prefix)
    tasks = list(all_tasks)

    positional_filter = args.filter
    task_tree_mode = False
    if positional_filter:
        if positional_filter[0].isdigit():
            task_name, error, code = resolve_task(root, prefix, positional_filter)
            if error:
                core.err(error)
                return code
            tasks = collect_task_tree(all_tasks, task_name)
            task_tree_mode = True
        else:
            if not args.assignee:
                args.assignee = positional_filter

    status_filter = args.status
    if status_filter is None:
        status_filter = "all" if task_tree_mode else "active"

    if status_filter == "active":
        tasks = [t for t in tasks if t["status"] in ("ready", "in-progress", "review", "verified")]
    elif status_filter != "all":
        tasks = [t for t in tasks if t["status"] == status_filter]

    if args.assignee:
        tasks = [t for t in tasks if t["assignee"] == args.assignee]

    if getattr(args, "type", None):
        tasks = [t for t in tasks if t.get("type", "feature") == args.type]

    tasks = pull_in_subtasks(tasks, all_tasks)
    rows = group_tasks_for_display(tasks)

    if getattr(args, "editor", False):
        if not rows:
            print("no matching tasks")
            return core.EXIT_OK
        tasks_dir = core.tasks_dir_path(root, prefix)
        files = [str(tasks_dir / f"{t['name']}.md") for t, _depth in rows]
        editor = os.environ.get("EDITOR", "vim")
        os.execvp(editor, [editor] + files)
        return core.EXIT_OK
    elif getattr(args, "json", False):
        task_list = []
        for t, _depth in rows:
            task_list.append({
                "id": t["id"],
                "name": t["name"],
                "type": t.get("type", "feature"),
                "status": t["status"],
                "assignee": t["assignee"],
                "owner": t["owner"],
            })
        print(json.dumps(task_list, indent=2))
    elif getattr(args, "quiet", False):
        for t, _depth in rows:
            print(t["name"])
    else:
        output = format_table(rows)
        if output:
            print(output)


def cmd_show(args, root, prefix):
    """Handle the show subcommand."""
    task_name, error, code = resolve_task(root, prefix, args.task)
    if error:
        core.err(error)
        return code

    tasks_dir = Path(root) / prefix / "artifacts" / "tasks" if prefix else Path(root) / "artifacts" / "tasks"
    spec = tasks_dir / f"{task_name}.md"

    if not spec.exists():
        core.err(f"task spec missing: {task_name}")
        return core.EXIT_NOT_FOUND

    try:
        text = spec.read_text(encoding="utf-8")
    except OSError as e:
        core.err(f"cannot read task: {e}")
        return core.EXIT_NOT_FOUND

    if getattr(args, "json", False):
        fm = core.parse_frontmatter_for_json(text)
        fm["body"] = core.extract_body(text)
        print(json.dumps(fm, indent=2))
    elif getattr(args, "editor", False):
        editor = os.environ.get("EDITOR", "vim")
        os.execvp(editor, [editor, str(spec)])
    else:
        print(text, end="")
    return core.EXIT_OK


def cmd_create(args, root, prefix):
    """Handle the create subcommand."""
    description = args.description
    if not description or not description.strip():
        core.err("description required")
        return core.EXIT_USAGE

    agent = args.assignee or ""
    owner = args.owner or "user"
    task_type = getattr(args, "type", "feature") or "feature"
    explicit_status = args.status
    parent = args.parent or ""

    tasks_dir = core.tasks_dir_path(root, prefix)
    tasks_dir.mkdir(parents=True, exist_ok=True)

    parent_name = None
    if parent:
        parent_name, error, code = resolve_task(root, prefix, parent)
        if error:
            core.err(f"parent task not found: {parent}")
            return core.EXIT_NOT_FOUND

    if explicit_status:
        status = explicit_status
    elif parent_name:
        parent_spec = tasks_dir / f"{parent_name}.md"
        try:
            parent_fm = core.parse_frontmatter(parent_spec.read_text(encoding="utf-8"))
            ps = parent_fm.get("status", "backlog")
            status = ps if ps in ("backlog", "ready") else "backlog"
        except OSError:
            status = "backlog"
    else:
        status = "backlog"

    if status not in ("backlog", "ready"):
        core.err("--status must be 'backlog' or 'ready'")
        return core.EXIT_USAGE

    slug = core.slugify(description)
    title = core.title_from_description(description)
    today = datetime.date.today().isoformat()

    fm_lines = [
        "---",
        "kind: task",
        f"name: PLACEHOLDER",
        f"type: {task_type}",
        f"status: {status}",
        f"assignee: {agent}",
        f"owner: {owner}",
    ]
    if parent_name:
        fm_lines.append(f'parent: "[[{parent_name}]]"')
    fm_lines.append(f"created: {today}")
    fm_lines.append("---")

    body_lines = [
        "",
        f"# {title}",
        "",
        "## Requirements",
        "",
        description.strip(),
        "",
        "## Verification",
        "",
        "- [ ] (placeholder)",
        "",
    ]

    content_template = "\n".join(fm_lines) + "\n" + "\n".join(body_lines)

    try:
        filepath = create_task_file(tasks_dir, slug, "")
    except RuntimeError as e:
        core.err(str(e))
        return core.EXIT_USAGE

    task_name = filepath.stem
    content = content_template.replace("name: PLACEHOLDER", f"name: {task_name}")
    filepath.write_text(content, encoding="utf-8")

    if parent_name:
        parent_path = tasks_dir / f"{parent_name}.md"
        try:
            append_frontmatter_list(parent_path, "subtasks", f"[[{task_name}]]")
        except Exception:
            print(
                f"warning: created {task_name} but failed to update parent subtasks list",
                file=sys.stderr,
            )

    if parent_name:
        msg = auto_promote_parent(tasks_dir, task_name, status)
        if msg:
            print(msg, file=sys.stderr)

    print(task_name)
    return core.EXIT_OK


def _term_menu_picker(task_name, current, options):
    """Arrow-key menu using simple-term-menu. Returns chosen status or None."""
    from simple_term_menu import TerminalMenu

    title = f"{task_name}  [current: {current}]"
    labels = [f"  {opt}  " for opt in options]
    menu = TerminalMenu(
        labels,
        title=title,
        menu_cursor_style=("fg_cyan", "bold"),
        menu_highlight_style=("bg_cyan", "fg_black", "bold"),
        status_bar=f"current status: {current}",
        status_bar_style=("fg_yellow", "italic"),
    )
    idx = menu.show()
    if idx is None:
        return None
    return options[idx]


def _numbered_picker(task_name, current, options):
    """Fallback numbered picker for environments without arrow-key support."""
    print(f"{task_name}: current status is \033[1m{current}\033[0m")
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")

    try:
        choice = input("select> ")
    except (EOFError, KeyboardInterrupt):
        return None

    try:
        idx = int(choice)
    except ValueError:
        core.err(f"invalid choice: {choice}")
        return "INVALID"

    if idx < 1 or idx > len(options):
        core.err(f"choice out of range: {idx} (1-{len(options)})")
        return "INVALID"

    return options[idx - 1]


def _interactive_status_picker(task_name, current, *, force=False):
    """Show an interactive picker for status transitions.

    Uses simple-term-menu for arrow-key navigation when available,
    falls back to a numbered picker otherwise.

    When *force* is True, all statuses (except the current one) are
    shown, not just valid transitions.

    Returns the chosen status string, or None if no valid transition
    or user cancels.  Returns "INVALID" on bad input (numbered fallback).
    """
    if force:
        options = sorted(s for s in core.VALID_STATUSES if s != current)
    else:
        options = sorted(allowed_from(current))
    if not options:
        print(f"{task_name}: status is {current} — no valid transitions")
        return None

    try:
        return _term_menu_picker(task_name, current, options)
    except Exception:
        # Fall back to numbered picker if term menu fails
        return _numbered_picker(task_name, current, options)


def cmd_status(args, root, prefix):
    """Handle the status subcommand."""
    query = args.task
    new_status = args.new_status
    force = getattr(args, "force", False)

    # Resolve task first (needed for both interactive and direct paths)
    task_name, error, code = resolve_task(root, prefix, query)
    if error:
        core.err(error)
        return code

    tasks_dir = core.tasks_dir_path(root, prefix)
    spec = tasks_dir / f"{task_name}.md"

    try:
        text = spec.read_text(encoding="utf-8")
    except OSError:
        core.err(f"cannot read task: {spec}")
        return core.EXIT_NOT_FOUND

    fm = core.parse_frontmatter(text)
    current = fm.get("status", "")

    # Interactive picker when new_status is omitted
    if new_status is None:
        if not sys.stdin.isatty():
            core.err("new_status argument required in non-interactive mode")
            core.err("  usage: openstation status <task> <new-status>")
            return core.EXIT_USAGE
        new_status = _interactive_status_picker(task_name, current, force=force)
        if new_status is None:
            return core.EXIT_OK
        if new_status == "INVALID":
            return core.EXIT_USAGE

    if new_status not in core.VALID_STATUSES:
        core.err(f"invalid status: {new_status}")
        return core.EXIT_USAGE

    if current == new_status:
        print(f"{task_name}: already at {new_status}")
        return core.EXIT_OK

    if not validate_transition(current, new_status):
        if force:
            core.warn(f"forced transition {current} → {new_status} (not a valid lifecycle transition)")
        else:
            if current == "review" and new_status == "done":
                core.err(f"invalid transition: review → done")
                core.err(f"  task is in review — run verification first before marking done")
                core.err(f"  use: openstation run --task {task_name} --verify --attached")
                return core.EXIT_INVALID_TRANSITION
            allowed = allowed_from(current)
            allowed_str = ", ".join(sorted(allowed)) if allowed else "(none)"
            core.err(f"invalid transition: {current} → {new_status}")
            core.err(f"       allowed from {current}: {allowed_str}")
            return core.EXIT_INVALID_TRANSITION

    # --- Hook execution (pre-transition) ---
    from openstation import hooks
    hook_err = hooks.run_matched(
        root, prefix, task_name, current, new_status, spec, phase="pre",
    )
    if hook_err:
        return hook_err

    try:
        update_frontmatter(spec, current, new_status)
    except OSError:
        core.err(f"cannot write task: {spec}")
        return core.EXIT_USAGE

    print(f"{task_name}: {current} → {new_status}")

    msg = auto_promote_parent(tasks_dir, task_name, new_status)
    if msg:
        print(msg)

    # --- Hook execution (post-transition) ---
    hooks.run_matched(
        root, prefix, task_name, current, new_status, spec, phase="post",
    )

    return core.EXIT_OK
