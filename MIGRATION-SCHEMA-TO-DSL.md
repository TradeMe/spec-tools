# Migrating from Schema Validator to DSL Validator

This guide helps you migrate from the deprecated `check-schema` command to the newer, more powerful `validate-dsl` command.

## Overview

The **Schema Validator** (`check-schema`) is being deprecated in favor of the **DSL Validator** (`validate-dsl`). The DSL validator offers a more comprehensive and flexible approach to validating markdown specifications with:

- **Type definitions**: Define reusable module and class types
- **Multi-pass validation**: Structured validation pipeline with AST processing
- **Content validators**: Extensible validation for specific content patterns (EARS, Gherkin, etc.)
- **Reference validation**: Type-checked cross-document links with cardinality constraints
- **Better error reporting**: Precise source location and actionable error messages

## Key Differences

| Feature | Schema Validator | DSL Validator |
|---------|-----------------|---------------|
| **Configuration** | Single config file (`.specschemaconfig`) | YAML type definitions in `spec_types/` directory |
| **Type System** | None - validates all files the same way | Rich type system with modules and classes |
| **Validation** | Single-pass metadata and heading checks | Multi-pass AST, structure, content, and reference validation |
| **Content Validation** | EARS format only | Extensible content validators (EARS, Gherkin, custom) |
| **References** | Not validated | Full link resolution with type checking |
| **Reusability** | Configuration per project | Reusable type definitions across projects |
| **Flexibility** | Fixed schema structure | Flexible type composition |

## Migration Steps

### Step 1: Understanding Your Current Schema

First, review your existing `.specschemaconfig` file. A typical schema configuration looks like:

```yaml
# .specschemaconfig (OLD)
patterns:
  - specs/*.md

metadata:
  required:
    - ID
    - Version
    - Date
    - Status

headings:
  required:
    - level: 1
      pattern: "^Specification:\\s+.+$"
    - level: 2
      text: "Overview"
    - level: 2
      pattern: "^Requirements\\s+\\(EARS Format\\)$"

ears:
  enabled: true
  sections:
    - "Requirements (EARS Format)"
    - "Non-Functional Requirements"
```

### Step 2: Create Type Definitions Directory

Create a `spec_types/` directory in your project root:

```bash
mkdir -p spec_types/modules
mkdir -p spec_types/classes
mkdir -p spec_types/content-validators
```

### Step 3: Create Module Type Definition

Convert your schema configuration into a module type definition. Create `spec_types/modules/requirement.yaml`:

```yaml
# spec_types/modules/requirement.yaml (NEW)
name: Requirement
description: Technical requirement specification with EARS format

# File matching patterns (equivalent to 'patterns' in old config)
patterns:
  - "specs/*.md"

# Identifier pattern for requirement documents
identifier:
  pattern: "^SPEC-[0-9]{3}$"
  location: metadata  # Can be: title, metadata, or first_heading
  field: ID           # For metadata location

# Required metadata fields (equivalent to 'metadata.required' in old config)
metadata:
  required:
    - name: ID
      pattern: "^SPEC-[0-9]{3}$"
    - name: Version
      pattern: "^[0-9]+\\.[0-9]+$"
    - name: Date
      pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"
    - name: Status
      allowed_values: [Draft, Approved, Provisional, Planned, Deprecated]

# Section structure (equivalent to 'headings' in old config)
sections:
  - level: 1
    pattern: "^Specification:\\s+.+$"
    required: true

  - level: 2
    text: "Overview"
    required: true

  - level: 2
    text: "Requirements (EARS Format)"
    required: true
    content_validator: ears  # Replaces 'ears.enabled' and 'ears.sections'

  - level: 2
    text: "Non-Functional Requirements"
    required: false
    content_validator: ears

# Reference constraints (NEW - not available in old validator)
references:
  allowed_types:
    - Requirement
    - Contract
  max_outgoing: 50
```

### Step 4: Create Content Validator Definitions (Optional)

If you need to customize content validation behavior, create content validator definitions. For EARS format:

```yaml
# spec_types/content-validators/ears.yaml (OPTIONAL)
name: ears
description: Easy Approach to Requirements Syntax validator

patterns:
  unconditional:
    - "^The (system|application|software) shall .+"
  event_driven:
    - "^WHEN .+, (the )?(system|application|software) shall .+"
  conditional:
    - "^IF .+, THEN (the )?(system|application|software) shall .+"
  optional:
    - "^WHERE .+, (the )?(system|application|software) shall .+"

# Requirement ID patterns to match
requirement_markers:
  - "^\\*\\*REQ-[0-9]{3}\\*\\*:"
  - "^\\*\\*NFR-[0-9]{3}\\*\\*:"
  - "^\\*\\*TEST-[0-9]{3}\\*\\*:"
```

**Note**: The DSL validator includes built-in EARS and Gherkin validators, so this step is optional unless you need custom patterns.

### Step 5: Create Configuration File

Create `spec_types/config.yaml` to define global settings:

```yaml
# spec_types/config.yaml
version: "1.0"

# Global settings
gitignore: true
specignore: true

# Default severity levels
severity:
  missing_metadata: error
  missing_heading: error
  invalid_structure: error
  broken_reference: error
  content_validation: error
```

### Step 6: Test the Migration

Run the DSL validator to test your new configuration:

```bash
# Test with your new type definitions
spec-check validate-dsl

# Or test a specific directory
spec-check validate-dsl specs/

# Use verbose mode to see detailed validation results
spec-check validate-dsl --verbose
```

Compare the output with your old schema validator:

```bash
# Old command (deprecated)
spec-check check-schema --verbose

# New command
spec-check validate-dsl --verbose
```

### Step 7: Update CI/CD Pipeline

