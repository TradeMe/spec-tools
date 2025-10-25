"""
Type definitions for the valid project test fixture.

This demonstrates using Python/Pydantic for type definitions instead of YAML.
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
    allow_circular_references=True,
)

# ============================================================================
# Requirement Module
# ============================================================================


class AcceptanceCriterion(SpecClass):
    """Acceptance criterion following Gherkin format."""

    heading_pattern: str = r"^AC-\d{2}:"
    heading_level: int = 3
    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"AC-\d{2}", location="heading", scope="module_instance"
    )


requirement_module = SpecModule(
    name="Requirement",
    version="1.0",
    description="Technical requirement specification",
    file_pattern=r"^REQ-\d{3}\.md$",
    location_pattern=r"requirements/",
    identifier=IdentifierSpec(pattern=r"REQ-\d{3}", location="title", scope="global"),
    sections=[
        SectionSpec(heading="Overview", heading_level=2, required=True),
        SectionSpec(heading="Acceptance Criteria", heading_level=2, required=False),
    ],
    references=[
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
    ],
    classes={
        "AcceptanceCriterion": AcceptanceCriterion(),
    },
)

# ============================================================================
# Contract Module
# ============================================================================

contract_module = SpecModule(
    name="Contract",
    version="1.0",
    description="Business contract specification",
    file_pattern=r"^CTR-\d{3}\.md$",
    location_pattern=r"contracts/",
    identifier=IdentifierSpec(pattern=r"CTR-\d{3}", location="title", scope="global"),
    sections=[
        SectionSpec(heading="Purpose", heading_level=2, required=True),
        SectionSpec(heading="Parties", heading_level=2, required=True),
        SectionSpec(heading="Terms", heading_level=2, required=True),
    ],
    references=[
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
    ],
)

# ============================================================================
# Architecture Decision Record (ADR) Module
# ============================================================================

adr_module = SpecModule(
    name="ADR",
    version="1.0",
    description="Architectural Decision Record",
    file_pattern=r"^ADR-\d{3}\.md$",
    location_pattern=r"adrs/",
    identifier=IdentifierSpec(pattern=r"ADR-\d{3}", location="title", scope="global"),
    sections=[
        SectionSpec(heading="Context", heading_level=2, required=True),
        SectionSpec(heading="Decision", heading_level=2, required=True),
        SectionSpec(heading="Consequences", heading_level=2, required=True),
        SectionSpec(heading="Status", heading_level=2, required=False),
    ],
    references=[
        Reference(
            name="supersedes",
            source_type="ADR",
            target_type="ADR",
            cardinality=Cardinality(min=0, max=None),
            link_format="id_reference",
        ),
    ],
)
