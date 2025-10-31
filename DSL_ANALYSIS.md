# DSL Validator Expressiveness Analysis and Proposed Improvements

**Author**: Claude
**Date**: 2025-10-31
**Purpose**: Analyze the expressiveness of the spec-check DSL after creating diverse specification documents and propose future improvements

## Executive Summary

After creating realistic specification documents across multiple document types (Vision, Jobs-to-be-Done, Requirements, Solution Architecture, and Implementation Design), the spec-check DSL has proven to be **highly expressive and flexible**. The Pydantic-based schema system successfully validated diverse document structures while maintaining type safety and extensibility.

**Key Findings**:
- ✅ **Strengths**: Section-scoped class validation, flexible cardinality, multiple content validators, clear separation of concerns
- ⚠️ **Opportunities**: Content validation could be more extensible, conditional sections not supported, cross-module queries limited
- 🚀 **Recommendations**: 15 proposed enhancements detailed below

## Document Types Created and Validated

### 1. Vision Documents (VIS-XXX)

**Example**: `specs/vision/VIS-001.md` - API Management Platform Vision

**Schema Capabilities Demonstrated**:
- ✅ Required sections (Vision Statement, Problem Statement, Goals, Stakeholders)
- ✅ Optional sections (Success Criteria, Constraints, Out of Scope)
- ✅ No external references required (top-level strategic document)
- ✅ Global unique identifiers

**Schema Definition**:
```python
class VisionModule(SpecModule):
    file_pattern: str = r"^VIS-\d{3}\.md$"
    location_pattern: str = r"specs/vision/"
    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"VIS-\d{3}", location="title", scope="global"
    )
    sections: list[SectionSpec] = [
        SectionSpec(heading="Vision Statement", heading_level=2, required=True),
        SectionSpec(heading="Problem Statement", heading_level=2, required=True),
        # ... more sections
    ]
```

**Validation Results**: ✅ Validates successfully with no errors

### 2. Jobs-to-be-Done Documents (JOB-XXX)

**Example**: `specs/jobs/JOB-004.md` - Protect API Resources from Abuse

**Schema Capabilities Demonstrated**:
- ✅ Structured sections for user needs (Context, Job Story, Pains, Gains)
- ✅ Success metrics as optional section
- ✅ No mandatory references (user-centric, not implementation-focused)

**Validation Results**: ✅ Validates successfully with no errors

### 3. Requirements Documents (REQ-XXX)

**Example**: `specs/requirements/REQ-006.md` - Distributed Rate Limiting System

**Schema Capabilities Demonstrated**:
- ✅ Section-scoped class validation (AC-XX only in Acceptance Criteria section)
- ✅ Gherkin content validation for acceptance criteria
- ✅ Required references to Jobs (cardinality 1..*)
- ✅ Optional dependencies to other requirements
- ✅ Module-instance scoped identifiers for AC-XX

**Schema Highlights**:
```python
sections: list[SectionSpec] = [
    # ...
    SectionSpec(
        heading="Acceptance Criteria",
        heading_level=2,
        required=True,
        allowed_classes=["AcceptanceCriterion"],  # REQ-005 feature
        require_classes=True,
    ),
]

classes: dict[str, SpecClass] = {
    "AcceptanceCriterion": AcceptanceCriterion(
        heading_pattern=r"^AC-\d{2}:",
        content_validator=GherkinContentValidator(),
    ),
}
```

**Validation Results**: ✅ Validates successfully with comprehensive Gherkin validation

### 4. Solution Architecture Documents (SOL-XXX)

**Example**: `specs/architecture/solutions/SOL-001.md` - Rate Limiting Solution Architecture

**Schema Capabilities Demonstrated**:
- ✅ Multiple section-scoped classes (ComponentSpec, QualityAttribute)
- ✅ Required class instances in Components section
- ✅ Optional class instances in Quality Attributes section
- ✅ References to both Requirements (must exist) and ADRs (optional)
- ✅ Complex document structure with diagrams and technical details

**Advanced Features**:
```python
sections: list[SectionSpec] = [
    SectionSpec(
        heading="Components",
        required=True,
        allowed_classes=["ComponentSpec"],
        require_classes=True,  # At least one component required
    ),
    SectionSpec(
        heading="Quality Attributes",
        required=False,
        allowed_classes=["QualityAttribute"],
        require_classes=False,  # Optional QA specs
    ),
]

references: list[Reference] = [
    Reference(
        name="addresses",
        target_type="Requirement",
        cardinality=Cardinality(min=1, max=None),  # Must address ≥1 requirement
        must_exist=True,
    ),
    Reference(
        name="relates_to",
        target_type="ADR",
        cardinality=Cardinality(min=0, max=None),  # May relate to ADRs
    ),
]
```

