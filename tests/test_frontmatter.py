"""Tests for parse_frontmatter() edge cases in openstation.core."""

import pytest

from openstation.core import parse_frontmatter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def wrap(body):
    """Wrap body lines in YAML frontmatter delimiters."""
    return f"---\n{body}\n---\n\n# body\n"


# ---------------------------------------------------------------------------
# Regression: standard behaviour must not change
# ---------------------------------------------------------------------------

class TestStandardFrontmatter:
    def test_basic_key_value(self):
        text = wrap("kind: task\nname: my-task\nstatus: ready\n")
        fm = parse_frontmatter(text)
        assert fm["kind"] == "task"
        assert fm["name"] == "my-task"
        assert fm["status"] == "ready"

    def test_returns_empty_dict_when_no_frontmatter(self):
        assert parse_frontmatter("# just a heading\n\nsome body") == {}

    def test_returns_empty_dict_on_empty_string(self):
        assert parse_frontmatter("") == {}

    def test_multiple_fields(self):
        text = wrap("kind: agent\nname: researcher\nmodel: claude-sonnet-4-6\n")
        fm = parse_frontmatter(text)
        assert fm["kind"] == "agent"
        assert fm["name"] == "researcher"
        assert fm["model"] == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# Values containing colons
# ---------------------------------------------------------------------------

class TestColonValues:
    def test_value_with_colon(self):
        """partition(chr(58)) splits on first colon -- rest of value is preserved."""
        text = wrap("description: Fix: the auth bug\n")
        fm = parse_frontmatter(text)
        assert fm["description"] == "Fix: the auth bug"

    def test_value_with_multiple_colons(self):
        text = wrap("description: A: B: C\n")
        fm = parse_frontmatter(text)
        assert fm["description"] == "A: B: C"

    def test_url_value(self):
        text = wrap("source: https://example.com/path\n")
        fm = parse_frontmatter(text)
        assert fm["source"] == "https://example.com/path"


# ---------------------------------------------------------------------------
# Quoted values
# ---------------------------------------------------------------------------

class TestQuotedValues:
    def test_double_quoted_value(self):
        text = wrap('name: "my-task"\n')
        fm = parse_frontmatter(text)
        assert fm["name"] == "my-task"

    def test_single_quoted_value(self):
        text = wrap("name: 'my-task'\n")
        fm = parse_frontmatter(text)
        assert fm["name"] == "my-task"

    def test_double_quoted_value_with_spaces(self):
        text = wrap('description: "Fix the auth bug"\n')
        fm = parse_frontmatter(text)
        assert fm["description"] == "Fix the auth bug"

    def test_single_quoted_value_with_spaces(self):
        text = wrap("description: 'Fix the auth bug'\n")
        fm = parse_frontmatter(text)
        assert fm["description"] == "Fix the auth bug"

    def test_unquoted_value_unchanged(self):
        text = wrap("status: ready\n")
        fm = parse_frontmatter(text)
        assert fm["status"] == "ready"

    def test_mismatched_quotes_not_stripped(self):
        """Only strip when opening and closing quote match."""
        text = wrap('name: "mismatch\'\n')
        fm = parse_frontmatter(text)
        assert fm["name"] == '"mismatch\''

    def test_single_char_value_not_stripped(self):
        """A value that is a single pipe char -- too short (len < 2) to quote-strip."""
        text = wrap("flag: |\n")
        fm = parse_frontmatter(text)
        assert fm["flag"] == "|"


# ---------------------------------------------------------------------------
# Comment lines
# ---------------------------------------------------------------------------

