"""
DSL (Domain-Specific Language) for markdown specification validation.

This package implements a comprehensive type system for markdown documents,
enabling schema-based validation with ID-based reference resolution using
Pydantic models.
"""

# Layer-specific models
from spec_check.dsl.layers import (
    LAYER_MODULES,
    AcceptanceCriterion,
    ArchitectureDecisionModule,
    JobModule,
    RequirementModule,
)

# Pydantic-based models
from spec_check.dsl.models import (
    Cardinality,
    GlobalConfig,
    IdentifierSpec,
    Reference,
    SectionSpec,
    SpecClass,
    SpecModule,
    ValidationError,
)
from spec_check.dsl.registry import SpecTypeRegistry
from spec_check.dsl.section_tree import SectionNode, SectionTree, build_section_tree
from spec_check.dsl.validator import DSLValidator, ValidationResult

__all__ = [
    # Section tree
    "SectionNode",
    "SectionTree",
    "build_section_tree",
    # Pydantic models
    "Cardinality",
    "GlobalConfig",
    "IdentifierSpec",
    "Reference",
    "SectionSpec",
    "SpecClass",
    "SpecModule",
    "ValidationError",
    "SpecTypeRegistry",
    # Layer-specific models
    "JobModule",
    "RequirementModule",
    "ArchitectureDecisionModule",
    "AcceptanceCriterion",
    "LAYER_MODULES",
    # Validator
    "DSLValidator",
    "ValidationResult",
]
