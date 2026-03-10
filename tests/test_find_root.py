"""Tests for find_root() — vault discovery including git worktree support."""

import os
import subprocess
from pathlib import Path
from unittest.mock import patch

import pytest

from openstation.core import find_root


@pytest.fixture
def project_dir(tmp_path):
    """Create a project with .openstation/ directory."""
    (tmp_path / ".openstation").mkdir()
    return tmp_path


@pytest.fixture
def source_repo_dir(tmp_path):
    """Create a source repo with agents/ + install.sh."""
    (tmp_path / "agents").mkdir()
    (tmp_path / "install.sh").touch()
    return tmp_path


@pytest.fixture
def worktree_env(tmp_path):
    """Create a real git repo with a worktree that shares the main repo's .openstation/.

    Layout:
      tmp_path/main/       — main git repo with .openstation/
      tmp_path/worktree/   — git worktree (no .openstation/)
    """
    main = tmp_path / "main"
    main.mkdir()

    # Init a real git repo
    subprocess.run(["git", "init"], cwd=main, capture_output=True, check=True)
    subprocess.run(
        ["git", "commit", "--allow-empty", "-m", "init"],
        cwd=main, capture_output=True, check=True,
        env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
             "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"},
    )

    # Create .openstation/ in main
    (main / ".openstation").mkdir()

    wt_path = tmp_path / "worktree"
    subprocess.run(
        ["git", "worktree", "add", str(wt_path), "-b", "wt-branch"],
        cwd=main, capture_output=True, check=True,
    )

    return main, wt_path


# --- Normal (non-worktree) behavior ---


class TestFindRootNormal:
    """find_root() works as before in normal projects."""

    def test_finds_openstation_dir(self, project_dir):
        root, prefix = find_root(start=str(project_dir))
        assert root == project_dir
        assert prefix == ".openstation"

    def test_finds_openstation_from_subdirectory(self, project_dir):
        sub = project_dir / "deep" / "nested"
        sub.mkdir(parents=True)
        root, prefix = find_root(start=str(sub))
        assert root == project_dir
        assert prefix == ".openstation"

    def test_finds_source_repo(self, source_repo_dir):
        root, prefix = find_root(start=str(source_repo_dir))
        assert root == source_repo_dir
        assert prefix == ""

    def test_returns_none_when_nothing_found(self, tmp_path):
        root, prefix = find_root(start=str(tmp_path))
        assert root is None
        assert prefix is None


# --- No git subprocess when .openstation/ found locally ---


class TestNoGitWhenLocal:
    """Git subprocess is never invoked when .openstation/ is found locally."""

    def test_no_subprocess_when_openstation_found(self, project_dir):
        with patch("subprocess.run") as mock_run:
            root, prefix = find_root(start=str(project_dir))
            assert root == project_dir
            assert prefix == ".openstation"
            mock_run.assert_not_called()


# --- Worktree detection ---


class TestWorktreeDetection:
    """find_root() resolves .openstation/ from main worktree."""

    def test_finds_vault_from_worktree(self, worktree_env):
        main, wt = worktree_env
        root, prefix = find_root(start=str(wt))
        assert root == main
        assert prefix == ".openstation"

    def test_finds_vault_from_worktree_subdirectory(self, worktree_env):
        main, wt = worktree_env
        sub = wt / "src" / "pkg"
        sub.mkdir(parents=True)
        root, prefix = find_root(start=str(sub))
        assert root == main
        assert prefix == ".openstation"

    def test_source_repo_from_worktree(self, tmp_path):
        """Source repo heuristic (agents/ + install.sh) also works via worktree fallback."""
        main = tmp_path / "main"
        main.mkdir()
        subprocess.run(["git", "init"], cwd=main, capture_output=True, check=True)
        subprocess.run(
            ["git", "commit", "--allow-empty", "-m", "init"],
            cwd=main, capture_output=True, check=True,
            env={**os.environ, "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
                 "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t"},
        )
        # Source repo markers in main
        (main / "agents").mkdir()
        (main / "install.sh").touch()

        wt_path = tmp_path / "worktree"
        subprocess.run(
            ["git", "worktree", "add", str(wt_path), "-b", "wt-src"],
            cwd=main, capture_output=True, check=True,
        )

        root, prefix = find_root(start=str(wt_path))
        assert root == main
        assert prefix == ""


# --- Graceful degradation ---


class TestGracefulDegradation:
    """find_root() degrades gracefully when git is unavailable."""

    def test_no_git_binary(self, tmp_path):
        """Returns None, None when git is not installed."""
        with patch("subprocess.run", side_effect=FileNotFoundError("git not found")):
            root, prefix = find_root(start=str(tmp_path))
            assert root is None
            assert prefix is None

    def test_not_a_git_repo(self, tmp_path):
        """Returns None, None when CWD is not in a git repo."""
        root, prefix = find_root(start=str(tmp_path))
        assert root is None
        assert prefix is None
