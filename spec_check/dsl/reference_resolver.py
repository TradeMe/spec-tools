"""
Reference resolution and validation.

This is Pass 7 of the multi-pass validation architecture.
Resolves references against the ID registry and validates:
- Target existence
- Type matching
- Cardinality constraints
"""

from dataclasses import dataclass
from pathlib import Path

from spec_check.dsl.id_registry import ClassInstance, IDRegistry, ModuleInstance
from spec_check.dsl.models import Reference as ReferenceDefinition
from spec_check.dsl.models import SpecModule
from spec_check.dsl.reference_extractor import Reference


@dataclass
class ResolutionResult:
    """Result of resolving a single reference."""

    reference: Reference
    """The original reference."""

    resolved: bool
    """Whether the reference was resolved successfully."""

    target_module: ModuleInstance | None = None
    """Resolved module instance (for module references)."""

    target_class: ClassInstance | None = None
    """Resolved class instance (for class references)."""

    error: str | None = None
    """Error message if resolution failed."""

    warning: str | None = None
    """Warning message (e.g., type mismatch but reference exists)."""


@dataclass
class CardinalityViolation:
    """Represents a cardinality constraint violation."""

    source_module_id: str
    """Source module with the violation."""

    source_file: Path
    """Source file."""

    reference_def: ReferenceDefinition
    """Reference definition that was violated."""

    expected_cardinality: str
    """Expected cardinality (e.g., '1', '1..*')."""

    actual_count: int
    """Actual number of references found."""

    message: str
    """Error message."""


