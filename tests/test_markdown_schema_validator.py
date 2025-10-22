"""Tests for markdown_schema_validator module."""

import tempfile
from pathlib import Path

import pytest

from spec_tools.markdown_schema_validator import (
    EARSValidator,
    MarkdownParser,
    MarkdownSchemaValidator,
    SchemaViolation,
)


class TestMarkdownParser:
    """Tests for MarkdownParser."""

    @pytest.mark.req("REQ-007", "REQ-008", "REQ-009")
    def test_parse_headings(self):
        """Test parsing of markdown headings."""
        content = """# Title
## Section 1
### Subsection 1.1
## Section 2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            metadata, headings = MarkdownParser.parse_file(path)

            assert len(headings) == 1  # One top-level heading
            assert headings[0].level == 1
            assert headings[0].text == "Title"
            assert len(headings[0].children) == 2  # Two H2 sections
            assert headings[0].children[0].text == "Section 1"
            assert len(headings[0].children[0].children) == 1  # One H3
            assert headings[0].children[0].children[0].text == "Subsection 1.1"
        finally:
            path.unlink()

    @pytest.mark.req("REQ-010", "REQ-013")
    def test_parse_metadata_after_h1(self):
        """Test parsing metadata fields after H1 heading."""
        content = """# Specification: Test Spec

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview
Content here.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            metadata, headings = MarkdownParser.parse_file(path)

            assert len(metadata) == 4
            assert metadata["ID"] == "SPEC-001"
            assert metadata["Version"] == "1.0"
            assert metadata["Date"] == "2025-10-22"
            assert metadata["Status"] == "Draft"
            assert len(headings) == 1
            assert headings[0].text == "Specification: Test Spec"
        finally:
            path.unlink()

    @pytest.mark.req("REQ-011", "REQ-013")
    def test_parse_metadata_before_h1(self):
        """Test parsing metadata fields before any heading."""
        content = """**ID**: SPEC-001
**Version**: 1.0

# Title
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            metadata, headings = MarkdownParser.parse_file(path)

            assert len(metadata) == 2
            assert metadata["ID"] == "SPEC-001"
            assert metadata["Version"] == "1.0"
        finally:
            path.unlink()

    @pytest.mark.req("REQ-012", "REQ-013")
    def test_parse_body_content(self):
        """Test that body content is captured under headings."""
        content = """# Title

**ID**: SPEC-001

## Section

This is body content.
More content here.

