"""
Main DSL validator orchestrating all validation passes.

Implements the multi-pass validation architecture:
- Pass 1: AST Construction (using ast_parser.py)
- Pass 2: Section Hierarchy (section_tree.py)
- Pass 3: Type Assignment (this module)
- Pass 4: Structural Validation (structural_validator.py)
- Pass 5: Content Validation (content_validators/)
- Pass 6: Reference Extraction (reference_extractor.py)
- Pass 7: Reference Resolution (reference_resolver.py)
"""

import re
from dataclasses import dataclass, field
from pathlib import Path

from spec_check.ast_parser import MarkdownDocument, parse_markdown_file
from spec_check.dsl.id_registry import IDRegistry
from spec_check.dsl.models import SpecModule
from spec_check.dsl.reference_extractor import (
    Reference,
    ReferenceExtractor,
    build_reference_graph,
    detect_circular_references,
)
from spec_check.dsl.reference_resolver import (
    CardinalityViolation,
    ReferenceResolver,
    ResolutionResult,
)
from spec_check.dsl.registry import SpecTypeRegistry
from spec_check.dsl.section_tree import SectionTree, build_section_tree


@dataclass
class ValidationError:
    """Represents a validation error."""

    error_type: str
    """Error type (e.g., 'missing_section', 'broken_reference')."""

    severity: str = "error"
    """Severity: error, warning, info."""

    file_path: str | None = None
    """Source file path."""

    line: int | None = None
    """Line number."""

    column: int | None = None
    """Column offset."""

    message: str = ""
    """Error message."""

    suggestion: str | None = None
    """Suggestion for fixing the error."""

    context: str | None = None
    """Surrounding context for better understanding."""

    def __str__(self) -> str:
        """Format error for display."""
        location = ""
        if self.file_path:
            location = str(self.file_path)
            if self.line:
                location += f":{self.line}"
                if self.column:
                    location += f":{self.column}"

        severity_prefix = f"{self.severity}: " if self.severity != "error" else ""

        result = f"{location}: {severity_prefix}{self.message}"

        if self.suggestion:
            result += f"\n  Suggestion: {self.suggestion}"

        if self.context:
            result += f"\n  Context: {self.context}"

        return result


@dataclass
class ValidationResult:
    """Result of DSL validation."""

    success: bool
    """Whether validation passed (no errors)."""

    errors: list[ValidationError] = field(default_factory=list)
    """List of validation errors."""

    warnings: list[ValidationError] = field(default_factory=list)
    """List of validation warnings."""

    info: list[ValidationError] = field(default_factory=list)
    """List of informational messages."""

    documents_validated: int = 0
    """Number of documents validated."""

    references_validated: int = 0
    """Number of references validated."""

    def get_all_messages(self) -> list[ValidationError]:
        """Get all messages (errors, warnings, info) sorted by severity."""
        return self.errors + self.warnings + self.info

    def __str__(self) -> str:
        """Format validation result for display."""
        lines = []

        for error in self.errors:
            lines.append(str(error))

        for warning in self.warnings:
            lines.append(str(warning))

        for info_msg in self.info:
            lines.append(str(info_msg))

        summary = (
            f"\nValidation {'PASSED' if self.success else 'FAILED'}: "
            f"{len(self.errors)} errors, {len(self.warnings)} warnings, "
            f"{len(self.info)} info messages"
        )
        summary += f"\nDocuments validated: {self.documents_validated}"
        summary += f"\nReferences validated: {self.references_validated}"

        lines.append(summary)

        return "\n".join(lines)


@dataclass
class UnmanagedFile:
    """Represents an unmanaged markdown file.

    Unmanaged files are in scope but don't have formal type definitions.
    They can be referenced from other documents and can reference other documents,
    but they don't receive structural validation.
    """

    file_path: Path
    """Path to the markdown file."""

    content: str
    """Markdown content."""

    references: list[Reference] = field(default_factory=list)
    """Extracted references from this unmanaged file."""


@dataclass
class DocumentContext:
    """Context for a single document being validated."""

    file_path: Path
    """Path to the markdown file."""

    content: str
    """Markdown content."""

    parsed_doc: MarkdownDocument | None = None
    """Parsed markdown document with metadata."""

    module_def: SpecModule | None = None
    """Matched module definition."""

    module_id: str | None = None
    """Extracted module ID."""

    section_tree: SectionTree | None = None
    """Section hierarchy."""

    references: list[Reference] = field(default_factory=list)
    """Extracted references."""