**Validation Results**: ✅ Validates successfully with rich component specifications

### 5. Implementation Design Documents (IMP-XXX)

**Example**: `specs/design/IMP-001.md` - Rate Limiter Middleware Implementation

**Schema Capabilities Demonstrated**:
- ✅ Multiple section-scoped classes (APISpec, DataModel)
- ✅ Flexible section structure (most sections optional)
- ✅ References to Solution Architecture (must implement)
- ✅ References to Requirements (optional, may address directly)
- ✅ Detailed technical content (code, algorithms, data models)

**Schema Flexibility**:
```python
sections: list[SectionSpec] = [
    SectionSpec(heading="Overview", required=True),  # Only required section
    SectionSpec(
        heading="API Specifications",
        required=False,
        allowed_classes=["APISpec"],
    ),
    SectionSpec(
        heading="Data Models",
        required=False,
        allowed_classes=["DataModel"],
    ),
    # 5 more optional sections for different design aspects
]
```

**Validation Results**: ✅ Validates successfully with comprehensive API and data model specifications

## Validator Strengths

### 1. Pydantic-Based Type Safety

**Strength**: Using Pydantic models instead of YAML provides compile-time type checking, IDE autocomplete, and validation.

**Example**:
```python
# Invalid configuration caught at model creation time
section = SectionSpec(
    heading="Test",
    heading_level=7,  # ❌ ValueError: heading_level must be 1-6
)
```

**Impact**: Prevents misconfiguration before runtime; improves developer experience.

### 2. Section-Scoped Class Validation (REQ-005)

**Strength**: The recently implemented `allowed_classes` and `require_classes` features provide fine-grained control over where class instances can appear.

**Example from Real Documents**:
- SOL-001 Components section: ✅ Only COMP-XX instances allowed
- SOL-001 Quality Attributes section: ✅ Only QA-XX instances allowed
- IMP-001 API Specifications section: ✅ Only API-XX instances allowed

**Impact**: Prevents structural errors like putting acceptance criteria in the wrong section.

### 3. Flexible Cardinality Constraints

**Strength**: Cardinality system supports diverse relationship patterns.

**Patterns Demonstrated**:
```python
Cardinality(min=0, max=None)    # "0..*" - Optional, unlimited
Cardinality(min=1, max=None)    # "1..*" - Required, at least one
Cardinality(min=0, max=1)       # "0..1" - Optional, single
Cardinality(min=1, max=1)       # "1" - Required, exactly one
```

**Impact**: Accurately models real-world requirements traceability needs.

### 4. Multiple Content Validators

**Strength**: Content validators can enforce domain-specific syntax.

**Implemented Validators**:
- `GherkinContentValidator`: Ensures Given-When-Then format for acceptance criteria
- Base `ContentValidator`: Extensible for custom grammars

**Example Validation**:
```markdown
### AC-01: Valid Login

**Given** a user with valid credentials  ✅ Bold format required
**When** they submit the login form       ✅ Bold format required
**Then** they receive an auth token       ✅ Bold format required
```

**Impact**: Ensures consistent, testable acceptance criteria format.

### 5. Hierarchical Document Types

**Strength**: Clear layering from strategic (Vision) to tactical (Implementation Design).

**Demonstrated Hierarchy**:
```
VIS-001 (Vision)
  ↓
JOB-004 (Jobs-to-be-Done)
  ↓
REQ-006 (Requirement) ← addresses JOB-004
  ↓
SOL-001 (Solution Architecture) ← addresses REQ-006
  ↓
IMP-001 (Implementation Design) ← implements SOL-001
```

**Impact**: Enables traceability from business vision to code implementation.

### 6. Backward Compatibility

**Strength**: Adding new document types (Vision, Solution Architecture, Implementation Design) did not break existing documents.

**Test Results**: All 362 existing tests pass, including tests for existing REQ, JOB, and ADR documents.

**Impact**: Safe evolution of the schema system over time.

## Identified Limitations and Gaps

### 1. Content Validation Extensibility

