"""Tests for REQ-005: Section-Scoped Class Validation for DSL.

This requirement defines section-scoped class validation for the DSL system.
"""

from pathlib import Path

import pytest

from spec_check.dsl.layers import RequirementModule
from spec_check.dsl.models import (
    GherkinContentValidator,
    IdentifierSpec,
    SectionSpec,
    SpecClass,
    SpecModule,
)
from spec_check.dsl.registry import SpecTypeRegistry
from spec_check.dsl.validator import DSLValidator


class TestReq005:
    """Test suite for REQ-005 specification document."""

    def test_req_005_exists(self):
        """Test that REQ-005 specification exists."""
        req_file = Path("specs/requirements/REQ-005.md")
        assert req_file.exists(), "REQ-005.md should exist"

    def test_req_005_has_required_sections(self):
        """Test that REQ-005 has all required sections."""
        req_file = Path("specs/requirements/REQ-005.md")
        content = req_file.read_text()

        required_sections = [
            "## Purpose",
            "## Addresses",
            "## Description",
            "## Acceptance Criteria",
        ]

        for section in required_sections:
            assert section in content, f"REQ-005 missing {section} section"

    def test_req_005_has_acceptance_criteria(self):
        """Test that REQ-005 defines acceptance criteria."""
        req_file = Path("specs/requirements/REQ-005.md")
        content = req_file.read_text()

        assert "### AC-" in content, "REQ-005 should have acceptance criteria (AC-*)"
        assert "**Given**" in content, "AC should use Given-When-Then format"

    def test_req_005_addresses_job_003(self):
        """Test that REQ-005 addresses JOB-003."""
        req_file = Path("specs/requirements/REQ-005.md")
        content = req_file.read_text()

        assert "JOB-003" in content, "REQ-005 should reference JOB-003"


