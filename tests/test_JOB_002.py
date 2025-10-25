"""
Tests for JOB-002: Maintain Traceability Between Specifications and Tests.
"""

from pathlib import Path


class TestJob002:
    """Test JOB-002 specification."""

    def test_job_002_exists(self):
        """Test that JOB-002 spec file exists."""
        spec_path = Path("specs/jobs/JOB-002.md")
        assert spec_path.exists(), "JOB-002.md should exist"

    def test_job_002_has_required_sections(self):
        """Test that JOB-002 has all required sections."""
        spec_path = Path("specs/jobs/JOB-002.md")
        content = spec_path.read_text()

        required_sections = ["## Context", "## Job Story", "## Pains", "## Gains"]
        for section in required_sections:
            assert section in content, f"JOB-002 should have {section} section"

    def test_job_002_addresses_traceability(self):
        """Test that JOB-002 describes traceability needs."""
        spec_path = Path("specs/jobs/JOB-002.md")
        content = spec_path.read_text()

        # Check for key concepts related to traceability
        assert "traceability" in content.lower() or "coverage" in content.lower()
        assert "specification" in content.lower() or "requirement" in content.lower()