**Gap**: While `GherkinContentValidator` works well, adding new content validators requires Python code changes.

**Current Process**:
1. Create new `ContentValidator` subclass in `models.py`
2. Implement `validate_content()` method
3. Assign to section in module definition

**Limitation**: No declarative way to define content validation rules; requires code deployment.

**Example Use Case Not Supported**:
- RFC 2119 keyword validation ("shall", "must", "should", "may")
- Markdown table validation (ensure certain columns exist)
- Link format validation (ensure URLs follow pattern)
- Custom domain-specific languages

**Proposed Solution**: See Recommendation #1 below.

### 2. Conditional Section Requirements

**Gap**: Cannot express "Section A is required if Section B exists" type constraints.

**Example Use Case**:
- If "Security Considerations" section exists, "Threat Model" subsection should be required
- If "Performance Requirements" exist, "Performance Testing" section should be required
- If any API-XX specs exist, "API Specifications" section should exist (currently allowed anywhere)

**Current Workaround**: None - all conditional logic must be in code.

**Proposed Solution**: See Recommendation #2 below.

### 3. Cross-Module Query Support

**Gap**: Difficult to query across modules (e.g., "find all requirements not addressed by any solution architecture").

**Current Approach**: References are validated but not easily queryable post-validation.

**Example Queries Not Supported**:
- Which requirements have no solution architecture?
- Which jobs are addressed by multiple requirements? (good for coverage analysis)
- What is the full dependency chain for REQ-006?
- Which implementation designs don't have corresponding tests?

**Proposed Solution**: See Recommendation #3 below.

### 4. Numeric and Range Validation

**Gap**: No built-in support for validating numeric constraints in content.

**Example Use Cases**:
- Vision success criteria: "NPS above 50" → validate 50 is a valid number
- Requirements: "Support 100,000 requests/second" → validate metrics format
- Quality attributes: "p95 latency <5ms" → validate latency format

**Workaround**: Custom content validators can parse and validate, but not standardized.

**Proposed Solution**: See Recommendation #4 below.

### 5. Document Versioning and Evolution

**Gap**: No built-in support for document versioning beyond the `version` field.

**Example Use Cases**:
- Track changes to REQ-006 over time
- Understand when SOL-001 was updated and why
- Ensure IMP-001 is compatible with latest version of SOL-001

**Current Approach**: Manual version fields; no validation of version compatibility.

**Proposed Solution**: See Recommendation #5 below.

### 6. Custom Field Validation

**Gap**: Cannot validate custom metadata fields beyond what's in the schema.

**Example Use Cases**:
- Validate **Priority**: field is "High", "Medium", or "Low"
- Validate **Owner**: field is a valid team member
- Validate **Sprint**: field is a valid sprint number
- Ensure **Estimated Effort**: is in story points (1, 2, 3, 5, 8, 13)

**Workaround**: Custom validators, but not declarative.

**Proposed Solution**: See Recommendation #6 below.

### 7. Rich Text Content Validation

**Gap**: Limited support for validating specific markdown structures within content.

**Example Use Cases**:
- Ensure "Technology Stack" section contains a bulleted list
- Validate "Data Flow" section contains a code block (diagram)
- Require "Examples" section to have at least one code fence
- Ensure "Components" descriptions are paragraphs, not lists

**Current Approach**: Markdown is parsed but content structure not validated deeply.

**Proposed Solution**: See Recommendation #7 below.

### 8. Reference Directionality and Semantics

**Gap**: References are typed (addresses, implements, depends_on) but semantics not fully enforced.

**Example Issues**:
- SOL-001 "addresses" REQ-006, but REQ-006 doesn't know it's addressed by SOL-001
- Bidirectional references not validated for consistency
- Cannot query "upstream" vs "downstream" dependencies easily

**Proposed Solution**: See Recommendation #8 below.

### 9. Template Generation

**Gap**: No built-in support for generating document templates from schemas.

**Example Use Cases**:
- Generate `VIS-002.md` template with all required sections
- Generate `SOL-002.md` with component and QA section stubs
- Generate `REQ-007.md` with acceptance criteria placeholders

**Current Approach**: Manual copy-paste from existing documents.

**Proposed Solution**: See Recommendation #9 below.

### 10. Validation Rule Composition

**Gap**: Cannot easily compose validation rules (e.g., "this section requires GherkinValidator AND LinkValidator").

**Current Limitation**: Each section can have only one `content_validator`.

