"""Tests for find_root() — vault discovery using git toplevel resolution."""

import os
import subprocess
from unittest.mock import patch

import pytest

from openstation.core import find_root


_GIT_ENV = {
    **os.environ,
    "GIT_AUTHOR_NAME": "test",
    "GIT_AUTHOR_EMAIL": "t@t",
    "GIT_COMMITTER_NAME": "test",
    "GIT_COMMITTER_EMAIL": "t@t",
}


def _git_init(path):
    """Initialize a git repo with an empty commit."""
    subprocess.run(["git", "init"], cwd=path, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=path, capture_output=True, check=True, env=_GIT_ENV,
    )


def _git_worktree_add(main, wt_path, branch="wt-branch"):
    """Add a git worktree."""
    subprocess.run(
        ["git", "worktree", "add", str(wt_path), "-b", branch],
        cwd=main, capture_output=True, check=True,
    )


@pytest.fixture
def project_dir(tmp_path):
    """Create a git repo with .openstation/ directory."""
    _git_init(tmp_path)
    (tmp_path / ".openstation").mkdir()
    return tmp_path


# --- Main repo root ---


class TestFindRootMainRepo:
    """find_root() from main repo root and subdirectories."""

    def test_finds_openstation_dir(self, project_dir):
        root = find_root(start=str(project_dir))
        assert root == project_dir

    def test_finds_openstation_from_subdirectory(self, project_dir):
        sub = project_dir / "deep" / "nested"
        sub.mkdir(parents=True)
        root = find_root(start=str(sub))
        assert root == project_dir


# --- Worktree behavior ---


class TestWorktreeAttachedMode:
    """Worktree WITHOUT its own .openstation/ → attached mode (uses main repo)."""

    def test_finds_vault_from_worktree(self, tmp_path):
        main = tmp_path / "main"
        main.mkdir()
        _git_init(main)
        (main / ".openstation").mkdir()

        wt_path = tmp_path / "worktree"
        _git_worktree_add(main, wt_path)

        root = find_root(start=str(wt_path))
        assert root == main

    def test_finds_vault_from_worktree_subdirectory(self, tmp_path):
        main = tmp_path / "main"
        main.mkdir()
        _git_init(main)
        (main / ".openstation").mkdir()

        wt_path = tmp_path / "worktree"
        _git_worktree_add(main, wt_path)

        sub = wt_path / "src" / "pkg"
        sub.mkdir(parents=True)
        root = find_root(start=str(sub))
        assert root == main


class TestWorktreeIndependentMode:
    """Worktree WITH its own .openstation/ → independent vault (uses worktree root)."""

    def test_worktree_with_openstation_returns_worktree(self, tmp_path):
        """When a worktree has .openstation/, it's independent."""
        main = tmp_path / "main"
        main.mkdir()
        _git_init(main)
        (main / ".openstation").mkdir()
        (main / ".openstation" / ".gitkeep").touch()
        subprocess.run(["git", "add", ".openstation"], cwd=main, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add openstation"],
            cwd=main, capture_output=True, check=True, env=_GIT_ENV,
        )

        wt_path = tmp_path / "worktree"
        _git_worktree_add(main, wt_path, branch="wt-independent")

        assert (wt_path / ".openstation").is_dir(), "worktree should have .openstation"
        root = find_root(start=str(wt_path))
        assert root == wt_path

    def test_worktree_subdirectory_independent(self, tmp_path):
        """find_root from a subdirectory of an independent worktree."""
        main = tmp_path / "main"
        main.mkdir()
        _git_init(main)
        (main / ".openstation").mkdir()
        (main / ".openstation" / ".gitkeep").touch()
        subprocess.run(["git", "add", ".openstation"], cwd=main, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "-m", "add openstation"],
            cwd=main, capture_output=True, check=True, env=_GIT_ENV,
        )

        wt_path = tmp_path / "worktree"
        _git_worktree_add(main, wt_path, branch="wt-sub")

        sub = wt_path / "src" / "pkg"
        sub.mkdir(parents=True)
        root = find_root(start=str(sub))
        assert root == wt_path


# --- Non-git directories ---


class TestNonGitDirectories:
    """Non-git directories return None — no longer supported."""

    def test_returns_none_for_non_git_dir(self, tmp_path):
        assert find_root(start=str(tmp_path)) is None

    def test_returns_none_for_non_git_with_markers(self, tmp_path):
        """Even with OS markers, non-git dirs are not supported."""
        (tmp_path / ".openstation").mkdir()
        assert find_root(start=str(tmp_path)) is None

    def test_returns_none_for_git_repo_without_markers(self, tmp_path):
        """A git repo without OS markers returns None."""
        _git_init(tmp_path)
        assert find_root(start=str(tmp_path)) is None


# --- Graceful degradation ---


class TestGracefulDegradation:
    """find_root() degrades gracefully when git is unavailable."""

    def test_no_git_binary(self, tmp_path):
        """Returns None when git is not installed."""
        with patch("openstation.core.subprocess.run", side_effect=FileNotFoundError("git not found")):
            assert find_root(start=str(tmp_path)) is None
