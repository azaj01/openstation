"""Init subcommand — directory creation, file copying, agent template installation."""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

from openstation import core

OPENSTATION_HOME = Path(
    os.environ.get("OPENSTATION_DIR", Path.home() / ".local" / "share" / "openstation")
)

INIT_DIRS = [
    ".openstation/docs",
    ".openstation/artifacts/tasks",
    ".openstation/artifacts/agents",
    ".openstation/artifacts/research",
    ".openstation/artifacts/specs",
    ".openstation/agents",
    ".openstation/skills",
    ".openstation/commands",
    ".claude",
]

INIT_GITKEEP_DIRS = [
    ".openstation/artifacts/tasks",
    ".openstation/artifacts/agents",
    ".openstation/artifacts/research",
    ".openstation/artifacts/specs",
    ".openstation/agents",
    ".openstation/skills",
    ".openstation/commands",
]

def _discover_commands(source_dir):
    """Discover command files from the local cache."""
    cmd_dir = Path(source_dir) / ".openstation" / "commands"
    if not cmd_dir.is_dir():
        return []
    return sorted(f".openstation/commands/{p.name}" for p in cmd_dir.glob("*.md"))

INIT_SKILLS = [
    ".openstation/skills/openstation-execute/SKILL.md",
]

INIT_DOCS = [
    ".openstation/docs/lifecycle.md",
    ".openstation/docs/task.spec.md",
]

INIT_DEFAULT_AGENTS = [
    "architect",
    "author",
    "developer",
    "project-manager",
    "researcher",
]


class _InitStats:
    def __init__(self):
        self.created = 0
        self.updated = 0
        self.skipped = 0


def _init_info(msg, dry_run=False):
    prefix = "[would] " if dry_run else ""
    print(f"  {prefix}\033[1;32m✓\033[0m {msg}")


def _init_skip(msg, dry_run=False):
    prefix = "[would] " if dry_run else ""
    print(f"  {prefix}\033[1;33m⊘\033[0m {msg}")


def _init_warn(msg):
    print(f"  \033[1;33m!\033[0m {msg}", file=sys.stderr)


def _init_err(msg):
    print(f"  \033[1;31m✗\033[0m {msg}", file=sys.stderr)


def _copy_from_cache(src_relative, dst, source_dir, dry_run=False):
    """Copy a file from the local openstation cache. Returns True on success."""
    if dry_run:
        return True
    try:
        Path(dst).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(os.path.join(source_dir, src_relative), dst)
        return True
    except Exception as e:
        _init_err(f"Failed to copy {src_relative}: {e}")
        return False


def _discover_templates(source_dir):
    """Discover agent template names from the local cache."""
    tdir = Path(source_dir) / ".openstation" / "templates" / "agents"
    if not tdir.is_dir():
        return []
    return sorted(p.stem for p in tdir.glob("*.md"))


def _get_project_name():
    """Extract project name from CLAUDE.md H1 or fall back to dir name."""
    claude_md = Path("CLAUDE.md")
    if claude_md.is_file():
        try:
            for line in claude_md.read_text(encoding="utf-8").splitlines():
                if line.startswith("# "):
                    name = line[2:].strip()
                    if name != "Open Station":
                        return name
        except OSError:
            pass
    return Path.cwd().name


def _adapt_template(content, project_name):
    """Adapt agent template for the target project."""
    content = content.replace("the project", project_name)
    lines = content.splitlines()
    filtered = [
        l for l in lines
        if not re.match(r"^\s*#\s*---\s*(Role-based|Task-system).*---\s*$", l)
    ]
    return "\n".join(filtered) + "\n"


def _install_agents(source_dir, agents_filter, force, dry_run, stats):
    """Install agent templates into .openstation/artifacts/agents/."""
    print("Installing agent templates...")

    agent_names = _discover_templates(source_dir)
    if not agent_names:
        agent_names = list(INIT_DEFAULT_AGENTS)

    if agents_filter:
        requested = [n.strip() for n in agents_filter.split(",")]
        agent_names = [n for n in agent_names if n in requested]

    project_name = _get_project_name()

    for name in agent_names:
        dst = f".openstation/artifacts/agents/{name}.md"
        dst_path = Path(dst)

        if dst_path.is_file() and not force:
            _init_skip(f"{dst} (exists, skipped)", dry_run)
            stats.skipped += 1
        else:
            if dry_run:
                _init_info(dst, dry_run=True)
            else:
                try:
                    src = Path(source_dir) / ".openstation" / "templates" / "agents" / f"{name}.md"
                    content = src.read_text(encoding="utf-8")
                    adapted = _adapt_template(content, project_name)
                    dst_path.parent.mkdir(parents=True, exist_ok=True)
                    dst_path.write_text(adapted, encoding="utf-8")
                    _init_info(dst)
                except Exception as e:
                    _init_err(f"Failed to install agent template {name}: {e}")
                    continue
            stats.created += 1

        link = f".openstation/agents/{name}.md"
        target = f"../artifacts/agents/{name}.md"
        link_path = Path(link)
        if not dry_run:
            if link_path.is_symlink() or link_path.is_file():
                link_path.unlink()
            link_path.parent.mkdir(parents=True, exist_ok=True)
            os.symlink(target, str(link_path))
        _init_info(f"{link} → {target}", dry_run)


