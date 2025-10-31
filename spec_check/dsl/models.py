"""
Pydantic models for specification type definitions.

This module provides the base models for defining specification types using
Pydantic instead of YAML. This provides type safety, IDE support, inheritance,
and composability.
"""

import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator

from spec_check.ast_parser import MarkdownDocument


class Cardinality(BaseModel):
    """
    Represents cardinality constraints for references.

    Supports patterns like:
    - 1 (exactly one)
    - 0..1 (zero or one)
    - 1..* (one or more)
    - 0..* (zero or more)
    - n..m (between n and m)
    """

    min: int = Field(default=0, ge=0)
    max: int | None = Field(default=None, ge=0)

    def __str__(self) -> str:
        """String representation of cardinality."""
        if self.max is None:
            if self.min == 0:
                return "0..*"
            return f"{self.min}..*"
        if self.min == self.max:
            return str(self.min)
        return f"{self.min}..{self.max}"

    @field_validator("max")
    @classmethod
    def max_must_be_greater_than_min(cls, v: int | None, info) -> int | None:
        """Validate that max >= min if both are specified."""
        if v is not None and "min" in info.data and v < info.data["min"]:
            raise ValueError(f"max ({v}) must be >= min ({info.data['min']})")
        return v

    @classmethod
    def parse(cls, value: str) -> "Cardinality":
        """
        Parse cardinality from string format.

        Examples:
            "1" -> Cardinality(min=1, max=1)
            "0..1" -> Cardinality(min=0, max=1)
            "1..*" -> Cardinality(min=1, max=None)
        """
        if ".." not in value:
            # Single number
            n = int(value)
            return cls(min=n, max=n)

        parts = value.split("..")
        min_val = int(parts[0])
        max_val = None if parts[1] == "*" else int(parts[1])
        return cls(min=min_val, max=max_val)


class IdentifierSpec(BaseModel):
    """
    Defines how identifiers are formatted and located.

    Identifiers can appear in:
    - title: The H1 heading (e.g., "# REQ-001: Title")
    - heading: Any heading (for class-level IDs)
    - metadata: YAML frontmatter

    Scope determines uniqueness:
    - global: Must be unique across all documents
    - module_instance: Must be unique within the module type
    - section: Must be unique within a section
    """

    pattern: str = Field(description="Regex pattern for the identifier (e.g., 'REQ-\\d{3}')")
    location: Literal["title", "heading", "metadata"] = Field(
        default="title", description="Where the identifier appears"
    )
    scope: Literal["global", "module_instance", "section"] = Field(
        default="global", description="Uniqueness scope"
    )

    @field_validator("pattern")
    @classmethod
    def pattern_must_be_valid_regex(cls, v: str) -> str:
        """Validate that pattern is a valid regex."""
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e
        return v


class ValidationError(BaseModel):
    """Represents a validation error."""

    error_type: str
    severity: Literal["error", "warning", "info"] = "error"
    file_path: str
    line: int | None = None
    column: int | None = None
    message: str
    suggestion: str | None = None
    context: str | None = None


class ContentValidator(BaseModel):
    """
    Base class for content validators.

    Subclasses implement specific content validation logic such as:
    - Gherkin Given-When-Then syntax
    - RFC-2119 keywords (shall, must, should, may)
    - Custom domain-specific grammars
    """

    def validate_content(self, section_content: list, file_path: Path) -> list[ValidationError]:
        """
        Validate section content.

        Args:
            section_content: List of AST nodes representing section content
            file_path: Path to the markdown file

        Returns:
            List of validation errors
        """
        return []  # Base implementation accepts all content


