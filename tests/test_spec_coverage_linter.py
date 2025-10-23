"""Tests for the spec coverage linter."""

from spec_tools.spec_coverage_linter import SpecCoverageLinter


class TestSpecCoverageLinter:
    """Test suite for SpecCoverageLinter."""

    def test_extract_requirements_from_spec(self, tmp_path):
        """Test extracting requirement IDs from a spec file."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "test-spec.md"
        spec_file.write_text(
            """
# Test Specification

**ID**: SPEC-001

**REQ-001**: The system shall do something.

**REQ-002**: The system shall do something else.

**NFR-001**: The system shall be fast.
"""
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        requirements = linter.extract_requirements_from_spec(spec_file)

        assert "SPEC-001/REQ-001" in requirements
        assert "SPEC-001/REQ-002" in requirements
        assert "SPEC-001/NFR-001" in requirements
        assert len(requirements) == 3

    def test_extract_requirements_from_tests(self, tmp_path):
        """Test extracting requirement markers from test files."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_example.py"
        test_file.write_text(
            '''"""Test module."""

import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_something():
    """Test for REQ-001."""
    assert True

@pytest.mark.req("SPEC-999/REQ-002", "SPEC-999/REQ-003")
def test_combined():
    """Test for REQ-002 and REQ-003."""
    assert True

def test_unmarked():
    """Test without marker."""
    assert True
'''
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        test_to_reqs = linter.extract_requirements_from_tests(test_file)

        assert "test_example.py::test_something" in test_to_reqs
        assert "SPEC-999/REQ-001" in test_to_reqs["test_example.py::test_something"]

        assert "test_example.py::test_combined" in test_to_reqs
        assert "SPEC-999/REQ-002" in test_to_reqs["test_example.py::test_combined"]
        assert "SPEC-999/REQ-003" in test_to_reqs["test_example.py::test_combined"]

        # Unmarked test should not appear
        assert "test_example.py::test_unmarked" not in test_to_reqs

    def test_extract_requirements_from_class_tests(self, tmp_path):
        """Test extracting requirements from class-based tests."""
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_class.py"
        test_file.write_text(
            '''"""Test module with class."""

import pytest

class TestFeature:
    """Test class."""

    @pytest.mark.req("SPEC-999/REQ-001")
    def test_method(self):
        """Test method."""
        assert True
'''
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        test_to_reqs = linter.extract_requirements_from_tests(test_file)

        assert "test_class.py::TestFeature::test_method" in test_to_reqs
        assert "SPEC-999/REQ-001" in test_to_reqs["test_class.py::TestFeature::test_method"]

    def test_full_coverage(self, tmp_path):
        """Test when all requirements are covered."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text(
            """**ID**: SPEC-999

**REQ-001**: Do something.
**REQ-002**: Do something else.
"""
        )

        # Create tests
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text(
            """import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_req_001():
    assert True

@pytest.mark.req("SPEC-999/REQ-002")
def test_req_002():
    assert True
"""
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_requirements == 2
        assert result.covered_requirements == 2
        assert len(result.uncovered_requirements) == 0
        assert result.coverage_percentage == 100.0

    def test_partial_coverage(self, tmp_path):
        """Test when some requirements are uncovered."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text(
            """**ID**: SPEC-999

**REQ-001**: Do something.
**REQ-002**: Do something else.
**REQ-003**: Do another thing.
"""
        )

        # Create tests (only covering REQ-001)
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text(
            """import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_req_001():
    assert True
"""
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        assert not result.is_valid
        assert result.total_requirements == 3
        assert result.covered_requirements == 1
        assert len(result.uncovered_requirements) == 2
        assert "SPEC-999/REQ-002" in result.uncovered_requirements
        assert "SPEC-999/REQ-003" in result.uncovered_requirements
        assert result.coverage_percentage < 100.0

    def test_tests_without_markers(self, tmp_path):
        """Test detection of tests without requirement markers."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Do something.")

        # Create tests with some unmarked
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text(
            """import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_marked():
    assert True

def test_unmarked():
    assert True
"""
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.total_tests == 2
        assert result.tests_with_requirements == 1
        assert len(result.tests_without_requirements) == 1
        assert "test_feature.py::test_unmarked" in result.tests_without_requirements[0]

    def test_multiple_specs(self, tmp_path):
        """Test with multiple spec files."""
        # Create multiple specs
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature1.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Feature 1.")
        (spec_dir / "feature2.md").write_text("**ID**: SPEC-999\n\n**REQ-002**: Feature 2.")

        # Create tests
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_features.py").write_text(
            """import pytest

@pytest.mark.req("SPEC-999/REQ-001", "REQ-002")
def test_both():
    assert True
"""
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_requirements == 2
        assert result.covered_requirements == 2

    def test_requirement_to_tests_mapping(self, tmp_path):
        """Test the requirement-to-tests mapping."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Do something.")

        # Create multiple tests for same requirement
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text(
            """import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_req_001_a():
    assert True

@pytest.mark.req("SPEC-999/REQ-001")
def test_req_001_b():
    assert True
"""
        )

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        assert "SPEC-999/REQ-001" in result.requirement_to_tests
        assert len(result.requirement_to_tests["SPEC-999/REQ-001"]) == 2

    def test_empty_specs_dir(self, tmp_path):
        """Test with no spec files."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.total_requirements == 0
        assert result.coverage_percentage == 0.0

    def test_result_string_representation(self, tmp_path):
        """Test the string representation of results."""
        # Create minimal setup
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Do something.")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        result_str = str(result)
        assert "SPEC COVERAGE REPORT" in result_str
        assert "Coverage:" in result_str
        assert "REQ-001" in result_str

    def test_malformed_test_file_handling(self, tmp_path):
        """Test that malformed test files are handled gracefully."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Do something.")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Create a malformed Python file
        (tests_dir / "test_malformed.py").write_text("def test_something(:\n    # Invalid syntax")

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        # Should not crash, should report uncovered requirement
        assert result.total_requirements == 1
        assert "SPEC-999/REQ-001" in result.uncovered_requirements

    def test_complete_coverage_with_tests_without_markers(self, tmp_path):
        """Test reporting when all requirements are covered but some tests lack markers."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Do something.")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        # Test with marker
        (tests_dir / "test_feature.py").write_text("""
import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_requirement_one():
    pass

def test_helper_function():
    # This test has no requirement marker
    pass
""")

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        # All requirements covered, but some tests without markers
        assert result.coverage_percentage == 100.0
        assert len(result.tests_without_requirements) > 0
        assert any("test_helper_function" in test for test in result.tests_without_requirements)

    def test_100_percent_coverage_passes(self, tmp_path):
        """Test that 100% coverage results in is_valid=True."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("**ID**: SPEC-999\n\n**REQ-001**: Do something.")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        (tests_dir / "test_feature.py").write_text("""
import pytest

@pytest.mark.req("SPEC-999/REQ-001")
def test_requirement_one():
    pass
""")

        linter = SpecCoverageLinter(root_dir=tmp_path)
        result = linter.lint()

        # 100% coverage should pass
        assert result.is_valid
        assert result.coverage_percentage == 100.0
        assert "✅ Spec coverage validation PASSED" in str(result)
