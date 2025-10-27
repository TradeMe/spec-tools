# SPEC-005: Pydantic-Based Type Definitions

**Status**: Draft
**Created**: 2025-10-25
**Author**: Claude
**Supersedes**: SPEC-004 (YAML-based DSL)

## Overview

This specification defines a Pydantic-based type definition system for markdown specifications, replacing the YAML-based approach with Python code that provides better type safety, IDE support, and composability.

## Motivation

The YAML-based type definition system (SPEC-004) has several limitations:

- **Limited Expressiveness**: Complex validation logic is awkward to express in YAML
- **No Type Safety**: YAML schemas themselves are not type-checked
- **Poor IDE Support**: No autocomplete, go-to-definition, or refactoring tools
- **Limited Composability**: YAML lacks inheritance and code reuse mechanisms
- **Runtime-Only Validation**: Errors in type definitions only discovered when validating specs

Using Pydantic models as the type definition language addresses all these issues while leveraging the proven Python-as-DSL pattern used by SQLAlchemy, Django ORM, and FastAPI.

## Requirements

### SPEC-005/REQ-001: Pydantic Base Models

The system shall provide Pydantic base models for defining specification types:

- `SpecModule` - File-level specification types (Requirements, Contracts, ADRs)
- `SpecClass` - Section-level reusable components (Acceptance Criteria, Risks)
- `Reference` - Typed relationships between modules with cardinality
- `ContentValidator` - Base for content validation (Gherkin, RFC-2119, etc.)
- `IdentifierSpec` - Identifier format and uniqueness rules
- `SectionSpec` - Section structure and content requirements

### SPEC-005/REQ-002: Type Safety

The system shall validate type definitions at load time using Pydantic's validation system. Invalid type definitions shall raise clear errors before any specifications are validated.

### SPEC-005/REQ-003: Inheritance and Composition

The system shall support:

- Class inheritance for extending module types
- Mixin classes for cross-cutting concerns
- Field reuse through composition
- Method overrides for custom validation logic

### SPEC-005/REQ-004: Python Module Loading

The system shall load type definitions from Python modules using standard Python import mechanisms. Type definition directories shall be valid Python packages with `__init__.py` files.

### SPEC-005/REQ-005: Validation Pass Integration

The system shall integrate with the 7-pass validation architecture:

- Pass 1-2: AST construction and section tree building (unchanged)
- Pass 3: Type assignment using `SpecModule.matches_file()`
- Pass 4: Structural validation using `SpecModule.validate_structure()`
- Pass 5: Content validation using `ContentValidator` instances
- Pass 6: Reference extraction using `Reference` definitions
- Pass 7: Reference resolution and cardinality validation

### SPEC-005/REQ-006: Backward Compatibility

The system shall maintain the same CLI interface and validation output format. Users should be able to switch from YAML to Pydantic definitions without changing their workflows.

### SPEC-005/REQ-007: Example Type Definitions

The system shall provide example type definitions for common specification types:

- `RequirementModule` - Technical requirements with acceptance criteria
- `ContractModule` - Business contracts with terms and parties
- `ArchitectureDecisionModule` - ADRs with context and consequences

## Design

### Core Type Hierarchy

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Literal, Callable
from pathlib import Path

class Cardinality(BaseModel):
    """Represents cardinality constraints (0..1, 1, 0..*, 1..*, n..m)"""
    min: int = 0
    max: Optional[int] = None  # None means unbounded

class IdentifierSpec(BaseModel):
    """Defines identifier format and location"""
    pattern: str  # Regex pattern
    location: Literal["title", "heading", "metadata"] = "title"
    scope: Literal["global", "module_instance", "section"] = "global"

class ContentValidator(BaseModel):
    """Base class for content validation"""
    def validate_content(
        self, section_content: List[ASTNode]
    ) -> List[ValidationError]:
        raise NotImplementedError

class SectionSpec(BaseModel):
    """Defines a section in a module"""
    heading: str
    heading_level: int
    required: bool = False
    content_validator: Optional[ContentValidator] = None

class Reference(BaseModel):
    """Defines a typed reference relationship"""
    name: str
    source_type: str
    target_type: str
    cardinality: Cardinality = Cardinality()
    allowed_sections: Optional[List[str]] = None
    must_exist: bool = True

class SpecClass(BaseModel):
    """Defines a reusable section-level component"""
    heading_pattern: str
    heading_level: int
    identifier: Optional[IdentifierSpec] = None
    content_validator: Optional[ContentValidator] = None