class GherkinContentValidator(ContentValidator):
    """
    Validates that content follows Gherkin Given-When-Then format.

    Expects acceptance criteria to contain at least one complete Gherkin
    scenario with Given, When, Then keywords in bold format.

    Example valid format:
        **Given** a user with valid credentials
        **When** they submit the login form
        **Then** they receive an authentication token
    """

    def validate_content(
        self, section_content: list, file_path: Path, raw_content: str | None = None
    ) -> list[ValidationError]:
        """
        Validate that section content follows Gherkin format.

        Args:
            section_content: List of AST nodes representing section content (may be empty)
            file_path: Path to the markdown file
            raw_content: Optional raw markdown content for the section

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        # Try to get content from AST nodes first, then fall back to raw content
        content_text = self._extract_text_from_ast(section_content)
        if not content_text.strip() and raw_content:
            content_text = raw_content

        if not content_text.strip():
            errors.append(
                ValidationError(
                    error_type="empty_content",
                    severity="error",
                    file_path=str(file_path),
                    message="Acceptance criterion has no content",
                    suggestion="Add Gherkin-style Given-When-Then format",
                )
            )
            return errors

        # Check for required Gherkin keywords in bold format
        has_given = "**Given**" in content_text
        has_when = "**When**" in content_text
        has_then = "**Then**" in content_text

        # Check for unbolded keywords (common mistake)
        has_unbolded_given = "Given" in content_text and not has_given
        has_unbolded_when = "When" in content_text and not has_when
        has_unbolded_then = "Then" in content_text and not has_then

        # Report missing or improperly formatted keywords
        if not (has_given and has_when and has_then):
            missing_keywords = []
            if not has_given:
                if has_unbolded_given:
                    missing_keywords.append("Given (must be bold: **Given**)")
                else:
                    missing_keywords.append("Given")
            if not has_when:
                if has_unbolded_when:
                    missing_keywords.append("When (must be bold: **When**)")
                else:
                    missing_keywords.append("When")
            if not has_then:
                if has_unbolded_then:
                    missing_keywords.append("Then (must be bold: **Then**)")
                else:
                    missing_keywords.append("Then")

            keywords_str = ", ".join(missing_keywords)
            errors.append(
                ValidationError(
                    error_type="invalid_gherkin_format",
                    severity="error",
                    file_path=str(file_path),
                    message=f"Missing or improperly formatted Gherkin keywords: {keywords_str}",
                    suggestion="Use bold format: **Given** ... **When** ... **Then** ...",
                    context=content_text[:200] if len(content_text) > 200 else content_text,
                )
            )

        return errors

    def _extract_text_from_ast(self, ast_nodes: list) -> str:
        """
        Extract text content from AST nodes.

        Note: Currently the section tree doesn't populate content nodes,
        so this returns an empty string. The actual validation happens
        in the enhanced validate_content method below.

        Args:
            ast_nodes: List of AST nodes from markdown parser

        Returns:
            Extracted text content
        """
        text_parts = []

        for node in ast_nodes:
            if hasattr(node, "literal") and node.literal:
                text_parts.append(node.literal)
            elif hasattr(node, "children"):
                text_parts.append(self._extract_text_from_ast(node.children))

        return " ".join(text_parts)


class SectionSpec(BaseModel):
    """
    Defines a section in a module.

    Sections can be:
    - Required or optional
    - Validated for content format
    - Restricted to certain heading levels
    - Associated with child class instances
    """

    heading: str = Field(description="Expected heading text")
    heading_level: int = Field(default=2, ge=1, le=6)
    required: bool = Field(default=False)
    content_validator: ContentValidator | None = Field(default=None)
    allowed_sections: list[str] | None = Field(
        default=None, description="Allowed subsection headings"
    )


class Reference(BaseModel):
    """
    Defines a typed reference relationship between modules.

    References represent relationships like:
    - implements: Requirement implements Contract
    - depends_on: Requirement depends on another Requirement
    - validates: Test validates Requirement
    - supersedes: ADR supersedes previous ADR
    """

    name: str = Field(description="Reference type name (e.g., 'implements')")
    source_type: str = Field(description="Source module type name")
    target_type: str = Field(description="Target module type name")
    cardinality: Cardinality = Field(default_factory=Cardinality)
    link_format: Literal["id_reference", "path_reference", "url"] = Field(default="id_reference")
    allowed_sections: list[str] | None = Field(
        default=None, description="Sections where this reference can appear"
    )
    must_exist: bool = Field(default=True, description="Target must exist in the document set")
    allow_circular: bool = Field(default=True, description="Allow circular references")

    def validate_count(self, count: int) -> bool:
        """
        Validate that a count satisfies the cardinality constraint.

        Args:
            count: The actual number of references found

        Returns:
            True if count satisfies the cardinality constraint, False otherwise
        """
        if count < self.cardinality.min:
            return False
        if self.cardinality.max is not None and count > self.cardinality.max:
            return False
        return True

    def parse_cardinality(self) -> tuple[int, int | None]:
        """
        Extract min and max values from the cardinality constraint.

        Returns:
            Tuple of (min, max) where max may be None for unbounded
        """
        return (self.cardinality.min, self.cardinality.max)


class SpecClass(BaseModel):
    """
    Defines a reusable section-level component.

    SpecClass represents patterns like:
    - Acceptance Criterion (AC-001, AC-002, etc.)
    - Risk Assessment
    - Contract Clause
    - Test Case

    These are section-level elements that can appear multiple times
    within a module and have their own identifiers.
    """

    heading_pattern: str = Field(description="Regex pattern for heading (e.g., '^AC-\\d+:')")
    heading_level: int = Field(default=3, ge=1, le=6)
    identifier: IdentifierSpec | None = Field(default=None)
    content_validator: ContentValidator | None = Field(default=None)

    @field_validator("heading_pattern")
    @classmethod
    def heading_pattern_must_be_valid_regex(cls, v: str) -> str:
        """Validate that heading_pattern is a valid regex."""
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e
        return v


class SpecModule(BaseModel):
    """
    Defines a file-level specification type.

    SpecModule represents document types like:
    - Requirement
    - Contract
    - Architecture Decision Record (ADR)
    - Test Plan
    - Design Document

    Each module type defines:
    - File naming patterns
    - Directory location patterns
    - Required and optional sections
    - Allowed references to other modules
    - Reusable class definitions (subsection patterns)
    """

    name: str = Field(description="Module type name (e.g., 'Requirement')")
    version: str = Field(default="1.0")
    description: str = Field(description="Human-readable description")

    file_pattern: str = Field(description="Regex pattern for filename (e.g., '^REQ-\\d{3}\\.md$')")
    location_pattern: str = Field(
        description="Regex pattern for directory path (e.g., 'requirements/')"
    )

    identifier: IdentifierSpec | None = Field(default=None)
    sections: list[SectionSpec] = Field(default_factory=list)
    references: list[Reference] = Field(default_factory=list)
    classes: dict[str, SpecClass] = Field(default_factory=dict)

    @field_validator("file_pattern", "location_pattern")
    @classmethod
    def pattern_must_be_valid_regex(cls, v: str) -> str:
        """Validate that patterns are valid regex."""
        try:
            re.compile(v)
        except re.error as e:
            raise ValueError(f"Invalid regex pattern: {e}") from e
        return v

    @field_validator("sections")
    @classmethod
    def at_least_one_required_section(cls, v: list[SectionSpec]) -> list[SectionSpec]:
        """Ensure at least one section is required."""
        if v and not any(section.required for section in v):
            raise ValueError("Module must have at least one required section")
        return v

    def matches_file(self, file_path: Path) -> bool:
        """
        Check if this module type applies to a file.

        Args:
            file_path: Path to check

        Returns:
            True if file matches this module type
        """
        # Check filename
        if not re.match(self.file_pattern, file_path.name):
            return False

        # Check location (use search to match anywhere in path)
        if not re.search(self.location_pattern, str(file_path)):
            return False

        return True

    def validate_structure(self, doc: MarkdownDocument, section_tree) -> list[ValidationError]:
        """
        Validate document structure against module definition.

        This implements Pass 4 of the validation architecture.

        Args:
            doc: Parsed markdown document
            section_tree: Section tree built from the document

        Returns:
            List of validation errors
        """
        errors: list[ValidationError] = []

        # Check required sections
        for section_spec in self.sections:
            if section_spec.required:
                found = self._find_section(section_tree, section_spec)
                if not found:
                    errors.append(
                        ValidationError(
                            error_type="missing_section",
                            severity="error",
                            file_path=str(doc.file_path) if doc.file_path else "unknown",
                            message=f"Required section '{section_spec.heading}' not found",
                            suggestion=f"Add a level {section_spec.heading_level} "
                            f"heading: {'#' * section_spec.heading_level} {section_spec.heading}",
                        )
                    )

        return errors

    def _find_section(self, section_tree, section_spec: SectionSpec) -> bool:
        """Find a section matching the spec in the section tree."""

        # Simplified implementation - real version would traverse tree
        # For now, just check if heading exists
        def traverse(node) -> bool:
            if hasattr(node, "heading") and node.heading == section_spec.heading:
                if node.level == section_spec.heading_level:
                    return True
            if hasattr(node, "subsections"):
                for child in node.subsections:
                    if traverse(child):
                        return True
            return False

        if hasattr(section_tree, "root"):
            return traverse(section_tree.root)
        return False


class GlobalConfig(BaseModel):
    """
    Global configuration for specification validation.

    This replaces the YAML-based config.yaml file with a Pydantic model.
    """

    version: str = Field(default="1.0")
    markdown_flavor: Literal["github", "gitlab", "commonmark"] = Field(default="github")
    link_formats: dict[str, dict] = Field(default_factory=dict)
    allow_circular_references: bool = Field(default=True)
    fail_on_warnings: bool = Field(default=False)

    @classmethod
    def default(cls) -> "GlobalConfig":
        """Create default configuration."""
        return cls(
            link_formats={
                "id_reference": {"pattern": r"^[A-Z]+-\d+$"},
                "class_reference": {"pattern": r"^#[A-Z]+-\d+$"},
            }
        )
