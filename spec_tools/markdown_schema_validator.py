"""Markdown schema validator for structured markdown documents.

This module validates markdown files against a defined schema, checking:
- Heading structure and hierarchy
- Required and optional sections
- Metadata fields
- EARS format requirements
- Body content patterns
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

import pathspec


@dataclass
class HeadingNode:
    """Represents a heading in a markdown document."""

    level: int
    text: str
    line_number: int
    children: list["HeadingNode"] = field(default_factory=list)
    body_lines: list[tuple[int, str]] = field(default_factory=list)


@dataclass
class SchemaViolation:
    """Represents a schema validation violation."""

    file_path: str
    line_number: int
    severity: str  # 'error' or 'warning'
    message: str

    def __str__(self) -> str:
        return f"{self.file_path}:{self.line_number} [{self.severity.upper()}] {self.message}"


@dataclass
class SchemaValidationResult:
    """Result of markdown schema validation."""

    total_files: int
    valid_files: int
    invalid_files: int
    violations: list[SchemaViolation]
    markdown_files_checked: int

    @property
    def is_valid(self) -> bool:
        """Returns True if all files are valid."""
        return self.invalid_files == 0

    def __str__(self) -> str:
        """Format validation results for display."""
        lines = []
        lines.append("\nMarkdown Schema Validation Results:")
        lines.append(f"  Files checked: {self.markdown_files_checked}")
        lines.append(f"  Valid files: {self.valid_files}")
        lines.append(f"  Invalid files: {self.invalid_files}")
        lines.append(f"  Total violations: {len(self.violations)}")

        if self.violations:
            lines.append("\nViolations:")
            for violation in self.violations:
                lines.append(f"  {violation}")

        return "\n".join(lines)


class MarkdownParser:
    """Parse markdown files into a structured tree."""

    HEADING_PATTERN = re.compile(r"^(#{1,6})\s+(.+)$")
    METADATA_PATTERN = re.compile(r"^\*\*([^*]+)\*\*:\s*(.+)$")

    @staticmethod
    def parse_file(file_path: Path) -> tuple[dict[str, str], list[HeadingNode]]:
        """Parse a markdown file into metadata and heading tree.

        Args:
            file_path: Path to the markdown file

        Returns:
            Tuple of (metadata dict, list of top-level heading nodes)
        """
        metadata = {}
        headings = []
        current_stack: list[HeadingNode] = []
        metadata_section = False  # Track if we're in the metadata section after H1
        in_code_block = False  # Track if we're inside a code block

        try:
            with open(file_path, encoding="utf-8") as f:
                lines = f.readlines()
        except Exception as e:
            raise RuntimeError(f"Failed to read {file_path}: {e}") from e

        for i, line in enumerate(lines, start=1):
            line = line.rstrip("\n")

            # Check for code block delimiter
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                # Add to current heading's body if we have one
                if current_stack:
                    if line.strip() or current_stack[-1].body_lines:
                        current_stack[-1].body_lines.append((i, line))
                continue

            # Skip processing content inside code blocks
            if in_code_block:
                if current_stack:
                    current_stack[-1].body_lines.append((i, line))
                continue

            # Check for heading
            heading_match = MarkdownParser.HEADING_PATTERN.match(line)
            if heading_match:
                level = len(heading_match.group(1))
                text = heading_match.group(2).strip()
                node = HeadingNode(level=level, text=text, line_number=i)

                # Pop from stack until we find the parent level
                while current_stack and current_stack[-1].level >= level:
                    current_stack.pop()

                # Add to parent or top-level
                if current_stack:
                    current_stack[-1].children.append(node)
                else:
                    headings.append(node)

                current_stack.append(node)

                # Enable metadata parsing after first H1 heading
                if level == 1 and len(headings) == 1:
                    metadata_section = True
                # Disable metadata parsing when we hit H2 or any other heading after H1
                elif metadata_section and level >= 2:
                    metadata_section = False

                continue

            # Check for metadata (bold key: value pairs)
            # Can appear before first heading OR right after H1 heading
            if not headings or metadata_section:
                metadata_match = MarkdownParser.METADATA_PATTERN.match(line)
                if metadata_match:
                    key = metadata_match.group(1).strip()
                    value = metadata_match.group(2).strip()
                    metadata[key] = value
                    continue

            # Check if it's a blank line in metadata section
            if metadata_section and not line.strip():
                continue

            # Non-metadata content after H1 disables metadata section
            is_not_metadata = not MarkdownParser.METADATA_PATTERN.match(line)
            if metadata_section and line.strip() and is_not_metadata:
                metadata_section = False

            # Add line to current heading's body
            if current_stack:
                # Skip empty lines at the start of body
                if line.strip() or current_stack[-1].body_lines:
                    current_stack[-1].body_lines.append((i, line))

        return metadata, headings

    @staticmethod
    def flatten_headings(headings: list[HeadingNode]) -> list[HeadingNode]:
        """Flatten heading tree into a list."""
        result = []
        for heading in headings:
            result.append(heading)
            if heading.children:
                result.extend(MarkdownParser.flatten_headings(heading.children))
        return result


class EARSValidator:
    """Validator for EARS (Easy Approach to Requirements Syntax) format."""

    # EARS patterns - support both "The system shall" and test-specific patterns
    # like "Unit tests shall", "Integration tests shall", etc.
    SUBJECT_PATTERN = r"(The system|The [\w\s]+|Unit tests|Integration tests|[\w\s]+ tests)"

    UNCONDITIONAL = re.compile(rf"\b{SUBJECT_PATTERN}\s+shall\b", re.IGNORECASE)
    EVENT_DRIVEN = re.compile(rf"\bWHEN\b.*\b{SUBJECT_PATTERN}\s+shall\b", re.IGNORECASE)
    CONDITIONAL = re.compile(rf"\bIF\b.*\bTHEN\b.*\b{SUBJECT_PATTERN}\s+shall\b", re.IGNORECASE)
    UNWANTED = re.compile(rf"\bWHILE\b.*\b{SUBJECT_PATTERN}\s+shall\b", re.IGNORECASE)
    STATE_DRIVEN = re.compile(rf"\bWHILE\b.*\b{SUBJECT_PATTERN}\s+shall\b", re.IGNORECASE)
    OPTIONAL = re.compile(rf"\bWHERE\b.*\b{SUBJECT_PATTERN}\s+shall\b", re.IGNORECASE)

    REQUIREMENT_ID = re.compile(r"^\*\*(REQ|NFR|TEST)-\d+\*\*:")

    @staticmethod
    def is_ears_compliant(text: str) -> bool:
        """Check if a requirement statement follows EARS format."""
        # Must contain "shall"
        if not re.search(r"\bshall\b", text, re.IGNORECASE):
            return False

        # Check if matches any EARS pattern
        patterns = [
            EARSValidator.UNCONDITIONAL,
            EARSValidator.EVENT_DRIVEN,
            EARSValidator.CONDITIONAL,
            EARSValidator.UNWANTED,
            EARSValidator.STATE_DRIVEN,
            EARSValidator.OPTIONAL,
        ]

        for pattern in patterns:
            if pattern.search(text):
                return True

        return False

    @staticmethod
    def validate_requirement(line_num: int, line: str, file_path: str) -> SchemaViolation | None:
        """Validate a requirement line follows EARS format.

        Args:
            line_num: Line number in file
            line: Line content
            file_path: Path to file

        Returns:
            SchemaViolation if invalid, None if valid
        """
        # Check if line starts with requirement ID
        if not EARSValidator.REQUIREMENT_ID.match(line.strip()):
            return None  # Not a requirement line

        # Extract requirement text (after the ID)
        text = EARSValidator.REQUIREMENT_ID.sub("", line).strip()

        if not EARSValidator.is_ears_compliant(text):
            return SchemaViolation(
                file_path=file_path,
                line_number=line_num,
                severity="error",
                message=f"Requirement does not follow EARS format: {text[:50]}...",
            )

        return None


class MarkdownSchemaValidator:
    """Validates markdown files against a defined schema."""

    DEFAULT_CONFIG_FILE = ".specschemaconfig"
    DEFAULT_GITIGNORE_FILE = ".gitignore"

    def __init__(
        self,
        root_dir: str = ".",
        config_file: str | None = None,
        respect_gitignore: bool = True,
    ):
        """Initialize the markdown schema validator.

        Args:
            root_dir: Root directory to scan
            config_file: Path to schema configuration file
            respect_gitignore: Whether to respect .gitignore patterns
        """
        self.root_dir = Path(root_dir).resolve()
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.respect_gitignore = respect_gitignore
        self.schema = self._load_schema()
        self.gitignore_spec = self._load_gitignore() if respect_gitignore else None

    def _load_schema(self) -> dict:
        """Load schema configuration from file.

        Returns:
            Dictionary with schema configuration
        """
        config_path = self.root_dir / self.config_file

        # Default schema for EARS spec files if no config exists
        if not config_path.exists():
            return {
                "files": ["specs/*.md"],
                "metadata_fields": {
                    "required": ["ID", "Version", "Date", "Status"],
                    "optional": [],
                },
                "headings": {
                    "required": [
                        {"level": 1, "pattern": r"^Specification:\s+.+$"},
                        {"level": 2, "text": "Overview"},
                        {"level": 2, "pattern": r"^Requirements\s+\(EARS Format\)$"},
                    ],
                    "optional": [
                        {"level": 2, "text": "Configuration File Format"},
                        {"level": 2, "text": "Examples"},
                        {"level": 2, "text": "Non-Functional Requirements"},
                        {"level": 2, "text": "Test Coverage"},
                    ],
                },
                "ears_validation": {
                    "enabled": True,
                    "sections": [
                        "Requirements (EARS Format)",
                        "Non-Functional Requirements",
                        "Test Coverage",
                    ],
                },
            }

        # TODO: Load from YAML file when implemented
        raise NotImplementedError("Custom schema config file loading not yet implemented")

    def _load_gitignore(self) -> pathspec.PathSpec | None:
        """Load .gitignore patterns.

        Returns:
            PathSpec object or None if .gitignore doesn't exist
        """
        gitignore_path = self.root_dir / self.DEFAULT_GITIGNORE_FILE
        if not gitignore_path.exists():
            return None

        try:
            with open(gitignore_path, encoding="utf-8") as f:
                patterns = f.read().splitlines()
            return pathspec.PathSpec.from_lines("gitwildmatch", patterns)
        except Exception:
            return None

    def get_markdown_files(self) -> list[Path]:
        """Get all markdown files matching the schema file patterns.

        Returns:
            List of Path objects for markdown files
        """
        file_patterns = self.schema.get("files", ["**/*.md"])
        matched_files = set()

        for pattern in file_patterns:
            # Use pathspec for glob pattern matching
            spec = pathspec.PathSpec.from_lines("gitwildmatch", [pattern])

            for file_path in self.root_dir.rglob("*"):
                if not file_path.is_file():
                    continue

                # Get relative path for pattern matching
                try:
                    rel_path = file_path.relative_to(self.root_dir)
                except ValueError:
                    continue

                # Skip if ignored by .gitignore
                if self.gitignore_spec and self.gitignore_spec.match_file(str(rel_path)):
                    continue

                # Skip .git directory
                if ".git" in rel_path.parts:
                    continue

                # Skip jobs/ directory (JTBD files have different schema)
                if "jobs" in rel_path.parts:
                    continue

                # Skip principles.md (meta-documentation without requirements)
                if file_path.name == "principles.md":
                    continue

                # Check if matches pattern
                if spec.match_file(str(rel_path)):
                    matched_files.add(file_path)

        return sorted(matched_files)

    def validate_metadata(self, metadata: dict[str, str], file_path: Path) -> list[SchemaViolation]:
        """Validate metadata fields against schema.

        Args:
            metadata: Dictionary of metadata key-value pairs
            file_path: Path to the file being validated

        Returns:
            List of schema violations
        """
        violations = []
        metadata_config = self.schema.get("metadata_fields", {})
        required_fields = metadata_config.get("required", [])

        for field_name in required_fields:
            if field_name not in metadata:
                violations.append(
                    SchemaViolation(
                        file_path=str(file_path.relative_to(self.root_dir)),
                        line_number=1,
                        severity="error",
                        message=f"Missing required metadata field: {field_name}",
                    )
                )

        return violations

    def validate_headings(
        self, headings: list[HeadingNode], file_path: Path
    ) -> list[SchemaViolation]:
        """Validate heading structure against schema.

        Args:
            headings: List of top-level heading nodes
            file_path: Path to the file being validated

        Returns:
            List of schema violations
        """
        violations = []
        all_headings = MarkdownParser.flatten_headings(headings)
        heading_config = self.schema.get("headings", {})
        required_headings = heading_config.get("required", [])

        for required in required_headings:
            level = required.get("level")
            text = required.get("text")
            pattern = required.get("pattern")

            # Find matching heading
            found = False
            for heading in all_headings:
                if heading.level != level:
                    continue

                if text and heading.text == text:
                    found = True
                    break
                elif pattern and re.match(pattern, heading.text):
                    found = True
                    break

            if not found:
                violations.append(
                    SchemaViolation(
                        file_path=str(file_path.relative_to(self.root_dir)),
                        line_number=1,
                        severity="error",
                        message=f"Missing required heading: level {level}, "
                        f"{'text=' + repr(text) if text else 'pattern=' + repr(pattern)}",
                    )
                )

        return violations

    def validate_ears_format(
        self, headings: list[HeadingNode], file_path: Path
    ) -> list[SchemaViolation]:
        """Validate EARS format requirements in relevant sections.

        Args:
            headings: List of top-level heading nodes
            file_path: Path to the file being validated

        Returns:
            List of schema violations
        """
        violations = []
        ears_config = self.schema.get("ears_validation", {})

        if not ears_config.get("enabled", False):
            return violations

        ears_sections = ears_config.get("sections", [])
        all_headings = MarkdownParser.flatten_headings(headings)

        # Find headings that should contain EARS requirements
        for heading in all_headings:
            # Check if this heading or any parent matches EARS sections
            for section_name in ears_sections:
                if section_name in heading.text or heading.text == section_name:
                    # Validate all body lines in this section (skip code blocks)
                    in_code_block = False
                    for line_num, line in heading.body_lines:
                        # Check for code block delimiter
                        if line.strip().startswith("```"):
                            in_code_block = not in_code_block
                            continue

                        # Skip lines inside code blocks
                        if in_code_block:
                            continue

                        violation = EARSValidator.validate_requirement(
                            line_num, line, str(file_path.relative_to(self.root_dir))
                        )
                        if violation:
                            violations.append(violation)

                    # Recursively validate children
                    for child in heading.children:
                        in_code_block = False
                        for line_num, line in child.body_lines:
                            # Check for code block delimiter
                            if line.strip().startswith("```"):
                                in_code_block = not in_code_block
                                continue

                            # Skip lines inside code blocks
                            if in_code_block:
                                continue

                            violation = EARSValidator.validate_requirement(
                                line_num, line, str(file_path.relative_to(self.root_dir))
                            )
                            if violation:
                                violations.append(violation)

        return violations

    def validate_file(self, file_path: Path) -> list[SchemaViolation]:
        """Validate a single markdown file against the schema.

        Args:
            file_path: Path to the markdown file

        Returns:
            List of schema violations
        """
        violations = []

        try:
            metadata, headings = MarkdownParser.parse_file(file_path)
        except Exception as e:
            violations.append(
                SchemaViolation(
                    file_path=str(file_path.relative_to(self.root_dir)),
                    line_number=1,
                    severity="error",
                    message=f"Failed to parse file: {e}",
                )
            )
            return violations

        # Validate metadata
        violations.extend(self.validate_metadata(metadata, file_path))

        # Validate heading structure
        violations.extend(self.validate_headings(headings, file_path))

        # Validate EARS format
        violations.extend(self.validate_ears_format(headings, file_path))

        return violations

    def validate(self) -> SchemaValidationResult:
        """Validate all markdown files against the schema.

        Returns:
            SchemaValidationResult with validation results
        """
        files = self.get_markdown_files()
        all_violations = []
        valid_files = 0
        invalid_files = 0

        for file_path in files:
            violations = self.validate_file(file_path)

            if violations:
                invalid_files += 1
                all_violations.extend(violations)
            else:
                valid_files += 1

        return SchemaValidationResult(
            total_files=len(files),
            valid_files=valid_files,
            invalid_files=invalid_files,
            violations=all_violations,
            markdown_files_checked=len(files),
        )