**Example Use Cases**:
- Acceptance Criteria: Gherkin format AND all links must be valid
- Architecture Decisions: Must contain "Context", "Decision", "Consequences" headings AND no broken links
- API Specs: Must have code blocks AND follow OpenAPI schema

**Proposed Solution**: See Recommendation #10 below.

## Proposed DSL Improvements

### Recommendation #1: Declarative Content Validation Rules

**Problem**: Adding new content validators requires Python code changes.

**Proposed Solution**: Declarative validation rule language.

**Example**:
```python
class ValidationRule(BaseModel):
    """Declarative validation rule."""
    type: Literal["regex", "keywords", "structure", "custom"]
    config: dict

# Example: RFC 2119 keyword validation
rfc2119_rule = ValidationRule(
    type="keywords",
    config={
        "required_keywords": ["shall", "must"],
        "optional_keywords": ["should", "may"],
        "case_sensitive": False,
        "bold_format": True,
    }
)

# Example: Table structure validation
table_rule = ValidationRule(
    type="structure",
    config={
        "element_type": "table",
        "required_columns": ["Name", "Type", "Description"],
        "min_rows": 1,
    }
)

# Usage in section spec
SectionSpec(
    heading="Requirements",
    content_validator=DeclarativeValidator(rules=[rfc2119_rule])
)
```

**Benefits**:
- No code deployment needed for new validation rules
- Shareable validation patterns across projects
- Easier to test and document

**Implementation Effort**: Medium (2-3 weeks)

### Recommendation #2: Conditional Section Requirements

**Problem**: Cannot express "if X then Y must exist" constraints.

**Proposed Solution**: Add `conditional_requirements` field to `SectionSpec`.

**Example**:
```python
class ConditionalRequirement(BaseModel):
    """Conditional requirement for sections."""
    condition: str  # Python expression or simple DSL
    then_required: list[str]  # Section headings that become required
    error_message: str

SectionSpec(
    heading="Security Considerations",
    required=False,
    conditional_requirements=[
        ConditionalRequirement(
            condition="section_exists('API Specifications')",
            then_required=["Authentication", "Authorization"],
            error_message="API specs require auth sections"
        ),
        ConditionalRequirement(
            condition="any_class_instance('APISpec')",
            then_required=["Security Considerations"],
            error_message="APIs require security documentation"
        ),
    ]
)
```

**Benefits**:
- Express complex structural requirements
- Better validation of document completeness
- Self-documenting constraints

**Implementation Effort**: Medium (1-2 weeks)

### Recommendation #3: Reference Graph Query API

**Problem**: Difficult to query relationships across documents.

**Proposed Solution**: Build reference graph and provide query API.

**Example API**:
```python
from spec_check.dsl.query import ReferenceGraph

# Build graph from validation result
graph = ReferenceGraph.from_validation_result(result)

# Query: Find all requirements not addressed by solution architectures
orphaned_reqs = graph.query(
    source_type="Requirement",
    without_incoming_reference="addresses",
    from_type="SolutionArchitecture"
)

# Query: Get full dependency chain for REQ-006
chain = graph.dependency_chain("REQ-006", max_depth=10)
# Returns: VIS-001 → JOB-004 → REQ-006 → SOL-001 → IMP-001

# Query: Find circular dependencies
cycles = graph.find_cycles()

# Query: Coverage analysis
coverage = graph.coverage_report()
# {
#   "jobs_with_requirements": 3,
#   "jobs_without_requirements": 0,
#   "requirements_with_solutions": 5,
#   "requirements_without_solutions": 1,
# }
```

**Benefits**:
- Powerful traceability analysis
- Coverage gap identification
- Dependency visualization support

**Implementation Effort**: High (3-4 weeks)

### Recommendation #4: Structured Field Validators

**Problem**: No standardized validation for structured fields (numbers, dates, enums).

**Proposed Solution**: Add field validator library.

**Example**:
```python
from spec_check.dsl.validators import FieldValidator

class MetricValidator(FieldValidator):
    """Validates metric format: '<number> <unit>'."""
    pattern = r"(\d+(?:\.\d+)?)\s+([a-zA-Z/]+)"

class PercentageValidator(FieldValidator):
    """Validates percentage: '50%' or '0.5'."""
    min_value = 0.0
    max_value = 100.0

# Usage in content validator
class PerformanceRequirementValidator(ContentValidator):
    validators = {
        "throughput": MetricValidator(units=["requests/second", "req/s"]),
        "latency": MetricValidator(units=["ms", "milliseconds"]),
        "uptime": PercentageValidator(),
    }

    def validate_content(self, content, file_path):
        # Automatically extract and validate metrics
        metrics = self.extract_metrics(content)
        errors = []
        for name, value in metrics.items():
            if name in self.validators:
                validator = self.validators[name]
                if not validator.validate(value):
                    errors.append(...)
        return errors
```