Update your CI/CD configuration to use the new command:

```yaml
# .github/workflows/ci.yml

# OLD (deprecated)
- name: Validate schema
  run: spec-check check-schema

# NEW
- name: Validate DSL
  run: spec-check validate-dsl
```

### Step 8: Update pyproject.toml (Optional)

If you're using `pyproject.toml` for configuration, update it:

```toml
# pyproject.toml

# OLD (deprecated)
[tool.spec-check.check-schema]
config = ".specschemaconfig"
use_gitignore = true

# NEW
[tool.spec-check.validate-dsl]
type_dir = "spec_types"
use_gitignore = true
strict = false
```

### Step 9: Remove Old Configuration

Once you've verified the migration works correctly, remove the old configuration:

```bash
# Remove old schema config file
rm .specschemaconfig
```

## Advanced Features in DSL Validator

The DSL validator provides several features not available in the schema validator:

### 1. Reusable Class Definitions

Define reusable section patterns that can be shared across multiple module types:

```yaml
# spec_types/classes/acceptance-criteria.yaml
name: AcceptanceCriteria
description: Gherkin-style acceptance criteria section

heading:
  pattern: "^Acceptance Criteria$"
  level: 3

content_validator: gherkin

constraints:
  min_scenarios: 1
  max_scenarios: 10
```

Use in module definitions:

```yaml
# spec_types/modules/requirement.yaml
sections:
  - level: 2
    text: "Test Cases"
    classes:
      - AcceptanceCriteria  # Reference the shared class
```

### 2. Reference Validation

Validate cross-document links with type checking:

```yaml
# spec_types/modules/requirement.yaml
references:
  allowed_types:
    - Requirement
    - Architecture  # Links can only point to these types
  min_outgoing: 0   # Minimum number of outgoing links
  max_outgoing: 20  # Maximum number of outgoing links
  cardinality: many # Can reference many documents
```

### 3. Multiple Document Types

Define different types for different kinds of specifications:

```yaml
# spec_types/modules/architecture.yaml
name: Architecture
patterns:
  - "architecture/*.md"
  - "ADRs/ADR-*.md"

# spec_types/modules/contract.yaml
name: Contract
patterns:
  - "contracts/*.md"
```

### 4. Built-in Content Validators

The DSL validator includes built-in validators:

- **EARS**: Easy Approach to Requirements Syntax
- **Gherkin**: Given-When-Then format for acceptance criteria
- **Custom**: Create your own content validators

### 5. Strict Mode

Enable strict mode to warn about files that don't match any type:

```bash
spec-check validate-dsl --strict
```

This helps ensure all markdown files are properly typed and validated.

## Common Migration Patterns

### Pattern 1: Simple Specification Files

**Before** (Schema Validator):
```yaml
# .specschemaconfig
patterns: ["specs/*.md"]
metadata:
  required: [ID, Version, Date, Status]
headings:
  required:
    - {level: 1, pattern: "^Specification:.+"}
    - {level: 2, text: "Overview"}
ears:
  enabled: true
  sections: ["Requirements"]
```

**After** (DSL Validator):
```yaml
# spec_types/modules/requirement.yaml
name: Requirement
patterns: ["specs/*.md"]
identifier:
  pattern: "^SPEC-[0-9]{3}$"
  location: metadata
  field: ID
metadata:
  required:
    - {name: ID, pattern: "^SPEC-[0-9]{3}$"}
    - {name: Version, pattern: "^[0-9]+\\.[0-9]+$"}
    - {name: Date, pattern: "^[0-9]{4}-[0-9]{2}-[0-9]{2}$"}
    - {name: Status}
sections:
  - {level: 1, pattern: "^Specification:.+", required: true}
  - {level: 2, text: "Overview", required: true}
  - {level: 2, text: "Requirements", required: true, content_validator: ears}
```

### Pattern 2: Multiple Document Types

The DSL validator excels when you have different types of documents:

```yaml
# spec_types/modules/requirement.yaml
name: Requirement
patterns: ["specs/req-*.md"]
# ... requirement-specific configuration

# spec_types/modules/design.yaml
name: Design
patterns: ["specs/design-*.md"]
# ... design-specific configuration

# spec_types/modules/adr.yaml
name: ADR
patterns: ["architecture/ADR-*.md"]
# ... ADR-specific configuration
```

## Troubleshooting

### Issue: Validation fails after migration

**Solution**: Run with `--verbose` to see detailed error messages:
```bash
spec-check validate-dsl --verbose
```

Compare the validation results with the old validator to identify differences.

### Issue: Files not being validated

**Solution**: Check that your patterns in `spec_types/modules/*.yaml` match your file paths. Use `--strict` mode to see which files don't match any type:
```bash
spec-check validate-dsl --strict
```

### Issue: Content validation too strict/lenient

**Solution**: Customize the content validator patterns in `spec_types/content-validators/` or adjust the severity levels in `spec_types/config.yaml`.

### Issue: Migration seems complex

**Solution**: Start with built-in types to see examples:
```bash
spec-check validate-dsl --builtin-types specs/
```

The built-in types include examples for Job, Requirement, and ADR document types.

## Getting Help

If you encounter issues during migration:

1. Check the [DSL Validator Specification](specs/future/specification-dsl.md) for detailed information
2. Review [Technical Note TN-005](context/technical-notes/TN-005.md) for implementation details
3. Use `spec-check validate-dsl --help` for command-line options
4. Open an issue at https://github.com/TradeMe/spec-check/issues

## Timeline

- **Current**: Both validators are available
- **Deprecation Notice**: Schema validator is now deprecated (this release)
- **Future**: Schema validator will be removed in version 2.0.0

We recommend migrating as soon as possible to take advantage of the improved validation capabilities.
