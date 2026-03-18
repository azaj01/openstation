"""Tests for the self-update subcommand."""

import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from openstation import core
from openstation import update


class TestCurrentVersion(unittest.TestCase):
    """Tests for _current_version()."""

    def test_returns_tag_when_exact(self):
        with mock.patch.object(update, "_git", return_value=(0, "v0.10.0")):
            result = update._current_version(Path("/fake"))
        self.assertEqual(result, "v0.10.0")

    def test_falls_back_to_describe(self):
        def side_effect(*args, **kwargs):
            if "--exact-match" in args:
                return (128, "")
            return (0, "v0.9.0-3-gabcdef")
        with mock.patch.object(update, "_git", side_effect=side_effect):
            result = update._current_version(Path("/fake"))
        self.assertEqual(result, "v0.9.0-3-gabcdef")

    def test_returns_unknown_on_failure(self):
        with mock.patch.object(update, "_git", return_value=(128, "")):
            result = update._current_version(Path("/fake"))
        self.assertEqual(result, "unknown")


class TestLatestTag(unittest.TestCase):
    """Tests for _latest_tag()."""

    def test_returns_first_tag(self):
        calls = []
        def side_effect(*args, **kwargs):
            calls.append(args)
            if "fetch" in args:
                return (0, "")
            if "tag" in args:
                return (0, "v0.10.0\nv0.9.0\nv0.8.0")
            return (0, "")
        with mock.patch.object(update, "_git", side_effect=side_effect):
            result = update._latest_tag(Path("/fake"))
        self.assertEqual(result, "v0.10.0")

    def test_returns_none_on_no_tags(self):
        with mock.patch.object(update, "_git", return_value=(0, "")):
            result = update._latest_tag(Path("/fake"))
        self.assertIsNone(result)


class TestRelinkBinary(unittest.TestCase):
    """Tests for _relink_binary()."""

    def test_creates_symlink(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            dist = install_dir / "dist"
            dist.mkdir()
            (dist / "openstation").write_text("#!/usr/bin/env python3\n")

            bin_dir = Path(tmpdir) / "bin"
            with mock.patch.object(update, "BIN_DIR", bin_dir):
                result = update._relink_binary(install_dir)

            self.assertTrue(result)
            link = bin_dir / "openstation"
            self.assertTrue(link.is_symlink())
            self.assertEqual(
                os.readlink(str(link)),
                str(dist / "openstation"),
            )

    def test_replaces_existing_symlink(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            dist = install_dir / "dist"
            dist.mkdir()
            (dist / "openstation").write_text("#!/usr/bin/env python3\n")

            bin_dir = Path(tmpdir) / "bin"
            bin_dir.mkdir()
            old_link = bin_dir / "openstation"
            old_link.symlink_to("/nonexistent/old")

            with mock.patch.object(update, "BIN_DIR", bin_dir):
                result = update._relink_binary(install_dir)

            self.assertTrue(result)
            self.assertEqual(
                os.readlink(str(old_link)),
                str(dist / "openstation"),
            )

    def test_fails_when_binary_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            (install_dir / "dist").mkdir()
            # No openstation binary

            result = update._relink_binary(install_dir)
            self.assertFalse(result)


class TestCmdSelfUpdate(unittest.TestCase):
    """Tests for cmd_self_update()."""

    def _make_args(self, version=None):
        return mock.Mock(version=version)

    def test_fails_when_no_install_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            fake_home = Path(tmpdir) / "nonexistent"
            with mock.patch.object(update, "OPENSTATION_HOME", fake_home):
                rc = update.cmd_self_update(self._make_args())
        self.assertEqual(rc, core.EXIT_USAGE)

    def test_fails_when_not_git_repo(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            # No .git directory
            with mock.patch.object(update, "OPENSTATION_HOME", install_dir):
                rc = update.cmd_self_update(self._make_args())
        self.assertEqual(rc, core.EXIT_USAGE)

    def test_already_up_to_date(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            (install_dir / ".git").mkdir()

            with mock.patch.object(update, "OPENSTATION_HOME", install_dir), \
                 mock.patch.object(update, "_current_version", return_value="v0.10.0"), \
                 mock.patch.object(update, "_latest_tag", return_value="v0.10.0"), \
                 mock.patch.object(update, "_git", return_value=(0, "")), \
                 mock.patch.object(update, "_check_project_hint"):
                rc = update.cmd_self_update(self._make_args())
        self.assertEqual(rc, core.EXIT_OK)

    def test_updates_to_latest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            (install_dir / ".git").mkdir()
            dist = install_dir / "dist"
            dist.mkdir()
            (dist / "openstation").write_text("#!/usr/bin/env python3\n")

            bin_dir = Path(tmpdir) / "bin"

            with mock.patch.object(update, "OPENSTATION_HOME", install_dir), \
                 mock.patch.object(update, "BIN_DIR", bin_dir), \
                 mock.patch.object(update, "_current_version", return_value="v0.9.0"), \
                 mock.patch.object(update, "_latest_tag", return_value="v0.10.0"), \
                 mock.patch.object(update, "_git", return_value=(0, "")), \
                 mock.patch.object(update, "_check_project_hint"):
                rc = update.cmd_self_update(self._make_args())
        self.assertEqual(rc, core.EXIT_OK)

    def test_pins_to_specific_version(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            (install_dir / ".git").mkdir()
            dist = install_dir / "dist"
            dist.mkdir()
            (dist / "openstation").write_text("#!/usr/bin/env python3\n")

            bin_dir = Path(tmpdir) / "bin"

            with mock.patch.object(update, "OPENSTATION_HOME", install_dir), \
                 mock.patch.object(update, "BIN_DIR", bin_dir), \
                 mock.patch.object(update, "_current_version", return_value="v0.9.0"), \
                 mock.patch.object(update, "_git", return_value=(0, "")), \
                 mock.patch.object(update, "_check_project_hint"):
                rc = update.cmd_self_update(self._make_args(version="v0.10.0"))
        self.assertEqual(rc, core.EXIT_OK)

    def test_auto_prefixes_v(self):
        """Bare version numbers get a 'v' prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            install_dir = Path(tmpdir)
            (install_dir / ".git").mkdir()
            dist = install_dir / "dist"
            dist.mkdir()
            (dist / "openstation").write_text("#!/usr/bin/env python3\n")

            bin_dir = Path(tmpdir) / "bin"
            git_calls = []

            def track_git(*args, **kwargs):
                git_calls.append(args)
                return (0, "")

            with mock.patch.object(update, "OPENSTATION_HOME", install_dir), \
                 mock.patch.object(update, "BIN_DIR", bin_dir), \
                 mock.patch.object(update, "_current_version", return_value="v0.9.0"), \
                 mock.patch.object(update, "_git", side_effect=track_git), \
                 mock.patch.object(update, "_check_project_hint"):
                rc = update.cmd_self_update(self._make_args(version="0.10.0"))

        self.assertEqual(rc, core.EXIT_OK)
        # The fetch call should use v0.10.0, not 0.10.0
        fetch_calls = [c for c in git_calls if "fetch" in c]
        self.assertTrue(any("v0.10.0" in c for c in fetch_calls))


class TestCheckProjectHint(unittest.TestCase):
    """Tests for _check_project_hint()."""

    def test_prints_hint_when_openstation_dir_exists(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            (Path(tmpdir) / ".openstation").mkdir()
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                # Should not raise
                update._check_project_hint()
            finally:
                os.chdir(original_cwd)

    def test_silent_when_no_openstation_dir(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                update._check_project_hint()
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
