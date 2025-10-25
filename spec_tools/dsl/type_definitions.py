"""
Type definition system for DSL validation.

Defines and loads YAML-based type definitions for modules, classes,
references, and content validators.
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class IdentifierDefinition:
    """Defines how identifiers work for a module or class."""

    pattern: str
    """Regex pattern for valid identifiers."""

    location: str = "title"
    """Where the identifier appears: title, frontmatter, first_heading, heading."""

    scope: str = "global"
    """Uniqueness scope: global, directory, module_type, module_instance, section."""

    format: str | None = None
    """Optional format string for identifier generation."""

    def matches(self, identifier: str) -> bool:
        """Check if an identifier matches this definition's pattern."""
        return bool(re.match(self.pattern, identifier))


@dataclass
class ReferenceDefinition:
    """Defines an allowed reference type between modules or classes."""

    name: str
    """Reference relationship name (e.g., 'implements', 'depends_on')."""

    reference_type: str
    """Type: module_reference, class_reference, or external_reference."""

    target_module: str | None = None
    """Expected target module type (for module references)."""

    target_class: str | None = None
    """Expected target class type (for class references)."""

    cardinality: str = "0..*"
    """Cardinality constraint: 1, 0..1, 1..*, 0..*, n..m."""

    required: bool = False
    """Whether this reference is required."""

    link_format: str = "id_reference"
    """Link format: id_reference, class_reference, external_reference."""

    link_pattern: str | None = None
    """Optional regex pattern for link validation."""

    allowed_sections: list[str] | None = None
    """Sections where this reference can appear."""

    bidirectional: bool = False
    """Whether this reference is bidirectional."""

    must_exist: bool = True
    """Whether the target must exist."""

    allow_circular: bool = True
    """Whether circular dependencies are allowed."""

    def parse_cardinality(self) -> tuple[int, int | None]:
        """
        Parse cardinality into (min, max) tuple.

        Returns:
            (min, max) where max is None for unlimited
        """
        if self.cardinality == "1":
            return (1, 1)
        elif self.cardinality == "0..1":
            return (0, 1)
        elif self.cardinality == "1..*":
            return (1, None)
        elif self.cardinality == "0..*":
            return (0, None)
        elif ".." in self.cardinality:
            parts = self.cardinality.split("..")
            min_val = int(parts[0])
            max_val = None if parts[1] == "*" else int(parts[1])
            return (min_val, max_val)
        else:
            # Default to exact count
            return (int(self.cardinality), int(self.cardinality))

    def validate_count(self, count: int) -> bool:
        """Check if a reference count satisfies the cardinality constraint."""
        min_val, max_val = self.parse_cardinality()
        if count < min_val:
            return False
        if max_val is not None and count > max_val:
            return False
        return True


@dataclass
class ContentValidatorDefinition:
    """Defines a content validator for section content."""

    name: str
    """Validator name."""

    description: str = ""
    """Human-readable description."""

    grammar: dict[str, Any] = field(default_factory=dict)
    """Grammar definition for parsing content."""

    rules: list[dict[str, Any]] = field(default_factory=list)
    """Validation rules."""


@dataclass
class SectionDefinition:
    """Defines a required or optional section in a document."""

    heading: str
    """Expected heading text (can be pattern)."""

    level: int
    """Expected heading level."""

    required: bool = True
    """Whether this section is required."""

    content_type: str | None = None
    """Content validator to apply."""

    subsections: list[dict[str, Any]] = field(default_factory=list)
    """Expected subsections (classes or sections)."""

    fields: list[dict[str, Any]] = field(default_factory=list)
    """Required fields within this section."""


@dataclass
class ClassDefinition:
    """Defines a reusable section class (e.g., TestCase, AcceptanceCriterion)."""

    name: str
    """Class name."""

    description: str = ""
    """Human-readable description."""

    heading_pattern: str = ".*"
    """Regex pattern for section headings of this class."""

    level: int | list[int] = 3
    """Expected heading level(s)."""

    identifier: IdentifierDefinition | None = None
    """Identifier definition for class instances."""

    content_type: str | None = None
    """Content validator to apply."""

    sections: list[SectionDefinition] = field(default_factory=list)
    """Required subsections within this class."""

    fields: list[dict[str, Any]] = field(default_factory=list)
    """Required fields."""

    references: list[ReferenceDefinition] = field(default_factory=list)
    """Allowed references from this class."""

    usable_in: list[str] = field(default_factory=list)
    """Module types where this class can be used."""

    def matches_heading(self, heading_text: str) -> bool:
        """Check if a heading matches this class definition."""
        return bool(re.match(self.heading_pattern, heading_text))


