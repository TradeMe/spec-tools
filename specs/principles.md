# Specification Architecture Principles

**Date**: 2025-10-23
**Version**: 1.0

## Overview

This document explains the architectural layers of the spec-tools specification system, from high-level Jobs to be Done down to implementation code. Understanding this architecture enables effective use of specifications for requirements management, test planning, and traceability.

## Architectural Layers

The specification system consists of five interconnected layers, each serving a distinct purpose:

```
┌─────────────────────────────────────────────────────────────┐
│                     Layer 1: Jobs to be Done                │
│  High-level user capabilities and outcomes                  │
│  (What users need to accomplish and why)                    │
│  Example: SPEC-003/JOB-001 "Extract Requirements"           │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Groups related requirements
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Layer 2: Requirements (EARS)              │
│  Precise, testable specifications in EARS format            │
│  (Detailed "shall" statements defining behavior)            │
│  Example: SPEC-003/REQ-001 "System shall scan directory"    │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Traced to tests via markers
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Layer 3: Requirement Tests (pytest)            │
│  Test functions linked to requirements via @pytest.mark.req │
│  (Validates that requirements are correctly implemented)    │
│  Example: @pytest.mark.req("SPEC-003/REQ-001")              │
│           test_scans_specs_directory()                      │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Tests implementation
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                Layer 4: Unit Tests (pytest)                 │
│  Additional tests for implementation details                │
│  (Tests specific functions, edge cases, internals)          │
│  Example: test_parse_requirement_id_with_invalid_format()   │
└─────────────────────────────────────────────────────────────┘
                            │
                            │ Tests implementation
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Layer 5: Implementation Code              │
│  Python modules implementing the requirements               │
│  (Actual functionality that fulfills specifications)        │
│  Example: spec_coverage_linter.py                           │
└─────────────────────────────────────────────────────────────┘
```

## Layer Details

### Layer 1: Jobs to be Done (JTBD)

**Purpose:** Provide high-level abstraction over requirements that explains what users need to accomplish and why it matters.

**Location:** `specs/jobs/*.md`

**Format:**
```markdown
### SPEC-XXX/JOB-YYY: [Job Name]

**Description:** [What users need to accomplish]

**Why It Matters:** [Business value and user impact]

**Related Requirements:** Links to all requirements that support this job

**Success Criteria:** High-level outcomes that indicate job completion
```

**Key Characteristics:**
- **User-focused:** Describes capabilities from user perspective
- **Outcome-oriented:** Focuses on what gets accomplished, not how
- **Groups requirements:** One job typically relates to 3-10 requirements
- **Provides context:** Explains "why" behind the "what"
- **Not 1:1 with specs:** Jobs organize requirements thematically, not by file structure

**Example:**
- **SPEC-003/JOB-001:** Extract Requirements from Specification Files
  - Related to: REQ-001, REQ-002, REQ-003, REQ-041, REQ-042
  - Accomplishes: Automatic discovery and extraction of all requirements with unique IDs

### Layer 2: Requirements (EARS Format)

**Purpose:** Define precise, testable, unambiguous specifications using Easy Approach to Requirements Syntax.

**Location:** `specs/*.md` (main specification files)

**Format:**
```markdown
**REQ-XXX** [Related to [SPEC-XXX/JOB-YYY](...)]: [EARS formatted requirement]
```

**EARS Patterns:**
- **Unconditional:** `[Subject] shall [action]`
- **Event-driven:** `WHEN [condition], [subject] shall [action]`
- **Conditional:** `IF [condition], THEN [subject] shall [action]`
- **Optional:** `WHERE [condition], [subject] shall [action]`
- **State-driven:** `WHILE [condition], [subject] shall [action]`

**Key Characteristics:**
- **Testable:** Each requirement can be validated through tests
- **Atomic:** Each requirement specifies one clear behavior
- **Unambiguous:** EARS format eliminates interpretation ambiguity
- **Traceable:** Fully qualified IDs (SPEC-XXX/REQ-XXX) ensure uniqueness
- **Linked to jobs:** Each requirement relates to one or more jobs