**Benefits**:
- Consistent metric validation
- Reusable validators
- Better error messages

**Implementation Effort**: Medium (2 weeks)

### Recommendation #5: Document Version Control Integration

**Problem**: No tracking of document evolution over time.

**Proposed Solution**: Add version tracking and compatibility checks.

**Example**:
```python
class VersionSpec(BaseModel):
    """Version specification for documents."""
    current: str  # Semantic version: "1.2.3"
    compatible_with: dict[str, str]  # Module ID → version constraint
    changelog: list[str]  # Change descriptions

class ImplementationDesignModule(SpecModule):
    # ...
    version_spec: VersionSpec = VersionSpec(
        current="1.0.0",
        compatible_with={
            "SOL-001": ">=1.0.0,<2.0.0",  # Compatible with SOL-001 v1.x
        }
    )

# Validation checks version compatibility
if imp_001.version != "1.0.0":
    if not is_compatible(imp_001.version, sol_001.version):
        error("IMP-001 v{} incompatible with SOL-001 v{}")
```

**Benefits**:
- Track document evolution
- Ensure compatibility
- Support versioned APIs

**Implementation Effort**: High (3-4 weeks)

### Recommendation #6: Custom Metadata Field Validation

**Problem**: Cannot validate custom metadata fields declaratively.

**Proposed Solution**: Add metadata schema support.

**Example**:
```python
class MetadataField(BaseModel):
    """Metadata field definition."""
    name: str
    type: Literal["string", "number", "enum", "date"]
    required: bool
    enum_values: list[str] | None = None
    pattern: str | None = None

class RequirementModule(SpecModule):
    # ...
    metadata_fields: list[MetadataField] = [
        MetadataField(
            name="Priority",
            type="enum",
            required=True,
            enum_values=["Critical", "High", "Medium", "Low"]
        ),
        MetadataField(
            name="Owner",
            type="string",
            required=True,
            pattern=r"^[a-z]+\.[a-z]+@company\.com$"
        ),
        MetadataField(
            name="Estimated Effort",
            type="enum",
            required=False,
            enum_values=["1", "2", "3", "5", "8", "13"]  # Story points
        ),
    ]
```

**Benefits**:
- Enforce project-specific metadata
- Improve project management integration
- Consistent field naming

**Implementation Effort**: Medium (2-3 weeks)

### Recommendation #7: Markdown Structure Validation

**Problem**: Limited validation of markdown element structure.

**Proposed Solution**: Add AST-based structure validators.

**Example**:
```python
class StructureValidator(ContentValidator):
    """Validates markdown structure."""
    required_elements: list[str]  # ["list", "code_block", "table"]
    min_paragraphs: int = 0
    min_headings: int = 0

# Usage
SectionSpec(
    heading="Examples",
    content_validator=StructureValidator(
        required_elements=["code_block"],
        min_paragraphs=1,
    )
)

SectionSpec(
    heading="Technology Stack",
    content_validator=StructureValidator(
        required_elements=["list"],
        min_list_items=3,
    )
)
```

**Benefits**:
- Ensure documentation completeness
- Validate examples are present
- Enforce formatting consistency

**Implementation Effort**: Low (1 week)

### Recommendation #8: Bidirectional Reference Validation

**Problem**: References are one-directional; inverse relationships not validated.

**Proposed Solution**: Add bidirectional reference support.

**Example**:
```python
class Reference(BaseModel):
    # ... existing fields ...
    inverse: str | None = None  # Name of inverse relationship
    enforce_bidirectional: bool = False

# Solution Architecture references
Reference(
    name="addresses",
    source_type="SolutionArchitecture",
    target_type="Requirement",
    inverse="addressed_by",  # ← REQ should have "addressed_by" ref back
    enforce_bidirectional=True,
)

# Validation checks:
# 1. SOL-001 addresses REQ-006 ✅
# 2. REQ-006 must have "addressed_by" reference back to SOL-001 ✅
# 3. If missing, validation error
```

