"""
Tests for REQ-002: Specification Coverage Tracking System.
"""

from pathlib import Path


class TestReq002:
    """Test REQ-002 specification."""

    def test_req_002_exists(self):
        """Test that REQ-002 spec file exists."""
        spec_path = Path("specs/requirements/REQ-002.md")
        assert spec_path.exists(), "REQ-002.md should exist"

    def test_req_002_has_required_sections(self):
        """Test that REQ-002 has all required sections."""
        spec_path = Path("specs/requirements/REQ-002.md")
        content = spec_path.read_text()

        required_sections = [
            "## Purpose",
            "## Description",
            "## Acceptance Criteria",
            "## Jobs Addressed",
        ]
        for section in required_sections:
            assert section in content, f"REQ-002 should have {section} section"

    def test_req_002_addresses_job_002(self):
        """Test that REQ-002 addresses JOB-002."""
        spec_path = Path("specs/requirements/REQ-002.md")
        content = spec_path.read_text()

        assert "JOB-002" in content, "REQ-002 should reference JOB-002"

    def test_req_002_has_acceptance_criteria(self):
        """Test that REQ-002 has properly formatted acceptance criteria."""
        spec_path = Path("specs/requirements/REQ-002.md")
        content = spec_path.read_text()

        # Check for AC-## format
        assert "### AC-" in content, "REQ-002 should have AC-## format criteria"
