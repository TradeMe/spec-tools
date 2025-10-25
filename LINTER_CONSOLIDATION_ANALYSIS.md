# Linter Consolidation Analysis

## Executive Summary

The project now has a robust Pydantic-based DSL for defining spec types (`spec_tools/dsl/`), but the existing linters were built before this infrastructure existed. This creates significant overlap, duplication, and opportunities for consolidation.

**Key Finding**: 4 out of 6 linters can be deprecated or significantly refactored to use the Pydantic validation infrastructure.

## Current Linters

| Linter | File | Status | Recommendation |
|--------|------|--------|----------------|
| **SpecLinter** | `linter.py` | ⚠️ Partially Redundant | Refactor: Only validate non-spec files |
| **UniqueSpecsLinter** | `unique_specs_linter.py` | ❌ Redundant | **DEPRECATE**: Integrate into Pydantic validation |
| **SpecCoverageLinter** | `spec_coverage_linter.py` | ✅ Keep | Refactor to use Pydantic patterns |
| **StructureLinter** | `structure_linter.py` | ❌ Redundant | **DEPRECATE**: Redundant with coverage |
| **MarkdownSchemaValidator** | `markdown_schema_validator.py` | ❌ Redundant | **DEPRECATE**: Use Pydantic validation |
| **MarkdownLinkValidator** | `markdown_link_validator.py` | ⚠️ Partially Redundant | Integrate with `reference_resolver.py` |

## Detailed Analysis

### 1. SpecLinter (Allowlist Validator)

**Current Behavior**:
- Uses `.specallowlist` file with gitignore-style patterns
- Validates ALL project files match allowlist patterns
- Includes: specs, Python code, configs, docs, etc.

**Problem**:
- Spec file patterns are now defined in Pydantic models (`file_pattern`, `location_pattern`)
- Having two sources of truth for spec file locations
- Allowlist mixes concerns (spec validation + project structure validation)

**Overlap with Pydantic**:
```python
# In .specallowlist:
*.md                          # Generic - too broad
specs/**/*.md                 # Overlaps with Pydantic

# In Pydantic (layers.py):
class JobModule(SpecModule):
    file_pattern: str = r"^JOB-\d{3}\.md$"      # More specific
    location_pattern: str = r"specs/jobs/"       # Structured hierarchy
```

**Recommendation**:
1. **Keep** allowlist for non-spec files (Python code, configs, etc.)
2. **Remove** spec file patterns from allowlist
3. **Add** validation that all markdown files in `specs/` match a Pydantic module type
4. Alternative: Create a "ProjectStructure" Pydantic model that defines the entire project layout

**Updated `.specallowlist`** would look like:
```
# Python package
spec_tools/**/*.py
tests/**/*.py

# Configuration
pyproject.toml
uv.lock
.specallowlist

# Note: spec files are validated by Pydantic types, not allowlist
```

### 2. UniqueSpecsLinter

**Current Behavior**:
- Extracts SPEC IDs using regex: `\*\*ID\*\*:\s*(SPEC-\d+)`
- Extracts requirement IDs using regex: `\*\*([A-Z]+-\d{3})\*\*:`
- Validates uniqueness globally
- Uses hardcoded directory exclusions: `future/`, `jobs/`, `principles.md`

**Problem**:
- Hardcoded patterns duplicate Pydantic `IdentifierSpec`
- No awareness of identifier scope (global vs module_instance vs section)
- Manual exclusion logic instead of using module types

**Pydantic Solution**:
```python
# In models.py:
class IdentifierSpec(BaseModel):
    pattern: str = "REQ-\\d{3}"              # Centralized pattern
    location: Literal["title", "heading", "metadata"]
    scope: Literal["global", "module_instance", "section"]  # Scope-aware!

# In id_registry.py:
class IDRegistry:
    """Tracks identifier occurrences with scope awareness."""
    # Already exists but not used by linters!
```

