"""
Tests for REQ-003: Markdown Schema Validation System.
"""

from pathlib import Path


class TestReq003:
    """Test REQ-003 specification."""

    def test_req_003_exists(self):
        """Test that REQ-003 spec file exists."""
        spec_path = Path("specs/requirements/REQ-003.md")
        assert spec_path.exists(), "REQ-003.md should exist"

    def test_req_003_has_required_sections(self):
        """Test that REQ-003 has all required sections."""
        spec_path = Path("specs/requirements/REQ-003.md")
        content = spec_path.read_text()

        required_sections = [
            "## Purpose",
            "## Description",
            "## Acceptance Criteria",
            "## Jobs Addressed",
        ]
        for section in required_sections:
            assert section in content, f"REQ-003 should have {section} section"

    def test_req_003_addresses_job_003(self):
        """Test that REQ-003 addresses JOB-003."""
        spec_path = Path("specs/requirements/REQ-003.md")
        content = spec_path.read_text()

        assert "JOB-003" in content, "REQ-003 should reference JOB-003"

    def test_req_003_has_acceptance_criteria(self):
        """Test that REQ-003 has properly formatted acceptance criteria."""
        spec_path = Path("specs/requirements/REQ-003.md")
        content = spec_path.read_text()

        # Check for AC-## format
        assert "### AC-" in content, "REQ-003 should have AC-## format criteria"
