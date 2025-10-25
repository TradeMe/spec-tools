"""
Built-in specification type definitions.

This module provides example type definitions for common specification types
using the Pydantic-based DSL. These serve as both reference implementations
and ready-to-use types for common use cases.
"""

from spec_tools.dsl.models import (
    Cardinality,
    IdentifierSpec,
    Reference,
    SectionSpec,
    SpecClass,
    SpecModule,
)

# ============================================================================
# Requirement Module
# ============================================================================


class AcceptanceCriterion(SpecClass):
    """
    A single acceptance criterion following Gherkin-style format.

    Example:
        ### AC-01: Valid Credentials
        Given a user with valid credentials
        When they submit the login form
        Then they receive a JWT token
    """

    heading_pattern: str = r"^AC-\d{2}:"
    heading_level: int = 3
    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"AC-\d{2}",
        location="heading",
        scope="module_instance",
    )


class RequirementModule(SpecModule):
    """
    Technical requirement specification.

    Requirements define functional or non-functional system capabilities
    with acceptance criteria and implementation contracts.

    Example filename: REQ-001.md
    Location: requirements/
    """

    name: str = "Requirement"
    version: str = "1.0"
    description: str = "Technical requirement specification"

    file_pattern: str = r"^REQ-\d{3}\.md$"
    location_pattern: str = r"requirements/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"REQ-\d{3}",
        location="title",
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Overview", heading_level=2, required=True),
        SectionSpec(heading="Acceptance Criteria", heading_level=2, required=False),
    ]

    references: list[Reference] = [
        Reference(
            name="implements",
            source_type="Requirement",
            target_type="Contract",
            cardinality=Cardinality(min=1, max=1),
            link_format="id_reference",
            must_exist=True,
        ),
        Reference(
            name="depends_on",
            source_type="Requirement",
            target_type="Requirement",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
            allow_circular=False,
        ),
    ]

    classes: dict[str, SpecClass] = {
        "AcceptanceCriterion": AcceptanceCriterion(),
    }


# ============================================================================
# Contract Module
# ============================================================================


class ContractModule(SpecModule):
    """
    Business contract specification.

    Contracts define service-level agreements, business rules, and
    commitments between parties.

    Example filename: CTR-001.md
    Location: contracts/
    """

    name: str = "Contract"
    version: str = "1.0"
    description: str = "Business contract specification"

    file_pattern: str = r"^CTR-\d{3}\.md$"
    location_pattern: str = r"contracts/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"CTR-\d{3}",
        location="title",
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Purpose", heading_level=2, required=True),
        SectionSpec(heading="Parties", heading_level=2, required=True),
        SectionSpec(heading="Terms", heading_level=2, required=True),
    ]

    references: list[Reference] = [
        Reference(
            name="supersedes",
            source_type="Contract",
            target_type="Contract",
            cardinality=Cardinality(min=0, max=1),
            link_format="id_reference",
        ),
        Reference(
            name="references",
            source_type="Contract",
            target_type="ADR",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
    ]


# ============================================================================
# Architecture Decision Record (ADR) Module
# ============================================================================


class ArchitectureDecisionModule(SpecModule):
    """
    Architecture Decision Record (ADR).

    ADRs document significant architectural decisions, their context,
    rationale, and consequences.

    Example filename: ADR-001.md
    Location: adrs/
    """

    name: str = "ADR"
    version: str = "1.0"
    description: str = "Architectural Decision Record"

    file_pattern: str = r"^ADR-\d{3}\.md$"
    location_pattern: str = r"adrs/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"ADR-\d{3}",
        location="title",
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Context", heading_level=2, required=True),
        SectionSpec(heading="Decision", heading_level=2, required=True),
        SectionSpec(heading="Consequences", heading_level=2, required=True),
        SectionSpec(heading="Status", heading_level=2, required=False),
    ]

    references: list[Reference] = [
        Reference(
            name="supersedes",
            source_type="ADR",
            target_type="ADR",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
        Reference(
            name="see_also",
            source_type="ADR",
            target_type="ADR",
            cardinality=Cardinality(min=0, max=None),
            link_format="url",
            must_exist=False,
        ),
    ]


# ============================================================================
# Registry of Built-in Types
# ============================================================================

# Export all built-in module types
BUILTIN_MODULES = {
    "Requirement": RequirementModule(),
    "Contract": ContractModule(),
    "ADR": ArchitectureDecisionModule(),
}