**Example:**
```markdown
**REQ-001** [Related to [SPEC-003/JOB-001](...)]: The system shall scan the
specs directory to find all markdown files containing requirement definitions.
```

### Layer 3: Requirement Tests

**Purpose:** Validate that requirements are correctly implemented in code.

**Location:** `tests/*.py`

**Format:**
```python
@pytest.mark.req("SPEC-XXX/REQ-YYY")
def test_descriptive_name():
    """Test that validates the requirement."""
    # Test implementation
```

**Key Characteristics:**
- **Requirement-linked:** Uses `@pytest.mark.req()` decorator with fully qualified IDs
- **Validates specifications:** Tests "what" the requirement says should happen
- **Traceable:** Coverage linter ensures all requirements have tests
- **May cover multiple requirements:** One test can validate multiple related requirements

**Example:**
```python
@pytest.mark.req("SPEC-003/REQ-001")
def test_scans_specs_directory():
    """Test that system finds all markdown files in specs directory."""
    # Test implementation validates REQ-001
```

### Layer 4: Unit Tests

**Purpose:** Test implementation details, edge cases, and internal functions beyond requirement specifications.

**Location:** `tests/*.py`

**Format:**
```python
def test_specific_implementation_detail():
    """Test internal function or edge case."""
    # Test implementation
```

**Key Characteristics:**
- **No requirement markers:** These tests don't directly trace to requirements
- **Implementation-focused:** Tests "how" the code works internally
- **Complementary:** Provides additional coverage beyond requirement tests
- **Allowed without specs:** Not all tests need requirement links

**Example:**
```python
def test_parse_requirement_id_handles_malformed_input():
    """Test that parser gracefully handles invalid input."""
    # Tests implementation detail not specified in requirements
```

### Layer 5: Implementation Code

**Purpose:** The actual Python code that fulfills the requirements.

**Location:** `spec_check/*.py`

**Key Characteristics:**
- **Implements requirements:** Code behavior must satisfy all requirements
- **Tested at multiple levels:** Covered by both requirement tests and unit tests
- **Traceable:** Requirements → Tests → Code provides full traceability

**Example:**
```python
def scan_specs_directory(root_dir: Path) -> list[Path]:
    """Scan specs directory for markdown files.

    Implements: SPEC-003/REQ-001
    """
    # Implementation code
```

## Relationships Between Layers

### JTBD → Requirements (1:Many)

- **One job** groups **multiple related requirements**
- Jobs provide thematic organization across requirement sets
- Requirements link back to their parent job(s) for context

**Example:**
```
SPEC-003/JOB-001: Extract Requirements
├── SPEC-003/REQ-001: Scan directory
├── SPEC-003/REQ-002: Extract IDs
├── SPEC-003/REQ-003: Support custom prefixes
├── SPEC-003/REQ-041: Extract spec IDs
└── SPEC-003/REQ-042: Form qualified IDs
```

### Requirements → Requirement Tests (1:Many)

- **One requirement** may have **multiple tests** covering different scenarios
- **One test** may validate **multiple related requirements**
- Tests link to requirements via `@pytest.mark.req("SPEC-XXX/REQ-YYY")`
- Coverage linter validates this traceability

**Example:**
```
SPEC-003/REQ-007: Extract markers
├── test_extracts_single_marker()
├── test_extracts_multiple_markers()
└── test_extracts_markers_from_class_methods()
```

### Requirements → Implementation (Many:Many)

- **Multiple requirements** may be implemented by **one function**
- **One requirement** may require **multiple functions** to implement
- Comments in code can reference requirement IDs for clarity

**Example:**
```python
# Implements: SPEC-003/REQ-001, SPEC-003/REQ-041, SPEC-003/REQ-042
def extract_requirements_from_specs(specs_dir: Path) -> dict[str, Requirement]:
    """Extract all requirements with fully qualified IDs."""
    # Implementation satisfies multiple related requirements
```

