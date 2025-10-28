"""Tests for CLI functionality."""

import subprocess
import sys


def test_version_flag_reports_package_version():
    """Test that --version reports the correct package version from metadata.

    This test reproduces issue #32 where spec-check --version reports
    an outdated hardcoded version (0.1.0) instead of the actual installed
    package version from package metadata.

    The version should be sourced from importlib.metadata.version('spec-check')
    rather than hardcoded in the source.
    """
    # Run spec-check --version
    result = subprocess.run(
        [sys.executable, "-m", "spec_check.cli", "--version"],
        capture_output=True,
        text=True,
    )

    # Should exit successfully
    assert result.returncode == 0

    # Get the actual package version
    from importlib.metadata import version

    expected_version = version("spec-check")

    # Version output should contain the package version
    # Format is "spec-check <version>"
    version_output = result.stdout.strip()

    assert f"spec-check {expected_version}" in version_output, (
        f"Expected version output to contain 'spec-check {expected_version}', "
        f"but got: {version_output}"
    )
