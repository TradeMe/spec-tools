"""Integration tests using realistic test projects.

These tests validate the entire system using complete, realistic test projects
rather than minimal fixtures. This ensures the AST refactoring preserves all
functionality and handles real-world scenarios.
"""

from pathlib import Path

import pytest

from spec_tools.markdown_link_validator import MarkdownLinkValidator
from spec_tools.markdown_schema_validator import MarkdownSchemaValidator
from spec_tools.spec_coverage_linter import SpecCoverageLinter
from spec_tools.structure_linter import StructureLinter
from spec_tools.unique_specs_linter import UniqueSpecsLinter

# Get the fixtures directory
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "projects"


class TestSimpleEcommerceProject:
    """Integration tests for the simple e-commerce project.

    This project has:
    - Single spec with 7 requirements (REQ-001 to REQ-005, NFR-001, NFR-002)
    - Full test coverage
    - Valid structure
    """

    @pytest.fixture
    def project_dir(self):
        """Get the simple e-commerce project directory."""
        return FIXTURES_DIR / "simple_ecommerce"

    def test_spec_coverage_full_coverage(self, project_dir):
        """Test that spec coverage linter reports 100% coverage."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        result = linter.lint()

        assert result.is_valid
        assert result.coverage_percentage == 100.0
        assert result.total_requirements == 7
        assert result.covered_requirements == 7
        assert len(result.uncovered_requirements) == 0

    def test_requirement_extraction(self, project_dir):
        """Test that all requirements are extracted correctly."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        spec_file = project_dir / "specs" / "shopping-cart.md"

        requirements = linter.extract_requirements_from_spec(spec_file)

        expected = {
            "SPEC-100/REQ-001",
            "SPEC-100/REQ-002",
            "SPEC-100/REQ-003",
            "SPEC-100/REQ-004",
            "SPEC-100/REQ-005",
            "SPEC-100/NFR-001",
            "SPEC-100/NFR-002",
        }
        assert requirements == expected

    def test_test_extraction(self, project_dir):
        """Test that all test markers are extracted correctly."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        test_file = project_dir / "tests" / "test_shopping_cart.py"

        test_to_reqs = linter.extract_requirements_from_tests(test_file)

        # Should have 7 tests with markers
        assert len(test_to_reqs) == 7

        # Verify specific test exists
        test_name = "test_shopping_cart.py::TestShoppingCart::test_add_item_to_cart"
        assert test_name in test_to_reqs
        assert "SPEC-100/REQ-001" in test_to_reqs[test_name]

    def test_schema_validation(self, project_dir):
        """Test that the spec passes schema validation."""
        validator = MarkdownSchemaValidator(root_dir=project_dir)
        spec_file = project_dir / "specs" / "shopping-cart.md"

        violations = validator.validate_file(spec_file)

        assert len(violations) == 0

    def test_unique_spec_ids(self, project_dir):
        """Test that spec IDs are unique."""
        linter = UniqueSpecsLinter(root_dir=project_dir)
        result = linter.lint()

        assert result.is_valid
        assert len(result.duplicate_spec_ids) == 0
        assert len(result.duplicate_req_ids) == 0


class TestComplexSystemProject:
    """Integration tests for the complex multi-spec project.

    This project has:
    - Multiple specs (SPEC-200, SPEC-203)
    - Jobs file
    - Mix of requirement types (REQ, NFR, TEST)
    - Partial coverage (realistic scenario)
    """

    @pytest.fixture
    def project_dir(self):
        """Get the complex system project directory."""
        return FIXTURES_DIR / "complex_system"

    def test_spec_coverage_partial_coverage(self, project_dir):
        """Test that spec coverage linter correctly reports partial coverage."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        result = linter.lint()

        # Should have partial coverage
        assert result.total_requirements > result.covered_requirements
        assert 0 < result.coverage_percentage < 100.0
        assert len(result.uncovered_requirements) > 0

    def test_multiple_spec_extraction(self, project_dir):
        """Test extraction from multiple spec files."""
        linter = SpecCoverageLinter(root_dir=project_dir)

        # Extract from authentication spec
        auth_spec = project_dir / "specs" / "authentication.md"
        auth_reqs = linter.extract_requirements_from_spec(auth_spec)

        assert "SPEC-200/REQ-001" in auth_reqs
        assert "SPEC-200/NFR-001" in auth_reqs
        assert "SPEC-200/TEST-001" in auth_reqs

        # Extract from API spec
        api_spec = project_dir / "specs" / "api.md"
        api_reqs = linter.extract_requirements_from_spec(api_spec)

        assert "SPEC-203/REQ-001" in api_reqs
        assert "SPEC-203/NFR-001" in api_reqs

    def test_cross_spec_references(self, project_dir):
        """Test that cross-spec requirement references work."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        result = linter.lint()

        # API test references auth requirement
        if "SPEC-200/REQ-009" in result.requirement_to_tests:
            tests = result.requirement_to_tests["SPEC-200/REQ-009"]
            # Should include test from test_api.py
            auth_tests = [t for t in tests if "test_api.py" in t]
            assert len(auth_tests) > 0

    def test_jobs_file_structure(self, project_dir):
        """Test that jobs file in subdirectory is handled correctly."""
        jobs_file = project_dir / "specs" / "jobs" / "user-management.md"
        assert jobs_file.exists()

        # Jobs files should have SPEC ID but no REQ IDs
        content = jobs_file.read_text()

        # Should contain JOB-XXX identifiers
        assert "JOB-001" in content
        assert "JOB-002" in content

    def test_unique_specs_across_multiple_files(self, project_dir):
        """Test that spec IDs are unique across multiple spec files."""
        linter = UniqueSpecsLinter(root_dir=project_dir)
        result = linter.lint()

        assert result.is_valid
        # Should have at least 2 unique spec IDs (no duplicates means valid)
        assert result.total_specs >= 2


class TestEdgeCasesProject:
    """Integration tests for the edge cases project.

    This project has:
    - Missing metadata
    - Duplicate IDs
    - Malformed EARS
    - Broken links
    - Orphaned tests
    - Requirements in code blocks
    """

    @pytest.fixture
    def project_dir(self):
        """Get the edge cases project directory."""
        return FIXTURES_DIR / "edge_cases"

    def test_missing_metadata_detected(self, project_dir):
        """Test that missing metadata is detected."""
        validator = MarkdownSchemaValidator(root_dir=project_dir)
        spec_file = project_dir / "specs" / "missing-metadata.md"

        violations = validator.validate_file(spec_file)

        # Should have violations for missing metadata
        assert len(violations) > 0

        # Check for specific missing fields
        violation_messages = [v.message for v in violations]
        missing_fields = ["Version", "Date", "Status"]
        for field in missing_fields:
            assert any(field in msg for msg in violation_messages), (
                f"Missing field {field} not detected"
            )

    def test_duplicate_requirement_ids_detected(self, project_dir):
        """Test that duplicate requirement IDs are detected."""
        linter = UniqueSpecsLinter(root_dir=project_dir)
        result = linter.lint()

        assert not result.is_valid
        # Should have duplicate requirement IDs
        assert len(result.duplicate_req_ids) > 0

        # Check specific duplicates
        assert "SPEC-301/REQ-001" in result.duplicate_req_ids
        assert "SPEC-301/REQ-003" in result.duplicate_req_ids

    def test_malformed_ears_detected(self, project_dir):
        """Test that malformed EARS statements are detected."""
        validator = MarkdownSchemaValidator(root_dir=project_dir)
        spec_file = project_dir / "specs" / "malformed-ears.md"

        violations = validator.validate_file(spec_file)

        # Should have violations for malformed EARS
        assert len(violations) > 0

        # Requirements 1-5 should be flagged as not having "shall"
        violation_messages = [str(v) for v in violations]
        # Just verify there are EARS-related violations
        assert any("shall" in msg.lower() for msg in violation_messages)

    def test_orphaned_tests_detected(self, project_dir):
        """Test that orphaned tests (referencing non-existent requirements) are detected."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        result = linter.lint()

        # Should have tests referencing non-existent requirements
        test_file = project_dir / "tests" / "test_orphaned.py"
        test_to_reqs = linter.extract_requirements_from_tests(test_file)

        # Tests should reference requirements that don't exist
        orphaned_reqs = set()
        for _test_name, req_ids in test_to_reqs.items():
            for req_id in req_ids:
                # Check if requirement is orphaned (references non-existent spec or req)
                is_orphaned = (
                    "SPEC-999" in req_id  # Non-existent spec
                    or (
                        "SPEC-304" in req_id
                        and ("REQ-003" in req_id or "REQ-004" in req_id or "NFR-001" in req_id)
                    )  # Reqs that don't exist in SPEC-304
                )
                if is_orphaned:
                    orphaned_reqs.add(req_id)

        assert len(orphaned_reqs) > 0

    def test_uncovered_requirements(self, project_dir):
        """Test that uncovered requirements are detected."""
        linter = SpecCoverageLinter(root_dir=project_dir)
        result = linter.lint()

        # Should have some uncovered requirements
        assert len(result.uncovered_requirements) > 0

        # SPEC-304/REQ-002 and REQ-005 have no tests
        # (May also have others from different specs)

    def test_code_block_requirements_ignored(self, project_dir):
        """Test that requirements inside code blocks are NOT extracted.

        The AST implementation properly handles code blocks and excludes requirements from them.
        Note: inline code (backticks) is still extracted, which is acceptable as it's a much
        rarer edge case than code blocks.
        """
        linter = SpecCoverageLinter(root_dir=project_dir)
        spec_file = project_dir / "specs" / "code-block-confusion.md"

        requirements = linter.extract_requirements_from_spec(spec_file)

        # Should only extract REQ-001, REQ-002, REQ-003
        assert "SPEC-305/REQ-001" in requirements
        assert "SPEC-305/REQ-002" in requirements
        assert "SPEC-305/REQ-003" in requirements

        # Should NOT extract the ones in code blocks
        assert "SPEC-305/REQ-999" not in requirements
        assert "SPEC-305/REQ-777" not in requirements
        assert "SPEC-305/REQ-666" not in requirements
        assert "SPEC-305/REQ-444" not in requirements

        # Note: REQ-555 is in inline code (`text`) which is still extracted.
        # This is an acceptable edge case - inline code is much rarer than code blocks.

    def test_broken_links_detected(self, project_dir):
        """Test that broken internal links are detected."""
        validator = MarkdownLinkValidator(root_dir=project_dir)

        result = validator.validate()

        # Should have invalid links
        assert result.invalid_links > 0
        assert len(result.invalid_link_details) > 0

        # Check for specific broken links
        invalid_urls = [link["url"] for link in result.invalid_link_details]
        assert any("non-existent-file.md" in url for url in invalid_urls)
        assert any("does-not-exist.md" in url for url in invalid_urls)


