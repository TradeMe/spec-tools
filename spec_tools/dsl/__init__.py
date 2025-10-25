"""
DSL (Domain-Specific Language) for markdown specification validation.

This package implements a comprehensive type system for markdown documents,
enabling schema-based validation with ID-based reference resolution.
"""

from spec_tools.dsl.section_tree import SectionNode, SectionTree, build_section_tree
from spec_tools.dsl.type_definitions import (
    ClassDefinition,
    ContentValidator,
    ModuleDefinition,
    ReferenceDefinition,
    TypeDefinitionLoader,
)
from spec_tools.dsl.validator import DSLValidator, ValidationResult

__all__ = [
    "SectionNode",
    "SectionTree",
    "build_section_tree",
    "ContentValidator",
    "ModuleDefinition",
    "ClassDefinition",
    "ReferenceDefinition",
    "TypeDefinitionLoader",
    "DSLValidator",
    "ValidationResult",
]