**REQ-001**: The system shall do something.
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            metadata, headings = MarkdownParser.parse_file(path)

            assert len(headings[0].children) == 1
            section = headings[0].children[0]
            assert section.text == "Section"
            assert len(section.body_lines) > 0

            # Check that requirement line is in body
            body_text = "\n".join(line for _, line in section.body_lines)
            assert "**REQ-001**:" in body_text
        finally:
            path.unlink()

    @pytest.mark.req("REQ-007")
    def test_flatten_headings(self):
        """Test flattening heading tree."""
        content = """# Title
## Section 1
### Subsection 1.1
### Subsection 1.2
## Section 2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False) as f:
            f.write(content)
            f.flush()
            path = Path(f.name)

        try:
            metadata, headings = MarkdownParser.parse_file(path)
            flat = MarkdownParser.flatten_headings(headings)

            assert len(flat) == 5  # 1 H1 + 2 H2 + 2 H3
            assert flat[0].text == "Title"
            assert flat[1].text == "Section 1"
            assert flat[2].text == "Subsection 1.1"
            assert flat[3].text == "Subsection 1.2"
            assert flat[4].text == "Section 2"
        finally:
            path.unlink()


class TestEARSValidator:
    """Tests for EARSValidator."""

    @pytest.mark.req("REQ-027", "REQ-031")
    def test_unconditional_requirement(self):
        """Test validation of unconditional requirements."""
        assert EARSValidator.is_ears_compliant("The system shall process all requests.")
        assert EARSValidator.is_ears_compliant("The application shall store data.")

    @pytest.mark.req("REQ-028")
    def test_event_driven_requirement(self):
        """Test validation of event-driven requirements (WHEN)."""
        assert EARSValidator.is_ears_compliant(
            "WHEN a user logs in, the system shall authenticate credentials."
        )
        assert EARSValidator.is_ears_compliant(
            "When receiving a request, the system shall validate the input."
        )

    @pytest.mark.req("REQ-029")
    def test_conditional_requirement(self):
        """Test validation of conditional requirements (IF/THEN)."""
        assert EARSValidator.is_ears_compliant(
            "IF the user is authenticated, THEN the system shall grant access."
        )
        assert EARSValidator.is_ears_compliant(
            "If data is invalid, then the system shall reject the request."
        )

    @pytest.mark.req("REQ-030")
    def test_optional_requirement(self):
        """Test validation of optional requirements (WHERE)."""
        assert EARSValidator.is_ears_compliant(
            "WHERE the user has permissions, the system shall allow modifications."
        )

    @pytest.mark.req("REQ-031")
    def test_test_requirements(self):
        """Test validation of test-specific requirements."""
        assert EARSValidator.is_ears_compliant("Unit tests shall cover all error cases.")
        assert EARSValidator.is_ears_compliant(
            "Integration tests shall validate end-to-end workflows."
        )

    @pytest.mark.req("REQ-032")
    def test_non_ears_compliant(self):
        """Test detection of non-compliant requirements."""
        # Missing "shall"
        assert not EARSValidator.is_ears_compliant("The system processes requests.")

        # Wrong structure
        assert not EARSValidator.is_ears_compliant("Process all requests quickly.")

    @pytest.mark.req("REQ-026")
    def test_requirement_id_pattern(self):
        """Test requirement ID pattern matching."""
        assert EARSValidator.REQUIREMENT_ID.match("**REQ-001**: ")
        assert EARSValidator.REQUIREMENT_ID.match("**REQ-123**: ")
        assert EARSValidator.REQUIREMENT_ID.match("**NFR-001**: ")
        assert EARSValidator.REQUIREMENT_ID.match("**TEST-001**: ")
        assert not EARSValidator.REQUIREMENT_ID.match("**INVALID-001**: ")
        assert not EARSValidator.REQUIREMENT_ID.match("REQ-001: ")

    @pytest.mark.req("REQ-025", "REQ-027")
    def test_validate_requirement_valid(self):
        """Test validation of a valid requirement line."""
        line = "**REQ-001**: The system shall process all requests."
        violation = EARSValidator.validate_requirement(1, line, "test.md")
        assert violation is None

    @pytest.mark.req("REQ-032")
    def test_validate_requirement_invalid(self):
        """Test validation of an invalid requirement line."""
        line = "**REQ-001**: The system processes requests."
        violation = EARSValidator.validate_requirement(1, line, "test.md")
        assert violation is not None
        assert isinstance(violation, SchemaViolation)
        assert violation.severity == "error"
        assert "EARS format" in violation.message

    @pytest.mark.req("REQ-025")
    def test_validate_non_requirement_line(self):
        """Test that non-requirement lines are not validated."""
        line = "This is just normal text."
        violation = EARSValidator.validate_requirement(1, line, "test.md")
        assert violation is None


class TestMarkdownSchemaValidator:
    """Tests for MarkdownSchemaValidator."""

    def create_temp_dir(self):
        """Create a temporary directory for testing."""
        return tempfile.mkdtemp()

    @pytest.mark.req("REQ-001", "REQ-002", "REQ-017", "TEST-001")
    def test_valid_spec_file(self):
        """Test validation of a valid specification file."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        spec_content = """# Specification: Test Feature

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

This is a test specification.

## Requirements (EARS Format)

### Functional Requirements

**REQ-001**: The system shall process all user requests.

**REQ-002**: WHEN a user submits data, the system shall validate the input.

**REQ-003**: IF validation fails, THEN the system shall return an error message.
"""
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text(spec_content)

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir)
            result = validator.validate()

            assert result.is_valid
            assert result.valid_files == 1
            assert result.invalid_files == 0
            assert len(result.violations) == 0
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-014", "REQ-015", "TEST-002")
    def test_missing_metadata(self):
        """Test detection of missing metadata fields."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        spec_content = """# Specification: Test Feature

**ID**: SPEC-001

## Overview

Content here.

## Requirements (EARS Format)

