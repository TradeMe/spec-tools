"""
Tests for Requirement specifications.

These tests verify that Requirements are properly structured and
address Jobs-to-be-Done with acceptance criteria.
"""

from pathlib import Path


class TestRequirementSpecifications:
    """Test Requirement specification structure and content."""

    def test_requirement_specs_exist(self):
        """Test that Requirement specification files exist."""
        req_dir = Path("specs/requirements")
        assert req_dir.exists(), "Requirements directory should exist"

        expected_reqs = ["REQ-001.md", "REQ-002.md", "REQ-003.md"]
        for req_file in expected_reqs:
            req_path = req_dir / req_file
            assert req_path.exists(), f"{req_file} should exist"

    def test_req_001_structure(self):
        """Test REQ-001 has required sections."""
        req_path = Path("specs/requirements/REQ-001.md")
        content = req_path.read_text()

        # Check required sections
        assert "## Purpose" in content
        assert "## Description" in content
        assert "## Acceptance Criteria" in content
        assert "## Jobs Addressed" in content

    def test_req_002_structure(self):
        """Test REQ-002 has required sections."""
        req_path = Path("specs/requirements/REQ-002.md")
        content = req_path.read_text()

        assert "## Purpose" in content
        assert "## Description" in content
        assert "## Acceptance Criteria" in content
        assert "## Jobs Addressed" in content

    def test_req_003_structure(self):
        """Test REQ-003 has required sections."""
        req_path = Path("specs/requirements/REQ-003.md")
        content = req_path.read_text()

        assert "## Purpose" in content
        assert "## Description" in content
        assert "## Acceptance Criteria" in content
        assert "## Jobs Addressed" in content

    def test_requirements_address_jobs(self):
        """Test that Requirements reference at least one Job."""
        req_dir = Path("specs/requirements")

        for req_file in req_dir.glob("REQ-*.md"):
            content = req_file.read_text()

            # Check for Jobs Addressed section
            assert "## Jobs Addressed" in content, f"{req_file.name} missing Jobs Addressed section"

            # Check that at least one JOB-xxx is mentioned
            assert "JOB-" in content, f"{req_file.name} should reference at least one Job"

    def test_requirement_identifiers_match_filename(self):
        """Test that Requirement IDs in files match their filenames."""
        req_dir = Path("specs/requirements")

        for req_file in req_dir.glob("REQ-*.md"):
            content = req_file.read_text()
            req_id = req_file.stem  # e.g., "REQ-001"

            # Check that the ID appears in the title
            assert req_id in content, f"{req_id} should appear in {req_file.name}"

    def test_acceptance_criteria_format(self):
        """Test that Requirements have properly formatted acceptance criteria."""
        req_dir = Path("specs/requirements")

        for req_file in req_dir.glob("REQ-*.md"):
            content = req_file.read_text()

            # Check for AC-## format
            assert "### AC-" in content, f"{req_file.name} should have AC-## format criteria"

            # Check for Given/When/Then or similar structure
            has_bdd = any(keyword in content for keyword in ["Given", "When", "Then"])
            assert has_bdd, f"{req_file.name} should have BDD-style acceptance criteria"
