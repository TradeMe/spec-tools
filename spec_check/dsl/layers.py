"""
Layer-specific specification type definitions.

This module provides Pydantic models for different specification layers:
- Jobs-to-be-Done: User/customer jobs, pains, and gains
- Requirements: Technical requirements with acceptance criteria
- Architecture: Architecture decisions and design documents

Each layer has specific structural requirements and validation rules.
"""

from spec_check.dsl.models import (
    Cardinality,
    GherkinContentValidator,
    IdentifierSpec,
    Reference,
    SectionSpec,
    SpecClass,
    SpecModule,
)

# ============================================================================
# Jobs-to-be-Done Layer
# ============================================================================


class JobModule(SpecModule):
    """
    Jobs-to-be-Done specification.

    Jobs describe what users are trying to accomplish, their pains, and gains.
    This is the highest abstraction layer in the specification hierarchy.

    Example filename: JOB-001.md
    Location: specs/jobs/

    Required sections:
    - Context: Who is the user and what situation are they in?
    - Job Story: What is the user trying to accomplish?
    - Pains: What problems/frustrations exist today?
    - Gains: What positive outcomes are desired?
    """

    name: str = "Job"
    version: str = "1.0"
    description: str = "Jobs-to-be-Done specification"

    file_pattern: str = r"^JOB-\d{3}\.md$"
    location_pattern: str = r"specs/jobs/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"JOB-\d{3}",
        location="title",
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Context", heading_level=2, required=True),
        SectionSpec(heading="Job Story", heading_level=2, required=True),
        SectionSpec(heading="Pains", heading_level=2, required=True),
        SectionSpec(heading="Gains", heading_level=2, required=True),
        SectionSpec(heading="Success Metrics", heading_level=2, required=False),
    ]

    # Jobs don't reference other modules - they're the top level
    references: list[Reference] = []


# ============================================================================
# Requirements Layer
# ============================================================================


class AcceptanceCriterion(SpecClass):
    """
    A single acceptance criterion following Gherkin-style format.

    Example:
        ### AC-01: Valid Login
        **Given** a user with valid credentials
        **When** they submit the login form
        **Then** they receive an authentication token
    """

    heading_pattern: str = r"^AC-\d{2}:"
    heading_level: int = 3
    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"AC-\d{2}",
        location="heading",
        scope="module_instance",
    )
    content_validator: GherkinContentValidator = GherkinContentValidator()


class RequirementModule(SpecModule):
    """
    Technical requirement specification.

    Requirements define specific functional or non-functional capabilities
    that satisfy one or more Jobs-to-be-Done. They include acceptance criteria
    and must reference the jobs they address.

    Example filename: REQ-001.md
    Location: specs/requirements/

    Required sections:
    - Purpose: What job(s) does this requirement address?
    - Description: Detailed requirement specification
    - Acceptance Criteria: Testable conditions for completion

    Required references:
    - Must reference at least one Job (addresses relationship)
    """

    name: str = "Requirement"
    version: str = "1.0"
    description: str = "Technical requirement specification"

    file_pattern: str = r"^REQ-\d{3}\.md$"
    location_pattern: str = r"specs/requirements/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"REQ-\d{3}",
        location="title",
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Purpose", heading_level=2, required=True),
        SectionSpec(heading="Description", heading_level=2, required=True),
        SectionSpec(
            heading="Acceptance Criteria",
            heading_level=2,
            required=True,
            allowed_classes=["AcceptanceCriterion"],
            require_classes=True,
        ),
        SectionSpec(heading="Dependencies", heading_level=2, required=False),
        SectionSpec(heading="Notes", heading_level=2, required=False),
    ]

    references: list[Reference] = [
        Reference(
            name="addresses",
            source_type="Requirement",
            target_type="Job",
            cardinality=Cardinality(min=1, max=None),  # Must address at least one job
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
# Architecture Layer
# ============================================================================


class ArchitectureDecisionModule(SpecModule):
    """
    Architecture Decision Record (ADR).

    ADRs document significant architectural decisions, their context,
    and consequences. They may reference requirements they enable.

    Example filename: ADR-001.md
    Location: specs/architecture/
    """

    name: str = "ADR"
    version: str = "1.0"
    description: str = "Architectural Decision Record"

    file_pattern: str = r"^ADR-\d{3}\.md$"
    location_pattern: str = r"specs/architecture/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"ADR-\d{3}",
        location="title",
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Status", heading_level=2, required=True),
        SectionSpec(heading="Context", heading_level=2, required=True),
        SectionSpec(heading="Decision", heading_level=2, required=True),
        SectionSpec(heading="Consequences", heading_level=2, required=True),
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
            name="enables",
            source_type="ADR",
            target_type="Requirement",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
    ]


class PrinciplesModule(SpecModule):
    """
    Principles Document.

    Documents architectural principles, design philosophy, and guiding
    tenets for the project. Typically one per project.

    Example filename: principles.md
    Location: specs/
    """

    name: str = "Principles"
    version: str = "1.0"
    description: str = "Principles Document"

    # Match principles.md specifically
    file_pattern: str = r"^principles\.md$"
    location_pattern: str = r"^specs/[^/]+\.md$"

    # No identifier required for principles
    identifier: IdentifierSpec | None = None

    sections: list[SectionSpec] = [
        SectionSpec(heading="Overview", heading_level=2, required=False),
    ]

    references: list[Reference] = []


class SpecificationModule(SpecModule):
    """
    Specification Document (SPEC).

    Specifications document detailed requirements for a system or feature.
    They typically contain multiple requirements organized into sections.

    Example filename: SPEC-001.md (or named like markdown-link-validator.md)
    Location: specs/
    """

    name: str = "Specification"
    version: str = "1.0"
    description: str = "Specification Document"

    # Match files starting with SPEC- or specific spec names
    file_pattern: str = r"^(SPEC-\d{3}|markdown-[\w-]+|spec-[\w-]+)\.md$"
    # Match files directly in specs/ root, excluding subdirs
    location_pattern: str = r"^specs/[^/]+\.md$"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"SPEC-\d{3}",
        location="metadata",  # ID is in metadata section
        scope="global",
    )

    sections: list[SectionSpec] = [
        SectionSpec(heading="Overview", heading_level=2, required=False),
        SectionSpec(heading="Requirements", heading_level=2, required=False),
    ]

    references: list[Reference] = [
        Reference(
            name="addresses",
            source_type="Specification",
            target_type="Job",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
    ]


# ============================================================================
# Registry of Layer-Specific Types
# ============================================================================

LAYER_MODULES = {
    "Job": JobModule(),
    "Requirement": RequirementModule(),
    "ADR": ArchitectureDecisionModule(),
    "Specification": SpecificationModule(),
    "Principles": PrinciplesModule(),
}
