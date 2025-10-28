"""
ID registry for tracking module and class instance identifiers.

This is built during Pass 3 (Type Assignment) and used during Pass 7
(Reference Resolution) to map IDs to their locations.
"""

from dataclasses import dataclass, field
from pathlib import Path

from spec_check.ast_parser import Position


@dataclass
class ModuleInstance:
    """Represents a module instance (document) in the registry."""

    module_id: str
    """The unique identifier for this module instance."""

    module_type: str
    """The type of module (e.g., 'Requirement', 'Contract')."""

    file_path: Path
    """Path to the markdown file."""

    position: Position
    """Source position where the ID appears."""

    metadata: dict[str, str] = field(default_factory=dict)
    """Additional metadata extracted from frontmatter or document."""


@dataclass
class ClassInstance:
    """Represents a class instance (section) in the registry."""

    class_id: str
    """The unique identifier for this class instance."""

    class_type: str
    """The type of class (e.g., 'TestCase', 'AcceptanceCriterion')."""

    module_id: str
    """The ID of the containing module."""

    file_path: Path
    """Path to the markdown file containing this section."""

    section_path: list[str]
    """Path from document root to this section (list of headings)."""

    position: Position
    """Source position where the section starts."""

    metadata: dict[str, str] = field(default_factory=dict)
    """Additional metadata extracted from section."""


class IDRegistry:
    """
    Registry mapping IDs to module and class instances.

    Built during Pass 3 (Type Assignment) and used during Pass 7
    (Reference Resolution).
    """

    def __init__(self):
        """Initialize empty registry."""
        self.modules: dict[str, ModuleInstance] = {}
        """Map of module ID -> ModuleInstance."""

        self.classes: dict[str, ClassInstance] = {}
        """Map of class ID -> ClassInstance."""

        self.module_duplicates: dict[str, list[ModuleInstance]] = {}
        """Track duplicate module IDs for error reporting."""

        self.class_duplicates: dict[str, list[ClassInstance]] = {}
        """Track duplicate class IDs for error reporting."""

    def register_module(
        self,
        module_id: str,
        module_type: str,
        file_path: Path,
        position: Position,
        metadata: dict[str, str] | None = None,
    ) -> bool:
        """
        Register a module instance.

        Args:
            module_id: The module identifier
            module_type: The module type name
            file_path: Path to the markdown file
            position: Source position of the identifier
            metadata: Optional metadata dictionary

        Returns:
            True if registered successfully, False if duplicate
        """
        instance = ModuleInstance(
            module_id=module_id,
            module_type=module_type,
            file_path=file_path,
            position=position,
            metadata=metadata or {},
        )

        # Check for duplicates
        if module_id in self.modules:
            # Track duplicate
            if module_id not in self.module_duplicates:
                self.module_duplicates[module_id] = [self.modules[module_id]]
            self.module_duplicates[module_id].append(instance)
            return False

        self.modules[module_id] = instance
        return True

    def register_class(
        self,
        class_id: str,
        class_type: str,
        module_id: str,
        file_path: Path,
        section_path: list[str],
        position: Position,
        metadata: dict[str, str] | None = None,
    ) -> bool:
        """
        Register a class instance.

        Args:
            class_id: The class identifier
            class_type: The class type name
            module_id: The containing module ID
            file_path: Path to the markdown file
            section_path: Path to the section (list of headings)
            position: Source position of the section
            metadata: Optional metadata dictionary

        Returns:
            True if registered successfully, False if duplicate
        """
        instance = ClassInstance(
            class_id=class_id,
            class_type=class_type,
            module_id=module_id,
            file_path=file_path,
            section_path=section_path,
            position=position,
            metadata=metadata or {},
        )

        # Check for duplicates
        if class_id in self.classes:
            # Track duplicate
            if class_id not in self.class_duplicates:
                self.class_duplicates[class_id] = [self.classes[class_id]]
            self.class_duplicates[class_id].append(instance)
            return False

        self.classes[class_id] = instance
        return True

    def get_module(self, module_id: str) -> ModuleInstance | None:
        """Get a module instance by ID."""
        return self.modules.get(module_id)

    def get_class(self, class_id: str) -> ClassInstance | None:
        """Get a class instance by ID."""
        return self.classes.get(class_id)

    def get_module_by_file(self, file_path: Path) -> ModuleInstance | None:
        """
        Get a module instance by its file path.

        This enables resolving cross-document references that use relative file paths
        instead of module IDs (e.g., './011-deployment-architecture.md' → 'ADR-011').

        Args:
            file_path: Absolute or relative path to the module file

        Returns:
            ModuleInstance if found, None otherwise
        """
        # Resolve to absolute path for comparison
        try:
            target_path = file_path.resolve()
        except (OSError, RuntimeError):
            # Path doesn't exist or can't be resolved
            return None

        # Search all registered modules for matching file path
        for module in self.modules.values():
            try:
                if module.file_path.resolve() == target_path:
                    return module
            except (OSError, RuntimeError):
                # Module file path can't be resolved, skip it
                continue

        return None

    def find_class_in_module(self, class_id: str, module_id: str) -> ClassInstance | None:
        """
        Find a class instance within a specific module.

        Args:
            class_id: The class identifier
            module_id: The module to search in

        Returns:
            ClassInstance if found, None otherwise
        """
        instance = self.classes.get(class_id)
        if instance and instance.module_id == module_id:
            return instance
        return None

    def get_modules_by_type(self, module_type: str) -> list[ModuleInstance]:
        """Get all module instances of a specific type."""
        return [m for m in self.modules.values() if m.module_type == module_type]

    def get_classes_by_type(self, class_type: str) -> list[ClassInstance]:
        """Get all class instances of a specific type."""
        return [c for c in self.classes.values() if c.class_type == class_type]

    def has_duplicates(self) -> bool:
        """Check if there are any duplicate IDs."""
        return bool(self.module_duplicates or self.class_duplicates)

    def get_all_duplicate_errors(self) -> list[dict[str, any]]:
        """
        Get all duplicate ID errors for reporting.

        Returns:
            List of error dictionaries
        """
        errors = []

        for module_id, instances in self.module_duplicates.items():
            errors.append(
                {
                    "type": "duplicate_module_id",
                    "id": module_id,
                    "locations": [
                        {
                            "file": str(inst.file_path),
                            "line": inst.position.line,
                            "column": inst.position.column,
                        }
                        for inst in instances
                    ],
                }
            )

        for class_id, instances in self.class_duplicates.items():
            errors.append(
                {
                    "type": "duplicate_class_id",
                    "id": class_id,
                    "locations": [
                        {
                            "file": str(inst.file_path),
                            "line": inst.position.line,
                            "column": inst.position.column,
                            "section": " > ".join(inst.section_path),
                        }
                        for inst in instances
                    ],
                }
            )

        return errors
