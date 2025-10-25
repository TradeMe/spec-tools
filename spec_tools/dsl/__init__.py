"""
DSL (Domain-Specific Language) for markdown specification validation.

This package implements a comprehensive type system for markdown documents,
enabling schema-based validation with ID-based reference resolution.

The DSL now uses Pydantic models for type definitions, providing type safety,
IDE support, and composability. The old YAML-based system is deprecated.
"""

# New Pydantic-based models
from spec_tools.dsl.models import (
    Cardinality,
    GlobalConfig,
    IdentifierSpec,
    Reference,
    SectionSpec,
    SpecClass,
    SpecModule,
    ValidationError,
)
from spec_tools.dsl.registry import SpecTypeRegistry
from spec_tools.dsl.section_tree import SectionNode, SectionTree, build_section_tree

# Old YAML-based models (deprecated, kept for backward compatibility)
from spec_tools.dsl.type_definitions import (
    ClassDefinition,
    ModuleDefinition,
    ReferenceDefinition,
    TypeDefinitionLoader,
)
from spec_tools.dsl.validator import DSLValidator, ValidationResult

__all__ = [
    # Section tree
    "SectionNode",
    "SectionTree",
    "build_section_tree",
    # New Pydantic models
    "Cardinality",
    "GlobalConfig",
    "IdentifierSpec",
    "Reference",
    "SectionSpec",
    "SpecClass",
    "SpecModule",
    "ValidationError",
    "SpecTypeRegistry",
    # Old models (deprecated)
    "ModuleDefinition",
    "ClassDefinition",
    "ReferenceDefinition",
    "TypeDefinitionLoader",
    # Validator
    "DSLValidator",
    "ValidationResult",
]