class SpecModule(BaseModel):
    """Defines a file-level specification type"""
    name: str
    version: str = "1.0"
    description: str

    file_pattern: str  # Regex for filename
    location_pattern: str  # Regex for directory path

    identifier: Optional[IdentifierSpec] = None
    sections: List[SectionSpec] = []
    references: List[Reference] = []
    classes: dict[str, SpecClass] = {}

    def matches_file(self, file_path: Path) -> bool:
        """Check if this module type applies to a file"""
        # Implementation
        pass

    def validate_structure(
        self, doc: ParsedDocument
    ) -> List[ValidationError]:
        """Validate document structure (Pass 4)"""
        # Implementation
        pass
```

### Type Registry

```python
class SpecTypeRegistry:
    """Central registry of specification types"""

    def __init__(self):
        self._modules: dict[str, SpecModule] = {}
        self._classes: dict[str, SpecClass] = {}

    def register_module(self, module: SpecModule) -> None:
        """Register a module type (validates at registration)"""
        self._modules[module.name] = module

    def get_module_for_file(self, file_path: Path) -> Optional[SpecModule]:
        """Find module type for a file"""
        for module in self._modules.values():
            if module.matches_file(file_path):
                return module
        return None

    @classmethod
    def load_from_package(cls, package_path: Path) -> "SpecTypeRegistry":
        """Load all type definitions from a Python package"""
        # Implementation discovers and imports all SpecModule instances
        pass
```

### Example: Requirement Module

```python
class AcceptanceCriterion(SpecClass):
    """A Gherkin-style acceptance criterion"""
    heading_pattern: str = r"^###\s+AC-\d+:\s+.+"
    heading_level: int = 3
    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"AC-\d+",
        location="heading",
        scope="module_instance"
    )
    content_validator: ContentValidator = GherkinValidator()

class RequirementModule(SpecModule):
    """Technical requirement specification"""
    name: str = "Requirement"
    description: str = "Technical requirement with acceptance criteria"

    file_pattern: str = r"^REQ-\d{3}\.md$"
    location_pattern: str = r"requirements/"

    identifier: IdentifierSpec = IdentifierSpec(
        pattern=r"REQ-\d{3}",
        location="title",
        scope="global"
    )

    sections: List[SectionSpec] = [
        SectionSpec(heading="Overview", heading_level=2, required=True),
        SectionSpec(heading="Acceptance Criteria", heading_level=2, required=True),
    ]

    references: List[Reference] = [
        Reference(
            name="implements",
            source_type="Requirement",
            target_type="Contract",
            cardinality=Cardinality(min=1, max=1),
        )
    ]

    classes: dict[str, SpecClass] = {
        "AcceptanceCriterion": AcceptanceCriterion()
    }
```

## Migration Path

### Phase 1: Implement Pydantic Models (This Spec)

1. Create Pydantic base models in `spec_check/dsl/models.py`
2. Create type registry in `spec_check/dsl/registry.py`
3. Update type loader to import Python modules
4. Update validator to use Pydantic models

### Phase 2: Update Test Fixtures

1. Convert test fixture YAML files to Python modules
2. Update integration tests to use Python imports
3. Verify all tests pass

### Phase 3: Documentation and Examples

1. Create example type definitions for common use cases
2. Update CLI documentation
3. Create migration guide for YAML users

## Non-Requirements

- **YAML Support**: This spec explicitly replaces YAML. No backward compatibility needed.
- **Dynamic Loading**: Type definitions are Python code, imported at startup, not runtime.
- **Serialization**: Type definitions don't need to serialize to JSON/YAML.

## Test Requirements

### SPEC-005/TEST-001: Type Definition Validation

Type definitions with invalid fields shall raise Pydantic ValidationError at load time.

### SPEC-005/TEST-002: Inheritance

Subclasses of SpecModule shall inherit and override parent fields correctly.

### SPEC-005/TEST-003: Registry Loading

Registry shall discover and load all SpecModule instances from a Python package.

### SPEC-005/TEST-004: File Matching

`SpecModule.matches_file()` shall correctly match files based on file_pattern and location_pattern.

### SPEC-005/TEST-005: Integration

End-to-end validation using Pydantic type definitions shall match previous YAML-based behavior.

## References

- SPEC-004: Specification DSL (superseded by this spec)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [SQLAlchemy ORM](https://docs.sqlalchemy.org/) - Similar Python-as-DSL pattern
- [FastAPI](https://fastapi.tiangolo.com/) - Uses Pydantic for API definitions
