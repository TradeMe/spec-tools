"""
Tests for REQ-001: Markdown Link Validation System.
"""

from pathlib import Path


class TestReq001:
    """Test REQ-001 specification."""

    def test_req_001_exists(self):
        """Test that REQ-001 spec file exists."""
        spec_path = Path("specs/requirements/REQ-001.md")
        assert spec_path.exists(), "REQ-001.md should exist"

    def test_req_001_has_required_sections(self):
        """Test that REQ-001 has all required sections."""
        spec_path = Path("specs/requirements/REQ-001.md")
        content = spec_path.read_text()

        required_sections = [
            "## Purpose",
            "## Description",
            "## Acceptance Criteria",
            "## Jobs Addressed",
        ]
        for section in required_sections:
            assert section in content, f"REQ-001 should have {section} section"

    def test_req_001_addresses_job_001(self):
        """Test that REQ-001 addresses JOB-001."""
        spec_path = Path("specs/requirements/REQ-001.md")
        content = spec_path.read_text()

        assert "JOB-001" in content, "REQ-001 should reference JOB-001"

    def test_req_001_has_acceptance_criteria(self):
        """Test that REQ-001 has properly formatted acceptance criteria."""
        spec_path = Path("specs/requirements/REQ-001.md")
        content = spec_path.read_text()

        # Check for AC-## format
        assert "### AC-" in content, "REQ-001 should have AC-## format criteria"
