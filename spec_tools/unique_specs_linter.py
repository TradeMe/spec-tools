"""Unique spec requirements linter for validating spec and requirement ID uniqueness."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from spec_tools.ast_parser import parse_markdown_file


@dataclass
class UniqueSpecsResult:
    """Result of unique specs validation."""

    total_specs: int
    total_requirements: int
    duplicate_spec_ids: dict[str, list[str]] = field(default_factory=dict)
    duplicate_req_ids: dict[str, list[str]] = field(default_factory=dict)
    is_valid: bool = True

    def __str__(self) -> str:
        """Format the result as a human-readable string."""
        lines = []
        lines.append("=" * 60)
        lines.append("UNIQUE SPECS VALIDATION REPORT")
        lines.append("=" * 60)
        lines.append(f"Total specs: {self.total_specs}")
        lines.append(f"Total requirements: {self.total_requirements}")
        lines.append("")

        if self.duplicate_spec_ids:
            lines.append("❌ Duplicate SPEC IDs:")
            for spec_id, files in sorted(self.duplicate_spec_ids.items()):
                lines.append(f"  {spec_id}:")
                for file in sorted(files):
                    lines.append(f"    - {file}")
            lines.append("")

        if self.duplicate_req_ids:
            lines.append("❌ Duplicate Requirement IDs:")
            for req_id, locations in sorted(self.duplicate_req_ids.items()):
                lines.append(f"  {req_id}:")
                for location in sorted(locations):
                    lines.append(f"    - {location}")
            lines.append("")

        if self.is_valid:
            lines.append("✅ All spec IDs and requirement IDs are unique")
        else:
            lines.append("❌ Unique specs validation FAILED")

        lines.append("=" * 60)
        return "\n".join(lines)


class UniqueSpecsLinter:
    """Linter to validate that spec IDs and requirement IDs are unique."""

    # Pattern to match SPEC ID in metadata
    SPEC_ID_PATTERN = re.compile(r"^\*\*ID\*\*:\s*(SPEC-\d+)", re.MULTILINE)

    # Pattern to match requirement IDs in spec files
    REQ_PATTERN = re.compile(r"\*\*([A-Z]+-\d{3})\*\*:")

    def __init__(
        self,
        specs_dir: Path | None = None,
        root_dir: Path | None = None,
    ):
        """Initialize the unique specs linter.

        Args:
            specs_dir: Directory containing spec files (default: root_dir/specs)
            root_dir: Root directory of the project (default: current directory)
        """
        self.root_dir = Path(root_dir) if root_dir else Path.cwd()
        self.specs_dir = Path(specs_dir) if specs_dir else self.root_dir / "specs"

    def extract_spec_id(self, spec_file: Path) -> str | None:
        """Extract the SPEC ID from a spec file.

        Uses the AST parser to extract the spec ID from metadata.

        Args:
            spec_file: Path to the spec markdown file

        Returns:
            SPEC ID if found, None otherwise
        """
        try:
            doc = parse_markdown_file(spec_file)
            return doc.spec_id
        except Exception:
            pass
        return None

    def extract_requirements(self, spec_file: Path) -> set[str]:
        """Extract all requirement IDs from a spec file.

        Uses the AST parser to properly handle code blocks and extract
        only genuine requirements.

        Args:
            spec_file: Path to the spec markdown file

        Returns:
            Set of requirement IDs (not fully qualified) found in the spec
        """
        try:
            doc = parse_markdown_file(spec_file)
            # Get requirements, excluding code blocks
            requirements = doc.get_requirement_ids(include_code_blocks=False)
            # Extract just the REQ-XXX part (not SPEC-XXX/REQ-XXX)
            return {req_id.split("/")[-1] for req_id in requirements}
        except Exception:
            pass
        return set()

    def lint(self) -> UniqueSpecsResult:
        """Run the unique specs linter.

        Returns:
            UniqueSpecsResult with validation results
        """
        # Track SPEC IDs and their files
        spec_id_to_files: dict[str, list[str]] = {}

        # Track fully qualified requirement IDs (SPEC-XXX/REQ-YYY) and their locations
        req_id_to_locations: dict[str, list[str]] = {}

        # Track requirements within each spec for uniqueness
        spec_req_duplicates: dict[str, list[str]] = {}

        total_requirements = 0

        # Process all spec files (excluding future/, jobs/, and principles.md)
        for spec_file in self.specs_dir.rglob("*.md"):
            relative_path = str(spec_file.relative_to(self.root_dir))

            # Skip future/, jobs/ directories and principles.md
            rel_to_specs = spec_file.relative_to(self.specs_dir)
            if "future" in rel_to_specs.parts or "jobs" in rel_to_specs.parts:
                continue
            if spec_file.name == "principles.md":
                continue

            # Extract SPEC ID
            spec_id = self.extract_spec_id(spec_file)
            if spec_id:
                if spec_id not in spec_id_to_files:
                    spec_id_to_files[spec_id] = []
                spec_id_to_files[spec_id].append(relative_path)

            # Extract requirements
            requirements = self.extract_requirements(spec_file)
            total_requirements += len(requirements)

            # Check for duplicate requirements within this spec using AST
            req_counts: dict[str, int] = {}
            try:
                doc = parse_markdown_file(spec_file)
                # Count all requirements (including those in code blocks) for dup detection
                for req in doc.requirements:
                    if not req.is_in_code_block:  # Only count real requirements
                        req_counts[req.req_id] = req_counts.get(req.req_id, 0) + 1
            except Exception:
                pass

            # Track within-spec duplicates
            for req_id, count in req_counts.items():
                if count > 1:
                    fq_req_id = f"{spec_id}/{req_id}" if spec_id else req_id
                    spec_req_duplicates[fq_req_id] = [f"{relative_path} (appears {count} times)"]

            # Track fully qualified requirement IDs for global uniqueness
            if spec_id:
                for req_id in requirements:
                    fq_req_id = f"{spec_id}/{req_id}"
                    if fq_req_id not in req_id_to_locations:
                        req_id_to_locations[fq_req_id] = []
                    req_id_to_locations[fq_req_id].append(relative_path)

        # Find duplicate SPEC IDs (same SPEC ID in multiple files)
        duplicate_spec_ids = {
            spec_id: files for spec_id, files in spec_id_to_files.items() if len(files) > 1
        }

        # Combine within-spec duplicates with spec_req_duplicates
        duplicate_req_ids = spec_req_duplicates.copy()

        # Determine if validation passed
        is_valid = not duplicate_spec_ids and not duplicate_req_ids

        return UniqueSpecsResult(
            total_specs=len(spec_id_to_files),
            total_requirements=total_requirements,
            duplicate_spec_ids=duplicate_spec_ids,
            duplicate_req_ids=duplicate_req_ids,
            is_valid=is_valid,
        )