class DSLValidator:
    """
    Main DSL validator implementing multi-pass validation.

    Usage:
        registry = SpecTypeRegistry.load_from_package(Path(".spec-types"))
        validator = DSLValidator(registry)
        result = validator.validate(Path("specs"))
    """

    def __init__(self, type_registry: SpecTypeRegistry):
        """
        Initialize the DSL validator.

        Args:
            type_registry: Type registry with loaded spec definitions
        """
        self.type_registry = type_registry
        self.id_registry = IDRegistry()
        self.documents: dict[Path, DocumentContext] = {}
        self.unmanaged_files: dict[Path, UnmanagedFile] = {}
        self.errors: list[ValidationError] = []
        self.warnings: list[ValidationError] = []
        self.info: list[ValidationError] = []

    def validate(
        self,
        root_path: Path,
        use_gitignore: bool = True,
        use_specignore: bool = True,
        specignore_file: str = ".specignore",
        strict: bool = False,
    ) -> ValidationResult:
        """
        Validate all markdown documents in a directory tree.

        Args:
            root_path: Root directory to search for markdown files
            use_gitignore: Whether to respect .gitignore patterns (default: True)
            use_specignore: Whether to use .specignore file (default: True)
            specignore_file: Path to specignore file (default: .specignore)
            strict: Whether to warn about unclassified files (default: False)

        Returns:
            Validation result
        """
        # Reset state
        self.id_registry = IDRegistry()
        self.documents = {}
        self.unmanaged_files = {}
        self.errors = []
        self.warnings = []
        self.info = []

        # Find all markdown files
        markdown_files = self._find_markdown_files(root_path, use_gitignore)

        # Load .specignore patterns
        specignore_spec = None
        if use_specignore:
            specignore_patterns = self._load_specignore_patterns(root_path / specignore_file)
            if specignore_patterns:
                try:
                    from pathspec import PathSpec
                    from pathspec.patterns import GitWildMatchPattern

                    specignore_spec = PathSpec.from_lines(GitWildMatchPattern, specignore_patterns)
                except ImportError:
                    self.warnings.append(
                        ValidationError(
                            error_type="missing_dependency",
                            severity="warning",
                            message="pathspec library not available, .specignore will be ignored",
                            suggestion="Install pathspec: pip install pathspec",
                        )
                    )

        # Pass 1 & 2: Parse and classify documents
        for file_path in markdown_files:
            self._process_and_classify_document(file_path, root_path, specignore_spec, strict)

        # Pass 3: Type assignment and ID registration (only for typed docs)
        for _file_path, doc_ctx in self.documents.items():
            self._assign_type_and_register(doc_ctx)

        # Check for duplicate IDs
        if self.id_registry.has_duplicates():
            for error_data in self.id_registry.get_all_duplicate_errors():
                self._add_duplicate_error(error_data)

        # Pass 4: Structural validation
        for doc_ctx in self.documents.values():
            if doc_ctx.module_def:
                self._validate_structure(doc_ctx)

        # Pass 5: Content validation
        # TODO: Implement content validation once content validators are ready

        # Pass 6: Reference extraction (typed and unmanaged docs)
        ref_extractor = ReferenceExtractor(self.type_registry.config)

        # Extract from typed documents
        for doc_ctx in self.documents.values():
            doc_ctx.references = ref_extractor.extract_references(
                doc_ctx.file_path,
                doc_ctx.content,
                doc_ctx.module_id,
                doc_ctx.module_def,
            )

        # Extract from unmanaged documents
        for unmanaged in self.unmanaged_files.values():
            unmanaged.references = ref_extractor.extract_references(
                unmanaged.file_path,
                unmanaged.content,
                None,  # No module ID
                None,  # No module definition
            )

        # Pass 7: Reference resolution
        ref_resolver = ReferenceResolver(self.id_registry, self.unmanaged_files)
        all_references: list[Reference] = []

        # Resolve typed document references
        for doc_ctx in self.documents.values():
            for reference in doc_ctx.references:
                all_references.append(reference)
                result = ref_resolver.resolve_reference(reference, doc_ctx.module_def)
                self._process_resolution_result(result)

            # Validate cardinality (only for typed documents)
            if doc_ctx.module_id and doc_ctx.module_def:
                violations = ref_resolver.validate_cardinality(
                    doc_ctx.module_id, doc_ctx.module_def, doc_ctx.references
                )
                for violation in violations:
                    self._add_cardinality_error(violation)

        # Resolve unmanaged document references
        for unmanaged in self.unmanaged_files.values():
            for reference in unmanaged.references:
                all_references.append(reference)
                result = ref_resolver.resolve_reference(reference, None)
                self._process_resolution_result(result)

        # Detect circular references
        ref_graph = build_reference_graph(all_references)
        cycles = detect_circular_references(ref_graph, allow_circular=False)
        for cycle in cycles:
            self._add_circular_reference_error(cycle)

        # Build result
        total_documents = len(self.documents) + len(self.unmanaged_files)
        return ValidationResult(
            success=len(self.errors) == 0,
            errors=self.errors,
            warnings=self.warnings,
            info=self.info,
            documents_validated=total_documents,
            references_validated=len(all_references),
        )

    def _process_document(self, file_path: Path) -> None:
        """Pass 1 & 2: Parse document and build section tree."""
        try:
            # Read content
            content = file_path.read_text()

            # Pass 1: Parse AST
            doc = parse_markdown_file(file_path)

            # Pass 2: Build section tree
            section_tree = build_section_tree(doc)

            # Store context
            self.documents[file_path] = DocumentContext(
                file_path=file_path,
                content=content,
                parsed_doc=doc,
                section_tree=section_tree,
            )

        except Exception as e:
            self.errors.append(
                ValidationError(
                    error_type="parse_error",
                    severity="error",
                    file_path=str(file_path),
                    message=f"Failed to parse document: {e}",
                )
            )

    def _assign_type_and_register(self, doc_ctx: DocumentContext) -> None:
        """Pass 3: Assign module type and register IDs."""
        # Find matching module definition
        module_def = self.type_registry.get_module_for_file(doc_ctx.file_path)

        if not module_def:
            # No matching type definition - this might be ok
            self.info.append(
                ValidationError(
                    error_type="no_type_match",
                    severity="info",
                    file_path=str(doc_ctx.file_path),
                    message="No type definition matches this document",
                )
            )
            return

        doc_ctx.module_def = module_def

        # Extract module ID
        if module_def.identifier and doc_ctx.section_tree:
            module_id = self._extract_module_id(doc_ctx, module_def)

            if not module_id:
                pattern = module_def.identifier.pattern
                location = module_def.identifier.location
                self.errors.append(
                    ValidationError(
                        error_type="missing_identifier",
                        severity="error",
                        file_path=str(doc_ctx.file_path),
                        message=f"Module identifier not found. Expected pattern: {pattern}",
                        suggestion=f"Add identifier in {location}",
                    )
                )
                return

            doc_ctx.module_id = module_id

            # Register in ID registry
            success = self.id_registry.register_module(
                module_id=module_id,
                module_type=module_def.name,
                file_path=doc_ctx.file_path,
                position=doc_ctx.section_tree.root.position,
            )

            if not success:
                # Duplicate ID - will be reported later
                pass

    def _extract_module_id(self, doc_ctx: DocumentContext, module_def: SpecModule) -> str | None:
        """Extract module ID from document based on identifier definition."""
        if not module_def.identifier or not doc_ctx.section_tree:
            return None

        location = module_def.identifier.location

        if location == "title":
            # Extract from document title (root heading or first H1)
            root = doc_ctx.section_tree.root

            # Check root section ID first
            if root.section_id:
                return root.section_id

            # If root has no ID, check first subsection (first H1)
            if root.subsections and root.subsections[0].section_id:
                return root.subsections[0].section_id

        elif location == "metadata":
            # Extract from document metadata (frontmatter or bold key-value pairs)
            if doc_ctx.parsed_doc and doc_ctx.parsed_doc.metadata:
                # Look for ID field in metadata
                for key, value in doc_ctx.parsed_doc.metadata.items():
                    if key.upper() == "ID" and re.match(module_def.identifier.pattern, value):
                        return value

        # TODO: Support heading and other locations

        return None

    def _validate_structure(self, doc_ctx: DocumentContext) -> None:
        """Pass 4: Validate document structure against module definition."""
        if not doc_ctx.module_def or not doc_ctx.section_tree:
            return

        # Check required sections
        for section_def in doc_ctx.module_def.sections:
            if section_def.required:
                found = doc_ctx.section_tree.find_section(section_def.heading)
                if not found:
                    heading_prefix = "#" * section_def.heading_level
                    heading_text = section_def.heading
                    suggestion = (
                        f"Add a level-{section_def.heading_level} heading: "
                        f"{heading_prefix} {heading_text}"
                    )
                    self.errors.append(
                        ValidationError(
                            error_type="missing_section",
                            severity="error",
                            file_path=str(doc_ctx.file_path),
                            message=f"Required section '{section_def.heading}' not found",
                            suggestion=suggestion,
                        )
                    )

    def _process_resolution_result(self, result: ResolutionResult) -> None:
        """Process reference resolution result and add errors/warnings."""
        if not result.resolved:
            self.errors.append(
                ValidationError(
                    error_type="broken_reference",
                    severity="error",
                    file_path=str(result.reference.source_file),
                    line=result.reference.position.line,
                    column=result.reference.position.column,
                    message=result.error or "Reference could not be resolved",
                    context=result.reference.context,
                )
            )
        elif result.warning:
            self.warnings.append(
                ValidationError(
                    error_type="reference_warning",
                    severity="warning",
                    file_path=str(result.reference.source_file),
                    line=result.reference.position.line,
                    column=result.reference.position.column,
                    message=result.warning,
                    context=result.reference.context,
                )
            )

    def _add_duplicate_error(self, error_data: dict) -> None:
        """Add duplicate ID error."""
        locations_str = ", ".join(f"{loc['file']}:{loc['line']}" for loc in error_data["locations"])

        self.errors.append(
            ValidationError(
                error_type=error_data["type"],
                severity="error",
                message=f"Duplicate ID '{error_data['id']}' found in: {locations_str}",
                suggestion="Ensure all IDs are unique within their scope",
            )
        )

    def _add_cardinality_error(self, violation: CardinalityViolation) -> None:
        """Add cardinality violation error."""
        ref_def = violation.reference_def
        target = ref_def.target_type
        self.errors.append(
            ValidationError(
                error_type="cardinality_violation",
                severity="error",
                file_path=str(violation.source_file),
                message=violation.message,
                suggestion=f"Add {ref_def.name} reference to {target}",
            )
        )

    def _add_circular_reference_error(self, cycle: list[str]) -> None:
        """Add circular reference error."""
        cycle_str = " -> ".join(cycle)

        self.errors.append(
            ValidationError(
                error_type="circular_reference",
                severity="error",
                message=f"Circular dependency detected: {cycle_str}",
                suggestion="Remove or restructure references to break the cycle",
            )
        )

    def _process_and_classify_document(
        self, file_path: Path, root_path: Path, specignore_spec, strict: bool
    ) -> None:
        """Process document and classify as Typed or Unmanaged."""
        try:
            # Read content
            content = file_path.read_text()

            # Parse document
            doc = parse_markdown_file(file_path)
            section_tree = build_section_tree(doc)

            # Try to match against type definitions
            module_def = self.type_registry.get_module_for_file(file_path)

            if module_def:
                # TYPED: Store for full validation
                self.documents[file_path] = DocumentContext(
                    file_path=file_path,
                    content=content,
                    parsed_doc=doc,
                    section_tree=section_tree,
                )
            else:
                # Check if matches .specignore patterns
                rel_path = file_path.relative_to(root_path)
                is_specignored = specignore_spec and specignore_spec.match_file(str(rel_path))

                # UNMANAGED: Register but don't validate structure
                self.unmanaged_files[file_path] = UnmanagedFile(
                    file_path=file_path, content=content
                )

                # Warn in strict mode if not explicitly specignored
                if strict and not is_specignored:
                    self.warnings.append(
                        ValidationError(
                            error_type="unclassified_file",
                            severity="warning",
                            file_path=str(file_path),
                            message="File doesn't match any type definition",
                            suggestion=(
                                "Add to .specignore or create a type definition for this file"
                            ),
                        )
                    )

        except Exception as e:
            self.errors.append(
                ValidationError(
                    error_type="parse_error",
                    severity="error",
                    file_path=str(file_path),
                    message=f"Failed to parse document: {e}",
                )
            )

    def _find_markdown_files(self, root_path: Path, use_gitignore: bool) -> list[Path]:
        """Find markdown files, respecting .gitignore if enabled."""
        all_files = list(root_path.rglob("*.md"))

        # Always auto-exclude VCS directories
        filtered = [f for f in all_files if not self._is_vcs_directory(f)]

        if use_gitignore:
            gitignore_patterns = self._load_gitignore_patterns(root_path)
            if gitignore_patterns:
                try:
                    from pathspec import PathSpec
                    from pathspec.patterns import GitWildMatchPattern

                    spec = PathSpec.from_lines(GitWildMatchPattern, gitignore_patterns)
                    filtered = [
                        f for f in filtered if not spec.match_file(str(f.relative_to(root_path)))
                    ]
                except ImportError:
                    # pathspec not available, skip gitignore filtering
                    pass

        return filtered

    def _is_vcs_directory(self, file_path: Path) -> bool:
        """Check if file is in a VCS or tool directory.

        Note: .claude is NOT in this list - users may want to validate it.
        """
        vcs_dirs = {
            ".git",
            ".hg",
            ".svn",
            ".bzr",
            ".venv",
            "venv",
            "env",
            "node_modules",
            "__pycache__",
            ".pytest_cache",
        }
        return any(part in vcs_dirs for part in file_path.parts)

    def _load_gitignore_patterns(self, root_path: Path) -> list[str]:
        """Load patterns from .gitignore file."""
        return self._load_ignore_patterns(root_path / ".gitignore")

    def _load_specignore_patterns(self, file_path: Path) -> list[str]:
        """Load patterns from .specignore file."""
        return self._load_ignore_patterns(file_path)

    def _load_ignore_patterns(self, file_path: Path) -> list[str]:
        """Load patterns from an ignore file."""
        if not file_path.exists():
            return []

        patterns = []
        for line in file_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                patterns.append(line)
        return patterns
