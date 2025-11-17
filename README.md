# spec-check

[![CI](https://github.com/TradeMe/spec-check/workflows/CI/badge.svg)](https://github.com/TradeMe/spec-check/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

Tools for spec-driven development - a toolkit for managing and validating project specifications and files.

## Features

### Lint Tool

The `lint` tool validates that all files in your repository match patterns in an allowlist. Think of it as the inverse of `.gitignore` - instead of specifying what to ignore, you specify what files are allowed.

Key features:
- Uses gitignore-style glob patterns for flexible file matching
- Respects `.gitignore` patterns by default
- Supports complex patterns including character classes (e.g., `[0-9]`)
- Validates that all tracked files match at least one allowlist pattern
- Reports unmatched files for easy identification

### Markdown Link Validator

The `check-links` tool validates hyperlinks in markdown files to ensure documentation stays up-to-date and accessible.

Key features:
- Validates internal links (relative paths) resolve correctly
- Checks anchor links point to existing headings
- Validates external URLs are accessible
- Supports private URL patterns that are skipped during validation
- Concurrent external URL checking for performance
- Respects `.gitignore` patterns by default

### Spec Coverage Validator

The `check-coverage` tool ensures 100% traceability between specification requirements and tests.

Key features:
- Extracts requirement IDs from spec files (e.g., REQ-001, NFR-001)
- Validates every requirement has at least one corresponding test
- Reports coverage percentage and uncovered requirements
- Uses pytest markers for machine-readable test-to-requirement linking
- Identifies tests without requirement markers

### Structure Validator

The `check-structure` tool enforces consistent spec-to-test structure alignment.

Key features:
- Verifies each spec file has a corresponding test file or directory
- Supports flexible naming conventions (kebab-case to snake_case)
- Allows unit tests without corresponding specs
- Reports specs without tests
- Ensures consistent project organization

### DSL Validator

The `validate-dsl` tool validates markdown documents against type definitions using a sophisticated multi-pass validation architecture. This is the recommended validator for structured specifications.

Key features:
- **Type system**: Define reusable module and class types in YAML
- **Multi-pass validation**: AST parsing, section hierarchy, type assignment, structural validation, content validation, and reference resolution
- **Content validators**: Built-in EARS (Easy Approach to Requirements Syntax) and Gherkin validators with extensibility for custom patterns
- **Reference validation**: Type-checked cross-document links with cardinality constraints
- **Precise error reporting**: File path, line number, column offset, and actionable guidance
- **Built-in types**: Includes Job, Requirement, and ADR document types
- **Flexible type composition**: Module types, class types, and content validators can be mixed and matched

See [MIGRATION-SCHEMA-TO-DSL.md](MIGRATION-SCHEMA-TO-DSL.md) for migration from the deprecated `check-schema` command.

### ⚠️ Deprecated: Markdown Schema Validator

> **Note**: The `check-schema` command is deprecated and will be removed in version 2.0.0. Please migrate to `validate-dsl` for better validation capabilities. See [MIGRATION-SCHEMA-TO-DSL.md](MIGRATION-SCHEMA-TO-DSL.md) for the migration guide.

The `check-schema` tool validates markdown files against a defined structural schema (deprecated in favor of `validate-dsl`).

Legacy features:
- Metadata field validation (ID, Version, Date, Status)
- Heading structure and hierarchy validation
- EARS format compliance for requirement statements
- Configuration via `.specschemaconfig` file

## Installation

### Using uv (recommended)

```bash
uv pip install spec-check
```

### Using pip

```bash
pip install spec-check
```

### Development installation

```bash
# Clone the repository
git clone https://github.com/TradeMe/spec-check.git
cd spec-check

# Install with uv
uv venv
uv pip install -e ".[dev]"
```

## Configuration

spec-check can be configured via `pyproject.toml` for seamless integration with Python projects. This allows you to set default options without needing to pass command-line arguments every time.

### pyproject.toml Configuration

Add a `[tool.spec-check]` section to your `pyproject.toml`:

```toml
[tool.spec-check.lint]
allowlist = ".specallowlist"
use_gitignore = true

[tool.spec-check.check-links]
config = ".speclinkconfig"
timeout = 15
max_concurrent = 5
check_external = true
use_gitignore = true

[tool.spec-check.validate-dsl]
type_dir = "spec_types"
use_gitignore = true
use_specignore = true
strict = false

# Deprecated: Use validate-dsl instead
[tool.spec-check.check-schema]
config = ".specschemaconfig"
use_gitignore = true
```

### Configuration Options

#### Lint Command (`[tool.spec-check.lint]`)
- `allowlist` (string): Path to allowlist file (default: `.specallowlist`)
- `use_gitignore` (boolean): Respect .gitignore patterns (default: `true`)

#### Check Links Command (`[tool.spec-check.check-links]`)
- `config` (string): Path to config file for private URLs (default: `.speclinkconfig`)
- `timeout` (integer): Timeout for external URL requests in seconds (default: `10`)
- `max_concurrent` (integer): Maximum concurrent external URL requests (default: `10`)
- `check_external` (boolean): Validate external URLs (default: `true`)
- `use_gitignore` (boolean): Respect .gitignore patterns (default: `true`)

#### Validate DSL Command (`[tool.spec-check.validate-dsl]`)
- `type_dir` (string): Path to type definitions directory (default: `spec_types`)
- `builtin_types` (boolean): Use built-in types instead of custom types (default: `false`)
- `use_gitignore` (boolean): Respect .gitignore patterns (default: `true`)
- `use_specignore` (boolean): Use .specignore file (default: `true`)
- `specignore_file` (string): Path to specignore file (default: `.specignore`)
- `strict` (boolean): Warn about files that don't match any type (default: `false`)

#### Check Schema Command (Deprecated) (`[tool.spec-check.check-schema]`)
> **Deprecated**: Use `validate-dsl` instead
- `config` (string): Path to schema config file (default: `.specschemaconfig`)
- `use_gitignore` (boolean): Respect .gitignore patterns (default: `true`)

### Configuration Precedence

Configuration values are resolved in the following order (highest to lowest precedence):

1. **Command-line arguments** (e.g., `--timeout 30`)
2. **pyproject.toml configuration** (e.g., `timeout = 15` in `[tool.spec-check.check-links]`)
3. **Built-in defaults**

This means you can set project defaults in `pyproject.toml` and override them on the command line when needed.

## Usage

### Lint Command

Create a `.specallowlist` file in your project root with gitignore-style patterns:

```
# Documentation
*.md
docs/**/*.rst

# Source code
spec_check/**/*.py
tests/**/*.py

# Configuration files
*.toml
*.yaml
*.yml

# Specs with specific naming convention
specs/research-[0-9][0-9][0-9]-*.md
specs/design-*.md
```

Then run the linter:

```bash
# Lint the current directory
spec-check lint

# Lint a specific directory
spec-check lint /path/to/project

# Use a custom allowlist file
spec-check lint --allowlist .myallowlist

# Don't respect .gitignore patterns
spec-check lint --no-gitignore

# Verbose output
spec-check lint --verbose
```

### Exit Codes

- `0`: All files match the allowlist patterns
- `1`: Some files don't match or an error occurred

This makes it easy to integrate into CI/CD pipelines:

```yaml
# .github/workflows/ci.yml
- name: Validate file allowlist
  run: spec-check lint
```

### Check Links Command

Validate all hyperlinks in your markdown documentation:

```bash
# Check links in current directory
spec-check check-links

# Check links in a specific directory
spec-check check-links /path/to/docs

# Skip external URL validation (faster)
spec-check check-links --no-external

# Use a custom config file for private URLs
spec-check check-links --config .myconfigfile

# Set timeout for external URLs (default: 10 seconds)
spec-check check-links --timeout 30

# Limit concurrent requests (default: 10)
spec-check check-links --max-concurrent 5

# Verbose output
spec-check check-links --verbose
```

#### Private URL Configuration

Create a `.speclinkconfig` file to specify private URL patterns that should not be validated:

```
# Private domains (will skip any URL containing these domains)
internal.company.com
localhost

# Private URL prefixes (exact prefix match)
https://private.example.com/
http://localhost:
http://127.0.0.1:
```

#### What Gets Validated

- **Internal links**: `[text](./file.md)` - checked relative to the markdown file
- **Anchor links**: `[text](#heading)` - validated against headings in the file
- **Cross-file anchors**: `[text](./other.md#section)` - validates both file and heading
- **External URLs**: `[text](https://example.com)` - HTTP request to verify accessibility
- **Private URLs**: URLs matching configured patterns are skipped

#### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Validate documentation links
  run: spec-check check-links --no-external  # Skip external URLs in CI
```

### Check Coverage Command

Ensure all spec requirements have corresponding tests:

```bash
# Check coverage in current directory
spec-check check-coverage

# Check coverage in a specific directory
spec-check check-coverage /path/to/project

# Use custom specs and tests directories
spec-check check-coverage --specs-dir my-specs --tests-dir my-tests
```

#### Marking Tests with Requirements

Use pytest markers to link tests to requirements:

```python
import pytest

@pytest.mark.req("REQ-001")
def test_inline_link_parsing():
    """Test that inline links are parsed correctly."""
    # Test implementation
    assert True

# For tests covering multiple requirements:
@pytest.mark.req("REQ-002", "REQ-003")
def test_reference_style_links():
    """Test reference-style link parsing."""
    # Test implementation
    assert True
```

#### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Validate spec coverage
  run: spec-check check-coverage
```

### Check Structure Command

Validate spec-to-test structure alignment:

```bash
# Check structure in current directory
spec-check check-structure

# Check structure in a specific directory
spec-check check-structure /path/to/project

# Use custom specs and tests directories
spec-check check-structure --specs-dir my-specs --tests-dir my-tests
```

#### Structure Conventions

For a spec file `specs/feature-name.md`, the tool expects either:
- `tests/test_feature_name.py` (single test file)
- `tests/feature_name/` (test directory)

This allows unit tests without corresponding specs while ensuring all specs have requirement tests.

#### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Validate spec structure
  run: spec-check check-structure
```

### Validate DSL Command

Validate markdown documents against type definitions:

```bash
# Validate using custom type definitions in spec_types/
spec-check validate-dsl

# Validate specific directory
spec-check validate-dsl specs/

# Use built-in types (Job, Requirement, ADR)
spec-check validate-dsl --builtin-types specs/

# Use custom type definitions directory
spec-check validate-dsl --type-dir my_types/

# Enable strict mode (warn about untyped files)
spec-check validate-dsl --strict

# Verbose output with detailed validation results
spec-check validate-dsl --verbose
```

#### Type Definitions

Create type definitions in YAML format to describe document structure. The typical directory structure is:

```
spec_types/
  config.yaml              # Global configuration
  modules/
    requirement.yaml       # Module type definitions
    contract.yaml
    architecture.yaml
  classes/
    acceptance-criteria.yaml  # Shared class definitions
  content-validators/
    custom-validator.yaml    # Custom content validators
```

Example module type definition:

```yaml
# spec_types/modules/requirement.yaml
name: Requirement
description: Technical requirement specification

patterns:
  - "specs/req-*.md"

identifier:
  pattern: "^REQ-[0-9]{3}$"
  location: metadata
  field: ID

metadata:
  required:
    - name: ID
      pattern: "^REQ-[0-9]{3}$"
    - name: Version
    - name: Date
    - name: Status

sections:
  - level: 1
    pattern: "^Specification:.+"
    required: true
  - level: 2
    text: "Overview"
    required: true
  - level: 2
    text: "Requirements"
    required: true
    content_validator: ears  # Built-in EARS validator

references:
  allowed_types: [Requirement, Contract]
  max_outgoing: 50
```

#### Built-in Content Validators

The DSL validator includes built-in content validators:

- **EARS**: Easy Approach to Requirements Syntax
  - Unconditional: "The system shall..."
  - Event-driven: "WHEN [condition], the system shall..."
  - Conditional: "IF [condition], THEN the system shall..."
  - Optional: "WHERE [condition], the system shall..."

- **Gherkin**: Given-When-Then format
  - Scenario-based acceptance criteria
  - Given-When-Then structure validation

#### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Validate DSL
  run: spec-check validate-dsl
```

#### Migration from check-schema

If you're currently using `check-schema`, see [MIGRATION-SCHEMA-TO-DSL.md](MIGRATION-SCHEMA-TO-DSL.md) for a complete migration guide.

## Pattern Syntax

The allowlist uses gitignore-style glob patterns:

- `*` - matches any number of characters (except `/`)
- `**` - matches any number of directories
- `?` - matches a single character
- `[abc]` - matches one character in the set
- `[0-9]` - matches one character in the range
- `!pattern` - negates a pattern (matches files that don't match the pattern)

### Examples

```
# Match all Python files
*.py

# Match Python files in src directory and subdirectories
src/**/*.py

# Match numbered specification files
specs/spec-[0-9][0-9][0-9].md

# Match files with specific naming pattern
docs/architecture-*.md
docs/design-*.md

# Match multiple file types
*.{yml,yaml}
```

## Use Cases

1. **Enforce file organization**: Ensure all files follow your project's structure
2. **Validate spec compliance**: Make sure all files match expected patterns
3. **CI/CD validation**: Automatically check that no unexpected files are committed
4. **Documentation enforcement**: Ensure all code files have matching documentation
5. **Naming convention enforcement**: Validate files follow naming standards
6. **Test-to-requirement traceability**: Guarantee 100% requirement coverage with automated validation
7. **Spec-driven development**: Enforce consistent spec-to-test structure for better maintainability
8. **Documentation quality**: Ensure all links in documentation are valid and up-to-date
9. **Structured specifications**: Define and enforce document types with rich validation rules using the DSL validator
10. **Cross-document validation**: Validate references between specifications with type checking and cardinality constraints

## Example: Research Paper Repository

```
# .specallowlist
# Papers must follow naming: research-NNN-title.md
papers/research-[0-9][0-9][0-9]-*.md

# Supporting data files
papers/data-[0-9][0-9][0-9]-*.csv
papers/figures-[0-9][0-9][0-9]-*.{png,jpg,svg}

# Project files
*.md
LICENSE
.gitignore
.specallowlist
```

## Development

### Running Tests

```bash
# Activate virtual environment
source .venv/bin/activate

# Run tests
pytest tests/ -v

# Run tests with coverage
pytest tests/ -v --cov=spec_check --cov-report=term-missing
```

### Linting

```bash
# Check code with ruff
ruff check spec_check/ tests/

# Format code with ruff
ruff format spec_check/ tests/
```

### Building

```bash
# Build with flit
uv pip install flit
flit build
```

## Roadmap

Future tools planned for spec-check:

- **spec-graph**: Visualize dependencies between spec files
- **spec-init**: Initialize new spec-driven projects
- **spec-sync**: Keep specs in sync with implementation
- **spec-extract**: Extract requirements from code comments into spec files

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