**Recommendation**:
- **DEPRECATE** `unique_specs_linter.py` entirely
- **Integrate** uniqueness checking into the DSL validation pipeline (`dsl/validator.py`)
- Use `id_registry.py` which already tracks IDs with proper scope
- Leverage `IdentifierSpec.scope` for proper uniqueness validation:
  - `global`: Unique across all documents
  - `module_instance`: Unique within a module file
  - `section`: Unique within a section

### 3. SpecCoverageLinter

**Current Behavior**:
- Hardcoded regex for requirements: `\*\*([A-Z]+-\d{3})\*\*:`
- Manual "provisional spec" detection: checks for `future/`, `jobs/`, `principles.md`
- Extracts pytest markers: `@pytest.mark.req("REQ-001")`

**Problem**:
- Hardcoded patterns should come from Pydantic
- Manual exclusions should use module type metadata

**Pydantic Solution**:
```python
# Instead of hardcoded regex:
REQ_PATTERN = re.compile(r"\*\*([A-Z]+-\d{3})\*\*:")

# Use Pydantic module registry:
registry = SpecTypeRegistry.load_from_package()
for spec_file in specs_dir.rglob("*.md"):
    module_type = registry.match_file(spec_file)
    if module_type:
        # Use module_type.identifier.pattern instead of hardcoded regex
        pattern = module_type.identifier.pattern
```