@dataclass
class FrontmatterDefinition:
    """Defines frontmatter validation rules."""

    optional: bool = True
    """Whether frontmatter is optional."""

    allowed_keys: list[str] = field(default_factory=list)
    """Allowed frontmatter keys."""

    required_keys: list[str] = field(default_factory=list)
    """Required frontmatter keys."""

    validation: dict[str, dict[str, Any]] = field(default_factory=dict)
    """Per-key validation rules."""


@dataclass
class ModuleDefinition:
    """Defines a module type (e.g., Requirement, Contract, ADR)."""

    name: str
    """Module type name."""

    version: str = "1.0"
    """Type definition version."""

    description: str = ""
    """Human-readable description."""

    file_pattern: str = ".*\\.md$"
    """Regex pattern for file names."""

    location_pattern: str = ".*"
    """Regex pattern for file locations."""

    identifier: IdentifierDefinition | None = None
    """Module identifier definition."""

    frontmatter: FrontmatterDefinition | None = None
    """Frontmatter validation rules."""

    sections: list[SectionDefinition] = field(default_factory=list)
    """Required/optional sections."""

    references: list[ReferenceDefinition] = field(default_factory=list)
    """Allowed references from this module."""

    classes: dict[str, ClassDefinition] = field(default_factory=dict)
    """Inline class definitions (private to this module)."""

    def matches_file(self, file_path: Path) -> bool:
        """Check if a file path matches this module definition."""
        # Check file name
        if not re.match(self.file_pattern, file_path.name):
            return False

        # Check location
        if not re.match(self.location_pattern, str(file_path)):
            return False

        return True


@dataclass
class GlobalConfig:
    """Global DSL configuration."""

    dsl_version: str = "1.0"
    """DSL version."""

    markdown_flavor: str = "github"
    """Markdown flavor: github or gitlab."""

    allowed_features: dict[str, bool] = field(default_factory=dict)
    """Allowed markdown features."""

    id_resolution: dict[str, Any] = field(default_factory=dict)
    """ID resolution configuration."""

    link_formats: dict[str, dict[str, str]] = field(default_factory=dict)
    """Link format definitions."""

    validation: dict[str, Any] = field(default_factory=dict)
    """Validation settings."""

    error_reporting: dict[str, Any] = field(default_factory=dict)
    """Error reporting configuration."""


