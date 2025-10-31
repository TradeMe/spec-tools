"""Tests for Gherkin content validation."""

from pathlib import Path

import pytest

from spec_check.dsl.models import GherkinContentValidator


class TestGherkinContentValidator:
    """Test the GherkinContentValidator class directly."""

    def test_valid_gherkin_format(self):
        """Test that valid Gherkin format passes validation."""
        validator = GherkinContentValidator()

        # Create mock AST nodes with valid content
        content = [
            type("Node", (), {"literal": "**Given** a user with valid credentials"}),
            type("Node", (), {"literal": "**When** they submit the login form"}),
            type("Node", (), {"literal": "**Then** they receive an authentication token"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 0, "Valid Gherkin format should not produce errors"

    def test_valid_gherkin_with_and(self):
        """Test that Gherkin with And/But keywords passes validation."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "**Given** a user with valid credentials"}),
            type("Node", (), {"literal": "**And** the user is logged in"}),
            type("Node", (), {"literal": "**When** they submit the form"}),
            type("Node", (), {"literal": "**Then** they see success"}),
            type("Node", (), {"literal": "**And** they receive an email"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 0, "Valid Gherkin with And should not produce errors"

    def test_missing_given_keyword(self):
        """Test that missing Given keyword produces error."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "**When** they submit the form"}),
            type("Node", (), {"literal": "**Then** they see success"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert errors[0].error_type == "invalid_gherkin_format"
        assert "Given" in errors[0].message
        assert errors[0].severity == "error"

    def test_missing_when_keyword(self):
        """Test that missing When keyword produces error."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "**Given** a user"}),
            type("Node", (), {"literal": "**Then** they see success"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert errors[0].error_type == "invalid_gherkin_format"
        assert "When" in errors[0].message

    def test_missing_then_keyword(self):
        """Test that missing Then keyword produces error."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "**Given** a user"}),
            type("Node", (), {"literal": "**When** they submit"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert errors[0].error_type == "invalid_gherkin_format"
        assert "Then" in errors[0].message

    def test_missing_all_keywords(self):
        """Test that missing all keywords produces error."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "Some arbitrary content"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert errors[0].error_type == "invalid_gherkin_format"
        assert "Given" in errors[0].message
        assert "When" in errors[0].message
        assert "Then" in errors[0].message

    def test_unbolded_given_keyword(self):
        """Test that unbolded Given keyword produces error with hint."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "Given a user with valid credentials"}),
            type("Node", (), {"literal": "**When** they submit the form"}),
            type("Node", (), {"literal": "**Then** they see success"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert "Given" in errors[0].message
        assert "bold" in errors[0].message.lower()
        assert "**Given**" in errors[0].message

    def test_unbolded_when_keyword(self):
        """Test that unbolded When keyword produces error with hint."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "**Given** a user"}),
            type("Node", (), {"literal": "When they submit"}),
            type("Node", (), {"literal": "**Then** success"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert "When" in errors[0].message
        assert "bold" in errors[0].message.lower()

    def test_unbolded_then_keyword(self):
        """Test that unbolded Then keyword produces error with hint."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "**Given** a user"}),
            type("Node", (), {"literal": "**When** they submit"}),
            type("Node", (), {"literal": "Then success"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert "Then" in errors[0].message
        assert "bold" in errors[0].message.lower()

    def test_empty_content(self):
        """Test that empty content produces error."""
        validator = GherkinContentValidator()

        content = []

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert errors[0].error_type == "empty_content"
        assert errors[0].severity == "error"

    def test_whitespace_only_content(self):
        """Test that whitespace-only content produces error."""
        validator = GherkinContentValidator()

        content = [
            type("Node", (), {"literal": "   "}),
            type("Node", (), {"literal": "\n"}),
        ]

        errors = validator.validate_content(content, Path("test.md"))
        assert len(errors) == 1
        assert errors[0].error_type == "empty_content"


@pytest.mark.req("REQ-004")
class TestGherkinValidationIntegration:
    """Test Gherkin validation integrated with DSL validator."""

    def test_valid_requirement_with_gherkin_ac(self, tmp_path):
        """Test that valid requirement with Gherkin AC passes validation."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        # Create a valid requirement with Gherkin acceptance criteria
        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)

        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Purpose

This is a test requirement.

## Description

Testing Gherkin validation.

## Acceptance Criteria

### AC-01: Valid Login

**Given** a user with valid credentials
**When** they submit the login form
**Then** they receive an authentication token

### AC-02: Invalid Login

**Given** a user with invalid credentials
**When** they submit the login form
**Then** they see an error message
**And** they remain on the login page
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False)

        # Should succeed without Gherkin errors
        gherkin_errors = [e for e in result.errors if "gherkin" in e.error_type.lower()]
        assert len(gherkin_errors) == 0, f"Should have no Gherkin errors, got: {gherkin_errors}"

    def test_requirement_with_missing_given(self, tmp_path):
        """Test that requirement with missing Given produces error."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)

        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Purpose

Test requirement.

## Description

Testing Gherkin validation.

## Acceptance Criteria

### AC-01: Missing Given

**When** they submit the form
**Then** they see success
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False)

        # Should have Gherkin error about missing Given
        gherkin_errors = [e for e in result.errors if "gherkin" in e.error_type.lower()]
        assert len(gherkin_errors) > 0, "Should have Gherkin error for missing Given"
        assert any("Given" in e.message for e in gherkin_errors)

    def test_requirement_with_unbolded_keywords(self, tmp_path):
        """Test that requirement with unbolded keywords produces error."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)

        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Purpose

Test requirement.

## Description

Testing Gherkin validation.

## Acceptance Criteria

### AC-01: Unbolded Keywords

Given a user with valid credentials
When they submit the login form
Then they receive an authentication token
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False)

        # Should have Gherkin errors about unbolded keywords
        gherkin_errors = [e for e in result.errors if "gherkin" in e.error_type.lower()]
        assert len(gherkin_errors) > 0, "Should have Gherkin errors for unbolded keywords"
        assert any("bold" in e.message.lower() for e in gherkin_errors)

    def test_requirement_with_empty_ac(self, tmp_path):
        """Test that requirement with empty AC produces error."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)

        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Purpose

Test requirement.

## Description

Testing Gherkin validation.

## Acceptance Criteria

### AC-01: Empty Criterion

""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False)

        # Should have error about empty content
        empty_errors = [e for e in result.errors if "empty" in e.error_type.lower()]
        assert len(empty_errors) > 0, "Should have error for empty AC"

    def test_requirement_with_multiple_ac_some_invalid(self, tmp_path):
        """Test that validator catches errors in some ACs but not all."""
        from spec_check.dsl.registry import SpecTypeRegistry
        from spec_check.dsl.validator import DSLValidator

        specs_dir = tmp_path / "specs" / "requirements"
        specs_dir.mkdir(parents=True)

        req_file = specs_dir / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Purpose

Test requirement.

## Description

Testing Gherkin validation.

## Acceptance Criteria

### AC-01: Valid Criterion

**Given** a valid user
**When** they perform an action
**Then** they see success

### AC-02: Invalid Criterion (missing When)

**Given** an invalid user
**Then** they see error

### AC-03: Another Valid Criterion

**Given** another user
**When** they try something
**Then** it works
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False)

        # Should have exactly one Gherkin error (for AC-02)
        gherkin_errors = [e for e in result.errors if "gherkin" in e.error_type.lower()]
        assert len(gherkin_errors) == 1, (
            f"Should have exactly 1 Gherkin error, got: {len(gherkin_errors)}"
        )
        assert "When" in gherkin_errors[0].message
        # Check that the error context identifies which AC
        assert "AC-02" in gherkin_errors[0].context or "AC-02" in str(gherkin_errors[0].message)