def _create_claude_symlinks(dry_run, commands):
    """Create .claude/ → .openstation/ directory symlinks."""
    print("Creating symlinks...")

    if dry_run:
        _init_info(".claude/commands → ../.openstation/commands", dry_run=True)
        _init_info(".claude/agents → ../.openstation/agents", dry_run=True)
        _init_info(".claude/skills → ../.openstation/skills", dry_run=True)
        return

    # .claude/commands
    cp = Path(".claude/commands")
    if cp.is_symlink():
        cp.unlink()
        os.symlink("../.openstation/commands", str(cp))
        _init_info(".claude/commands → ../.openstation/commands")
    elif cp.is_dir():
        if any(cp.iterdir()):
            _init_warn(".claude/commands/ exists with files — merging")
            for f in commands:
                fname = Path(f).name
                fl = cp / fname
                ft = f"../../{f}"
                if fl.is_symlink() or fl.is_file():
                    fl.unlink()
                os.symlink(ft, str(fl))
                _init_info(f"{fl} → {ft}")
        else:
            cp.rmdir()
            os.symlink("../.openstation/commands", str(cp))
            _init_info(".claude/commands → ../.openstation/commands")
    elif not cp.exists():
        os.symlink("../.openstation/commands", str(cp))
        _init_info(".claude/commands → ../.openstation/commands")

    # .claude/agents (always replace)
    ap = Path(".claude/agents")
    if ap.is_symlink():
        ap.unlink()
    elif ap.is_dir():
        shutil.rmtree(str(ap))
    os.symlink("../.openstation/agents", str(ap))
    _init_info(".claude/agents → ../.openstation/agents")

    # .claude/skills
    sp = Path(".claude/skills")
    if sp.is_symlink():
        sp.unlink()
        os.symlink("../.openstation/skills", str(sp))
        _init_info(".claude/skills → ../.openstation/skills")
    elif sp.is_dir():
        if any(sp.iterdir()):
            _init_warn(".claude/skills/ exists with files — merging")
            for f in INIT_SKILLS:
                parts = Path(f).parts
                # paths are .openstation/skills/<name>/SKILL.md
                if len(parts) >= 3 and parts[1] == "skills":
                    skill_name = parts[2]
                    fl = sp / skill_name
                    ft = f"../../.openstation/skills/{skill_name}"
                    if fl.is_symlink():
                        fl.unlink()
                    elif fl.is_dir():
                        shutil.rmtree(str(fl))
                    os.symlink(ft, str(fl))
                    _init_info(f"{fl} → {ft}")
        else:
            sp.rmdir()
            os.symlink("../.openstation/skills", str(sp))
            _init_info(".claude/skills → ../.openstation/skills")
    elif not sp.exists():
        os.symlink("../.openstation/skills", str(sp))
        _init_info(".claude/skills → ../.openstation/skills")


def _create_user_symlinks(source_dir, dry_run, force):
    """Install .claude/ discovery files to ~/.claude/ (user-level).

    Creates symlinks under ~/.claude/commands/ and ~/.claude/agents/
    pointing to the vault's canonical files in *source_dir*.
    """
    user_claude = Path.home() / ".claude"
    source = Path(source_dir)

    print()
    print("\033[1mOpen Station — user-level install\033[0m")
    print()

    # ── commands ────────────────────────────────────────────────
    print("Installing commands to ~/.claude/commands/ ...")
    cmd_dir = user_claude / "commands"
    if not dry_run:
        cmd_dir.mkdir(parents=True, exist_ok=True)

    for f in _discover_commands(str(source)):
        fname = Path(f).name
        link = cmd_dir / fname
        # f is .openstation/commands/name.md — resolve against source
        target = source / f
        if link.is_symlink() or link.is_file():
            if not force and link.is_symlink():
                _init_skip(f"~/.claude/commands/{fname} (exists, skipped)", dry_run)
                continue
            if not dry_run:
                link.unlink()
        if not dry_run:
            os.symlink(str(target.resolve()), str(link))
        _init_info(f"~/.claude/commands/{fname} → {target}", dry_run)

    # ── agents ──────────────────────────────────────────────────
    print("Installing agents to ~/.claude/agents/ ...")
    agents_dir = user_claude / "agents"
    if not dry_run:
        agents_dir.mkdir(parents=True, exist_ok=True)

    # Discover agent specs from the source vault
    src_agents = source / ".openstation" / "agents"
    if src_agents.is_dir():
        for spec in sorted(src_agents.glob("*.md")):
            # Resolve through symlinks to get the real spec file
            real = spec.resolve()
            link = agents_dir / spec.name
            if link.is_symlink() or link.is_file():
                if not force and link.is_symlink():
                    _init_skip(f"~/.claude/agents/{spec.name} (exists, skipped)", dry_run)
                    continue
                if not dry_run:
                    link.unlink()
            if not dry_run:
                os.symlink(str(real), str(link))
            _init_info(f"~/.claude/agents/{spec.name} → {real}", dry_run)

    # ── skills ──────────────────────────────────────────────────
    print("Installing skills to ~/.claude/skills/ ...")
    skills_dir = user_claude / "skills"
    if not dry_run:
        skills_dir.mkdir(parents=True, exist_ok=True)

    for f in INIT_SKILLS:
        parts = Path(f).parts
        # paths are .openstation/skills/<name>/SKILL.md
        if len(parts) >= 3 and parts[1] == "skills":
            skill_name = parts[2]
            link = skills_dir / skill_name
            target = source / ".openstation" / "skills" / skill_name
            if link.is_symlink() or link.is_dir():
                if not force and link.is_symlink():
                    _init_skip(f"~/.claude/skills/{skill_name} (exists, skipped)", dry_run)
                    continue
                if not dry_run:
                    if link.is_symlink():
                        link.unlink()
                    elif link.is_dir():
                        shutil.rmtree(str(link))
            if not dry_run:
                os.symlink(str(target.resolve()), str(link))
            _init_info(f"~/.claude/skills/{skill_name} → {target}", dry_run)

    print()
    print("\033[1;32mUser-level .claude/ files installed.\033[0m")
    print()

    return core.EXIT_OK


