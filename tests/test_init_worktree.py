"""Tests for `openstation init --worktree` — linked-worktree symlink fix."""

import os
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest


@pytest.fixture()
def linked_worktree(tmp_path):
    """Create a main repo with .openstation/ (gitignored) and a linked worktree.

    Simulates the real setup: .openstation/ is gitignored (lives only in
    main repo), .claude/ is tracked with relative symlinks that become
    dangling in worktrees.

    Returns (main_repo, worktree_path).
    """
    main = tmp_path / "main"
    main.mkdir()

    subprocess.run(["git", "init", str(main)], capture_output=True, check=True)
    subprocess.run(
        ["git", "config", "user.email", "test@test.com"],
        cwd=str(main), capture_output=True, check=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Test"],
        cwd=str(main), capture_output=True, check=True,
    )

    # .openstation/ is gitignored — exists only in main repo filesystem
    gitignore = main / ".gitignore"
    gitignore.write_text(".openstation/\n")

    vault = main / ".openstation"
    for subdir in ("agents", "commands", "skills"):
        (vault / subdir).mkdir(parents=True)
        (vault / subdir / ".gitkeep").touch()

    # .claude/ IS tracked, with relative symlinks
    claude_dir = main / ".claude"
    claude_dir.mkdir()
    for name in ("agents", "commands", "skills"):
        os.symlink(f"../.openstation/{name}", str(claude_dir / name))

    subprocess.run(["git", "add", "-A"], cwd=str(main), capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "-m", "init"],
        cwd=str(main), capture_output=True, check=True,
    )

    # Create a linked worktree — .openstation/ won't be there
    wt = tmp_path / "worktree"
    subprocess.run(
        ["git", "worktree", "add", str(wt), "-b", "feature"],
        cwd=str(main), capture_output=True, check=True,
    )

    return main, wt


class TestIsLinkedWorktree:
    """Tests for _is_linked_worktree detection."""

    def test_linked_worktree_detected(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        from openstation.init import _is_linked_worktree
        is_linked, main_root = _is_linked_worktree()

        assert is_linked is True
        assert main_root == main.resolve()

    def test_main_repo_not_linked(self, linked_worktree, monkeypatch):
        main, _ = linked_worktree
        monkeypatch.chdir(main)

        from openstation.init import _is_linked_worktree
        is_linked, _ = _is_linked_worktree()

        assert is_linked is False

    def test_non_git_dir_not_linked(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        from openstation.init import _is_linked_worktree
        is_linked, _ = _is_linked_worktree()

        assert is_linked is False


class TestFixClaudeSymlinks:
    """Tests for _fix_claude_symlinks rewriting dangling relative -> absolute."""

    def test_dangling_symlinks_become_absolute(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        # Verify symlinks are dangling in the worktree
        for name in ("agents", "commands", "skills"):
            link = wt / ".claude" / name
            assert link.is_symlink(), f".claude/{name} should be a symlink"
            assert not link.exists(), f".claude/{name} should be dangling"

        from openstation.init import _fix_claude_symlinks
        fixed = _fix_claude_symlinks(main.resolve())

        assert fixed == 3

        # Verify symlinks now resolve correctly
        for name in ("agents", "commands", "skills"):
            link = wt / ".claude" / name
            assert link.is_symlink()
            assert link.exists(), f".claude/{name} should resolve after fix"
            target = os.readlink(str(link))
            assert os.path.isabs(target), f".claude/{name} target should be absolute"
            expected = str(main.resolve() / ".openstation" / name)
            assert target == expected

    def test_already_correct_symlinks_skipped(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        from openstation.init import _fix_claude_symlinks

        # First fix
        _fix_claude_symlinks(main.resolve())
        # Second fix should skip all
        fixed = _fix_claude_symlinks(main.resolve())
        assert fixed == 0

    def test_dry_run_does_not_modify(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        from openstation.init import _fix_claude_symlinks
        fixed = _fix_claude_symlinks(main.resolve(), dry_run=True)

        assert fixed == 3
        # Symlinks should still be dangling
        for name in ("agents", "commands", "skills"):
            link = wt / ".claude" / name
            assert not link.exists(), f".claude/{name} should still be dangling"

    def test_non_symlink_entries_skipped(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        # Replace one symlink with a real directory
        agents_link = wt / ".claude" / "agents"
        agents_link.unlink()
        agents_link.mkdir()

        from openstation.init import _fix_claude_symlinks
        fixed = _fix_claude_symlinks(main.resolve())

        # Only commands and skills should be fixed, agents skipped
        assert fixed == 2
        assert agents_link.is_dir() and not agents_link.is_symlink()


class TestCheckDanglingSymlinks:
    """Tests for check_dangling_claude_symlinks."""

    def test_detects_dangling(self, linked_worktree, monkeypatch):
        _, wt = linked_worktree
        monkeypatch.chdir(wt)

        from openstation.init import check_dangling_claude_symlinks
        broken = check_dangling_claude_symlinks()

        assert set(broken) == {"agents", "commands", "skills"}

    def test_no_dangling_after_fix(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        from openstation.init import _fix_claude_symlinks, check_dangling_claude_symlinks
        _fix_claude_symlinks(main.resolve())
        broken = check_dangling_claude_symlinks()

        assert broken == []


class TestCmdInitWorktree:
    """Tests for the cmd_init_worktree CLI handler."""

    def test_refuses_in_main_repo(self, linked_worktree, monkeypatch):
        main, _ = linked_worktree
        monkeypatch.chdir(main)

        from openstation.init import cmd_init_worktree
        args = SimpleNamespace(dry_run=False)
        rc = cmd_init_worktree(args)

        assert rc == 1  # EXIT_USAGE

    def test_refuses_in_non_git_dir(self, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)

        from openstation.init import cmd_init_worktree
        args = SimpleNamespace(dry_run=False)
        rc = cmd_init_worktree(args)

        assert rc == 1  # EXIT_USAGE

    def test_fixes_symlinks_in_worktree(self, linked_worktree, monkeypatch):
        main, wt = linked_worktree
        monkeypatch.chdir(wt)

        from openstation.init import cmd_init_worktree
        args = SimpleNamespace(dry_run=False)
        rc = cmd_init_worktree(args)

        assert rc == 0
        for name in ("agents", "commands", "skills"):
            link = wt / ".claude" / name
            assert link.is_symlink()
            assert link.exists()
