"""Tests for the spec linter."""

from pathlib import Path

import pytest

from spec_check.linter import SpecLinter


class TestSpecLinter:
    """Test suite for SpecLinter."""

    def test_simple_allowlist(self, tmp_path):
        """Test basic allowlist functionality."""
        # Create test files
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / ".specallowlist").write_text("*.md\n")

        # Create linter and run
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # Should have one unmatched file (test.py)
        assert not result.is_valid
        assert result.total_files == 2
        assert result.matched_files == 1
        assert len(result.unmatched_files) == 1
        assert "test.py" in result.unmatched_files

    def test_all_files_matched(self, tmp_path):
        """Test when all files match the allowlist."""
        # Create test files
        (tmp_path / "test1.md").write_text("# Test 1")
        (tmp_path / "test2.md").write_text("# Test 2")
        (tmp_path / ".specallowlist").write_text("*.md\n")

        # Create linter and run
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # All files should match
        assert result.is_valid
        assert result.total_files == 2
        assert result.matched_files == 2
        assert len(result.unmatched_files) == 0

    def test_directory_patterns(self, tmp_path):
        """Test patterns with directory paths."""
        # Create directory structure
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        (src_dir / "main.py").write_text("print('main')")
        (src_dir / "utils.py").write_text("print('utils')")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_main.py").write_text("def test(): pass")

        (tmp_path / "README.md").write_text("# README")
        (tmp_path / ".specallowlist").write_text("src/**/*.py\ntests/**/*.py\n*.md\n")

        # Create linter and run
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # All files should match
        assert result.is_valid
        assert result.total_files == 4

    def test_character_class_patterns(self, tmp_path):
        """Test patterns with character classes like [0-9]."""
        # Create files with specific naming
        specs_dir = tmp_path / "specs"
        specs_dir.mkdir()

        (specs_dir / "research-001-foo.md").write_text("# Research 1")
        (specs_dir / "research-002-bar.md").write_text("# Research 2")
        (specs_dir / "research-123-baz.md").write_text("# Research 3")
        (specs_dir / "other.md").write_text("# Other")

        (tmp_path / ".specallowlist").write_text("specs/research-[0-9][0-9][0-9]-*.md\n")

        # Create linter and run
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # Only the numbered research files should match
        assert not result.is_valid
        assert result.total_files == 4
        assert result.matched_files == 3
        assert len(result.unmatched_files) == 1
        assert str(Path("specs/other.md")) in result.unmatched_files

    def test_gitignore_respected(self, tmp_path):
        """Test that .gitignore patterns are respected."""
        # Create files
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "ignored.log").write_text("log data")

        # Create .gitignore
        (tmp_path / ".gitignore").write_text("*.log\n")

        # Create allowlist
        (tmp_path / ".specallowlist").write_text("*.md\n")

        # Create linter with gitignore enabled
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=True)
        result = linter.lint()

        # Should only see the .md file, .log is ignored
        assert result.is_valid
        assert result.total_files == 1
        assert "ignored.log" not in result.unmatched_files

    def test_gitignore_disabled(self, tmp_path):
        """Test that .gitignore can be disabled."""
        # Create files
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "ignored.log").write_text("log data")

        # Create .gitignore
        (tmp_path / ".gitignore").write_text("*.log\n")

        # Create allowlist
        (tmp_path / ".specallowlist").write_text("*.md\n*.log\n")

        # Create linter with gitignore disabled
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # Should see both files
        assert result.is_valid
        assert result.total_files == 2

    def test_comments_ignored(self, tmp_path):
        """Test that comments in allowlist are ignored."""
        # Create test file
        (tmp_path / "test.md").write_text("# Test")

        # Create allowlist with comments
        (tmp_path / ".specallowlist").write_text(
            "# This is a comment\n*.md  # This matches markdown files\n# Another comment\n"
        )

        # Create linter and run
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        assert result.is_valid

    def test_missing_allowlist_file(self, tmp_path):
        """Test error when allowlist file doesn't exist."""
        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)

        with pytest.raises(FileNotFoundError) as exc_info:
            linter.lint()

        assert ".specallowlist" in str(exc_info.value)

    def test_empty_allowlist(self, tmp_path):
        """Test error when allowlist has no patterns."""
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / ".specallowlist").write_text("# Only comments\n")

        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)

        with pytest.raises(ValueError) as exc_info:
            linter.lint()

        assert "No patterns found" in str(exc_info.value)

    def test_custom_allowlist_name(self, tmp_path):
        """Test using a custom allowlist filename."""
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / ".myallowlist").write_text("*.md\n")

        linter = SpecLinter(root_dir=tmp_path, allowlist_file=".myallowlist", use_gitignore=False)
        result = linter.lint()

        assert result.is_valid

    def test_nested_directories(self, tmp_path):
        """Test with deeply nested directory structure."""
        # Create nested structure
        deep_dir = tmp_path / "a" / "b" / "c" / "d"
        deep_dir.mkdir(parents=True)
        (deep_dir / "file.md").write_text("# Deep file")

        (tmp_path / ".specallowlist").write_text("**/*.md\n")

        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        assert result.is_valid
        assert result.total_files == 1

    def test_allowlist_file_excluded_from_check(self, tmp_path):
        """Test that the allowlist file itself is not checked."""
        (tmp_path / ".specallowlist").write_text("*.md\n")

        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # Should be valid even though .specallowlist doesn't match *.md
        assert result.is_valid
        assert result.total_files == 0

    def test_git_directory_ignored(self, tmp_path):
        """Test that .git directory is always ignored."""
        # Create .git directory with files
        git_dir = tmp_path / ".git"
        git_dir.mkdir()
        (git_dir / "config").write_text("git config")

        (tmp_path / "README.md").write_text("# README")
        (tmp_path / ".specallowlist").write_text("*.md\n")

        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # Should only see README.md, not .git/config
        assert result.is_valid
        assert result.total_files == 1

    def test_vcs_directories_auto_ignored(self, tmp_path):
        """Test that VCS directories are automatically ignored.

        This test reproduces issue #31 where .git (and other VCS directories)
        should be automatically ignored regardless of .gitignore contents.

        Standard file linters (ripgrep, fd, tree) automatically ignore VCS
        directories like .git/, .hg/, .svn/, .bzr/ regardless of .gitignore.
        spec-check should do the same.
        """
        # Create VCS directories
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "config").write_text("git config")

        (tmp_path / ".hg").mkdir()
        (tmp_path / ".hg" / "hgrc").write_text("hg config")

        (tmp_path / ".svn").mkdir()
        (tmp_path / ".svn" / "entries").write_text("svn entries")

        (tmp_path / ".bzr").mkdir()
        (tmp_path / ".bzr" / "branch.conf").write_text("bzr config")

        # Also create VCS control files (edge case - .git as file not directory)
        (tmp_path / "submodule" / ".git").mkdir(parents=True)
        (tmp_path / "submodule" / ".git").rmdir()  # Remove dir
        (tmp_path / "submodule" / ".git").write_text("gitdir: ../.git")  # Write as file

        # Create regular files
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / ".specallowlist").write_text("**/*.md\n")

        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        # Should only see README.md, not any VCS files
        # The submodule/.git file should also be ignored
        assert result.is_valid, f"Expected valid, but got unmatched: {result.unmatched_files}"
        assert result.total_files == 1, f"Expected 1 file, got {result.total_files}"
        assert result.matched_files == 1
        assert len(result.unmatched_files) == 0, (
            f"VCS files should be auto-ignored, but found: {result.unmatched_files}"
        )

    def test_result_string_representation(self, tmp_path):
        """Test the string representation of LintResult."""
        (tmp_path / "test.md").write_text("# Test")
        (tmp_path / "test.py").write_text("print('hello')")
        (tmp_path / ".specallowlist").write_text("*.md\n")

        linter = SpecLinter(root_dir=tmp_path, use_gitignore=False)
        result = linter.lint()

        result_str = str(result)
        assert "Total files checked: 2" in result_str
        assert "Matched files: 1" in result_str
        assert "Unmatched files: 1" in result_str
        assert "test.py" in result_str
