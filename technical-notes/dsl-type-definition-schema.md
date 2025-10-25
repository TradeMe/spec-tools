# Type Definition Schema Design

**Date**: 2025-10-25
**Status**: Implementation
**Related Spec**: SPEC-004

## Overview

This document defines the YAML schema for DSL type definitions, incorporating ID-based reference resolution where links are treated as typed references to module and class instances.

## Core Concepts

### Reference Semantics

The DSL treats markdown links as typed references to identified entities:

1. **Module Instance Reference**: Link to a document by its module ID
   - Syntax: `[text](MODULE-ID)` or `[text](MODULE-ID.md)`
   - Resolution: Find document with ID `MODULE-ID`
   - Type checking: Verify target is expected module type

2. **Class Instance Reference**: Link to a section by its class ID
   - Syntax: `[text](#CLASS-ID)` or `[text](MODULE-ID#CLASS-ID)`
   - Resolution: Find section with ID `CLASS-ID` in specified or current document
   - Type checking: Verify target is expected class type

3. **External Reference**: Link to external resource
   - Syntax: `[text](http://...)` or `[text](https://...)`
   - No resolution: Tracked but not validated against type system

### ID-Based Linking Benefits

- **Location independence**: Documents can move without breaking references
- **Type safety**: Links are validated against type definitions
- **Semantic clarity**: Link type conveys relationship meaning
- **Refactoring support**: IDs are stable, paths are not

## YAML Schema Structure

### Module Type Definition

A module defines a document class (e.g., Requirement, Contract, ADR).

```yaml
# Type definition file: .spec-types/requirement.yaml
module:
  # Module metadata
  name: Requirement
  version: "1.0"
  description: "Technical requirement specification"

  # File pattern matching
  file_pattern: "^REQ-\\d{3}\\.md$"
  location_pattern: "^specs/requirements/"

  # Module identifier
  identifier:
    pattern: "^REQ-\\d{3}$"
    location: title  # or: frontmatter, first_heading
    scope: global    # or: directory, module_type
    format: "REQ-{number:03d}"

  # Frontmatter (optional)
  frontmatter:
    optional: true
    allowed_keys:
      - id
      - version
      - status
      - created
      - updated
    required_keys: []
    validation:
      status:
        type: enum
        values: [draft, review, approved, deprecated]
      version:
        type: string
        pattern: "^\\d+\\.\\d+$"

  # Section structure
  sections:
    - heading: "Overview"
      level: 2
      required: true
      content_type: text

    - heading: "Requirements"
      level: 2
      required: true
      content_type: ears_requirements
      subsections:
        - class: FunctionalRequirement
          cardinality: "1..*"

    - heading: "Acceptance Criteria"
      level: 2
      required: true
      subsections:
        - class: AcceptanceCriterion
          cardinality: "1..*"

    - heading: "Test Coverage"
      level: 2
      required: false
      content_type: test_references

  # References to other modules (by ID)
  references:
    - name: implements
      target_module: Contract
      cardinality: "1"
      link_format: id_reference  # Links use module IDs
      required: true

    - name: depends_on
      target_module: Requirement
      cardinality: "0..*"
      link_format: id_reference
      allow_circular: false

    - name: validated_by
      target_class: TestCase
      cardinality: "1..*"
      link_format: class_reference

  # Inline class definitions (private to this module)
  classes:
    FunctionalRequirement:
      heading_pattern: "^REQ-\\d{3}/FR-\\d{2}:"
      level: 3
      identifier:
        pattern: "^REQ-\\d{3}/FR-\\d{2}$"
        location: heading
        scope: module_instance  # Unique within this document
      fields:
        - name: description
          type: ears_statement
          required: true
        - name: rationale
          type: text
          required: false

    AcceptanceCriterion:
      heading_pattern: "^AC-\\d{2}:"
      level: 3
      identifier:
        pattern: "^AC-\\d{2}$"
        location: heading
        scope: section  # Unique within parent section
      content_type: gherkin
      fields:
        - name: given
          type: text
          required: true
        - name: when
          type: text
          required: true
        - name: then
          type: text
          required: true
```

### Shared Class Definition

Classes can be defined in separate files for reuse across modules.