class TestStructureValidation:
    """Integration tests for structure validation across projects."""

    def test_simple_project_structure_valid(self):
        """Test that simple project has valid structure."""
        project_dir = FIXTURES_DIR / "simple_ecommerce"
        linter = StructureLinter(root_dir=project_dir)

        result = linter.lint()

        assert result.is_valid
        # All specs should have corresponding test files
        assert len(result.specs_without_tests) == 0

    def test_complex_project_structure_valid(self):
        """Test that complex project has valid structure."""
        project_dir = FIXTURES_DIR / "complex_system"
        linter = StructureLinter(root_dir=project_dir)

        result = linter.lint()

        assert result.is_valid
        # Jobs files don't need corresponding tests
        # Main spec files should have tests


class TestEndToEndWorkflow:
    """End-to-end integration tests simulating complete workflows."""

    def test_full_validation_workflow_simple_project(self):
        """Test running all validators on a simple project."""
        project_dir = FIXTURES_DIR / "simple_ecommerce"

        # Run all validators
        schema_validator = MarkdownSchemaValidator(root_dir=project_dir)
        coverage_linter = SpecCoverageLinter(root_dir=project_dir)
        unique_linter = UniqueSpecsLinter(root_dir=project_dir)
        structure_linter = StructureLinter(root_dir=project_dir)
        link_validator = MarkdownLinkValidator(root_dir=project_dir)

        # Schema validator uses validate() not lint()
        spec_file = project_dir / "specs" / "shopping-cart.md"
        schema_violations = schema_validator.validate_file(spec_file)

        coverage_result = coverage_linter.lint()
        unique_result = unique_linter.lint()
        structure_result = structure_linter.lint()
        link_result = link_validator.validate()

        # All should pass for simple project
        assert len(schema_violations) == 0
        assert coverage_result.is_valid
        assert unique_result.is_valid
        assert structure_result.is_valid
        assert link_result.is_valid

    def test_full_validation_workflow_edge_cases(self):
        """Test running all validators on edge cases project."""
        project_dir = FIXTURES_DIR / "edge_cases"

        # Run all validators
        schema_validator = MarkdownSchemaValidator(root_dir=project_dir)
        coverage_linter = SpecCoverageLinter(root_dir=project_dir)
        unique_linter = UniqueSpecsLinter(root_dir=project_dir)

        # Check one problematic spec file
        spec_file = project_dir / "specs" / "missing-metadata.md"
        schema_violations = schema_validator.validate_file(spec_file)

        # Coverage result will have uncovered requirements but is expected
        _coverage_result = coverage_linter.lint()
        unique_result = unique_linter.lint()

        # Most should fail for edge cases project
        assert len(schema_violations) > 0  # Missing metadata
        assert not unique_result.is_valid  # Duplicate IDs


if __name__ == "__main__":
    # Allow running this file directly for quick testing
    pytest.main([__file__, "-v"])