### Unit Tests → Implementation (Many:1)

- **Multiple unit tests** validate **one function** thoroughly
- Unit tests complement requirement tests with implementation details
- Not directly linked to requirements (no pytest markers)

## File Organization

```
spec-tools/
├── specs/
│   ├── jobs/                              # Layer 1: Jobs to be Done
│   │   ├── markdown-link-validator.md     # SPEC-001 jobs
│   │   ├── markdown-schema-validator.md   # SPEC-002 jobs
│   │   └── spec-coverage-linter.md        # SPEC-003 jobs
│   │
│   ├── markdown-link-validator.md         # Layer 2: SPEC-001 requirements
│   ├── markdown-schema-validator.md       # Layer 2: SPEC-002 requirements
│   └── spec-coverage-linter.md            # Layer 2: SPEC-003 requirements
│
├── tests/                                  # Layers 3 & 4: Tests
│   ├── test_markdown_link_validator.py    # Requirement + unit tests
│   ├── test_markdown_schema_validator.py  # Requirement + unit tests
│   └── test_spec_coverage_linter.py       # Requirement + unit tests
│
└── spec_check/                             # Layer 5: Implementation
    ├── markdown_link_validator.py
    ├── markdown_schema_validator.py
    └── spec_coverage_linter.py
```

## Traceability Flow

### Downward Traceability (User Need → Implementation)

```
User Need
  ↓
Jobs to be Done (What users accomplish)
  ↓
Requirements (Precise specifications)
  ↓
Requirement Tests (Validate specifications)
  ↓
Implementation (Code that fulfills requirements)
```

### Upward Traceability (Code → Business Value)

```
Implementation Code
  ↓
Unit Tests (Validates implementation details)
  ↓
Requirement Tests (Validates specifications)
  ↓
Requirements (Testable behaviors)
  ↓
Jobs to be Done (User value and business outcomes)
```

## Bidirectional Linking

### Jobs ↔ Requirements

**In Job Files (`specs/jobs/*.md`):**
```markdown
**Related Requirements:**
- [SPEC-003/REQ-001](../spec-coverage-linter.md#req-001)
- [SPEC-003/REQ-002](../spec-coverage-linter.md#req-002)
```

**In Specification Files (`specs/*.md`):**
```markdown
**REQ-001** [Related to [SPEC-003/JOB-001](jobs/spec-coverage-linter.md#spec-003job-001)]:
The system shall scan the specs directory...
```

### Requirements ↔ Tests

**In Specification Files:**
- Requirements documented with fully qualified IDs (SPEC-XXX/REQ-XXX)

**In Test Files:**
```python
@pytest.mark.req("SPEC-003/REQ-001")  # Links test to requirement
def test_scans_specs_directory():
    """Test description."""
```

**Validation:**
- Coverage linter ensures all requirements have tests
- Coverage linter validates all test markers reference real requirements

## Benefits of This Architecture

### 1. Multiple Abstraction Levels

- **Executives/Product:** Focus on Jobs to be Done (user value)
- **Requirements Engineers:** Focus on Requirements (detailed specifications)
- **Developers:** Focus on Tests and Implementation (technical details)

### 2. Complete Traceability

- Track from business value (JTBD) → requirements → tests → code
- Understand impact of code changes on requirements and business value
- Verify all requirements are tested and implemented

### 3. Maintainability

- Jobs remain stable even as requirements evolve
- Requirements provide detailed specifications without losing big picture
- Bidirectional links keep documentation synchronized

### 4. Quality Assurance

- Coverage linter ensures no untested requirements
- Schema validator ensures consistent documentation format
- Structure linter ensures proper organization

### 5. Gradual Adoption

- Start with requirements, add jobs later for organization
- Configure coverage thresholds to allow gradual improvement
- Unit tests allowed without requirement links

## Validation Tools

### check-schema
Validates that specification and job files follow correct markdown schema:
- Required metadata (ID, Version, Date, Status)
- Required heading structure
- EARS format compliance for requirements

