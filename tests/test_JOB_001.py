"""
Tests for JOB-001: Ensure Documentation Links Remain Valid.
"""

from pathlib import Path


class TestJob001:
    """Test JOB-001 specification."""

    def test_job_001_exists(self):
        """Test that JOB-001 spec file exists."""
        spec_path = Path("specs/jobs/JOB-001.md")
        assert spec_path.exists(), "JOB-001.md should exist"

    def test_job_001_has_required_sections(self):
        """Test that JOB-001 has all required sections."""
        spec_path = Path("specs/jobs/JOB-001.md")
        content = spec_path.read_text()

        required_sections = ["## Context", "## Job Story", "## Pains", "## Gains"]
        for section in required_sections:
            assert section in content, f"JOB-001 should have {section} section"

    def test_job_001_addresses_link_validation(self):
        """Test that JOB-001 describes link validation needs."""
        spec_path = Path("specs/jobs/JOB-001.md")
        content = spec_path.read_text()

        # Check for key concepts related to link validation
        assert "link" in content.lower() or "hyperlink" in content.lower()
        assert "documentation" in content.lower()
