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
        for doc_ctx in self.documents.values():
            if doc_ctx.module_def:
                self._validate_content(doc_ctx)

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

    def _validate_content(self, doc_ctx: DocumentContext) -> None:
        """Pass 5: Validate section content using content validators."""
        if not doc_ctx.module_def or not doc_ctx.section_tree:
            return

        # Track which class instances have been validated (to avoid double validation)
        validated_class_instances: set[int] = set()

        # Step 1: Validate section-level content (from SectionSpec.content_validator)
        for section_def in doc_ctx.module_def.sections:
            if section_def.content_validator:
                section_node = doc_ctx.section_tree.find_section(section_def.heading)
                if section_node:
                    # Extract raw content for this section
                    raw_content = self._extract_section_content(
                        doc_ctx.content, section_node, doc_ctx.section_tree
                    )
                    content_errors = section_def.content_validator.validate_content(
                        section_node.content, doc_ctx.file_path, raw_content=raw_content
                    )
                    for error in content_errors:
                        if error.severity == "error":
                            self.errors.append(error)
                        elif error.severity == "warning":
                            self.warnings.append(error)
                        else:
                            self.info.append(error)

        # Identify restricted classes (classes that are listed in any section's allowed_classes)
        restricted_classes = set()
        for section_def in doc_ctx.module_def.sections:
            if section_def.allowed_classes:
                restricted_classes.update(section_def.allowed_classes)

        # Step 2: Validate section-scoped classes (AC-03, AC-05, AC-06, AC-08)
        # For sections with allowed_classes, only validate classes within those sections
        for section_def in doc_ctx.module_def.sections:
            if section_def.allowed_classes:
                section_node = doc_ctx.section_tree.find_section(section_def.heading)
                if section_node:
                    found_instances: list[tuple[str, object]] = []

                    # Find all descendants of this section (not just direct subsections)
                    all_descendants = self._get_all_descendants(section_node)

                    for subsection in all_descendants:
                        # Check if this subsection matches any allowed class
                        for class_name in section_def.allowed_classes:
                            class_spec = doc_ctx.module_def.classes.get(class_name)
                            if class_spec:
                                pattern = re.compile(class_spec.heading_pattern)
                                if pattern.match(subsection.heading):
                                    # This subsection is a class instance - validate it
                                    found_instances.append((class_name, subsection))
                                    validated_class_instances.add(id(subsection))

                                    # AC-08: Validate heading level
                                    if subsection.level != class_spec.heading_level:
                                        expected_level = class_spec.heading_level
                                        self.warnings.append(
                                            ValidationError(
                                                error_type="incorrect_heading_level",
                                                severity="warning",
                                                file_path=str(doc_ctx.file_path),
                                                line=subsection.position.line,
                                                message=(
                                                    f"Class instance '{subsection.heading}' has "
                                                    f"heading level {subsection.level}, expected "
                                                    f"level {expected_level}"
                                                ),
                                                suggestion=(
                                                    f"Change heading to level {expected_level}: "
                                                    f"{'#' * expected_level} {subsection.heading}"
                                                ),
                                                context=f"In section: {section_node.heading}",
                                            )
                                        )

                                    # Validate content if validator exists
                                    if class_spec.content_validator:
                                        raw_content = self._extract_section_content(
                                            doc_ctx.content, subsection, doc_ctx.section_tree
                                        )
                                        content_errors = (
                                            class_spec.content_validator.validate_content(
                                                subsection.content,
                                                doc_ctx.file_path,
                                                raw_content=raw_content,
                                            )
                                        )
                                        for error in content_errors:
                                            # Add context about which class instance this is
                                            section_info = (
                                                f"In section: {section_node.heading} > "
                                                f"{subsection.heading}"
                                            )
                                            if error.context:
                                                error.context = f"{section_info}\n{error.context}"
                                            else:
                                                error.context = section_info
                                            if error.severity == "error":
                                                self.errors.append(error)
                                            elif error.severity == "warning":
                                                self.warnings.append(error)
                                            else:
                                                self.info.append(error)

                    # AC-05: Enforce require_classes constraint
                    if section_def.require_classes and not found_instances:
                        classes_str = ", ".join(section_def.allowed_classes)
                        self.errors.append(
                            ValidationError(
                                error_type="missing_required_classes",
                                severity="error",
                                file_path=str(doc_ctx.file_path),
                                message=(
                                    f"Section '{section_def.heading}' requires at least one "
                                    f"instance of: {classes_str}"
                                ),
                                suggestion=(
                                    f"Add at least one subsection matching the pattern(s) for: "
                                    f"{classes_str}"
                                ),
                            )
                        )

        # Step 3: Detect misplaced class instances (AC-04)
        # Check ALL sections for restricted classes that aren't allowed there
        for section_def in doc_ctx.module_def.sections:
            section_node = doc_ctx.section_tree.find_section(section_def.heading)
            if section_node:
                # Get all descendants of this section
                all_descendants = self._get_all_descendants(section_node)

                for subsection in all_descendants:
                    # Check if this subsection matches any restricted class pattern
                    for class_name, class_spec in doc_ctx.module_def.classes.items():
                        # Only check restricted classes
                        if class_name not in restricted_classes:
                            continue

                        pattern = re.compile(class_spec.heading_pattern)
                        if pattern.match(subsection.heading):
                            # This is a restricted class instance
                            # Is it allowed in this section?
                            if (
                                section_def.allowed_classes is None
                                or class_name not in section_def.allowed_classes
                            ):
                                # Find which section should contain this class
                                correct_sections = []
                                for other_section in doc_ctx.module_def.sections:
                                    if (
                                        other_section.allowed_classes
                                        and class_name in other_section.allowed_classes
                                    ):
                                        correct_sections.append(other_section.heading)

                                if correct_sections:
                                    suggestion = f"Move this to the '{correct_sections[0]}' section"
                                else:
                                    suggestion = (
                                        f"Remove this class instance from '{section_def.heading}'"
                                    )

                                allowed_msg = (
                                    f"Allowed classes in '{section_node.heading}': "
                                    f"{', '.join(section_def.allowed_classes)}"
                                    if section_def.allowed_classes
                                    else f"Section '{section_node.heading}' does not allow "
                                    f"restricted classes"
                                )

                                self.errors.append(
                                    ValidationError(
                                        error_type="misplaced_class_instance",
                                        severity="error",
                                        file_path=str(doc_ctx.file_path),
                                        line=subsection.position.line,
                                        message=(
                                            f"Class '{class_name}' instance "
                                            f"'{subsection.heading}' found in section "
                                            f"'{section_node.heading}' but not allowed there"
                                        ),
                                        suggestion=suggestion,
                                        context=allowed_msg,
                                    )
                                )

        # Step 4: Global validation for unrestricted classes (AC-07: backward compatibility)
        # For classes that are not in any section's allowed_classes, validate globally
        unrestricted_classes = set(doc_ctx.module_def.classes.keys()) - restricted_classes

        for class_name in unrestricted_classes:
            class_spec = doc_ctx.module_def.classes[class_name]
            if class_spec.content_validator:
                # Find all sections matching the class pattern (global search)
                pattern = re.compile(class_spec.heading_pattern)
                all_sections = doc_ctx.section_tree.get_all_sections()

                for section_node in all_sections:
                    # Skip if already validated in section-scoped context
                    if id(section_node) in validated_class_instances:
                        continue

                    if section_node.level == class_spec.heading_level and pattern.match(
                        section_node.heading
                    ):
                        # Extract raw content for this section
                        raw_content = self._extract_section_content(
                            doc_ctx.content, section_node, doc_ctx.section_tree
                        )
                        # This section matches the class pattern, validate its content
                        content_errors = class_spec.content_validator.validate_content(
                            section_node.content, doc_ctx.file_path, raw_content=raw_content
                        )
                        for error in content_errors:
                            # Add context about which class instance this is
                            section_info = f"In section: {section_node.heading}"
                            if error.context:
                                error.context = f"{section_info}\n{error.context}"
                            else:
                                error.context = section_info
                            if error.severity == "error":
                                self.errors.append(error)
                            elif error.severity == "warning":
                                self.warnings.append(error)
                            else:
                                self.info.append(error)

    def _get_all_descendants(self, section_node) -> list:
        """
        Get all descendants of a section node recursively.

        Args:
            section_node: The section node to get descendants from

        Returns:
            List of all descendant section nodes
        """
        descendants = []
        if hasattr(section_node, "subsections"):
            for subsection in section_node.subsections:
                descendants.append(subsection)
                # Recursively get descendants of subsections
                descendants.extend(self._get_all_descendants(subsection))
        return descendants

    def _extract_section_content(self, file_content: str, section_node, section_tree) -> str:
        """
        Extract the raw markdown content for a section.

        Args:
            file_content: Full file content
            section_node: The section node to extract content for
            section_tree: The section tree for context

        Returns:
            Raw content of the section (excluding the heading and subsections)
        """
        lines = file_content.split("\n")
        start_line = section_node.position.line

        # Find the end line (next section at same or higher level, or end of document)
        end_line = len(lines)
        all_sections = section_tree.get_all_sections()

        for other_section in all_sections:
            if other_section.position.line > start_line:
                # Check if this is a sibling or higher level section
                if other_section.level <= section_node.level:
                    end_line = other_section.position.line - 1
                    break
                # Check if this is a direct subsection (we want to exclude subsections)
                elif (
                    other_section in section_node.subsections
                    and other_section.position.line < end_line
                ):
                    end_line = other_section.position.line - 1

        # Extract content (skip the heading line itself)
        content_lines = lines[start_line:end_line]
        return "\n".join(content_lines)

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
        """Check if file is in a VCS metadata directory.

        Only excludes actual version control system directories, not build artifacts.
        Build artifacts (.venv, node_modules, etc.) should be excluded via .gitignore.

        Note: .claude is NOT in this list - users may want to validate it.
        """
        vcs_dirs = {".git", ".hg", ".svn", ".bzr"}
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