```yaml
# Type definition file: .spec-types/classes/test-case.yaml
class:
  name: TestCase
  description: "Executable test case specification"
  usable_in: [Requirement, TestSuite, ADR]

  # Class identifier
  identifier:
    pattern: "^TC-\\d{3}$"
    location: heading
    scope: global

  # Structure
  heading_pattern: "^TC-\\d{3}:"
  level: [3, 4]  # Can be level 3 or 4

  # Content
  sections:
    - heading: "Setup"
      level: +1  # One level deeper than class heading
      required: true
      content_type: text

    - heading: "Execution"
      level: +1
      required: true
      content_type: text

    - heading: "Verification"
      level: +1
      required: true
      content_type: text

    - heading: "Teardown"
      level: +1
      required: false
      content_type: text

  # References from this class
  references:
    - name: tests
      target_module: Requirement
      cardinality: "1"
      link_format: id_reference
```

### Reference Type Definitions

References define typed relationships with validation rules.

```yaml
# In module or class definition
references:
  - name: implements           # Relationship name
    type: module_reference     # or: class_reference, external_reference
    target_module: Contract    # Expected target module type
    cardinality: "1"           # 1, 0..1, 1..*, 0..*, n..m
    required: true             # Must have this reference
    link_format: id_reference  # Link uses ID, not file path

    # Link validation
    link_pattern: "^CONTRACT-[A-Z]{3}-\\d{4}$"

    # Location constraints
    allowed_sections:          # Where this reference can appear
      - "Overview"
      - "Requirements"

    # Directionality
    bidirectional: false       # One-way reference only

    # Validation
    must_exist: true           # Target must exist
    allow_circular: false      # No circular dependencies

  - name: validated_by
    type: class_reference
    target_class: TestCase
    target_module: TestSuite   # Optional: constrain which modules
    cardinality: "1..*"
    link_format: class_reference

  - name: see_also
    type: external_reference
    cardinality: "0..*"
    required: false
```

### Content Type Validators

Content validators define how to parse and validate section content.

```yaml
# In .spec-types/content-validators/gherkin.yaml
content_validator:
  name: gherkin
  description: "Gherkin Given/When/Then format"

  # Expression grammar
  grammar:
    type: structured
    components:
      - name: given
        pattern: "^Given (.+)$"
        required: true
        multiline: false

      - name: when
        pattern: "^When (.+)$"
        required: true
        multiline: false

      - name: then
        pattern: "^Then (.+)$"
        required: true
        multiline: false

      - name: and
        pattern: "^And (.+)$"
        required: false
        multiline: false

  # Validation rules
  rules:
    - name: must_have_all_clauses
      check: all_required_present
      message: "Gherkin format requires Given, When, and Then clauses"

    - name: clauses_must_be_ordered
      check: ordered
      order: [given, when, then]
      message: "Clauses must appear in order: Given, When, Then"

# EARS validator
content_validator:
  name: ears
  description: "EARS (Easy Approach to Requirements Syntax)"

  grammar:
    type: pattern_match
    patterns:
      unconditional:
        pattern: "^The system shall (.+)$"

      event_driven:
        pattern: "^WHEN (.+), the system shall (.+)$"
        captures:
          - name: trigger
            index: 1
          - name: response
            index: 2

      state_driven:
        pattern: "^WHILE (.+), the system shall (.+)$"
        captures:
          - name: state
            index: 1
          - name: behavior
            index: 2

      optional:
        pattern: "^WHERE (.+), the system shall (.+)$"
        captures:
          - name: condition
            index: 1
          - name: behavior
            index: 2

  rules:
    - name: must_match_pattern
      check: matches_one_pattern
      message: "Must follow EARS format (unconditional, WHEN, WHILE, or WHERE)"
```

### Type Definition Directory Structure

```
.spec-types/
├── modules/
│   ├── requirement.yaml
│   ├── contract.yaml
│   ├── adr.yaml
│   └── test-suite.yaml
│
├── classes/
│   ├── test-case.yaml
│   ├── risk-assessment.yaml
│   └── acceptance-criterion.yaml
│
├── content-validators/
│   ├── gherkin.yaml
│   ├── ears.yaml
│   ├── table.yaml
│   └── identifier.yaml
│
└── config.yaml  # Global configuration
```

### Global Configuration

