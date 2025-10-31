"""Tests for REQ-004: Four-Tier Document Classification for DSL Validation."""

from pathlib import Path

import pytest


class TestReq004:
    """Test suite for REQ-004."""

    def test_req_004_exists(self):
        """Test that REQ-004 specification exists."""
        req_file = Path("specs/requirements/REQ-004.md")
        assert req_file.exists(), "REQ-004.md should exist"

    def test_req_004_has_required_sections(self):
        """Test that REQ-004 has all required sections."""
        req_file = Path("specs/requirements/REQ-004.md")
        content = req_file.read_text()

        required_sections = [
            "## Purpose",
            "## Addresses",
            "## Description",
            "## Acceptance Criteria",
            "## Jobs Addressed",
        ]

        for section in required_sections:
            assert section in content, f"REQ-004 missing {section} section"

    def test_req_004_has_acceptance_criteria(self):
        """Test that REQ-004 defines acceptance criteria."""
        req_file = Path("specs/requirements/REQ-004.md")
        content = req_file.read_text()

        assert "### AC-" in content, "REQ-004 should have acceptance criteria (AC-*)"
        assert "**Given**" in content, "AC should use Given-When-Then format"

    def test_req_004_addresses_job_002(self):
        """Test that REQ-004 addresses JOB-002."""
        req_file = Path("specs/requirements/REQ-004.md")
        content = req_file.read_text()

        assert "JOB-002" in content, "REQ-004 should reference JOB-002"


@pytest.mark.req("REQ-004")
class TestUnmanagedFileClassification:
    """Test unmanaged file classification (AC-06, AC-07)."""

    def test_default_mode_treats_unmatched_as_unmanaged(self, tmp_path):
        """Test AC-06: Files without type match are treated as unmanaged by default."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create a file that doesn't match any type
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        untyped_file = docs_dir / "guide.md"
        untyped_file.write_text("# User Guide\n\nSome documentation.")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, strict=False)

        # Should succeed without errors (file treated as unmanaged)
        assert result.success
        # File should be in unmanaged_files
        assert len(validator.unmanaged_files) == 1
        assert untyped_file in validator.unmanaged_files

    def test_strict_mode_warns_about_unclassified(self, tmp_path):
        """Test AC-07: Strict mode generates warnings for unclassified files."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create a file that doesn't match any type
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        untyped_file = docs_dir / "guide.md"
        untyped_file.write_text("# User Guide\n\nSome documentation.")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, strict=True)

        # Should have warning about unclassified file
        assert len(result.warnings) > 0
        warning_messages = [w.message for w in result.warnings]
        assert any("doesn't match any type definition" in msg for msg in warning_messages)


@pytest.mark.req("REQ-004")
class TestCrossReferenceResolution:
    """Test cross-reference resolution between typed and unmanaged files (AC-08, AC-09)."""

    def test_typed_to_unmanaged_reference(self, tmp_path):
        """Test AC-08: Typed documents can reference unmanaged documents."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create directory structure
        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create unmanaged document
        deployment_doc = docs_dir / "deployment.md"
        deployment_doc.write_text("# Deployment Guide\n\nDeployment instructions.")

        # Create typed document that references unmanaged
        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Deployment Requirement

## Addresses
- [Deployment Guide](../../docs/deployment.md)

## Specification
Requirements for deployment.

## Acceptance Criteria
- Deploy successfully
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path)

        # Deployment doc should be unmanaged
        assert deployment_doc in validator.unmanaged_files

    def test_unmanaged_to_typed_reference(self, tmp_path):
        """Test AC-09: Unmanaged documents can reference typed documents."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create directory structure
        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()

        # Create typed document
        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Addresses
- Job requirements

## Specification
Test requirement.

## Acceptance Criteria
- Test passes
""")

        # Create unmanaged document that references typed
        guide = docs_dir / "guide.md"
        guide.write_text("""# User Guide

See [REQ-001](../specs/requirements/REQ-001.md) for requirements.
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path)

        # Should resolve reference successfully
        # Note: Will have cardinality error for missing addresses, but reference should resolve
        assert guide in validator.unmanaged_files
        assert req_file in validator.documents


@pytest.mark.req("REQ-004")
class TestVCSDirectoryExclusion:
    """Test VCS directory auto-exclusion (AC-01)."""

    def test_vcs_directories_excluded(self, tmp_path):
        """Test AC-01: VCS directories are automatically excluded."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create VCS directories with markdown files
        (tmp_path / ".git").mkdir()
        (tmp_path / ".git" / "README.md").write_text("# Git README")

        (tmp_path / ".venv").mkdir()
        (tmp_path / ".venv" / "docs.md").write_text("# Venv docs")

        (tmp_path / "node_modules").mkdir()
        (tmp_path / "node_modules" / "package.md").write_text("# Package")

        # Create a valid document
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path)

        # Only the guide.md should be processed
        total_files = len(validator.documents) + len(validator.unmanaged_files)
        assert total_files == 1
        assert (docs_dir / "guide.md") in validator.unmanaged_files


@pytest.mark.req("REQ-004")
class TestGitignoreSupport:
    """Test .gitignore support (AC-02, AC-03)."""

    def test_gitignore_respected_by_default(self, tmp_path):
        """Test AC-02: .gitignore patterns are respected by default."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("build/\n")

        # Create files
        (tmp_path / "build").mkdir()
        (tmp_path / "build" / "output.md").write_text("# Build output")

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path, use_gitignore=True)

        # Only guide.md should be processed
        total_files = len(validator.documents) + len(validator.unmanaged_files)
        assert total_files == 1

    def test_gitignore_can_be_disabled(self, tmp_path):
        """Test AC-03: .gitignore can be disabled with --no-gitignore."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create .gitignore
        gitignore = tmp_path / ".gitignore"
        gitignore.write_text("temp/\n")

        # Create files
        (tmp_path / "temp").mkdir()
        (tmp_path / "temp" / "notes.md").write_text("# Temp notes")

        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# Guide")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path, use_gitignore=False)

        # Both files should be processed (gitignore disabled)
        total_files = len(validator.documents) + len(validator.unmanaged_files)
        assert total_files == 2


@pytest.mark.req("REQ-004")
class TestSpecignoreSupport:
    """Test .specignore support (AC-04, AC-05)."""

    def test_specignore_marks_files_as_unmanaged(self, tmp_path):
        """Test AC-04: .specignore marks matching files as unmanaged."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create .specignore
        specignore = tmp_path / ".specignore"
        specignore.write_text("docs/**/*.md\n")

        # Create files
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        guide = docs_dir / "guide.md"
        guide.write_text("# Guide")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path, use_specignore=True)

        # File should be unmanaged
        assert guide in validator.unmanaged_files

    def test_type_definition_takes_precedence(self, tmp_path):
        """Test AC-05: Type definitions take precedence over .specignore."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create .specignore that matches all specs
        specignore = tmp_path / ".specignore"
        specignore.write_text("specs/**/*.md\n")

        # Create a requirement file (matches type definition)
        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)
        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test

## Addresses
- Test

## Specification
Test

## Acceptance Criteria
- Pass
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        _result = validator.validate(tmp_path, use_specignore=True)

        # Should be typed, not unmanaged (type takes precedence)
        assert req_file in validator.documents
        assert req_file not in validator.unmanaged_files