def cmd_init(args):
    """Handle the init subcommand."""
    no_agents = args.no_agents
    agents_filter = args.agents
    dry_run = args.dry_run
    force = args.force
    user_mode = args.user

    source_dir = OPENSTATION_HOME
    if not source_dir.is_dir():
        _init_err(
            "openstation not installed. Run:\n"
            "  curl -fsSL https://raw.githubusercontent.com/"
            "leonprou/openstation/main/install.sh | bash"
        )
        return core.EXIT_USAGE

    if not (source_dir / ".openstation" / "docs" / "lifecycle.md").is_file():
        _init_err(
            f"Install directory does not look like an Open Station repo: "
            f"{source_dir}\n  Re-run the installer to fix."
        )
        return core.EXIT_USAGE

    source_dir_str = str(source_dir.resolve())

    # --user: install .claude/ files to user-level config and return early
    if user_mode:
        return _create_user_symlinks(source_dir_str, dry_run, force)

    cwd = Path.cwd()
    is_reinit = (cwd / ".openstation").is_dir()

    try:
        subprocess.run(
            ["git", "rev-parse", "--git-dir"],
            capture_output=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        _init_warn("Not inside a git repository. Proceeding anyway.")

    stats = _InitStats()

    print()
    print("\033[1mOpen Station\033[0m")
    print()

    print("Creating directories...")
    for d in INIT_DIRS:
        dp = Path(d)
        if not dp.is_dir():
            if not dry_run:
                dp.mkdir(parents=True, exist_ok=True)
            _init_info(f"{d}/", dry_run)
            stats.created += 1

    for d in INIT_GITKEEP_DIRS:
        gk = Path(d) / ".gitkeep"
        if not gk.is_file():
            if not dry_run:
                Path(d).mkdir(parents=True, exist_ok=True)
                gk.touch()

    commands = _discover_commands(source_dir_str)
    print("Installing commands...")
    for f in commands:
        # f is already .openstation/commands/... — use as both src and dst
        if not _copy_from_cache(f, f, source_dir_str, dry_run):
            return core.EXIT_USAGE
        _init_info(f, dry_run)
        stats.updated += 1

    print("Installing skills...")
    for f in INIT_SKILLS:
        # f is already .openstation/skills/... — use as both src and dst
        if not dry_run:
            Path(f).parent.mkdir(parents=True, exist_ok=True)
        if not _copy_from_cache(f, f, source_dir_str, dry_run):
            return core.EXIT_USAGE
        _init_info(f, dry_run)
        stats.updated += 1

    print("Installing docs...")
    for f in INIT_DOCS:
        # f is already .openstation/docs/... — use as both src and dst
        if not _copy_from_cache(f, f, source_dir_str, dry_run):
            return core.EXIT_USAGE
        _init_info(f, dry_run)
        stats.updated += 1

    if no_agents:
        print("Skipping agent specs (--no-agents)")
    else:
        _install_agents(source_dir_str, agents_filter, force, dry_run, stats)

    _create_claude_symlinks(dry_run, commands)

    print()
    if is_reinit:
        total = stats.updated + stats.created
        print(
            f"\033[1;32mOpen Station re-initialized "
            f"({total} files updated, {stats.skipped} skipped).\033[0m"
        )
    else:
        print("\033[1;32mOpen Station initialized successfully!\033[0m")
        print()
        print("Next steps:")
        print("  1. Review .openstation/docs/lifecycle.md")
        print("  2. Customize agent specs in .openstation/agents/")
        print("  3. Create your first task: /openstation.create <description>")
        print("  4. Run an agent: claude --agent <name>")
    print()

    return core.EXIT_OK
