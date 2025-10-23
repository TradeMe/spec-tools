"""Semantic test-adherence analyzer for validating test-requirement alignment."""

import ast
import re
from dataclasses import dataclass
from pathlib import Path

from spec_tools.llm_provider import LLMProvider
from spec_tools.semantic_test_result import (
    SemanticAnalysisResult,
    SemanticTestAdherenceResult,
)


@dataclass
class Requirement:
    """Requirement extracted from a spec file."""

    req_id: str
    text: str
    file_path: Path
    line_number: int
    context: str | None = None


@dataclass
class TestFunction:
    """Test function extracted from a test file."""

    name: str
    full_name: str
    source_code: str
    docstring: str | None
    requirement_ids: list[str]
    file_path: Path
    line_number: int


class SemanticTestAnalyzer:
    """Analyzer for semantic test-adherence validation."""

    # Pattern to match requirement definitions in spec files
    # Format: **REQ-XXX**: requirement text
    REQ_PATTERN = re.compile(
        r"\*\*([A-Z]+-\d{3})\*\*:\s*(.+?)(?=\n\n|\*\*[A-Z]+-\d{3}\*\*:|$)", re.DOTALL
    )

    def __init__(
        self,
        llm_provider: LLMProvider,
        specs_dir: Path | None = None,
        tests_dir: Path | None = None,
        root_dir: Path | None = None,
        threshold: float = 0.7,
    ):
        """Initialize the semantic test analyzer.

        Args:
            llm_provider: LLM provider for semantic analysis
            specs_dir: Directory containing spec files (default: root_dir/specs)
            tests_dir: Directory containing test files (default: root_dir/tests)
            root_dir: Root directory of the project (default: current directory)
            threshold: Minimum confidence score for alignment (default: 0.7)
        """
        self.llm_provider = llm_provider
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.specs_dir = Path(specs_dir) if specs_dir else self.root_dir / "specs"
        self.tests_dir = Path(tests_dir) if tests_dir else self.root_dir / "tests"
        self.threshold = threshold

    def is_spec_provisional(self, spec_file: Path) -> bool:
        """Check if a spec is provisional and should be excluded from analysis.

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

    def extract_requirements(self) -> dict[str, Requirement]:
        """Extract all requirements from spec files.

        Returns:
            Dictionary mapping requirement IDs to Requirement objects
        """
        requirements = {}

        for spec_file in self.specs_dir.rglob("*.md"):
            # Skip provisional specs
            if self.is_spec_provisional(spec_file):
                continue

            try:
                content = spec_file.read_text(encoding="utf-8")
                lines = content.split("\n")

                # Find all requirements in the file
                for match in self.REQ_PATTERN.finditer(content):
                    req_id = match.group(1)
                    req_text = match.group(2).strip()

                    # Find line number
                    line_number = content[: match.start()].count("\n") + 1

                    # Extract context (section heading)
                    context = self._find_section_heading(lines, line_number)

                    requirements[req_id] = Requirement(
                        req_id=req_id,
                        text=req_text,
                        file_path=spec_file,
                        line_number=line_number,
                        context=context,
                    )

            except Exception as e:
                print(f"Warning: Could not read {spec_file}: {e}")

        return requirements

    def _find_section_heading(self, lines: list[str], line_number: int) -> str | None:
        """Find the most recent section heading before a given line.

        Args:
            lines: List of lines in the file
            line_number: Line number to search backwards from

        Returns:
            Section heading text or None
        """
        # Search backwards for a markdown heading
        for i in range(line_number - 1, -1, -1):
            line = lines[i].strip()
            if line.startswith("##") and not line.startswith("###"):
                # Remove markdown heading markers
                return line.lstrip("#").strip()
        return None

    def extract_tests(self) -> list[TestFunction]:
        """Extract all test functions with requirement markers from test files.

        Returns:
            List of TestFunction objects
        """
        tests = []

        for test_file in self.tests_dir.rglob("test_*.py"):
            try:
                content = test_file.read_text(encoding="utf-8")
                tree = ast.parse(content, filename=str(test_file))

                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                        # Extract requirement markers
                        req_ids = []
                        for decorator in node.decorator_list:
                            req_ids.extend(self._extract_req_from_decorator(decorator))

                        # Only include tests with requirement markers
                        if not req_ids:
                            continue

                        # Get test name (including class if present)
                        test_name = self._get_test_name(node, tree)
                        full_test_name = f"{test_file.relative_to(self.tests_dir)}::{test_name}"

                        # Extract source code
                        source_code = ast.get_source_segment(content, node)

                        # Extract docstring
                        docstring = ast.get_docstring(node)

                        tests.append(
                            TestFunction(
                                name=test_name,
                                full_name=full_test_name,
                                source_code=source_code or "",
                                docstring=docstring,
                                requirement_ids=req_ids,
                                file_path=test_file,
                                line_number=node.lineno,
                            )
                        )

            except Exception as e:
                print(f"Warning: Could not parse {test_file}: {e}")

        return tests

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

    def analyze(self, verbose: bool = False) -> SemanticTestAdherenceResult:
        """Run semantic test-adherence analysis.

        Args:
            verbose: Whether to print verbose progress information

        Returns:
            SemanticTestAdherenceResult with validation results
        """
        # Extract requirements and tests
        requirements = self.extract_requirements()
        tests = self.extract_tests()

        if verbose:
            print(f"Found {len(requirements)} requirements in {self.specs_dir}")
            print(f"Found {len(tests)} tests with requirement markers in {self.tests_dir}")

        # Analyze each test-requirement pair
        analyses: list[SemanticAnalysisResult] = []

        for test in tests:
            for req_id in test.requirement_ids:
                # Check if requirement exists
                requirement = requirements.get(req_id)
                if requirement is None:
                    # Requirement not found - add warning
                    analyses.append(
                        SemanticAnalysisResult(
                            requirement_id=req_id,
                            test_name=test.full_name,
                            aligned=False,
                            confidence=0.0,
                            explanation="Requirement not found in spec files",
                            error=f"Requirement {req_id} not found",
                        )
                    )
                    continue

                if verbose:
                    print(f"Analyzing: {req_id} ← {test.full_name}")

                # Perform semantic analysis using LLM
                result = self.llm_provider.analyze_test_requirement(
                    requirement_id=req_id,
                    requirement_text=requirement.text,
                    test_name=test.full_name,
                    test_code=test.source_code,
                    test_docstring=test.docstring,
                    context=requirement.context,
                )

                analyses.append(result)

        # Calculate totals
        total_pairs = len(analyses)
        aligned_pairs = sum(1 for a in analyses if a.aligned and a.confidence >= self.threshold)
        misaligned_pairs = sum(
            1
            for a in analyses
            if not a.aligned or a.confidence < self.threshold and a.error is None
        )
        error_pairs = sum(1 for a in analyses if a.error is not None)

        # Validation passes if all pairs are aligned
        is_valid = misaligned_pairs == 0 and error_pairs == 0

        return SemanticTestAdherenceResult(
            total_pairs=total_pairs,
            aligned_pairs=aligned_pairs,
            misaligned_pairs=misaligned_pairs,
            error_pairs=error_pairs,
            analyses=analyses,
            threshold=self.threshold,
            is_valid=is_valid,
        )