class TestCommentLines:
    def test_comment_line_skipped(self):
        text = wrap("# this is a comment\nname: my-task\n")
        fm = parse_frontmatter(text)
        assert not any(k.startswith("#") for k in fm)
        assert fm["name"] == "my-task"

    def test_inline_comment_not_stripped(self):
        """Inline comments are part of the value -- we only skip full-line comments."""
        text = wrap("name: my-task # inline\n")
        fm = parse_frontmatter(text)
        assert fm["name"] == "my-task # inline"

    def test_multiple_comment_lines(self):
        text = wrap("# first comment\n# second comment\nstatus: ready\n")
        fm = parse_frontmatter(text)
        assert not any(k.startswith("#") for k in fm)
        assert fm["status"] == "ready"

    def test_comment_after_field(self):
        text = wrap("kind: task\n# separator comment\nassignee: researcher\n")
        fm = parse_frontmatter(text)
        assert fm["kind"] == "task"
        assert fm["assignee"] == "researcher"
        assert len(fm) == 2


# ---------------------------------------------------------------------------
# Indented lines (list items / continuation lines)
# ---------------------------------------------------------------------------

class TestIndentedLines:
    def test_indented_list_item_skipped(self):
        text = wrap("subtasks:\n  - subtask-1\n  - subtask-2\nstatus: ready\n")
        fm = parse_frontmatter(text)
        assert not any(k.strip().startswith("-") for k in fm)
        assert fm["status"] == "ready"

    def test_tab_indented_line_skipped(self):
        text = "---\nsubtasks:\n\t- subtask-1\nstatus: ready\n---\n"
        fm = parse_frontmatter(text)
        assert "status" in fm
        assert not any(k.startswith("\t") for k in fm)

    def test_space_indented_continuation_skipped(self):
        text = wrap("name: my-task\n  continuation line\nassignee: researcher\n")
        fm = parse_frontmatter(text)
        assert "  continuation line" not in fm
        assert fm["name"] == "my-task"
        assert fm["assignee"] == "researcher"


# ---------------------------------------------------------------------------
# Empty frontmatter block
# ---------------------------------------------------------------------------

class TestEmptyFrontmatter:
    def test_empty_frontmatter_block(self):
        """An empty ---/--- block should return an empty dict, not crash."""
        text = "---\n---\n\n# body\n"
        assert parse_frontmatter(text) == {}

    def test_only_comments_in_frontmatter(self):
        text = "---\n# just a comment\n---\n\n# body\n"
        assert parse_frontmatter(text) == {}

    def test_only_blank_lines_in_frontmatter(self):
        text = "---\n\n\n---\n\n# body\n"
        assert parse_frontmatter(text) == {}


# ---------------------------------------------------------------------------
# Realistic mixed frontmatter
# ---------------------------------------------------------------------------

class TestRealisticFrontmatter:
    def test_full_task_frontmatter(self):
        text = (
            "---\n"
            "# Task metadata\n"
            "kind: task\n"
            'name: "fix-auth-flow"\n'
            "status: ready\n"
            "assignee: researcher\n"
            "owner: manual\n"
            "created: 2026-01-15\n"
            "description: Fix: the OAuth redirect bug\n"
            "subtasks:\n"
            "  - verify-redirect-url\n"
            "  - update-callback-handler\n"
            "---\n"
            "\n"
            "# Fix Auth Flow\n"
        )
        fm = parse_frontmatter(text)
        assert fm["kind"] == "task"
        assert fm["name"] == "fix-auth-flow"
        assert fm["status"] == "ready"
        assert fm["description"] == "Fix: the OAuth redirect bug"
        # Indented list items must not pollute scalar fields
        assert not any(k.strip().startswith("-") for k in fm)
        # Comment must not appear as a key
        assert not any(k.startswith("#") for k in fm)

    def test_agent_spec_frontmatter(self):
        text = (
            "---\n"
            "kind: agent\n"
            "name: 'code-reviewer'\n"
            "description: 'Reviews PRs for correctness'\n"
            "model: claude-sonnet-4-6\n"
            "allowed-tools:\n"
            "  - Read\n"
            "  - Grep\n"
            "---\n"
        )
        fm = parse_frontmatter(text)
        assert fm["kind"] == "agent"
        assert fm["name"] == "code-reviewer"
        assert fm["description"] == "Reviews PRs for correctness"
        assert fm["model"] == "claude-sonnet-4-6"