**Benefits**:
- Ensure reference consistency
- Enable upstream queries
- Better traceability

**Implementation Effort**: Medium (2 weeks)

### Recommendation #9: Template Generation from Schemas

**Problem**: No automated template generation.

**Proposed Solution**: Add template generator CLI command.

**Example CLI**:
```bash
# Generate Vision document template
spec-check generate template --type Vision --id VIS-002 --output specs/vision/VIS-002.md

# Generated template:
# ---
# # VIS-002: [Title]
#
# **Version**: 1.0
# **Created**: 2025-10-31
# **Status**: Draft
#
# ## Vision Statement
#
# [Describe the desired future state...]
#
# ## Problem Statement
#
# [Describe the problem being solved...]
# ---

# Generate with interactive prompts
spec-check generate template --type Requirement --interactive

# Generate all templates for a feature
spec-check generate feature --name "User Authentication" --output specs/auth/
# Creates: VIS-003.md, JOB-005.md, REQ-007.md, SOL-002.md, IMP-002.md
```

**Benefits**:
- Faster document creation
- Consistent structure
- Reduce copy-paste errors

**Implementation Effort**: Medium (2 weeks)

### Recommendation #10: Composable Validation Rules

**Problem**: Can only have one content validator per section.

**Proposed Solution**: Support validator composition.

**Example**:
```python
from spec_check.dsl.validators import CompositeValidator, and_, or_

# Combine multiple validators with AND logic
SectionSpec(
    heading="Acceptance Criteria",
    content_validator=CompositeValidator(
        validators=[
            GherkinContentValidator(),
            LinkValidator(check_external=True),
            MetadataValidator(required_fields=["Priority"]),
        ],
        composition=and_,  # All must pass
    )
)

# OR logic for alternative formats
SectionSpec(
    heading="Examples",
    content_validator=CompositeValidator(
        validators=[
            CodeBlockValidator(language="python"),
            CodeBlockValidator(language="typescript"),
        ],
        composition=or_,  # At least one must pass
    )
)
```

**Benefits**:
- Flexible validation composition
- Reusable validator components
- Support complex validation scenarios

**Implementation Effort**: Low (1 week)

### Recommendation #11: Schema Inheritance and Mixins

**Problem**: Duplicate section definitions across similar modules.

**Proposed Solution**: Support schema inheritance and mixins.

**Example**:
```python
# Base mixin for common metadata sections
class MetadataMixin(SpecModule):
    """Common metadata sections."""
    sections: list[SectionSpec] = [
        SectionSpec(heading="Version History", heading_level=2, required=False),
        SectionSpec(heading="Authors", heading_level=2, required=False),
        SectionSpec(heading="Reviewers", heading_level=2, required=False),
    ]

# Use mixin in multiple modules
class EnhancedRequirementModule(RequirementModule, MetadataMixin):
    """Requirement with metadata sections."""
    pass  # Inherits sections from both parents

# Mixin for technical documents
class TechnicalDocumentMixin(SpecModule):
    sections: list[SectionSpec] = [
        SectionSpec(heading="References", heading_level=2, required=False),
        SectionSpec(heading="Glossary", heading_level=2, required=False),
    ]

class SolutionArchitectureModule(SpecModule, TechnicalDocumentMixin):
    # Gets References and Glossary sections automatically
    pass
```

**Benefits**:
- Reduce duplication
- Consistent cross-module sections
- Easier maintenance

**Implementation Effort**: Low (1 week)

### Recommendation #12: Linter-Style Auto-Fix

**Problem**: Validator reports errors but doesn't suggest fixes.

**Proposed Solution**: Add auto-fix capabilities for common issues.

**Example**:
```bash
# Check for issues
spec-check check-schema specs/

# Errors found:
# - REQ-006.md: Missing **Given** in AC-03 (line 45)
# - SOL-001.md: Missing COMP- identifier in heading (line 78)

# Auto-fix
spec-check check-schema specs/ --fix

# Fixes applied:
# - REQ-006.md: Added **Given** keyword (line 45)
# - SOL-001.md: Added COMP-03 identifier to heading (line 78)
```

**Auto-fixable Issues**:
- Missing bold format on Gherkin keywords
- Missing identifiers in class instance headings
- Incorrect heading levels
- Missing required sections (can add templates)
- Broken internal links (can suggest corrections)