class TypeDefinitionLoader:
    """Loads type definitions from YAML files."""

    def __init__(self, type_dir: Path):
        """
        Initialize loader with type definition directory.

        Args:
            type_dir: Path to .spec-types directory
        """
        self.type_dir = type_dir
        self.modules: dict[str, ModuleDefinition] = {}
        self.classes: dict[str, ClassDefinition] = {}
        self.content_validators: dict[str, ContentValidatorDefinition] = {}
        self.config: GlobalConfig = GlobalConfig()

    def load_all(self) -> None:
        """Load all type definitions from the type directory."""
        # Load global config
        config_file = self.type_dir / "config.yaml"
        if config_file.exists():
            self.config = self._load_config(config_file)

        # Load modules
        modules_dir = self.type_dir / "modules"
        if modules_dir.exists():
            for yaml_file in modules_dir.glob("*.yaml"):
                module = self._load_module(yaml_file)
                self.modules[module.name] = module

        # Load shared classes
        classes_dir = self.type_dir / "classes"
        if classes_dir.exists():
            for yaml_file in classes_dir.glob("*.yaml"):
                class_def = self._load_class(yaml_file)
                self.classes[class_def.name] = class_def

        # Load content validators
        validators_dir = self.type_dir / "content-validators"
        if validators_dir.exists():
            for yaml_file in validators_dir.glob("*.yaml"):
                validator = self._load_content_validator(yaml_file)
                self.content_validators[validator.name] = validator

    def _load_config(self, config_file: Path) -> GlobalConfig:
        """Load global configuration from YAML."""
        with open(config_file) as f:
            data = yaml.safe_load(f)

        return GlobalConfig(
            dsl_version=data.get("dsl_version", "1.0"),
            markdown_flavor=data.get("markdown_flavor", "github"),
            allowed_features=data.get("allowed_features", {}),
            id_resolution=data.get("id_resolution", {}),
            link_formats=data.get("link_formats", {}),
            validation=data.get("validation", {}),
            error_reporting=data.get("error_reporting", {}),
        )

    def _load_module(self, yaml_file: Path) -> ModuleDefinition:
        """Load a module definition from YAML."""
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        module_data = data.get("module", {})

        # Parse identifier
        identifier = None
        if "identifier" in module_data:
            id_data = module_data["identifier"]
            identifier = IdentifierDefinition(
                pattern=id_data["pattern"],
                location=id_data.get("location", "title"),
                scope=id_data.get("scope", "global"),
                format=id_data.get("format"),
            )

        # Parse frontmatter
        frontmatter = None
        if "frontmatter" in module_data:
            fm_data = module_data["frontmatter"]
            frontmatter = FrontmatterDefinition(
                optional=fm_data.get("optional", True),
                allowed_keys=fm_data.get("allowed_keys", []),
                required_keys=fm_data.get("required_keys", []),
                validation=fm_data.get("validation", {}),
            )

        # Parse sections
        sections = []
        for section_data in module_data.get("sections", []):
            sections.append(
                SectionDefinition(
                    heading=section_data["heading"],
                    level=section_data["level"],
                    required=section_data.get("required", True),
                    content_type=section_data.get("content_type"),
                    subsections=section_data.get("subsections", []),
                    fields=section_data.get("fields", []),
                )
            )

        # Parse references
        references = []
        for ref_data in module_data.get("references", []):
            references.append(self._parse_reference(ref_data))

        # Parse inline classes
        classes = {}
        for class_name, class_data in module_data.get("classes", {}).items():
            classes[class_name] = self._parse_class(class_name, class_data)

        return ModuleDefinition(
            name=module_data["name"],
            version=module_data.get("version", "1.0"),
            description=module_data.get("description", ""),
            file_pattern=module_data.get("file_pattern", ".*\\.md$"),
            location_pattern=module_data.get("location_pattern", ".*"),
            identifier=identifier,
            frontmatter=frontmatter,
            sections=sections,
            references=references,
            classes=classes,
        )

    def _load_class(self, yaml_file: Path) -> ClassDefinition:
        """Load a shared class definition from YAML."""
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        class_data = data.get("class", {})
        return self._parse_class(class_data["name"], class_data)

    def _parse_class(self, name: str, class_data: dict[str, Any]) -> ClassDefinition:
        """Parse a class definition from dictionary."""
        # Parse identifier
        identifier = None
        if "identifier" in class_data:
            id_data = class_data["identifier"]
            identifier = IdentifierDefinition(
                pattern=id_data["pattern"],
                location=id_data.get("location", "heading"),
                scope=id_data.get("scope", "module_instance"),
                format=id_data.get("format"),
            )

        # Parse sections
        sections = []
        for section_data in class_data.get("sections", []):
            sections.append(
                SectionDefinition(
                    heading=section_data["heading"],
                    level=section_data["level"],
                    required=section_data.get("required", True),
                    content_type=section_data.get("content_type"),
                    subsections=section_data.get("subsections", []),
                    fields=section_data.get("fields", []),
                )
            )

        # Parse references
        references = []
        for ref_data in class_data.get("references", []):
            references.append(self._parse_reference(ref_data))

        return ClassDefinition(
            name=name,
            description=class_data.get("description", ""),
            heading_pattern=class_data.get("heading_pattern", ".*"),
            level=class_data.get("level", 3),
            identifier=identifier,
            content_type=class_data.get("content_type"),
            sections=sections,
            fields=class_data.get("fields", []),
            references=references,
            usable_in=class_data.get("usable_in", []),
        )

    def _parse_reference(self, ref_data: dict[str, Any]) -> ReferenceDefinition:
        """Parse a reference definition from dictionary."""
        return ReferenceDefinition(
            name=ref_data["name"],
            reference_type=ref_data.get("type", "module_reference"),
            target_module=ref_data.get("target_module"),
            target_class=ref_data.get("target_class"),
            cardinality=ref_data.get("cardinality", "0..*"),
            required=ref_data.get("required", False),
            link_format=ref_data.get("link_format", "id_reference"),
            link_pattern=ref_data.get("link_pattern"),
            allowed_sections=ref_data.get("allowed_sections"),
            bidirectional=ref_data.get("bidirectional", False),
            must_exist=ref_data.get("must_exist", True),
            allow_circular=ref_data.get("allow_circular", True),
        )

    def _load_content_validator(self, yaml_file: Path) -> ContentValidatorDefinition:
        """Load a content validator definition from YAML."""
        with open(yaml_file) as f:
            data = yaml.safe_load(f)

        validator_data = data.get("content_validator", {})
        return ContentValidatorDefinition(
            name=validator_data["name"],
            description=validator_data.get("description", ""),
            grammar=validator_data.get("grammar", {}),
            rules=validator_data.get("rules", []),
        )

    def get_module_for_file(self, file_path: Path) -> ModuleDefinition | None:
        """
        Find the module definition that matches a file path.

        Args:
            file_path: Path to the markdown file

        Returns:
            Matching module definition, or None if no match
        """
        matches = [m for m in self.modules.values() if m.matches_file(file_path)]

        if len(matches) == 0:
            return None
        elif len(matches) == 1:
            return matches[0]
        else:
            # Multiple matches - ambiguous
            # This should be reported as an error
            return None


# Export for type checking
ContentValidator = ContentValidatorDefinition
