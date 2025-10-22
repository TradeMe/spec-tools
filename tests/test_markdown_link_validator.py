"""Tests for the markdown link validator."""

from unittest.mock import MagicMock, Mock, patch

from spec_tools.markdown_link_validator import MarkdownLinkValidator


class TestMarkdownLinkValidator:
    """Test suite for MarkdownLinkValidator."""

    def test_find_inline_links(self, tmp_path):
        """Test extracting inline markdown links."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
# Test Document

This is a [link to file](./other.md) and another [link](../parent.md).
Visit [external site](https://example.com) for more info.
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        assert len(links) == 3
        assert links[0].url == "./other.md"
        assert links[1].url == "../parent.md"
        assert links[2].url == "https://example.com"
        assert links[2].is_external

    def test_find_links_with_anchors(self, tmp_path):
        """Test extracting links with anchor fragments."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
Jump to [section](#heading) or see [other file](./doc.md#introduction).
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        assert len(links) == 2
        assert links[0].url == ""
        assert links[0].anchor == "heading"
        assert links[1].url == "./doc.md"
        assert links[1].anchor == "introduction"

    def test_validate_internal_link_exists(self, tmp_path):
        """Test validating an internal link that exists."""
        # Create target file
        (tmp_path / "target.md").write_text("# Target")

        # Create source file
        md_file = tmp_path / "source.md"
        md_file.write_text("[link](./target.md)")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("source.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert is_valid
        assert reason == ""

    def test_validate_internal_link_not_found(self, tmp_path):
        """Test validating an internal link that doesn't exist."""
        md_file = tmp_path / "source.md"
        md_file.write_text("[link](./missing.md)")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("source.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert not is_valid
        assert "File not found" in reason

    def test_validate_internal_link_with_subdirectory(self, tmp_path):
        """Test validating internal links across subdirectories."""
        # Create directory structure
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        api_dir = tmp_path / "api"
        api_dir.mkdir()

        # Create files
        (docs_dir / "guide.md").write_text("[API](../api/reference.md)")
        (api_dir / "reference.md").write_text("# API Reference")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("docs/guide.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert is_valid

    def test_validate_anchor_in_same_file(self, tmp_path):
        """Test validating an anchor in the same file."""
        md_file = tmp_path / "doc.md"
        md_file.write_text(
            """
# Main Heading

Jump to [configuration](#configuration).

## Configuration

Some config info.
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("doc.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert is_valid

    def test_validate_anchor_not_found(self, tmp_path):
        """Test validating an anchor that doesn't exist."""
        md_file = tmp_path / "doc.md"
        md_file.write_text(
            """
# Main Heading

Jump to [missing](#nonexistent).
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("doc.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert not is_valid
        assert "Anchor #nonexistent not found" in reason

    def test_validate_anchor_in_different_file(self, tmp_path):
        """Test validating an anchor in a different file."""
        # Create target file with heading
        (tmp_path / "target.md").write_text(
            """
# API Reference

## Authentication

Login details here.
"""
        )

        # Create source file with link to anchor
        (tmp_path / "source.md").write_text("[Auth](./target.md#authentication)")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("source.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert is_valid

    def test_heading_to_anchor_conversion(self):
        """Test markdown heading to anchor ID conversion."""
        validator = MarkdownLinkValidator()

        # Test various heading formats
        assert validator._heading_to_anchor("Configuration") == "configuration"
        assert validator._heading_to_anchor("API Reference") == "api-reference"
        assert validator._heading_to_anchor("Getting Started!") == "getting-started"
        assert validator._heading_to_anchor("What's New?") == "whats-new"

    def test_classify_external_link(self, tmp_path):
        """Test classifying links as external or internal."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
[http link](http://example.com)
[https link](https://example.com)
[relative link](./file.md)
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        assert links[0].is_external
        assert links[1].is_external
        assert not links[2].is_external

    def test_private_url_detection_domain(self, tmp_path):
        """Test detecting private URLs by domain."""
        config_file = tmp_path / ".speclinkconfig"
        config_file.write_text(
            """
# Private domains
internal.company.com
localhost
"""
        )

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
[internal](https://internal.company.com/docs)
[local](http://localhost:8080)
[public](https://example.com)
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        validator.load_config()
        links = validator.extract_links_from_file("test.md")

        assert links[0].is_private
        assert links[1].is_private
        assert not links[2].is_private

    def test_private_url_detection_prefix(self, tmp_path):
        """Test detecting private URLs by prefix."""
        config_file = tmp_path / ".speclinkconfig"
        config_file.write_text(
            """
https://private.example.com/
http://127.0.0.1:
"""
        )

        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
[private](https://private.example.com/internal/doc)
[local](http://127.0.0.1:3000/api)
[public](https://example.com)
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        validator.load_config()
        links = validator.extract_links_from_file("test.md")

        assert links[0].is_private
        assert links[1].is_private
        assert not links[2].is_private

    def test_config_with_dash_prefix(self, tmp_path):
        """Test config file with YAML-style dash prefixes."""
        config_file = tmp_path / ".speclinkconfig"
        config_file.write_text(
            """
# Private URLs
- internal.company.com
- https://private.example.com/
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        validator.load_config()

        assert "internal.company.com" in validator.private_url_patterns
        assert "https://private.example.com/" in validator.private_url_patterns

    def test_no_config_file(self, tmp_path):
        """Test behavior when no config file exists."""
        validator = MarkdownLinkValidator(root_dir=tmp_path)
        validator.load_config()

        assert len(validator.private_url_patterns) == 0

    def test_get_markdown_files(self, tmp_path):
        """Test finding all markdown files."""
        # Create markdown files
        (tmp_path / "README.md").write_text("# README")
        (tmp_path / "doc.markdown").write_text("# Doc")
        (tmp_path / "not_markdown.txt").write_text("text")

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        md_files = validator.get_markdown_files()

        assert len(md_files) == 3
        assert "README.md" in md_files
        assert "doc.markdown" in md_files
        assert "docs/guide.md" in md_files

    def test_gitignore_respected(self, tmp_path):
        """Test that .gitignore patterns are respected."""
        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("ignored/\n*.tmp.md")

        # Create files
        (tmp_path / "included.md").write_text("# Included")
        (tmp_path / "test.tmp.md").write_text("# Ignored")

        ignored_dir = tmp_path / "ignored"
        ignored_dir.mkdir()
        (ignored_dir / "secret.md").write_text("# Secret")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        validator.load_gitignore()
        md_files = validator.get_markdown_files()

        assert "included.md" in md_files
        assert "test.tmp.md" not in md_files
        assert "ignored/secret.md" not in md_files

    def test_gitignore_disabled(self, tmp_path):
        """Test disabling .gitignore."""
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("*.tmp.md")

        (tmp_path / "included.md").write_text("# Included")
        (tmp_path / "test.tmp.md").write_text("# Also Included")

        validator = MarkdownLinkValidator(root_dir=tmp_path, use_gitignore=False)
        validator.load_gitignore()
        md_files = validator.get_markdown_files()

        assert "included.md" in md_files
        assert "test.tmp.md" in md_files

    @patch("urllib.request.urlopen")
    def test_validate_external_link_success(self, mock_urlopen, tmp_path):
        """Test validating a successful external link."""
        # Mock HTTP response
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_urlopen.return_value = mock_response

        md_file = tmp_path / "test.md"
        md_file.write_text("[link](https://example.com)")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        is_valid, reason = validator.validate_external_link(links[0])
        assert is_valid
        assert reason == ""

    @patch("urllib.request.urlopen")
    def test_validate_external_link_404(self, mock_urlopen, tmp_path):
        """Test validating an external link that returns 404."""
        import urllib.error

        mock_urlopen.side_effect = urllib.error.HTTPError(
            "https://example.com", 404, "Not Found", {}, None
        )

        md_file = tmp_path / "test.md"
        md_file.write_text("[link](https://example.com/missing)")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        is_valid, reason = validator.validate_external_link(links[0], retries=0)
        assert not is_valid
        assert "404" in reason

    def test_full_validation(self, tmp_path):
        """Test full validation workflow."""
        # Create some markdown files with various links
        (tmp_path / "README.md").write_text(
            """
# Project

See [documentation](./docs/guide.md) for details.
"""
        )

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text(
            """
# Guide

## Installation

Follow these steps.
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path, check_external=False)
        result = validator.validate()

        assert result.markdown_files_checked == 2
        assert result.total_links == 1
        assert result.valid_links == 1
        assert result.invalid_links == 0
        assert result.is_valid

    def test_validation_with_invalid_links(self, tmp_path):
        """Test validation with invalid links."""
        (tmp_path / "README.md").write_text(
            """
See [missing file](./nonexistent.md) and [bad anchor](#missing-section).
"""
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path, check_external=False)
        result = validator.validate()

        assert result.total_links == 2
        assert result.invalid_links == 2
        assert not result.is_valid
        assert len(result.invalid_link_details) == 2

    def test_validation_result_string(self, tmp_path):
        """Test LinkValidationResult string representation."""
        (tmp_path / "test.md").write_text("[link](./missing.md)")

        validator = MarkdownLinkValidator(root_dir=tmp_path, check_external=False)
        result = validator.validate()

        result_str = str(result)
        assert "Markdown files checked: 1" in result_str
        assert "Total links found: 1" in result_str
        assert "Invalid links: 1" in result_str
        assert "test.md" in result_str
        assert "missing.md" in result_str

    def test_link_outside_repository(self, tmp_path):
        """Test that links outside repository are rejected."""
        (tmp_path / "test.md").write_text("[escape](../../../etc/passwd)")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        is_valid, reason = validator.validate_internal_link(links[0])
        assert not is_valid
        assert "outside repository" in reason

    def test_extract_links_handles_unicode(self, tmp_path):
        """Test that link extraction handles unicode properly."""
        md_file = tmp_path / "test.md"
        md_file.write_text(
            """
[日本語](./japanese.md)
[Emoji 🎉](./party.md)
""",
            encoding="utf-8",
        )

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        assert len(links) == 2
        assert links[0].text == "日本語"
        assert links[1].text == "Emoji 🎉"

    def test_extract_links_handles_unreadable_file(self, tmp_path):
        """Test graceful handling of unreadable files."""
        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("nonexistent.md")

        assert len(links) == 0

    def test_multiple_links_same_line(self, tmp_path):
        """Test extracting multiple links on the same line."""
        md_file = tmp_path / "test.md"
        md_file.write_text("See [doc1](./doc1.md) and [doc2](./doc2.md) for info.")

        validator = MarkdownLinkValidator(root_dir=tmp_path)
        links = validator.extract_links_from_file("test.md")

        assert len(links) == 2
        assert all(link.line_number == 1 for link in links)
