"""Self-update subcommand — fetch latest version and re-link CLI binary."""

import os
import subprocess
from pathlib import Path

from openstation import core
from openstation.init import OPENSTATION_HOME


BIN_DIR = Path.home() / ".local" / "bin"


def _git(*args, cwd=None):
    """Run a git command and return (returncode, stdout)."""
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=str(cwd) if cwd else None,
            capture_output=True,
            text=True,
        )
        return result.returncode, result.stdout.strip()
    except FileNotFoundError:
        return 127, ""


def _current_version(install_dir):
    """Determine the currently checked-out version in the install cache.

    Tries ``git describe --tags --exact-match`` first, then falls
    back to the branch/detached-HEAD description.
    """
    rc, out = _git("describe", "--tags", "--exact-match", "HEAD", cwd=install_dir)
    if rc == 0 and out:
        return out
    # Fallback: abbreviated commit
    rc, out = _git("describe", "--tags", "--always", cwd=install_dir)
    if rc == 0 and out:
        return out
    return "unknown"


def _latest_tag(install_dir):
    """Fetch tags from remote and return the latest semver tag."""
    # Fetch all tags
    _git("fetch", "--tags", "--force", cwd=install_dir)
    # List tags sorted by version (descending), pick the first
    rc, out = _git("tag", "--list", "v*", "--sort=-version:refname", cwd=install_dir)
    if rc != 0 or not out:
        return None
    tags = out.splitlines()
    return tags[0] if tags else None


def _relink_binary(install_dir):
    """Re-create the CLI binary symlink."""
    cli_src = install_dir / "dist" / "openstation"
    cli_dst = BIN_DIR / "openstation"

    if not cli_src.is_file():
        core.err(f"CLI binary not found at {cli_src}")
        return False

    os.chmod(str(cli_src), 0o755)
    BIN_DIR.mkdir(parents=True, exist_ok=True)

    if cli_dst.is_symlink() or cli_dst.is_file():
        cli_dst.unlink()
    os.symlink(str(cli_src), str(cli_dst))
    return True


def cmd_self_update(args):
    """Handle the self-update subcommand."""
    install_dir = OPENSTATION_HOME
    target_version = args.version

    # Validate install cache exists and is a git repo
    if not install_dir.is_dir():
        core.err(
            "Open Station install cache not found.\n"
            "  Install first: curl -fsSL https://raw.githubusercontent.com/"
            "leonprou/openstation/main/install.sh | bash"
        )
        return core.EXIT_USAGE

    if not (install_dir / ".git").exists():
        core.err(
            f"Install cache at {install_dir} is not a git repo.\n"
            "  Re-run the installer with git available for self-update support."
        )
        return core.EXIT_USAGE

    # Check git is available
    rc, _ = _git("--version")
    if rc != 0:
        core.err("git is required for self-update but was not found on PATH.")
        return core.EXIT_USAGE

    # Determine current version
    old_version = _current_version(install_dir)

    # Determine target version
    if target_version:
        # Ensure the tag has a "v" prefix if it looks like a bare version
        if target_version[0].isdigit():
            target_version = f"v{target_version}"
        # Fetch the specific tag
        rc, _ = _git(
            "fetch", "--depth=1", "origin", "tag", target_version, "--force",
            cwd=install_dir,
        )
        if rc != 0:
            core.err(f"Failed to fetch version {target_version} from remote.")
            return core.EXIT_USAGE
        new_version = target_version
    else:
        new_version = _latest_tag(install_dir)
        if not new_version:
            core.err("Could not determine latest version from remote tags.")
            return core.EXIT_USAGE

    # Already up to date?
    if old_version == new_version:
        print(f"Already up to date: {new_version}")
        _check_project_hint()
        return core.EXIT_OK

    # Checkout target version (force handles dirty cache)
    rc, out = _git("checkout", "--force", new_version, cwd=install_dir)
    if rc != 0:
        core.err(f"Failed to checkout {new_version}: {out}")
        return core.EXIT_USAGE

    # Clean untracked files that might interfere
    _git("clean", "-fd", cwd=install_dir)

    # Re-link CLI binary
    if not _relink_binary(install_dir):
        return core.EXIT_USAGE

    print(f"Updated: {old_version} → {new_version}")

    _check_project_hint()

    return core.EXIT_OK


def _check_project_hint():
    """If CWD contains .openstation/, suggest running init."""
    if (Path.cwd() / ".openstation").is_dir():
        print()
        print("  hint: run `openstation init` to update this project's files")
