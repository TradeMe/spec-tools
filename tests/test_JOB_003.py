"""
Tests for JOB-003: Enforce Consistent Specification Structure.
"""

from pathlib import Path


class TestJob003:
    """Test JOB-003 specification."""

    def test_job_003_exists(self):
        """Test that JOB-003 spec file exists."""
        spec_path = Path("specs/jobs/JOB-003.md")
        assert spec_path.exists(), "JOB-003.md should exist"

    def test_job_003_has_required_sections(self):
        """Test that JOB-003 has all required sections."""
        spec_path = Path("specs/jobs/JOB-003.md")
        content = spec_path.read_text()

        required_sections = ["## Context", "## Job Story", "## Pains", "## Gains"]
        for section in required_sections:
            assert section in content, f"JOB-003 should have {section} section"

    def test_job_003_addresses_structure_validation(self):
        """Test that JOB-003 describes structure validation needs."""
        spec_path = Path("specs/jobs/JOB-003.md")
        content = spec_path.read_text()

        # Check for key concepts related to structure validation
        assert "structure" in content.lower() or "format" in content.lower()
        assert "specification" in content.lower() or "document" in content.lower()
