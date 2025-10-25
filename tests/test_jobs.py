"""
Tests for Jobs-to-be-Done specifications.

These tests verify that the Jobs specifications are properly structured
and describe user needs, pains, and desired outcomes.
"""

from pathlib import Path


class TestJobSpecifications:
    """Test Jobs-to-be-Done specification structure and content."""

    def test_job_specs_exist(self):
        """Test that Job specification files exist."""
        jobs_dir = Path("specs/jobs")
        assert jobs_dir.exists(), "Jobs directory should exist"

        expected_jobs = ["JOB-001.md", "JOB-002.md", "JOB-003.md"]
        for job_file in expected_jobs:
            job_path = jobs_dir / job_file
            assert job_path.exists(), f"{job_file} should exist"

    def test_job_001_structure(self):
        """Test JOB-001 has required sections."""
        job_path = Path("specs/jobs/JOB-001.md")
        content = job_path.read_text()

        # Check required sections
        assert "## Context" in content
        assert "## Job Story" in content
        assert "## Pains" in content
        assert "## Gains" in content

    def test_job_002_structure(self):
        """Test JOB-002 has required sections."""
        job_path = Path("specs/jobs/JOB-002.md")
        content = job_path.read_text()

        assert "## Context" in content
        assert "## Job Story" in content
        assert "## Pains" in content
        assert "## Gains" in content

    def test_job_003_structure(self):
        """Test JOB-003 has required sections."""
        job_path = Path("specs/jobs/JOB-003.md")
        content = job_path.read_text()

        assert "## Context" in content
        assert "## Job Story" in content
        assert "## Pains" in content
        assert "## Gains" in content

    def test_job_identifiers_match_filename(self):
        """Test that Job IDs in files match their filenames."""
        jobs_dir = Path("specs/jobs")

        for job_file in jobs_dir.glob("JOB-*.md"):
            content = job_file.read_text()
            job_id = job_file.stem  # e.g., "JOB-001"

            # Check that the ID appears in the title
            assert job_id in content, f"{job_id} should appear in {job_file.name}"
