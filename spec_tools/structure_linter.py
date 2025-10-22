"""Structure linter for validating spec-to-test structure alignment."""

from dataclasses import dataclass
from pathlib import Path


@dataclass
class StructureValidationResult:
    """Result of structure validation."""

    total_specs: int
    specs_with_tests: int
    specs_without_tests: list[str]
    total_test_dirs: int
    test_dirs_with_specs: int
    test_dirs_without_specs: list[str]
    spec_to_test_mapping: dict[str, str]
    is_valid: bool

    def __str__(self) -> str:
        """Format the result as a human-readable string."""
        lines = []
        lines.append("=" * 60)
        lines.append("SPEC-TEST STRUCTURE REPORT")
        lines.append("=" * 60)
        lines.append(f"Specs with tests: {self.specs_with_tests}/{self.total_specs}")
        lines.append(
            f"Test dirs/files with specs: {self.test_dirs_with_specs}/{self.total_test_dirs}"
        )
        lines.append("")

        if self.specs_without_tests:
            lines.append("❌ Specs Without Corresponding Tests:")
            for spec_name in sorted(self.specs_without_tests):
                lines.append(f"  - {spec_name}")
            lines.append("")

        if self.test_dirs_without_specs:
            lines.append("⚠️  Test Files/Directories Without Corresponding Specs:")
            for test_name in sorted(self.test_dirs_without_specs):
                lines.append(f"  - {test_name}")
            lines.append("")

        if self.spec_to_test_mapping:
            lines.append("✅ Valid Spec-Test Mappings:")
            for spec_name, test_path in sorted(self.spec_to_test_mapping.items()):
                lines.append(f"  - {spec_name} → {test_path}")
            lines.append("")

        if self.is_valid:
            lines.append("✅ Structure validation PASSED")
        else:
            lines.append("❌ Structure validation FAILED")

        lines.append("=" * 60)
        return "\n".join(lines)


class StructureLinter:
    """Linter to validate that spec files have corresponding test files/directories."""

    def __init__(
        self,
        specs_dir: Path | None = None,
        tests_dir: Path | None = None,
        root_dir: Path | None = None,
    ):
        """Initialize the structure linter.

        Args:
            specs_dir: Directory containing spec files (default: root_dir/specs)
            tests_dir: Directory containing test files (default: root_dir/tests)
            root_dir: Root directory of the project (default: current directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.specs_dir = Path(specs_dir) if specs_dir else self.root_dir / "specs"
        self.tests_dir = Path(tests_dir) if tests_dir else self.root_dir / "tests"

    def get_expected_test_paths(self, spec_file: Path) -> list[Path]:
        """Get the expected test file/directory paths for a spec file.

        For a spec file like "specs/foo-bar.md", we expect either:
        - tests/test_foo_bar.py
        - tests/foo_bar/ (directory)

        Args:
            spec_file: Path to the spec file

        Returns:
            List of possible test paths
        """
        # Get the spec name without extension
        spec_name = spec_file.stem

        # Convert kebab-case or any other format to snake_case for Python naming
        test_name = spec_name.replace("-", "_").replace(" ", "_")

        # Return possible test paths
        return [
            self.tests_dir / f"test_{test_name}.py",  # Single test file
            self.tests_dir / test_name,  # Test directory
        ]

    def find_test_for_spec(self, spec_file: Path) -> Path | None:
        """Find the corresponding test file or directory for a spec file.

        Args:
            spec_file: Path to the spec file

        Returns:
            Path to the test file/directory, or None if not found
        """
        expected_paths = self.get_expected_test_paths(spec_file)

        for path in expected_paths:
            if path.exists():
                return path

        return None

    def get_spec_for_test(self, test_path: Path) -> Path | None:
        """Find the corresponding spec file for a test file or directory.

        Args:
            test_path: Path to the test file or directory

        Returns:
            Path to the spec file, or None if not found
        """
        # Get the test name
        if test_path.is_file():
            # test_foo_bar.py -> foo_bar
            test_name = test_path.stem
            if test_name.startswith("test_"):
                test_name = test_name[5:]  # Remove "test_" prefix
            elif test_name == "__init__":
                # Skip __init__.py files
                return None
        else:
            # foo_bar/ -> foo_bar
            test_name = test_path.name

        # Try different naming conventions for spec files
        possible_spec_names = [
            test_name,  # foo_bar
            test_name.replace("_", "-"),  # foo-bar
            test_name.replace("_", " "),  # foo bar
        ]

        for spec_name in possible_spec_names:
            spec_file = self.specs_dir / f"{spec_name}.md"
            if spec_file.exists():
                return spec_file

        return None

    def get_all_requirement_test_paths(self) -> list[Path]:
        """Get all test files and directories that should correspond to specs.

        This excludes generic test files that don't follow the spec structure pattern.

        Returns:
            List of test file/directory paths
        """
        test_paths = []

        # Get all test files except __init__.py
        for test_file in self.tests_dir.rglob("test_*.py"):
            if test_file.name != "__init__.py":
                test_paths.append(test_file)

        # Get all immediate subdirectories in tests/
        # (not recursive, as those would be part of a test package)
        for item in self.tests_dir.iterdir():
            if item.is_dir() and not item.name.startswith("__"):
                test_paths.append(item)

        return test_paths

    def lint(self) -> StructureValidationResult:
        """Run the structure linter.

        Returns:
            StructureValidationResult with validation results
        """
        # Get all spec files
        spec_files = list(self.specs_dir.rglob("*.md"))

        # Check each spec has a corresponding test
        spec_to_test_mapping = {}
        specs_without_tests = []

        for spec_file in spec_files:
            test_path = self.find_test_for_spec(spec_file)
            spec_name = spec_file.relative_to(self.specs_dir)

            if test_path:
                test_rel_path = test_path.relative_to(self.tests_dir)
                spec_to_test_mapping[str(spec_name)] = str(test_rel_path)
            else:
                specs_without_tests.append(str(spec_name))

        # Check each test file/directory has a corresponding spec
        test_paths = self.get_all_requirement_test_paths()
        test_dirs_without_specs = []

        for test_path in test_paths:
            spec_file = self.get_spec_for_test(test_path)
            if not spec_file:
                test_rel_path = test_path.relative_to(self.tests_dir)
                test_dirs_without_specs.append(str(test_rel_path))

        # Calculate results
        total_specs = len(spec_files)
        specs_with_tests = total_specs - len(specs_without_tests)
        total_test_dirs = len(test_paths)
        test_dirs_with_specs = total_test_dirs - len(test_dirs_without_specs)

        # Validation passes if all specs have tests
        # (having tests without specs is allowed - those are unit tests)
        is_valid = len(specs_without_tests) == 0

        return StructureValidationResult(
            total_specs=total_specs,
            specs_with_tests=specs_with_tests,
            specs_without_tests=specs_without_tests,
            total_test_dirs=total_test_dirs,
            test_dirs_with_specs=test_dirs_with_specs,
            test_dirs_without_specs=test_dirs_without_specs,
            spec_to_test_mapping=spec_to_test_mapping,
            is_valid=is_valid,
        )