```yaml
# .spec-types/config.yaml
dsl_version: "1.0"

# Markdown flavor
markdown_flavor: github  # or: gitlab

# Allowed features
allowed_features:
  task_lists: true
  tables: true
  strikethrough: true
  math: false
  auto_linking: true

# ID resolution
id_resolution:
  # How to resolve module IDs to files
  module_id_to_file:
    strategy: pattern_match  # or: frontmatter, index_file
    pattern: "{id}.md"
    case_sensitive: false

  # How to resolve class IDs to sections
  class_id_to_section:
    strategy: heading_search
    search_scope: document  # or: current_section, global

# Reference link formats
link_formats:
  id_reference:
    # Link by ID: [text](REQ-001)
    pattern: "^[A-Z]+-\\d+$"
    resolution: id_lookup

  class_reference:
    # Link to section: [text](#TC-001) or [text](REQ-001#TC-001)
    pattern: "^(#|[A-Z]+-\\d+#)[A-Z]+-\\d+$"
    resolution: class_lookup

  external_reference:
    pattern: "^https?://"
    resolution: none

# Validation settings
validation:
  max_errors: 100
  fail_on_warning: false

  severity_levels:
    missing_required_section: error
    missing_optional_section: warning
    deprecated_pattern: warning
    style_violation: info

# Error reporting
error_reporting:
  format: human  # or: json, sarif, github_actions
  show_context: true
  context_lines: 3
  color: true
```

## ID Registry System

### Document ID Registry

During Pass 3 (Type Assignment), build a registry mapping IDs to documents:

```python
# Conceptual structure
id_registry = {
    'modules': {
        'SPEC-001': {
            'file_path': 'specs/requirements/user-auth.md',
            'module_type': 'Requirement',
            'line': 1,  # Where ID appears
        },
        'SPEC-002': {
            'file_path': 'specs/requirements/data-validation.md',
            'module_type': 'Requirement',
            'line': 1,
        },
        'CONTRACT-AUTH-0042': {
            'file_path': 'contracts/auth/oauth-implementation.md',
            'module_type': 'Contract',
            'line': 3,  # In frontmatter
        }
    },
    'classes': {
        'TC-001': {
            'file_path': 'specs/test-suites/auth-tests.md',
            'module_id': 'TESTSUITE-001',
            'section_path': ['Test Cases', 'TC-001: Login Success'],
            'class_type': 'TestCase',
            'line': 42,
        },
        'AC-01': {
            'file_path': 'specs/requirements/user-auth.md',
            'module_id': 'SPEC-001',
            'section_path': ['Acceptance Criteria', 'AC-01: Valid Credentials'],
            'class_type': 'AcceptanceCriterion',
            'line': 87,
        }
    }
}
```

### Reference Extraction

During Pass 6, extract references and classify them:

```python
# Link: [Auth spec](SPEC-002)
reference = {
    'source_file': 'specs/requirements/user-auth.md',
    'source_module_id': 'SPEC-001',
    'source_line': 15,
    'link_text': 'Auth spec',
    'link_target': 'SPEC-002',
    'reference_type': 'module_reference',
    'relationship': 'depends_on',  # Inferred from context or type def
}

# Link: [Test case](#TC-001)
reference = {
    'source_file': 'specs/requirements/user-auth.md',
    'source_module_id': 'SPEC-001',
    'source_line': 95,
    'link_text': 'Test case',
    'link_target': '#TC-001',
    'reference_type': 'class_reference',
    'relationship': 'validated_by',
}

# Link: [OAuth 2.0](https://oauth.net/2/)
reference = {
    'source_file': 'specs/requirements/user-auth.md',
    'source_module_id': 'SPEC-001',
    'source_line': 22,
    'link_text': 'OAuth 2.0',
    'link_target': 'https://oauth.net/2/',
    'reference_type': 'external_reference',
    'relationship': 'see_also',
}
```

### Reference Resolution

During Pass 7, resolve references against the ID registry:

```python
# For module reference SPEC-002
resolution = {
    'target_id': 'SPEC-002',
    'target_file': 'specs/requirements/data-validation.md',
    'target_module_type': 'Requirement',
    'exists': True,
    'type_matches': True,  # Expected Requirement, found Requirement
}

# For class reference TC-001
resolution = {
    'target_id': 'TC-001',
    'target_file': 'specs/test-suites/auth-tests.md',
    'target_module_id': 'TESTSUITE-001',
    'target_section': ['Test Cases', 'TC-001: Login Success'],
    'target_class_type': 'TestCase',
    'exists': True,
    'type_matches': True,
}

# Validation errors
errors = [
    {
        'type': 'broken_reference',
        'source': 'specs/requirements/user-auth.md:15',
        'message': 'Module reference SPEC-999 not found',
        'expected_type': 'Requirement',
        'suggestion': 'Valid requirement IDs: SPEC-001, SPEC-002, SPEC-003'
    },
    {
        'type': 'type_mismatch',
        'source': 'specs/requirements/user-auth.md:22',
        'message': 'Expected reference to Contract, found Requirement',
        'target_id': 'SPEC-002',
        'expected_type': 'Contract',
        'actual_type': 'Requirement',
    },
    {
        'type': 'cardinality_violation',
        'source': 'specs/requirements/user-auth.md',
        'message': 'Missing required reference of type "implements"',
        'expected_cardinality': '1',
        'actual_count': 0,
        'relationship': 'implements',
        'target_type': 'Contract',
    }
]
```