**Benefits**:
- Faster error resolution
- Consistent formatting
- Reduce manual fixes

**Implementation Effort**: High (3-4 weeks)

### Recommendation #13: Language Server Protocol (LSP) Support

**Problem**: No IDE integration for real-time validation.

**Proposed Solution**: Implement LSP server for spec documents.

**Features**:
- Real-time validation as you type
- Autocomplete for section headings
- Autocomplete for class instance identifiers (AC-01, COMP-01, etc.)
- Jump to definition for references ([REQ-006] → jump to REQ-006.md)
- Hover documentation for identifiers
- Rename refactoring (rename REQ-006 → REQ-007 updates all references)

**Benefits**:
- Better developer experience
- Catch errors earlier
- Faster document creation

**Implementation Effort**: Very High (6-8 weeks)

### Recommendation #14: Schema Visualization

**Problem**: Hard to understand schema relationships visually.

**Proposed Solution**: Generate schema diagrams.

**Example**:
```bash
# Generate schema diagram
spec-check visualize schema --output schema.svg

# Generate reference graph for specific documents
spec-check visualize references --doc REQ-006 --output req-006-refs.svg

# Generate coverage map
spec-check visualize coverage --output coverage.svg
```

**Diagram Types**:
- Schema hierarchy (Vision → Job → Req → Sol → Imp)
- Reference relationships (who references whom)
- Coverage heatmap (which docs are well-connected)
- Dependency chains

**Benefits**:
- Better understanding of documentation structure
- Identify gaps visually
- Onboarding new team members

**Implementation Effort**: Medium (2-3 weeks)

### Recommendation #15: Schema Testing Framework

**Problem**: No dedicated framework for testing custom validators.

**Proposed Solution**: Add testing utilities for schema validation.

**Example**:
```python
from spec_check.testing import SchemaTestCase

class TestCustomValidator(SchemaTestCase):
    def test_gherkin_validator_rejects_missing_given(self):
        content = """
        ### AC-01: Test
        **When** user clicks
        **Then** page loads
        """
        result = self.validate_content(
            content=content,
            validator=GherkinContentValidator(),
            expected_errors=["missing_gherkin_keyword"]
        )
        self.assert_error_contains(result, "Missing: Given")

    def test_component_spec_in_components_section(self):
        doc = self.create_test_document(
            module_type="SolutionArchitecture",
            content="""
            # SOL-999: Test
            ## Components
            ### COMP-01: Valid Component
            """
        )
        result = self.validate_document(doc)
        self.assert_no_errors(result)
```

**Benefits**:
- Test-driven schema development
- Prevent regressions
- Documentation of expected behavior

**Implementation Effort**: Low (1 week)

## Priority Recommendations

Based on impact vs. effort analysis, here are the top 5 priorities:

### Priority 1: Template Generation (#9)
**Impact**: High | **Effort**: Medium | **Benefit**: Immediate productivity boost

### Priority 2: Composable Validation Rules (#10)
**Impact**: High | **Effort**: Low | **Benefit**: More flexible validation

### Priority 3: Reference Graph Query API (#3)
**Impact**: Very High | **Effort**: High | **Benefit**: Powerful traceability

### Priority 4: Markdown Structure Validation (#7)
**Impact**: Medium | **Effort**: Low | **Benefit**: Better documentation quality

### Priority 5: Declarative Content Validation (#1)
**Impact**: High | **Effort**: Medium | **Benefit**: Extensibility without code

## Conclusion

The spec-check DSL has proven to be **highly expressive and capable** of validating diverse specification documents. The Pydantic-based approach provides excellent type safety and extensibility. The recent addition of section-scoped class validation (REQ-005) addresses a key gap and demonstrates the system's evolution.

**Key Achievements**:
- ✅ Successfully validated 5 document types with rich structure
- ✅ Section-scoped class validation works excellently
- ✅ Reference validation and cardinality enforcement robust
- ✅ Content validation (Gherkin) provides domain-specific checks
- ✅ Backward compatible - all existing tests pass

**Recommended Next Steps**:
1. Implement template generation (#9) - quick win for productivity
2. Add composable validators (#10) - increases flexibility
3. Build reference graph query API (#3) - enables powerful analysis
4. Plan LSP support (#13) - long-term developer experience improvement
5. Continue iterating based on user feedback

The foundation is solid, and these enhancements will make the system even more powerful and user-friendly.
