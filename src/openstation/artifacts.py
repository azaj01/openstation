"""Artifact discovery, resolution, listing, and display."""

import json
import os
from pathlib import Path

from openstation import core

# Artifact subdirectories to scan (excludes tasks — those use the task commands)
ARTIFACT_KINDS = ("agents", "research", "specs")


def _artifacts_base(root, prefix):
    """Return the base artifacts/ Path."""
    if prefix:
        return Path(root) / prefix / "artifacts"
    return Path(root) / "artifacts"


def discover_artifacts(root, prefix, kind=None):
    """Scan artifact subdirectories and return artifact dicts.

    When kind is given, only that subdirectory is scanned.
    When kind is None, scans all non-task subdirectories.
    """
    base = _artifacts_base(root, prefix)
    kinds = (kind,) if kind else ARTIFACT_KINDS
    artifacts = []

    for k in kinds:
        subdir = base / k
        if not subdir.is_dir():
            continue
        for entry in sorted(subdir.iterdir()):
            if not entry.is_file() or entry.suffix != ".md":
                continue
            try:
                text = entry.read_text(encoding="utf-8")
            except OSError:
                continue
            fm = core.parse_frontmatter(text)
            name = fm.get("name", entry.stem)
            desc = fm.get("description", "")
            if desc in (">-", ">", "|", "|-"):
                desc = core.parse_multiline_value(text, "description")
            # Use first non-empty line of body as summary fallback
            if not desc:
                body = core.extract_body(text)
                for line in body.splitlines():
                    line = line.strip().lstrip("#").strip()
                    if line:
                        desc = line[:80]
                        break
            artifacts.append({
                "name": name,
                "kind": k,
                "summary": desc,
                "path": str(entry),
            })
    return artifacts


def resolve_artifact(root, prefix, query):
    """Resolve an artifact name across research/, specs/, agents/.

    Returns (path, error_msg, exit_code).
    """
    base = _artifacts_base(root, prefix)
    matches = []

    for k in ARTIFACT_KINDS:
        subdir = base / k
        if not subdir.is_dir():
            continue
        # Exact stem match
        candidate = subdir / f"{query}.md"
        if candidate.is_file():
            matches.append(candidate)
            continue
        # Partial match
        for entry in sorted(subdir.iterdir()):
            if not entry.is_file() or entry.suffix != ".md":
                continue
            if query in entry.stem:
                matches.append(entry)

    if len(matches) == 1:
        return matches[0], None, core.EXIT_OK
    if len(matches) > 1:
        # Check for exact matches first
        exact = [m for m in matches if m.stem == query]
        if len(exact) == 1:
            return exact[0], None, core.EXIT_OK
        match_list = "\n".join(f"  {m.parent.name}/{m.stem}" for m in matches)
        return None, f"ambiguous artifact '{query}', matches:\n{match_list}", core.EXIT_AMBIGUOUS
    return None, f"artifact not found: {query}\n  hint: run 'openstation artifacts list' to see available artifacts", core.EXIT_NOT_FOUND


def format_artifacts_table(artifacts):
    """Format artifacts as an aligned table."""
    if not artifacts:
        return ""
    headers = ["Name", "Kind", "Summary"]
    keys = ["name", "kind", "summary"]
    mins = [10, 8, 20]

    widths = [max(mins[i], len(headers[i])) for i in range(len(headers))]
    for a in artifacts:
        for i, k in enumerate(keys):
            widths[i] = max(widths[i], len(str(a.get(k, ""))))

    def fmt_row(values):
        parts = []
        for i, v in enumerate(values):
            parts.append(str(v).ljust(widths[i]))
        return "   ".join(parts)

    lines = [fmt_row(headers)]
    lines.append(fmt_row(["-" * widths[i] for i in range(len(headers))]))
    for a in artifacts:
        lines.append(fmt_row([a.get(k, "") for k in keys]))
    return "\n".join(lines)


# --- Command handlers ---------------------------------------------------------

def cmd_artifacts_list(args, root, prefix):
    """Handle 'artifacts list' (and bare 'artifacts')."""
    kind = getattr(args, "kind", None)

    if kind and kind not in ARTIFACT_KINDS and kind != "tasks":
        core.err(f"unknown artifact kind: {kind}")
        core.err(f"  valid kinds: {', '.join(ARTIFACT_KINDS)}")
        return core.EXIT_USAGE

    if kind == "tasks":
        core.err("use 'openstation list' for tasks")
        return core.EXIT_USAGE

    artifacts = discover_artifacts(root, prefix, kind=kind)
    artifacts.sort(key=lambda a: (a["kind"], a["name"]))

    if getattr(args, "json", False):
        out = [{"name": a["name"], "kind": a["kind"], "summary": a["summary"]} for a in artifacts]
        print(json.dumps(out, indent=2))
    elif getattr(args, "quiet", False):
        for a in artifacts:
            print(a["name"])
    else:
        output = format_artifacts_table(artifacts)
        if output:
            print(output)
    return core.EXIT_OK


def cmd_artifacts_show(args, root, prefix):
    """Handle 'artifacts show <name>'."""
    name = args.name
    artifact_path, error, code = resolve_artifact(root, prefix, name)
    if error:
        core.err(error)
        return code

    text = artifact_path.read_text(encoding="utf-8")

    if getattr(args, "vim", False):
        editor = os.environ.get("EDITOR", "vim")
        os.execvp(editor, [editor, str(artifact_path)])
        return core.EXIT_OK  # unreachable

    if getattr(args, "json", False):
        fm = core.parse_frontmatter_for_json(text)
        fm["body"] = core.extract_body(text)
        print(json.dumps(fm, indent=2))
    else:
        print(text)
    return core.EXIT_OK
