"""Spec coverage linter for validating test-to-requirement traceability."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class SpecCoverageResult:
    """Result of spec coverage validation."""

    total_requirements: int
    covered_requirements: int
    uncovered_requirements: list[str]
    total_tests: int
    tests_with_requirements: int
    tests_without_requirements: list[str]
    requirement_to_tests: dict[str, list[str]]
    test_to_requirements: dict[str, list[str]]
    coverage_percentage: float
    is_valid: bool

    def __str__(self) -> str:
        """Format the result as a human-readable string."""
        lines = []
        lines.append("=" * 60)
        lines.append("SPEC COVERAGE REPORT")
        lines.append("=" * 60)
        lines.append(f"Coverage: {self.coverage_percentage:.1f}%")
        lines.append(f"Requirements: {self.covered_requirements}/{self.total_requirements} covered")
        lines.append(
            f"Tests: {self.tests_with_requirements}/{self.total_tests} linked to requirements"
        )
        lines.append("")

        if self.uncovered_requirements:
            lines.append("❌ Uncovered Requirements:")
            for req_id in sorted(self.uncovered_requirements):
                lines.append(f"  - {req_id}")
            lines.append("")

        if self.tests_without_requirements:
            lines.append("⚠️  Tests Without Requirement Markers:")
            for test_name in sorted(self.tests_without_requirements):
                lines.append(f"  - {test_name}")
            lines.append("")

        if self.is_valid:
            lines.append("✅ Spec coverage validation PASSED")
        else:
            lines.append("❌ Spec coverage validation FAILED")

        lines.append("=" * 60)
        return "\n".join(lines)


class SpecCoverageLinter:
    """Linter to validate that all spec requirements have corresponding tests."""

    # Pattern to match requirement IDs in spec files
    REQ_PATTERN = re.compile(r"\*\*([A-Z]+-\d{3})\*\*:")

    # Pattern to match SPEC ID in metadata
    SPEC_ID_PATTERN = re.compile(r"^\*\*ID\*\*:\s*(SPEC-\d+)", re.MULTILINE)

    def __init__(
        self,
        specs_dir: Path | None = None,
        tests_dir: Path | None = None,
        root_dir: Path | None = None,
        min_coverage: float = 100.0,
    ):
        """Initialize the spec coverage linter.

        Args:
            specs_dir: Directory containing spec files (default: root_dir/specs)
            tests_dir: Directory containing test files (default: root_dir/tests)
            root_dir: Root directory of the project (default: current directory)
            min_coverage: Minimum acceptable coverage percentage (default: 100.0)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.specs_dir = Path(specs_dir) if specs_dir else self.root_dir / "specs"
        self.tests_dir = Path(tests_dir) if tests_dir else self.root_dir / "tests"
        self.min_coverage = min_coverage

    def is_spec_provisional(self, spec_file: Path) -> bool:
        """Check if a spec is provisional and should be excluded from coverage.

        A spec is considered provisional if:
        1. It's in a 'future' subdirectory, OR
        2. Its Status metadata field is 'Provisional' or 'Planned'

        Args:
            spec_file: Path to the spec markdown file

        Returns:
            True if the spec is provisional and should be excluded
        """
        # Check if spec is in future/ directory
        relative_path = spec_file.relative_to(self.specs_dir)
        if "future" in relative_path.parts:
            return True

        # Check Status metadata field
        try:
            content = spec_file.read_text(encoding="utf-8")
            # Look for **Status**: value in the first 20 lines
            for line in content.split("\n")[:20]:
                if line.startswith("**Status**:"):
                    status = line.split(":", 1)[1].strip()
                    if status.lower() in ("provisional", "planned"):
                        return True
        except Exception:
            pass

        return False

    def extract_spec_id(self, spec_file: Path) -> str | None:
        """Extract the SPEC ID from a spec file.

        Args:
            spec_file: Path to the spec markdown file

        Returns:
            SPEC ID if found, None otherwise
        """
        try:
            content = spec_file.read_text(encoding="utf-8")
            match = self.SPEC_ID_PATTERN.search(content)
            return match.group(1) if match else None
        except Exception:
            return None

    def extract_requirements_from_spec(self, spec_file: Path) -> set[str]:
        """Extract all fully qualified requirement IDs from a spec file.

        Args:
            spec_file: Path to the spec markdown file

        Returns:
            Set of fully qualified requirement IDs (SPEC-XXX/REQ-YYY) found in the spec
        """
        requirements = set()
        content = spec_file.read_text(encoding="utf-8")

        # Get the SPEC ID for this file
        spec_id = self.extract_spec_id(spec_file)
        if not spec_id:
            # If no SPEC ID, skip this file
            return requirements

        for match in self.REQ_PATTERN.finditer(content):
            req_id = match.group(1)
            # Build fully qualified requirement ID
            fully_qualified_id = f"{spec_id}/{req_id}"
            requirements.add(fully_qualified_id)

        return requirements

    def extract_requirements_from_tests(self, test_file: Path) -> dict[str, list[str]]:
        """Extract requirement markers from test functions.

        Args:
            test_file: Path to the test Python file

        Returns:
            Dictionary mapping test names to requirement IDs
        """
        test_to_reqs = {}

        try:
            content = test_file.read_text(encoding="utf-8")
            tree = ast.parse(content, filename=str(test_file))

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                    # Look for @pytest.mark.req decorators
                    req_ids = []
                    for decorator in node.decorator_list:
                        req_ids.extend(self._extract_req_from_decorator(decorator))

                    # Build full test name (class.method or just method)
                    test_name = self._get_test_name(node, tree)
                    full_test_name = f"{test_file.relative_to(self.tests_dir)}::{test_name}"

                    if req_ids:
                        test_to_reqs[full_test_name] = req_ids

        except Exception as e:
            print(f"Warning: Could not parse {test_file}: {e}")

        return test_to_reqs

    def _extract_req_from_decorator(self, decorator: ast.expr) -> list[str]:
        """Extract requirement IDs from a decorator node.

        Args:
            decorator: AST decorator node

        Returns:
            List of requirement IDs found in the decorator
        """
        req_ids = []

        # Handle @pytest.mark.req("REQ-001")
        if isinstance(decorator, ast.Call):
            if self._is_req_marker(decorator.func):
                for arg in decorator.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        req_ids.append(arg.value)

        # Handle @pytest.mark.req without arguments (edge case)
        elif isinstance(decorator, ast.Attribute):
            if self._is_req_marker(decorator):
                pass  # No requirement ID specified

        return req_ids

    def _is_req_marker(self, node: ast.expr) -> bool:
        """Check if an AST node represents pytest.mark.req.

        Args:
            node: AST node to check

        Returns:
            True if the node is pytest.mark.req
        """
        if isinstance(node, ast.Attribute):
            # Check for pytest.mark.req
            if node.attr == "req":
                if isinstance(node.value, ast.Attribute):
                    if node.value.attr == "mark":
                        if isinstance(node.value.value, ast.Name):
                            return node.value.value.id == "pytest"
        return False

    def _get_test_name(self, func_node: ast.FunctionDef, tree: ast.Module) -> str:
        """Get the full test name including class if present.

        Args:
            func_node: Function definition node
            tree: Full AST tree

        Returns:
            Full test name (e.g., "TestClass::test_method" or "test_function")
        """
        # Find if this function is inside a class
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for item in node.body:
                    if item == func_node:
                        return f"{node.name}::{func_node.name}"
        return func_node.name

    def get_all_tests(self) -> list[str]:
        """Get all test function names from the test directory.

        Returns:
            List of full test names
        """
        all_tests = []

        for test_file in self.tests_dir.rglob("test_*.py"):
            try:
                content = test_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(test_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        test_name = self._get_test_name(node, tree)
                        full_test_name = f"{test_file.relative_to(self.tests_dir)}::{test_name}"
                        all_tests.append(full_test_name)

            except Exception as e:
                print(f"Warning: Could not parse {test_file}: {e}")

        return all_tests

    def lint(self) -> SpecCoverageResult:
        """Run the spec coverage linter.

        Returns:
            SpecCoverageResult with validation results
        """
        # Extract all requirements from spec files (excluding provisional specs)
        all_requirements = set()
        for spec_file in self.specs_dir.rglob("*.md"):
            # Skip provisional specs (future/planned features)
            if self.is_spec_provisional(spec_file):
                continue

            requirements = self.extract_requirements_from_spec(spec_file)
            all_requirements.update(requirements)

        # Extract all test-to-requirement mappings
        test_to_requirements = {}
        for test_file in self.tests_dir.rglob("test_*.py"):
            mappings = self.extract_requirements_from_tests(test_file)
            test_to_requirements.update(mappings)

        # Build reverse mapping: requirement to tests
        requirement_to_tests: dict[str, list[str]] = {}
        for test_name, req_ids in test_to_requirements.items():
            for req_id in req_ids:
                if req_id not in requirement_to_tests:
                    requirement_to_tests[req_id] = []
                requirement_to_tests[req_id].append(test_name)

        # Find uncovered requirements
        covered_requirements = set(requirement_to_tests.keys())
        uncovered_requirements = sorted(all_requirements - covered_requirements)

        # Find tests without requirement markers
        all_tests = self.get_all_tests()
        tests_without_requirements = sorted(set(all_tests) - set(test_to_requirements.keys()))

        # Calculate coverage
        total_requirements = len(all_requirements)
        covered_count = len(covered_requirements)
        coverage_percentage = (
            (covered_count / total_requirements * 100) if total_requirements > 0 else 0.0
        )

        # Validation passes if coverage meets or exceeds minimum threshold
        is_valid = coverage_percentage >= self.min_coverage

        return SpecCoverageResult(
            total_requirements=total_requirements,
            covered_requirements=covered_count,
            uncovered_requirements=uncovered_requirements,
            total_tests=len(all_tests),
            tests_with_requirements=len(test_to_requirements),
            tests_without_requirements=tests_without_requirements,
            requirement_to_tests=requirement_to_tests,
            test_to_requirements=test_to_requirements,
            coverage_percentage=coverage_percentage,
            is_valid=is_valid,
        )