@pytest.mark.req("REQ-005")
class TestSectionScopedClassValidation:
    """Tests for section-scoped class validation feature."""

    def test_allowed_classes_field_exists(self):
        """Test AC-01: allowed_classes field exists on SectionSpec."""
        section = SectionSpec(
            heading="Test Section",
            heading_level=2,
            required=True,
            allowed_classes=["TestClass"],
        )

        assert section.allowed_classes == ["TestClass"]
        assert isinstance(section.allowed_classes, list)

        # Test default value
        section_default = SectionSpec(heading="Default Section", heading_level=2)
        assert section_default.allowed_classes is None

    def test_require_classes_field_exists(self):
        """Test AC-02: require_classes field exists on SectionSpec."""
        section = SectionSpec(
            heading="Test Section",
            heading_level=2,
            required=True,
            allowed_classes=["TestClass"],
            require_classes=True,
        )

        assert section.require_classes is True
        assert isinstance(section.require_classes, bool)

        # Test default value
        section_default = SectionSpec(heading="Default Section", heading_level=2)
        assert section_default.require_classes is False

    def test_validate_within_section_scope(self, tmp_path):
        """Test AC-03: Validation only searches within section scope."""
        # Create a custom module without reference requirements to test section-scoped validation
        custom_module = SpecModule(
            name="TestRequirement",
            description="Test requirement without reference validation",
            file_pattern=r"^TEST-\d{3}\.md$",
            location_pattern=r".",
            identifier=IdentifierSpec(pattern=r"TEST-\d{3}", location="title", scope="global"),
            sections=[
                SectionSpec(heading="Purpose", heading_level=2, required=True),
                SectionSpec(heading="Description", heading_level=2, required=True),
                SectionSpec(
                    heading="Acceptance Criteria",
                    heading_level=2,
                    required=True,
                    allowed_classes=["AcceptanceCriterion"],
                    require_classes=True,
                ),
            ],
            classes={
                "AcceptanceCriterion": SpecClass(
                    heading_pattern=r"^AC-\d{2}:",
                    heading_level=3,
                    content_validator=GherkinContentValidator(),
                ),
            },
        )

        # Create a test document with AC in correct section
        test_doc = tmp_path / "TEST-001.md"
        test_doc.write_text("""# TEST-001: Test Requirement

## Purpose

Test purpose.

## Description

Test description.

## Acceptance Criteria

### AC-01: Valid Criterion
**Given** a test condition
**When** an action occurs
**Then** a result is expected
""")

        # Create registry with custom module
        registry = SpecTypeRegistry()
        registry.register_module(custom_module)

        # Validate
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False, use_specignore=False)

        # Should pass - AC-01 is in Acceptance Criteria section
        assert result.success, f"Validation failed: {result.errors}"

    def test_detect_misplaced_class_instances(self, tmp_path):
        """Test AC-04: Detect class instances outside allowed sections."""
        # Create the correct directory structure
        req_dir = tmp_path / "specs" / "requirements"
        req_dir.mkdir(parents=True)

        # Create a test document with AC in wrong section
        test_doc = req_dir / "REQ-002.md"
        test_doc.write_text("""# REQ-002: Test Requirement

## Purpose

Test purpose.

## Description

Test description.

## Acceptance Criteria

### AC-01: Valid Criterion
**Given** a test condition
**When** an action occurs
**Then** a result is expected

## Notes

### AC-02: Invalid Criterion Here
**Given** this is in Notes section
**When** it should be in Acceptance Criteria
**Then** it should generate an error
""")

        # Create registry with RequirementModule
        registry = SpecTypeRegistry()
        registry.register_module(RequirementModule())

        # Validate
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False, use_specignore=False)

        # Should fail - AC-02 is in Notes section
        assert not result.success
        assert any(e.error_type == "misplaced_class_instance" for e in result.errors)

        # Check error message
        misplaced_error = next(
            e for e in result.errors if e.error_type == "misplaced_class_instance"
        )
        assert "AC-02" in misplaced_error.message or "Notes" in misplaced_error.message

    def test_enforce_require_classes_constraint(self, tmp_path):
        """Test AC-05: Enforce require_classes constraint."""
        # Create the correct directory structure
        req_dir = tmp_path / "specs" / "requirements"
        req_dir.mkdir(parents=True)

        # Create a test document without any AC instances
        test_doc = req_dir / "REQ-003.md"
        test_doc.write_text("""# REQ-003: Test Requirement

## Purpose

Test purpose.

## Description

Test description.

## Acceptance Criteria

No acceptance criteria defined here.

## Notes

Some notes.
""")

        # Create registry with RequirementModule
        registry = SpecTypeRegistry()
        registry.register_module(RequirementModule())

        # Validate
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False, use_specignore=False)

        # Should fail - Acceptance Criteria section requires at least one AC instance
        assert not result.success
        assert any(e.error_type == "missing_required_classes" for e in result.errors)

        # Check error message
        missing_error = next(e for e in result.errors if e.error_type == "missing_required_classes")
        assert "Acceptance Criteria" in missing_error.message
        assert "AcceptanceCriterion" in missing_error.message

    def test_support_multiple_class_types_per_section(self, tmp_path):
        """Test AC-06: Support multiple class types per section."""

        # Create a custom module with multiple class types in one section
        class TestCaseClass(SpecClass):
            heading_pattern: str = r"^TC-\d{2}:"
            heading_level: int = 3
            content_validator: GherkinContentValidator = GherkinContentValidator()

        custom_module = SpecModule(
            name="CustomRequirement",
            description="Test module with multiple class types",
            file_pattern=r"^CUSTOM-\d{3}\.md$",
            location_pattern=r".",
            identifier=IdentifierSpec(pattern=r"CUSTOM-\d{3}", location="title", scope="global"),
            sections=[
                SectionSpec(heading="Purpose", heading_level=2, required=True),
                SectionSpec(
                    heading="Tests",
                    heading_level=2,
                    required=True,
                    allowed_classes=["AcceptanceCriterion", "TestCase"],
                    require_classes=True,
                ),
            ],
            classes={
                "AcceptanceCriterion": SpecClass(
                    heading_pattern=r"^AC-\d{2}:",
                    heading_level=3,
                    content_validator=GherkinContentValidator(),
                ),
                "TestCase": TestCaseClass(),
            },
        )

        # Create test document with both class types
        test_doc = tmp_path / "CUSTOM-001.md"
        test_doc.write_text("""# CUSTOM-001: Test Document

## Purpose

Test purpose.

## Tests

### AC-01: Acceptance Criterion
**Given** a condition
**When** an action
**Then** a result

### TC-01: Test Case
**Given** a test setup
**When** a test action
**Then** a test result
""")

        # Create registry and validate
        registry = SpecTypeRegistry()
        registry.register_module(custom_module)

        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False, use_specignore=False)

        # Should pass - both class types are allowed in Tests section
        assert result.success, f"Validation failed: {result.errors}"

    def test_backward_compatibility_unrestricted_sections(self, tmp_path):
        """Test AC-07: Backward compatibility for sections without allowed_classes."""
        # Create a custom module without allowed_classes restriction
        custom_module = SpecModule(
            name="LegacyModule",
            description="Module without section-scoped classes",
            file_pattern=r"^LEGACY-\d{3}\.md$",
            location_pattern=r".",
            identifier=IdentifierSpec(pattern=r"LEGACY-\d{3}", location="title", scope="global"),
            sections=[
                SectionSpec(heading="Content", heading_level=2, required=True),
                # No allowed_classes defined - should use global search
            ],
            classes={
                "Item": SpecClass(
                    heading_pattern=r"^ITEM-\d{2}:",
                    heading_level=3,
                ),
            },
        )

        # Create test document with class instances in unrestricted section
        test_doc = tmp_path / "LEGACY-001.md"
        test_doc.write_text("""# LEGACY-001: Legacy Document

## Content

### ITEM-01: First Item

Some content.

### ITEM-02: Second Item

More content.
""")

        # Create registry and validate
        registry = SpecTypeRegistry()
        registry.register_module(custom_module)

        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False, use_specignore=False)

        # Should pass - backward compatibility allows global search
        assert result.success, f"Validation failed: {result.errors}"

    def test_validate_section_hierarchy(self, tmp_path):
        """Test AC-08: Validate correct section heading hierarchy."""
        # Create the correct directory structure
        req_dir = tmp_path / "specs" / "requirements"
        req_dir.mkdir(parents=True)

        # Create a test document with incorrect heading level for AC
        test_doc = req_dir / "REQ-004.md"
        test_doc.write_text("""# REQ-004: Test Requirement

## Purpose

Test purpose.

## Description

Test description.

## Acceptance Criteria

#### AC-01: Wrong Level Criterion
**Given** a test condition
**When** an action occurs
**Then** a result is expected
""")

        # Create registry with RequirementModule
        registry = SpecTypeRegistry()
        registry.register_module(RequirementModule())

        # Validate
        validator = DSLValidator(registry)
        result = validator.validate(tmp_path, use_gitignore=False, use_specignore=False)

        # Should generate a warning about incorrect heading level
        assert any(e.error_type == "incorrect_heading_level" for e in result.warnings)

        # Check warning message
        level_warning = next(
            e for e in result.warnings if e.error_type == "incorrect_heading_level"
        )
        assert "AC-01" in level_warning.message
        assert "level" in level_warning.message.lower()

    def test_requirement_module_uses_section_scoped_classes(self):
        """Test AC-09: RequirementModule updated to use section-scoped classes."""
        req_module = RequirementModule()

        # Find the Acceptance Criteria section
        ac_section = next(
            (s for s in req_module.sections if s.heading == "Acceptance Criteria"), None
        )

        assert ac_section is not None, "Acceptance Criteria section should exist"
        assert ac_section.allowed_classes == ["AcceptanceCriterion"], (
            "Should allow only AcceptanceCriterion"
        )
        assert ac_section.require_classes is True, "Should require at least one AC instance"

        # Verify no other sections allow AcceptanceCriterion
        other_sections = [s for s in req_module.sections if s.heading != "Acceptance Criteria"]
        for section in other_sections:
            if section.allowed_classes:
                assert "AcceptanceCriterion" not in section.allowed_classes, (
                    f"AcceptanceCriterion should not be allowed in {section.heading}"
                )

    def test_comprehensive_test_coverage(self):
        """Test AC-10: Comprehensive test coverage for the feature."""
        # This is a meta-test that verifies all other tests exist
        test_methods = [method for method in dir(self) if method.startswith("test_")]

        # We should have tests for all ACs
        assert "test_allowed_classes_field_exists" in test_methods  # AC-01
        assert "test_require_classes_field_exists" in test_methods  # AC-02
        assert "test_validate_within_section_scope" in test_methods  # AC-03
        assert "test_detect_misplaced_class_instances" in test_methods  # AC-04
        assert "test_enforce_require_classes_constraint" in test_methods  # AC-05
        assert "test_support_multiple_class_types_per_section" in test_methods  # AC-06
        assert "test_backward_compatibility_unrestricted_sections" in test_methods  # AC-07
        assert "test_validate_section_hierarchy" in test_methods  # AC-08
        assert "test_requirement_module_uses_section_scoped_classes" in test_methods  # AC-09

        # Verify we have at least 10 test methods (including this meta-test)
        assert len(test_methods) >= 10, "Should have tests for all acceptance criteria"