### check-coverage
Validates traceability between requirements and tests:
- All requirements have test coverage
- All test markers reference valid requirements
- Coverage percentage meets configured threshold

### check-unique-specs
Ensures uniqueness of identifiers:
- All SPEC IDs are unique
- All JOB IDs are unique within their spec
- All REQ IDs are unique within their spec

### check-structure
Validates file organization:
- Test files/directories match spec file names
- Jobs files match their corresponding spec files

## Working with the System

### Creating a New Specification

1. **Define Jobs to be Done** (`specs/jobs/feature-name.md`)
   - Identify 3-7 high-level user capabilities
   - Explain why each job matters
   - Define success criteria

2. **Write Requirements** (`specs/feature-name.md`)
   - Create detailed EARS format requirements
   - Link each requirement to relevant job(s)
   - Use fully qualified IDs (SPEC-XXX/REQ-YYY)

3. **Implement Requirement Tests** (`tests/test_feature_name.py`)
   - Write tests with `@pytest.mark.req()` markers
   - Validate each requirement's behavior
   - Aim for complete requirement coverage

4. **Add Unit Tests** (`tests/test_feature_name.py`)
   - Test implementation details
   - Cover edge cases
   - No requirement markers needed

5. **Implement Code** (`spec_check/feature_name.py`)
   - Fulfill all requirements
   - Pass all tests
   - Optional: Comment with requirement IDs

### Modifying Existing Specifications

1. **Assess impact:** Check job description - does high-level capability change?
2. **Update requirements:** Modify or add EARS requirements
3. **Update tests:** Add/modify tests with requirement markers
4. **Update implementation:** Modify code to satisfy new requirements
5. **Run linters:** Verify coverage, schema, and structure compliance

## Questions and Examples

### Q: When should I create a new job vs. a new requirement?

**Create a new job when:**
- You're adding a fundamentally new user capability
- The change represents a different outcome users want to achieve

**Create a new requirement when:**
- You're adding detail to how an existing capability works
- You're specifying additional constraints or behaviors

**Example:**
- New job: "Validate External URLs" (new capability)
- New requirement: "Support 30-second timeout for URL validation" (detail)

### Q: Can one requirement relate to multiple jobs?

**Yes!** Some requirements support multiple related jobs.

**Example:**
```markdown
**REQ-043** [Related to SPEC-003/JOB-001, SPEC-003/JOB-003]:
WHEN a test references a requirement marker, the system shall validate
that the spec ID exists.
```

This requirement supports both "Extract Requirements" and "Analyze Coverage" jobs.

### Q: Do all tests need requirement markers?

**No.** Unit tests that validate implementation details don't need markers. Only tests that directly validate requirement specifications need `@pytest.mark.req()`.

**Example:**
```python
# Needs marker - validates requirement
@pytest.mark.req("SPEC-003/REQ-002")
def test_extracts_requirement_ids():
    """Test requirement extraction."""

# No marker needed - tests implementation detail
def test_handles_malformed_requirement_id():
    """Test parser error handling."""
```

### Q: How do I find what jobs exist?

Check `specs/jobs/*.md` files. Each specification has a corresponding jobs file that lists all high-level capabilities.

### Q: What if coverage is below 100%?

Configure `min_coverage` in `pyproject.toml`:

```toml
[tool.spec-tools.check-coverage]
min_coverage = 85.0  # Allow gradual improvement
```

Aim to increase coverage over time toward 100%.

## Summary

The five-layer architecture provides:

1. **Jobs to be Done** - User-focused capabilities and business value
2. **Requirements** - Precise, testable EARS specifications
3. **Requirement Tests** - Validation of specifications via pytest markers
4. **Unit Tests** - Additional coverage of implementation details
5. **Implementation** - Code that fulfills all requirements

Together, these layers ensure complete traceability from business value through implementation, enabling quality assurance, impact analysis, and maintainable specifications.
