"""Core linter logic for validating files against an allowlist."""

import os
from dataclasses import dataclass
from pathlib import Path

import pathspec


@dataclass
class LintResult:
    """Result of running the linter."""

    total_files: int
    matched_files: int
    unmatched_files: list[str]
    ignored_files: int

    @property
    def is_valid(self) -> bool:
        """Returns True if all files are matched."""
        return len(self.unmatched_files) == 0

    def __str__(self) -> str:
        """Human-readable summary of the lint result."""
        lines = [
            f"Total files checked: {self.total_files}",
            f"Matched files: {self.matched_files}",
            f"Unmatched files: {len(self.unmatched_files)}",
            f"Ignored files: {self.ignored_files}",
        ]

        if self.unmatched_files:
            lines.append("\nUnmatched files:")
            for file in sorted(self.unmatched_files):
                lines.append(f"  - {file}")

        return "\n".join(lines)


class SpecLinter:
    """Linter that validates all files match patterns in an allowlist.

    Similar to .gitignore but acts as an allowlist rather than a blocklist.
    Uses gitignore-style glob patterns.
    """

    DEFAULT_ALLOWLIST_FILE = ".specallowlist"
    DEFAULT_IGNORE_FILE = ".gitignore"

    def __init__(
        self,
        root_dir: Path | None = None,
        allowlist_file: str | None = None,
        use_gitignore: bool = True,
    ):
        """Initialize the linter.

        Args:
            root_dir: Root directory to scan. Defaults to current directory.
            allowlist_file: Name of the allowlist file. Defaults to .specallowlist
            use_gitignore: Whether to respect .gitignore patterns. Defaults to True.
        """
        self.root_dir = Path(root_dir or os.getcwd()).resolve()
        self.allowlist_file = allowlist_file or self.DEFAULT_ALLOWLIST_FILE
        self.use_gitignore = use_gitignore

        self.allowlist_spec: pathspec.PathSpec | None = None
        self.ignore_spec: pathspec.PathSpec | None = None

    def _strip_inline_comment(self, line: str) -> str:
        """Strip inline comments from a pattern line.

        Args:
            line: The pattern line potentially containing an inline comment.

        Returns:
            The pattern with inline comment removed.
        """
        # Find the first # that's not at the start
        # We need to be careful about escaped # characters
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            return stripped

        # Look for inline comment (# not at start of line)
        # Simple approach: split on # and take first part
        # This doesn't handle escaped #, but gitignore doesn't either
        parts = stripped.split("#", 1)
        return parts[0].strip()

    def load_patterns(self) -> tuple[list[str], list[str]]:
        """Load patterns from allowlist and gitignore files.

        Returns:
            Tuple of (allowlist_patterns, ignore_patterns)
        """
        # Load allowlist patterns
        allowlist_path = self.root_dir / self.allowlist_file
        allowlist_patterns = []

        if allowlist_path.exists():
            with open(allowlist_path) as f:
                for line in f:
                    pattern = self._strip_inline_comment(line)
                    if pattern and not pattern.startswith("#"):
                        allowlist_patterns.append(pattern)

        # Load gitignore patterns
        ignore_patterns = []
        if self.use_gitignore:
            gitignore_path = self.root_dir / self.DEFAULT_IGNORE_FILE
            if gitignore_path.exists():
                with open(gitignore_path) as f:
                    ignore_patterns = [
                        line.strip()
                        for line in f
                        if line.strip() and not line.strip().startswith("#")
                    ]

        # Always ignore .git directory
        if ".git" not in ignore_patterns and ".git/" not in ignore_patterns:
            ignore_patterns.append(".git/")

        return allowlist_patterns, ignore_patterns

    def compile_specs(self) -> None:
        """Compile the pathspec objects from pattern files."""
        allowlist_patterns, ignore_patterns = self.load_patterns()

        if allowlist_patterns:
            self.allowlist_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, allowlist_patterns
            )

        if ignore_patterns:
            self.ignore_spec = pathspec.PathSpec.from_lines(
                pathspec.patterns.GitWildMatchPattern, ignore_patterns
            )

    def get_all_files(self) -> set[str]:
        """Get all files in the repository, respecting gitignore.

        Returns:
            Set of relative file paths.
        """
        all_files = set()

        for root, dirs, files in os.walk(self.root_dir):
            root_path = Path(root)
            rel_root = root_path.relative_to(self.root_dir)

            # Filter directories based on ignore patterns
            if self.ignore_spec:
                # Check each directory
                dirs_to_remove = []
                for d in dirs:
                    dir_rel_path = str(rel_root / d)
                    # Normalize path for checking
                    check_path = dir_rel_path + "/"
                    if self.ignore_spec.match_file(check_path):
                        dirs_to_remove.append(d)

                for d in dirs_to_remove:
                    dirs.remove(d)

            # Add files (if not ignored)
            for file in files:
                file_rel_path = rel_root / file
                file_rel_str = str(file_rel_path)

                # Skip the allowlist file itself and .gitignore
                if (
                    file_rel_str == self.allowlist_file
                    or file == self.allowlist_file
                    or file_rel_str == self.DEFAULT_IGNORE_FILE
                    or file == self.DEFAULT_IGNORE_FILE
                ):
                    continue

                # Check if file is ignored
                if self.ignore_spec and self.ignore_spec.match_file(file_rel_str):
                    continue

                all_files.add(file_rel_str)

        return all_files

    def lint(self) -> LintResult:
        """Run the linter and return results.

        Returns:
            LintResult containing validation results.

        Raises:
            FileNotFoundError: If allowlist file doesn't exist.
        """
        # Check if allowlist file exists
        allowlist_path = self.root_dir / self.allowlist_file
        if not allowlist_path.exists():
            raise FileNotFoundError(
                f"Allowlist file not found: {self.allowlist_file}\n"
                f"Create a {self.allowlist_file} file with gitignore-style patterns."
            )

        # Compile the pattern specs
        self.compile_specs()

        if not self.allowlist_spec:
            raise ValueError(
                f"No patterns found in {self.allowlist_file}\n"
                f"Add at least one pattern to the allowlist."
            )

        # Get all files
        all_files = self.get_all_files()

        # Track statistics
        total_files = len(all_files)
        matched_files = []
        unmatched_files = []

        # Check each file against allowlist
        for file in all_files:
            if self.allowlist_spec.match_file(file):
                matched_files.append(file)
            else:
                unmatched_files.append(file)

        # Calculate ignored files (for informational purposes)
        # This is a rough estimate based on common patterns
        ignored_count = 0
        if self.use_gitignore and self.ignore_spec:
            # Just report that we're using gitignore; exact count is complex
            # since we skip ignored files during traversal
            pass

        return LintResult(
            total_files=total_files,
            matched_files=len(matched_files),
            unmatched_files=unmatched_files,
            ignored_files=ignored_count,
        )
