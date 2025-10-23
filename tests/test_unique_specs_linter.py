"""Tests for the unique specs linter."""

import pytest

from spec_tools.unique_specs_linter import UniqueSpecsLinter


@pytest.mark.req("REQ-001")
class TestSpecIdExtraction:
    """Test suite for SPEC ID extraction."""

    def test_extract_spec_id_valid(self, tmp_path):
        """Test extracting a valid SPEC ID from a spec file."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "test-spec.md"
        spec_file.write_text(
            """# Specification: Test Spec

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

This is a test specification.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        spec_id = linter.extract_spec_id(spec_file)

        assert spec_id == "SPEC-001"

    def test_extract_spec_id_missing(self, tmp_path):
        """Test extracting SPEC ID when none exists."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "no-id.md"
        spec_file.write_text(
            """# Specification: Test Spec

No ID metadata here.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        spec_id = linter.extract_spec_id(spec_file)

        assert spec_id is None


@pytest.mark.req("REQ-002")
class TestRequirementExtraction:
    """Test suite for requirement ID extraction."""

    def test_extract_requirements(self, tmp_path):
        """Test extracting requirement IDs from a spec file."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "test-spec.md"
        spec_file.write_text(
            """# Specification: Test Spec

**ID**: SPEC-001

## Requirements (EARS Format)

**REQ-001**: The system shall do something.

**REQ-002**: The system shall do something else.

**NFR-001**: The system shall be fast.

**TEST-001**: Unit tests shall cover all requirements.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        requirements = linter.extract_requirements(spec_file)

        assert "REQ-001" in requirements
        assert "REQ-002" in requirements
        assert "NFR-001" in requirements
        assert "TEST-001" in requirements
        assert len(requirements) == 4


@pytest.mark.req("REQ-003")
class TestUniqueSpecIds:
    """Test suite for unique SPEC ID validation."""

    def test_unique_spec_ids(self, tmp_path):
        """Test validation passes when all SPEC IDs are unique."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
"""
        )

        spec2 = spec_dir / "spec2.md"
        spec2.write_text(
            """# Specification: Spec 2

**ID**: SPEC-002

**REQ-001**: Requirement 1.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert len(result.duplicate_spec_ids) == 0
        assert result.total_specs == 2

    def test_duplicate_spec_ids(self, tmp_path):
        """Test validation fails when SPEC IDs are duplicated."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
"""
        )

        spec2 = spec_dir / "spec2.md"
        spec2.write_text(
            """# Specification: Spec 2

**ID**: SPEC-001

**REQ-002**: Requirement 2.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert not result.is_valid
        assert "SPEC-001" in result.duplicate_spec_ids
        assert len(result.duplicate_spec_ids["SPEC-001"]) == 2


@pytest.mark.req("REQ-004")
class TestUniqueRequirementIds:
    """Test suite for unique requirement ID validation."""

    def test_unique_requirements_within_spec(self, tmp_path):
        """Test validation passes when requirements within a spec are unique."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
**REQ-002**: Requirement 2.
**NFR-001**: Non-functional requirement 1.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert len(result.duplicate_req_ids) == 0

    def test_duplicate_requirements_within_spec(self, tmp_path):
        """Test validation fails when requirements are duplicated within a spec."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
**REQ-001**: Duplicate requirement 1.
**REQ-002**: Requirement 2.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert not result.is_valid
        assert "SPEC-001/REQ-001" in result.duplicate_req_ids
        assert "appears 2 times" in result.duplicate_req_ids["SPEC-001/REQ-001"][0]

    def test_same_req_id_different_specs_allowed(self, tmp_path):
        """Test that same requirement ID in different specs is allowed."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1 in SPEC-001.
"""
        )

        spec2 = spec_dir / "spec2.md"
        spec2.write_text(
            """# Specification: Spec 2

**ID**: SPEC-002

**REQ-001**: Requirement 1 in SPEC-002.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        # This should be valid because SPEC-001/REQ-001 and SPEC-002/REQ-001 are different
        assert result.is_valid
        assert result.total_requirements == 2


@pytest.mark.req("REQ-005")
class TestFullLinting:
    """Test suite for full linting scenarios."""

    def test_empty_specs_directory(self, tmp_path):
        """Test linting with no spec files."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_specs == 0
        assert result.total_requirements == 0

    def test_nested_specs(self, tmp_path):
        """Test linting with specs in nested directories."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        nested_dir = spec_dir / "nested"
        nested_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
"""
        )

        spec2 = nested_dir / "spec2.md"
        spec2.write_text(
            """# Specification: Spec 2

**ID**: SPEC-002

**REQ-001**: Requirement 1.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_specs == 2
        assert result.total_requirements == 2

    def test_multiple_violations(self, tmp_path):
        """Test linting with multiple types of violations."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        # Duplicate SPEC ID
        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
**REQ-001**: Duplicate in same spec.
"""
        )

        # Same SPEC ID in different file
        spec2 = spec_dir / "spec2.md"
        spec2.write_text(
            """# Specification: Spec 2

**ID**: SPEC-001

**REQ-002**: Requirement 2.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        assert not result.is_valid
        assert "SPEC-001" in result.duplicate_spec_ids
        assert "SPEC-001/REQ-001" in result.duplicate_req_ids

    def test_result_string_output(self, tmp_path):
        """Test that result string output is properly formatted."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        result_str = str(result)
        assert "UNIQUE SPECS VALIDATION REPORT" in result_str
        assert "Total specs: 1" in result_str
        assert "Total requirements: 1" in result_str
        assert "✅" in result_str

    def test_result_string_output_with_errors(self, tmp_path):
        """Test result string output with errors."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        spec1 = spec_dir / "spec1.md"
        spec1.write_text(
            """# Specification: Spec 1

**ID**: SPEC-001

**REQ-001**: Requirement 1.
"""
        )

        spec2 = spec_dir / "spec2.md"
        spec2.write_text(
            """# Specification: Spec 2

**ID**: SPEC-001

**REQ-002**: Requirement 2.
"""
        )

        linter = UniqueSpecsLinter(root_dir=tmp_path)
        result = linter.lint()

        result_str = str(result)
        assert "❌ Duplicate SPEC IDs:" in result_str
        assert "SPEC-001:" in result_str
        assert "❌ Unique specs validation FAILED" in result_str
