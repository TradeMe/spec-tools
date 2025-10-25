"""
Type definitions for spec-tools project specifications.

This package defines the layer-specific Pydantic models used to validate
the spec-tools project's own specifications.
"""

from spec_tools.dsl.models import (
    Cardinality,
    GlobalConfig,
    IdentifierSpec,
    Reference,
    SectionSpec,
    SpecClass,
    SpecModule,
)

# ============================================================================
# Global Configuration
# ============================================================================

config = GlobalConfig(
    version="1.0",
    markdown_flavor="github",
    link_formats={
        "id_reference": {"pattern": r"^[A-Z]+-\d+$"},
        "class_reference": {"pattern": r"^#[A-Z]+-\d+$"},
    },
    allow_circular_references=False,
)

# ============================================================================
# Job Module (Top Layer)
# ============================================================================

job_module = SpecModule(
    name="Job",
    version="1.0",
    description="Jobs-to-be-Done specification describing user needs and desired outcomes",
    file_pattern=r"^JOB-\d{3}\.md$",
    location_pattern=r"specs/jobs/",
    identifier=IdentifierSpec(pattern=r"JOB-\d{3}", location="title", scope="global"),
    sections=[
        SectionSpec(heading="Context", heading_level=2, required=True),
        SectionSpec(heading="Job Story", heading_level=2, required=True),
        SectionSpec(heading="Pains", heading_level=2, required=True),
        SectionSpec(heading="Gains", heading_level=2, required=True),
    ],
    references=[],  # Top level - no dependencies
)

# ============================================================================
# Requirement Module (Middle Layer)
# ============================================================================


class AcceptanceCriterion(SpecClass):
    """Acceptance criterion following Gherkin-style format."""

    heading_pattern: str = r"^AC-\d{2}:"
    heading_level: int = 3
    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"AC-\d{2}", location="heading", scope="module_instance"
    )


requirement_module = SpecModule(
    name="Requirement",
    version="1.0",
    description="Technical requirement specification that addresses Jobs-to-be-Done",
    file_pattern=r"^REQ-\d{3}\.md$",
    location_pattern=r"specs/requirements/",
    identifier=IdentifierSpec(pattern=r"REQ-\d{3}", location="title", scope="global"),
    sections=[
        SectionSpec(heading="Purpose", heading_level=2, required=True),
        SectionSpec(heading="Description", heading_level=2, required=True),
        SectionSpec(heading="Acceptance Criteria", heading_level=2, required=True),
        SectionSpec(heading="Jobs Addressed", heading_level=2, required=True),
    ],
    references=[
        Reference(
            name="addresses",
            source_type="Requirement",
            target_type="Job",
            cardinality=Cardinality(min=1, max=None),  # MUST reference at least 1 Job
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
    ],
    classes={
        "AcceptanceCriterion": AcceptanceCriterion(),
    },
)

# ============================================================================
# Architecture Decision Record Module (Bottom Layer)
# ============================================================================

adr_module = SpecModule(
    name="ADR",
    version="1.0",
    description="Architectural Decision Record documenting significant technical decisions",
    file_pattern=r"^ADR-\d{3}\.md$",
    location_pattern=r"specs/adrs/",
    identifier=IdentifierSpec(pattern=r"ADR-\d{3}", location="title", scope="global"),
    sections=[
        SectionSpec(heading="Context", heading_level=2, required=True),
        SectionSpec(heading="Decision", heading_level=2, required=True),
        SectionSpec(heading="Consequences", heading_level=2, required=True),
        SectionSpec(heading="Status", heading_level=2, required=False),
    ],
    references=[
        Reference(
            name="implements",
            source_type="ADR",
            target_type="Requirement",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
        Reference(
            name="supersedes",
            source_type="ADR",
            target_type="ADR",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
    ],
)
