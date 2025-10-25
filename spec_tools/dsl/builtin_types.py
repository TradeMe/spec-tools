"""
Built-in specification type definitions.

This module provides the default layer-specific type definitions:
- Job: Jobs-to-be-Done specifications (top layer)
- Requirement: Technical requirements that address Jobs (middle layer)
- ADR: Architecture Decision Records (bottom layer)

These types enforce the three-layer hierarchy where:
1. Jobs define user needs, pains, and desired outcomes
2. Requirements address Jobs and define technical solutions
3. ADRs document decisions that implement Requirements
"""

from spec_tools.dsl.layers import (
    AcceptanceCriterion,
    ArchitectureDecisionModule,
    JobModule,
    RequirementModule,
)

# ============================================================================
# Registry of Built-in Types
# ============================================================================

# Export all built-in module types
BUILTIN_MODULES = {
    "Job": JobModule(),
    "Requirement": RequirementModule(),
    "ADR": ArchitectureDecisionModule(),
}

# Export built-in class types
BUILTIN_CLASSES = {
    "AcceptanceCriterion": AcceptanceCriterion(),
}

__all__ = [
    "BUILTIN_MODULES",
    "BUILTIN_CLASSES",
    "JobModule",
    "RequirementModule",
    "ArchitectureDecisionModule",
    "AcceptanceCriterion",
]