**REQ-001**: The system shall do something.
"""
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text(spec_content)

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir)
            result = validator.validate()

            assert not result.is_valid
            assert result.invalid_files == 1

            # Should have violations for missing Version, Date, Status
            missing_fields = [
                v for v in result.violations if "Missing required metadata" in v.message
            ]
            assert len(missing_fields) == 3
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-018", "REQ-021", "REQ-023", "TEST-003")
    def test_missing_required_heading(self):
        """Test detection of missing required headings."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        spec_content = """# Specification: Test Feature

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Requirements (EARS Format)

**REQ-001**: The system shall do something.
"""
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text(spec_content)

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir)
            result = validator.validate()

            assert not result.is_valid
            # Should have violation for missing "Overview" heading
            overview_violations = [v for v in result.violations if "Overview" in v.message]
            assert len(overview_violations) == 1
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-032", "REQ-034", "TEST-004")
    def test_invalid_ears_format(self):
        """Test detection of invalid EARS format requirements."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        spec_content = """# Specification: Test Feature

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

Test content.

## Requirements (EARS Format)

**REQ-001**: The system processes requests.

**REQ-002**: Process data quickly.
"""
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text(spec_content)

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir)
            result = validator.validate()

            assert not result.is_valid
            # Should have violations for invalid EARS format
            ears_violations = [v for v in result.violations if "EARS format" in v.message]
            assert len(ears_violations) == 2
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-004", "TEST-005")
    def test_gitignore_respected(self):
        """Test that .gitignore patterns are respected."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        # Create a spec file
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text("# Title\n")

        # Create .gitignore to ignore specs directory
        gitignore = Path(temp_dir) / ".gitignore"
        gitignore.write_text("specs/\n")

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir, respect_gitignore=True)
            files = validator.get_markdown_files()

            # Should not find any files because specs/ is ignored
            assert len(files) == 0
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-005", "TEST-005")
    def test_gitignore_disabled(self):
        """Test validation with gitignore disabled."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        # Create a minimal valid spec file
        spec_content = """# Specification: Test

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview
Test

## Requirements (EARS Format)

**REQ-001**: The system shall work.
"""
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text(spec_content)

        # Create .gitignore to ignore specs directory
        gitignore = Path(temp_dir) / ".gitignore"
        gitignore.write_text("specs/\n")

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir, respect_gitignore=False)
            files = validator.get_markdown_files()

            # Should find files even though specs/ is in .gitignore
            assert len(files) == 1
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-020", "REQ-022", "TEST-003")
    def test_h1_pattern_matching(self):
        """Test that H1 heading pattern is validated correctly."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        # Invalid H1 (doesn't start with "Specification:")
        spec_content = """# Test Feature

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview
Test

## Requirements (EARS Format)

**REQ-001**: The system shall work.
"""
        spec_file = specs_dir / "test-spec.md"
        spec_file.write_text(spec_content)

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir)
            result = validator.validate()

            assert not result.is_valid
            # Should have violation for H1 not matching pattern
            h1_violations = [v for v in result.violations if "level 1" in v.message]
            assert len(h1_violations) >= 1
        finally:
            import shutil

            shutil.rmtree(temp_dir)

    @pytest.mark.req("REQ-048", "REQ-049", "TEST-006")
    def test_multiple_files(self):
        """Test validation of multiple files."""
        temp_dir = self.create_temp_dir()
        specs_dir = Path(temp_dir) / "specs"
        specs_dir.mkdir()

        # Valid spec
        valid_spec = """# Specification: Valid

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview
Test

## Requirements (EARS Format)

**REQ-001**: The system shall work.
"""
        (specs_dir / "valid.md").write_text(valid_spec)

        # Invalid spec (missing metadata)
        invalid_spec = """# Specification: Invalid

## Overview
Test

## Requirements (EARS Format)

**REQ-001**: The system shall work.
"""
        (specs_dir / "invalid.md").write_text(invalid_spec)

        try:
            validator = MarkdownSchemaValidator(root_dir=temp_dir)
            result = validator.validate()

            assert not result.is_valid
            assert result.valid_files == 1
            assert result.invalid_files == 1
            assert result.total_files == 2
        finally:
            import shutil

            shutil.rmtree(temp_dir)