**Recommendation**:
- **Keep** coverage linter (it's still needed)
- **Refactor** to use Pydantic patterns instead of hardcoded regex
- **Use** module type metadata to determine which specs need tests
- **Add** a `requires_tests` field to `SpecModule` model:
  ```python
  class SpecModule(BaseModel):
      # ...
      requires_tests: bool = True  # False for JTBD, meta-docs, etc.
  ```

### 4. StructureLinter

**Current Behavior**:
- Checks that `specs/foo-bar.md` has `tests/test_foo_bar.py` or `tests/foo_bar/`
- Converts kebab-case to snake_case

**Problem**:
- This is really just checking if test files exist
- The coverage linter already checks if requirements are tested
- Overlapping concerns with coverage linter

**Recommendation**:
- **DEPRECATE** structure linter entirely
- Coverage linter is sufficient - if requirements are tested, structure is correct
- Alternative: Add structure checking as a feature of coverage linter (simple addition)

### 5. MarkdownSchemaValidator

**Current Behavior**:
- Validates heading structure and hierarchy
- Validates metadata fields (ID, Version, Date, Status)
- Validates EARS format in requirements sections
- Uses `.specschemaconfig` file

**Problem**:
- **Heading structure** is now defined in `SpecModule.sections`
- **Metadata** should be defined as `SectionSpec` entries
- **EARS format** should be a `ContentValidator` subclass
- Completely overlaps with Pydantic validation

**Pydantic Solution**:
```python
# Heading structure already defined:
class RequirementModule(SpecModule):
    sections: list[SectionSpec] = [
        SectionSpec(heading="Purpose", heading_level=2, required=True),
        SectionSpec(heading="Acceptance Criteria", heading_level=2, required=True),
    ]

# EARS validation should be:
class EARSValidator(ContentValidator):
    """Validates Easy Approach to Requirements Syntax."""

    def validate_content(self, section_content: list, file_path: Path) -> list[ValidationError]:
        # Check for WHEN/IF/WHERE patterns
        # Return validation errors
        pass

# Usage in module:
sections: list[SectionSpec] = [
    SectionSpec(
        heading="Requirements",
        content_validator=EARSValidator(),  # Type-safe!
    ),
]
```

**Recommendation**:
- **DEPRECATE** `markdown_schema_validator.py`
- **Implement** `EARSValidator` as a `ContentValidator` subclass
- **Use** Pydantic's `validate_structure()` method (already implemented)
- **Add** metadata section validation to Pydantic models

### 6. MarkdownLinkValidator

**Current Behavior**:
- Generic link validation (internal + external)
- Checks that internal links resolve
- Validates external URLs are accessible
- Uses `.speclinkconfig` for private URL patterns

**Problem**:
- The Pydantic models define **typed** references via `Reference` objects
- Generic link validation doesn't understand reference semantics
- The project already has `reference_resolver.py` that validates typed references

**Pydantic Solution**:
```python
# In layers.py:
references: list[Reference] = [
    Reference(
        name="addresses",
        source_type="Requirement",
        target_type="Job",
        cardinality=Cardinality(min=1, max=None),  # Type-aware!
        link_format="id_reference",
        must_exist=True,
    ),
]

# reference_resolver.py already validates:
# - Target existence
# - Type matching
# - Cardinality constraints
```

**Recommendation**:
- **Keep** basic link validation for non-spec markdown files (README.md, docs)
- **Integrate** spec reference validation with `reference_resolver.py`
- **Use** typed references for specs, generic link checking for docs

## Consolidation Plan

### Phase 1: Core Integration (High Priority)

#### 1.1 Integrate Identifier Uniqueness into Pydantic
**Files to modify**:
- `spec_tools/dsl/validator.py` - Add uniqueness checking pass
- `spec_tools/dsl/id_registry.py` - Enhance to support scope-based uniqueness

**Files to deprecate**:
- `spec_tools/unique_specs_linter.py` ✂️
- Remove from `spec_tools/cli.py` command: `check-unique-specs`

**Implementation**:
```python
# In validator.py:
def validate(self, root_path: Path) -> ValidationResult:
    # ... existing passes ...

    # Pass 8: Validate identifier uniqueness
    errors.extend(self._validate_identifier_uniqueness())

def _validate_identifier_uniqueness(self) -> list[ValidationError]:
    """Validate identifiers are unique according to their scope."""
    errors = []

    # Check global scope IDs
    global_ids = self.id_registry.get_by_scope("global")
    for id_value, occurrences in global_ids.items():
        if len(occurrences) > 1:
            errors.append(ValidationError(
                error_type="duplicate_identifier",
                message=f"ID '{id_value}' appears in multiple files",
                # ...
            ))

    return errors
```

#### 1.2 Create EARS Content Validator
**Files to create**:
- `spec_tools/dsl/content_validators/ears.py`

**Files to modify**:
- `spec_tools/dsl/layers.py` - Use `EARSValidator` in `RequirementModule`

**Files to deprecate**:
- Remove EARS validation from `spec_tools/markdown_schema_validator.py`

**Implementation**:
```python
# In content_validators/ears.py:
class EARSValidator(ContentValidator):
    """
    Validates Easy Approach to Requirements Syntax.

    EARS patterns:
    - WHEN [trigger], [system] shall [response]
    - IF [condition], THEN [system] shall [action]
    - WHERE [feature], [system] shall [behavior]
    - WHILE [state], [system] shall [behavior]
    - [System] shall [action]
    """

    EARS_KEYWORDS = ["WHEN", "IF", "WHERE", "WHILE", "shall"]

    def validate_content(
        self,
        section_content: list,
        file_path: Path
    ) -> list[ValidationError]:
        errors = []
        # Implementation of EARS validation
        return errors
```

#### 1.3 Deprecate Markdown Schema Validator
**Rationale**: Completely superseded by Pydantic `validate_structure()`

**Files to deprecate**:
- `spec_tools/markdown_schema_validator.py` ✂️
- Remove from `spec_tools/cli.py` command: `check-schema`

**Migration**: Users should use `validate-dsl` command instead

### Phase 2: Linter Refactoring (Medium Priority)

#### 2.1 Refactor Coverage Linter to Use Pydantic
**Files to modify**:
- `spec_tools/spec_coverage_linter.py`

**Changes**:
```python
class SpecCoverageLinter:
    def __init__(self, registry: SpecTypeRegistry, ...):
        self.registry = registry  # Add registry parameter
        # ...

    def is_spec_provisional(self, spec_file: Path) -> bool:
        """Use Pydantic module type instead of hardcoded paths."""
        module_type = self.registry.match_file(spec_file)
        if not module_type:
            return True  # Unknown type = provisional

        # Check if module type requires tests
        return not getattr(module_type, 'requires_tests', True)

    def extract_requirements_from_spec(self, spec_file: Path) -> set[str]:
        """Use Pydantic identifier pattern instead of hardcoded regex."""
        module_type = self.registry.match_file(spec_file)
        if not module_type or not module_type.identifier:
            return set()

        # Use module type's identifier pattern
        pattern = re.compile(module_type.identifier.pattern)
        # ... extract using pattern ...
```

#### 2.2 Deprecate Structure Linter
**Rationale**: Redundant with coverage linter

**Files to deprecate**:
- `spec_tools/structure_linter.py` ✂️
- Remove from `spec_tools/cli.py` command: `check-structure`

**Alternative**: Add optional structure checking to coverage linter

#### 2.3 Update Allowlist Approach
**Files to modify**:
- `.specallowlist` - Remove spec patterns, keep only non-spec files
- `spec_tools/linter.py` - Add documentation about Pydantic validation

**Enhanced validation**:
```python
class SpecLinter:
    def lint(self) -> LintResult:
        # ... existing allowlist validation ...

        # NEW: Validate all .md files in specs/ match a Pydantic type
        specs_dir = self.root_dir / "specs"
        if specs_dir.exists():
            for spec_file in specs_dir.rglob("*.md"):
                module_type = registry.match_file(spec_file)
                if not module_type:
                    errors.append(f"Spec file doesn't match any type: {spec_file}")
```

### Phase 3: Documentation & Cleanup (Low Priority)

#### 3.1 Update Specs to Match Pydantic Structure
- Ensure all spec files conform to their Pydantic module types
- Run `validate-dsl` and fix any violations

#### 3.2 Update README
- Document the Pydantic-based validation approach
- Remove references to deprecated linters
- Add migration guide for projects using old linters

#### 3.3 Create Spec Structure Documentation
**New file**: `docs/DEFINING_SPEC_TYPES.md`

**Contents**:
- How to create custom `SpecModule` types
- How to define `SpecClass` patterns
- How to implement `ContentValidator` subclasses
- How to define typed `Reference` relationships
- Examples from `layers.py`

## Migration Path for Users

### For This Project

1. Run all existing linters one last time to ensure compliance
2. Implement Phase 1 changes (core integration)
3. Update spec files to conform to Pydantic types
4. Implement Phase 2 changes (linter refactoring)
5. Remove deprecated linters
6. Update CI/CD to use new commands

### For Other Projects Using spec-tools

**Breaking Changes**:
- `check-unique-specs` command removed → use `validate-dsl`
- `check-schema` command removed → use `validate-dsl`
- `check-structure` command removed → use `check-coverage`

**Migration Steps**:
1. Define Pydantic module types for your specs (see `layers.py`)
2. Replace `check-schema` with `validate-dsl` in CI
3. Replace `check-unique-specs` with `validate-dsl` in CI
4. Update `.specallowlist` to only include non-spec files
5. Optionally: Implement custom `ContentValidator` for domain-specific syntax

## Benefits of Consolidation

### 1. Single Source of Truth
- Identifier patterns defined once in Pydantic models
- File patterns defined once in Pydantic models
- Section structure defined once in Pydantic models

### 2. Type Safety
- IDE autocomplete for spec definitions
- Compile-time checking of references
- Inheritance for spec type variants

### 3. Extensibility
- Users can define custom `SpecModule` types
- Users can implement custom `ContentValidator` logic
- Users can define typed `Reference` relationships

### 4. Reduced Maintenance
- Fewer linters to maintain
- Less code duplication
- Easier to add new spec types

### 5. Better Error Messages
- Pydantic provides detailed validation errors
- Suggestions based on spec type definitions
- Context-aware error reporting

## Next Steps

1. Review and approve this analysis
2. Prioritize which phases to implement first
3. Create implementation tasks for approved phases
4. Update project roadmap

## Questions for Discussion

1. Should we keep `check-structure` as a separate command or integrate into `check-coverage`?
2. Should allowlist validation remain file-based (`.specallowlist`) or move to Pydantic `ProjectStructure` model?
3. Should we maintain backwards compatibility with deprecated commands (show deprecation warnings)?
4. What's the migration timeline for removing deprecated linters?
