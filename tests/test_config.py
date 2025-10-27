"""Tests for configuration loading from pyproject.toml."""

import sys
import tempfile
from pathlib import Path

import pytest

from spec_check.config import Config, find_pyproject_toml, load_config, merge_config_with_args


class MockArgs:
    """Mock command-line arguments."""

    def __init__(self, **kwargs):
        """Initialize with keyword arguments."""
        for key, value in kwargs.items():
            setattr(self, key, value)


def test_config_get():
    """Test Config.get() method."""
    config = Config({"lint": {"allowlist": "custom.txt"}, "timeout": 30})
    assert config.get("lint.allowlist") == "custom.txt"
    assert config.get("timeout") == 30
    assert config.get("nonexistent", "default") == "default"


def test_config_get_lint_config():
    """Test Config.get_lint_config() method."""
    config = Config({"lint": {"allowlist": "custom.txt", "use_gitignore": False}})
    lint_config = config.get_lint_config()
    assert lint_config == {"allowlist": "custom.txt", "use_gitignore": False}


def test_config_get_check_links_config():
    """Test Config.get_check_links_config() method."""
    config = Config({"check-links": {"timeout": 20, "max_concurrent": 5, "check_external": False}})
    links_config = config.get_check_links_config()
    assert links_config == {"timeout": 20, "max_concurrent": 5, "check_external": False}


def test_config_get_check_schema_config():
    """Test Config.get_check_schema_config() method."""
    config = Config({"check-schema": {"config": "custom.yaml", "use_gitignore": True}})
    schema_config = config.get_check_schema_config()
    assert schema_config == {"config": "custom.yaml", "use_gitignore": True}


def test_find_pyproject_toml():
    """Test finding pyproject.toml in directory tree."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create a nested directory structure
        nested_dir = tmp_path / "a" / "b" / "c"
        nested_dir.mkdir(parents=True)

        # Create pyproject.toml in root
        pyproject_path = tmp_path / "pyproject.toml"
        pyproject_path.write_text("[tool.spec-check]\n")

        # Should find it from nested directory
        found = find_pyproject_toml(nested_dir)
        assert found == pyproject_path


def test_find_pyproject_toml_not_found():
    """Test when pyproject.toml is not found."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        found = find_pyproject_toml(tmp_path)
        assert found is None


@pytest.mark.skipif(
    sys.version_info < (3, 11) and "tomli" not in sys.modules,
    reason="tomli not available",
)
def test_load_config():
    """Test loading configuration from pyproject.toml."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)
        pyproject_path = tmp_path / "pyproject.toml"

        # Write a test pyproject.toml
        pyproject_path.write_text(
            """
[tool.spec-check.lint]
allowlist = "custom.txt"
use_gitignore = false

[tool.spec-check.check-links]
timeout = 20
max_concurrent = 5
"""
        )

        config = load_config(tmp_path)
        assert config.get("lint.allowlist") == "custom.txt"
        assert config.get("lint.use_gitignore") is False
        assert config.get("check-links.timeout") == 20
        assert config.get("check-links.max_concurrent") == 5


def test_merge_config_with_args_lint():
    """Test merging config with command-line arguments for lint."""
    config = Config({"lint": {"allowlist": "from_toml.txt", "use_gitignore": False}})

    # Test with CLI args overriding config
    args = MockArgs(allowlist="from_cli.txt", no_gitignore=True)
    result = merge_config_with_args(config, args, "lint")
    assert result["allowlist_file"] == "from_cli.txt"
    assert result["use_gitignore"] is False

    # Test with config values used
    args = MockArgs(allowlist=None, no_gitignore=False)
    result = merge_config_with_args(config, args, "lint")
    assert result["allowlist_file"] == "from_toml.txt"
    assert result["use_gitignore"] is False


def test_merge_config_with_args_check_links():
    """Test merging config with command-line arguments for check-links."""
    config = Config(
        {
            "check-links": {
                "timeout": 20,
                "max_concurrent": 5,
                "check_external": False,
                "use_gitignore": False,
            }
        }
    )

    # Test with CLI args overriding some values
    args = MockArgs(
        config=None, timeout=30, max_concurrent=10, no_external=False, no_gitignore=True
    )
    result = merge_config_with_args(config, args, "check-links")
    assert result["timeout"] == 30  # CLI override
    assert result["max_concurrent"] == 10  # CLI override
    assert result["check_external"] is False  # from config
    assert result["use_gitignore"] is False  # CLI override

    # Test with config values used when CLI args are None
    args = MockArgs(
        config=None, timeout=None, max_concurrent=None, no_external=False, no_gitignore=False
    )
    result = merge_config_with_args(config, args, "check-links")
    assert result["timeout"] == 20  # from config
    assert result["max_concurrent"] == 5  # from config
    assert result["check_external"] is False  # from config
    assert result["use_gitignore"] is False  # from config


def test_merge_config_with_args_check_schema():
    """Test merging config with command-line arguments for check-schema."""
    config = Config({"check-schema": {"config": "from_toml.yaml", "use_gitignore": False}})

    # Test with CLI args
    args = MockArgs(config=None, no_gitignore=False)
    result = merge_config_with_args(config, args, "check-schema")
    assert result["config_file"] == "from_toml.yaml"
    assert result["respect_gitignore"] is False


def test_merge_config_with_args_defaults():
    """Test merging with empty config uses defaults."""
    config = Config({})

    # Test lint defaults
    args = MockArgs(allowlist=None, no_gitignore=False)
    result = merge_config_with_args(config, args, "lint")
    assert result["allowlist_file"] is None
    assert result["use_gitignore"] is True

    # Test check-links defaults
    args = MockArgs(
        config=None,
        timeout=None,
        max_concurrent=None,
        no_external=False,
        no_gitignore=False,
    )
    result = merge_config_with_args(config, args, "check-links")
    assert result["config_file"] is None
    assert result["timeout"] == 10
    assert result["max_concurrent"] == 10
    assert result["check_external"] is True
    assert result["use_gitignore"] is True

    # Test check-schema defaults
    args = MockArgs(config=None, no_gitignore=False)
    result = merge_config_with_args(config, args, "check-schema")
    assert result["config_file"] is None
    assert result["respect_gitignore"] is True