## Link Format Resolution Strategies

### Module ID Resolution

```yaml
# Strategy 1: Pattern-based (default)
module_id_to_file:
  strategy: pattern_match
  pattern: "{id}.md"
  search_paths:
    - "specs/requirements/"
    - "specs/contracts/"
  case_sensitive: false

# Strategy 2: Frontmatter-based
module_id_to_file:
  strategy: frontmatter
  frontmatter_key: id
  # Scan all markdown files for frontmatter with matching ID

# Strategy 3: Index file
module_id_to_file:
  strategy: index_file
  index_path: ".spec-types/id-index.yaml"
  # Use manually maintained or auto-generated index
```

### Class ID Resolution

```yaml
# Strategy 1: Heading search (default)
class_id_to_section:
  strategy: heading_search
  search_scope: document  # Search entire document
  heading_pattern: "^{id}:"

# Strategy 2: Scoped search
class_id_to_section:
  strategy: heading_search
  search_scope: current_section  # Only within current section
  heading_pattern: "^{id}:"
```

## Implementation Notes

### ID Uniqueness Validation

```python
def validate_id_uniqueness(id_registry, type_definitions):
    """Validate IDs are unique within their defined scope."""
    errors = []

    for module_type, module_def in type_definitions['modules'].items():
        scope = module_def['identifier']['scope']

        if scope == 'global':
            # Check no duplicate IDs across all modules of this type
            ids = get_all_ids_for_module_type(module_type)
            duplicates = find_duplicates(ids)
            for dup_id in duplicates:
                errors.append({
                    'type': 'duplicate_id',
                    'id': dup_id,
                    'scope': 'global',
                    'locations': get_id_locations(dup_id),
                })

        elif scope == 'directory':
            # Check no duplicates within same directory
            by_dir = group_by_directory(get_all_ids_for_module_type(module_type))
            for directory, ids in by_dir.items():
                duplicates = find_duplicates(ids)
                for dup_id in duplicates:
                    errors.append({
                        'type': 'duplicate_id',
                        'id': dup_id,
                        'scope': f'directory:{directory}',
                        'locations': get_id_locations_in_dir(dup_id, directory),
                    })

    return errors
```

### Reference Type Inference

When a link is found, infer the reference type based on context:

```python
def infer_reference_type(link_target, current_section, type_definition):
    """Determine what type of reference this link represents."""

    # External reference?
    if link_target.startswith(('http://', 'https://')):
        return 'external_reference'

    # Class reference (has fragment)?
    if '#' in link_target:
        return 'class_reference'

    # Module reference
    # Strip .md extension if present
    clean_target = link_target.replace('.md', '')

    # Check if matches module ID pattern
    for ref_def in type_definition['references']:
        if ref_def['type'] == 'module_reference':
            if matches_pattern(clean_target, ref_def.get('link_pattern', '.*')):
                return 'module_reference'

    # Default to module reference
    return 'module_reference'
```

## Example Type Definitions

See the examples directory:
- `.spec-types/modules/requirement.yaml` - Full requirement module
- `.spec-types/modules/contract.yaml` - Contract module
- `.spec-types/classes/test-case.yaml` - Reusable test case class
- `.spec-types/content-validators/gherkin.yaml` - Gherkin validator

## Migration Path

To migrate existing specs to DSL format:

1. Create type definitions that match current structure
2. Add IDs to documents if not present
3. Update links to use ID-based format
4. Run validation to find inconsistencies
5. Iteratively tighten type definitions

The system should provide a migration tool:
```bash
spec-tools migrate-to-dsl --analyze  # Report what needs changing
spec-tools migrate-to-dsl --convert  # Auto-convert where possible
```
