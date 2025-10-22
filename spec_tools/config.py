"""Configuration loading from pyproject.toml."""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Use tomllib for Python 3.11+, tomli for older versions
if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomli as tomllib
    except ImportError:
        tomllib = None  # type: ignore


class Config:
    """Configuration container for spec-tools settings."""

    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        """Initialize configuration.

        Args:
            config_dict: Dictionary containing configuration values.
        """
        self._config = config_dict or {}

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (can use dot notation for nested keys).
            default: Default value if key not found.

        Returns:
            Configuration value or default.
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
                if value is None:
                    return default
            else:
                return default
        return value

    def get_lint_config(self) -> Dict[str, Any]:
        """Get lint-specific configuration.

        Returns:
            Dictionary of lint configuration values.
        """
        return self.get("lint", {})

    def get_check_links_config(self) -> Dict[str, Any]:
        """Get check-links-specific configuration.

        Returns:
            Dictionary of check-links configuration values.
        """
        return self.get("check-links", {})

    def get_check_schema_config(self) -> Dict[str, Any]:
        """Get check-schema-specific configuration.

        Returns:
            Dictionary of check-schema configuration values.
        """
        return self.get("check-schema", {})


def find_pyproject_toml(start_path: Optional[Path] = None) -> Optional[Path]:
    """Find pyproject.toml by walking up the directory tree.

    Args:
        start_path: Starting directory. Defaults to current directory.

    Returns:
        Path to pyproject.toml if found, None otherwise.
    """
    if start_path is None:
        start_path = Path.cwd()
    else:
        start_path = Path(start_path).resolve()

    # Walk up the directory tree
    current = start_path
    while True:
        pyproject_path = current / "pyproject.toml"
        if pyproject_path.exists():
            return pyproject_path

        # Check if we've reached the root
        parent = current.parent
        if parent == current:
            break
        current = parent

    return None


def load_config(root_dir: Optional[Path] = None) -> Config:
    """Load configuration from pyproject.toml.

    Args:
        root_dir: Root directory to start searching. Defaults to current directory.

    Returns:
        Config object with loaded configuration.
    """
    if tomllib is None:
        # If tomli is not available and Python < 3.11, return empty config
        return Config()

    pyproject_path = find_pyproject_toml(root_dir)
    if pyproject_path is None:
        return Config()

    try:
        with open(pyproject_path, "rb") as f:
            data = tomllib.load(f)

        # Extract tool.spec-tools section
        tool_config = data.get("tool", {}).get("spec-tools", {})
        return Config(tool_config)
    except Exception:
        # If there's any error reading the file, return empty config
        return Config()


def merge_config_with_args(config: Config, args: Any, command: str) -> Dict[str, Any]:
    """Merge configuration from pyproject.toml with command-line arguments.

    Command-line arguments take precedence over pyproject.toml configuration.

    Args:
        config: Config object from pyproject.toml.
        args: Parsed command-line arguments.
        command: Command name ('lint', 'check-links', or 'check-schema').

    Returns:
        Dictionary of merged configuration values.
    """
    result = {}

    if command == "lint":
        cmd_config = config.get_lint_config()
        # allowlist file
        if args.allowlist is not None:
            result["allowlist_file"] = args.allowlist
        elif "allowlist" in cmd_config:
            result["allowlist_file"] = cmd_config["allowlist"]
        else:
            result["allowlist_file"] = None

        # use_gitignore
        if args.no_gitignore:
            result["use_gitignore"] = False
        elif "use_gitignore" in cmd_config:
            result["use_gitignore"] = cmd_config["use_gitignore"]
        else:
            result["use_gitignore"] = True

    elif command == "check-links":
        cmd_config = config.get_check_links_config()

        # config file
        if args.config is not None:
            result["config_file"] = args.config
        elif "config" in cmd_config:
            result["config_file"] = cmd_config["config"]
        else:
            result["config_file"] = None

        # timeout
        if args.timeout is not None:
            result["timeout"] = args.timeout
        elif "timeout" in cmd_config:
            result["timeout"] = cmd_config["timeout"]
        else:
            result["timeout"] = 10

        # max_concurrent
        if args.max_concurrent is not None:
            result["max_concurrent"] = args.max_concurrent
        elif "max_concurrent" in cmd_config:
            result["max_concurrent"] = cmd_config["max_concurrent"]
        else:
            result["max_concurrent"] = 10

        # check_external
        if args.no_external:
            result["check_external"] = False
        elif "check_external" in cmd_config:
            result["check_external"] = cmd_config["check_external"]
        else:
            result["check_external"] = True

        # use_gitignore
        if args.no_gitignore:
            result["use_gitignore"] = False
        elif "use_gitignore" in cmd_config:
            result["use_gitignore"] = cmd_config["use_gitignore"]
        else:
            result["use_gitignore"] = True

    elif command == "check-schema":
        cmd_config = config.get_check_schema_config()

        # config file
        if args.config is not None:
            result["config_file"] = args.config
        elif "config" in cmd_config:
            result["config_file"] = cmd_config["config"]
        else:
            result["config_file"] = None

        # respect_gitignore
        if args.no_gitignore:
            result["respect_gitignore"] = False
        elif "use_gitignore" in cmd_config:
            result["respect_gitignore"] = cmd_config["use_gitignore"]
        else:
            result["respect_gitignore"] = True

    return result