class ReferenceResolver:
    """
    Resolves references against the ID registry.

    This implements Pass 7 of the multi-pass validation architecture.
    """

    def __init__(self, registry: IDRegistry):
        """
        Initialize the reference resolver.

        Args:
            registry: ID registry built during Pass 3
        """
        self.registry = registry

    def resolve_reference(
        self, reference: Reference, module_def: SpecModule | None = None
    ) -> ResolutionResult:
        """
        Resolve a single reference.

        Args:
            reference: The reference to resolve
            module_def: Source module definition for type checking

        Returns:
            Resolution result
        """
        if reference.reference_type == "external_reference":
            # External references are not resolved
            return ResolutionResult(reference=reference, resolved=True)

        elif reference.reference_type == "module_reference":
            return self._resolve_module_reference(reference, module_def)

        elif reference.reference_type == "class_reference":
            return self._resolve_class_reference(reference, module_def)

        else:
            return ResolutionResult(
                reference=reference,
                resolved=False,
                error=f"Unknown reference type: {reference.reference_type}",
            )

    def _resolve_module_reference(
        self, reference: Reference, module_def: SpecModule | None
    ) -> ResolutionResult:
        """Resolve a module reference (link to another document by ID)."""
        # Extract target ID
        target_id = self._extract_module_id(reference.link_target)

        if not target_id:
            return ResolutionResult(
                reference=reference,
                resolved=False,
                error=f"Could not extract module ID from target: {reference.link_target}",
            )

        # Try to look up by module ID first
        target_module = self.registry.get_module(target_id)

        # If not found by ID and target looks like a file path, try file path resolution
        if not target_module and self._is_file_path(target_id):
            target_module = self._resolve_by_file_path(reference.source_file, target_id)

        if not target_module:
            # Check if there are similar IDs (for helpful error messages)
            suggestions = self._find_similar_module_ids(target_id)
            error_msg = f"Module reference '{target_id}' not found"
            if suggestions:
                error_msg += f". Did you mean: {', '.join(suggestions)}?"

            return ResolutionResult(reference=reference, resolved=False, error=error_msg)

        # Validate type if module definition specifies expected type
        warning = None
        if module_def and reference.relationship:
            ref_def = self._find_reference_definition(module_def, reference.relationship)
            if ref_def and ref_def.target_type:
                if target_module.module_type != ref_def.target_type:
                    warning = (
                        f"Type mismatch: expected {ref_def.target_type}, "
                        f"found {target_module.module_type}"
                    )

        return ResolutionResult(
            reference=reference,
            resolved=True,
            target_module=target_module,
            warning=warning,
        )

    def _resolve_class_reference(
        self, reference: Reference, module_def: SpecModule | None
    ) -> ResolutionResult:
        """Resolve a class reference (link to a section by ID)."""
        # Extract target ID
        target_id, target_module_id = self._extract_class_id(reference.link_target)

        if not target_id:
            return ResolutionResult(
                reference=reference,
                resolved=False,
                error=f"Could not extract class ID from target: {reference.link_target}",
            )

        # If target module specified, search within that module
        if target_module_id:
            target_class = self.registry.find_class_in_module(target_id, target_module_id)
        else:
            # Search in current module
            if reference.source_module_id:
                target_class = self.registry.find_class_in_module(
                    target_id, reference.source_module_id
                )
            else:
                # Fallback to global search
                target_class = self.registry.get_class(target_id)

        if not target_class:
            suggestions = self._find_similar_class_ids(target_id)
            error_msg = f"Class reference '{target_id}' not found"
            if suggestions:
                error_msg += f". Did you mean: {', '.join(suggestions)}?"

            return ResolutionResult(reference=reference, resolved=False, error=error_msg)

        # Validate type if module definition specifies expected type
        warning = None
        if module_def and reference.relationship:
            ref_def = self._find_reference_definition(module_def, reference.relationship)
            if ref_def and ref_def.target_class:
                if target_class.class_type != ref_def.target_class:
                    warning = (
                        f"Type mismatch: expected {ref_def.target_class}, "
                        f"found {target_class.class_type}"
                    )

        return ResolutionResult(
            reference=reference,
            resolved=True,
            target_class=target_class,
            warning=warning,
        )

    def validate_cardinality(
        self,
        module_id: str,
        module_def: SpecModule,
        references: list[Reference],
    ) -> list[CardinalityViolation]:
        """
        Validate that cardinality constraints are satisfied.

        Args:
            module_id: Source module ID
            module_def: Module definition with reference constraints
            references: All references from this module

        Returns:
            List of cardinality violations
        """
        violations = []

        # Get the module instance for error reporting
        module_instance = self.registry.get_module(module_id)
        if not module_instance:
            return violations

        # Check each reference definition
        for ref_def in module_def.references:
            # Count references of this type
            matching_refs = [
                r
                for r in references
                if r.source_module_id == module_id and r.relationship == ref_def.name
            ]

            count = len(matching_refs)

            # Validate cardinality
            if not ref_def.validate_count(count):
                min_val, max_val = ref_def.parse_cardinality()

                if count < min_val:
                    message = (
                        f"Missing required reference of type '{ref_def.name}'. "
                        f"Expected at least {min_val}, found {count}."
                    )
                else:
                    message = (
                        f"Too many references of type '{ref_def.name}'. "
                        f"Expected at most {max_val}, found {count}."
                    )

                violations.append(
                    CardinalityViolation(
                        source_module_id=module_id,
                        source_file=module_instance.file_path,
                        reference_def=ref_def,
                        expected_cardinality=ref_def.cardinality,
                        actual_count=count,
                        message=message,
                    )
                )

        return violations

    def _is_file_path(self, target: str) -> bool:
        """
        Check if a target looks like a file path rather than a module ID.

        File paths typically contain:
        - Directory separators (/ or \\)
        - Relative path indicators (./ or ../)
        - File extensions before they're stripped

        Args:
            target: The target string (already processed by _extract_module_id)

        Returns:
            True if target looks like a file path
        """
        # Check for path separators or relative path indicators
        return "/" in target or "\\" in target or target.startswith(".")

    def _resolve_by_file_path(self, source_file: Path, target_path: str) -> ModuleInstance | None:
        """
        Resolve a module reference using a file path.

        Converts a relative file path like './011-deployment-architecture'
        to an absolute path and looks it up in the registry.

        Args:
            source_file: Path to the source file containing the reference
            target_path: Relative or absolute file path to the target (without .md extension)

        Returns:
            ModuleInstance if found, None otherwise
        """
        # Add back the .md extension that was stripped by _extract_module_id
        if not target_path.endswith(".md"):
            target_path_with_ext = target_path + ".md"
        else:
            target_path_with_ext = target_path

        # Resolve relative to source file's directory
        target_file = source_file.parent / target_path_with_ext

        # Look up by file path in registry
        return self.registry.get_module_by_file(target_file)

    def _extract_module_id(self, link_target: str) -> str | None:
        """Extract module ID from link target."""
        # Remove .md extension
        target = link_target.replace(".md", "")

        # If has fragment, take the part before
        if "#" in target:
            target = target.split("#")[0]

        # If empty after processing, no module ID
        if not target:
            return None

        return target

    def _extract_class_id(self, link_target: str) -> tuple[str | None, str | None]:
        """
        Extract class ID and optional module ID from link target.

        Returns:
            (class_id, module_id) where module_id may be None
        """
        # Format: #CLASS-ID or MODULE-ID#CLASS-ID
        if "#" not in link_target:
            return (None, None)

        if link_target.startswith("#"):
            # Format: #CLASS-ID (same document)
            class_id = link_target[1:]
            return (class_id, None)
        else:
            # Format: MODULE-ID#CLASS-ID
            parts = link_target.split("#", 1)
            module_id = parts[0].replace(".md", "")
            class_id = parts[1]
            return (class_id, module_id)

    def _find_reference_definition(
        self, module_def: SpecModule, relationship: str
    ) -> Reference | None:
        """Find a reference definition by relationship name."""
        for ref_def in module_def.references:
            if ref_def.name == relationship:
                return ref_def
        return None

    def _find_similar_module_ids(self, target_id: str, max_suggestions: int = 3) -> list[str]:
        """Find similar module IDs for helpful error messages."""
        from difflib import get_close_matches

        all_ids = list(self.registry.modules.keys())
        return get_close_matches(target_id, all_ids, n=max_suggestions, cutoff=0.6)

    def _find_similar_class_ids(self, target_id: str, max_suggestions: int = 3) -> list[str]:
        """Find similar class IDs for helpful error messages."""
        from difflib import get_close_matches

        all_ids = list(self.registry.classes.keys())
        return get_close_matches(target_id, all_ids, n=max_suggestions, cutoff=0.6)
