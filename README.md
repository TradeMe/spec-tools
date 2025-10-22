# spec-tools

[![CI](https://github.com/calvingiles/spec-tools/workflows/CI/badge.svg)](https://github.com/calvingiles/spec-tools/actions)
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

## Installation

### Using uv (recommended)

```bash
uv pip install spec-tools
```

### Using pip

```bash
pip install spec-tools
```

### Development installation

```bash
# Clone the repository
git clone https://github.com/calvingiles/spec-tools.git
cd spec-tools

# Install with uv
uv venv
uv pip install -e ".[dev]"
```

## Usage

### Lint Command

Create a `.specallowlist` file in your project root with gitignore-style patterns:

```
# Documentation
*.md
docs/**/*.rst

# Source code
spec_tools/**/*.py
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
spec-tools lint

# Lint a specific directory
spec-tools lint /path/to/project

# Use a custom allowlist file
spec-tools lint --allowlist .myallowlist

# Don't respect .gitignore patterns
spec-tools lint --no-gitignore

# Verbose output
spec-tools lint --verbose
```

### Exit Codes

- `0`: All files match the allowlist patterns
- `1`: Some files don't match or an error occurred

This makes it easy to integrate into CI/CD pipelines:

```yaml
# .github/workflows/ci.yml
- name: Validate file allowlist
  run: spec-tools lint
```

### Check Links Command

Validate all hyperlinks in your markdown documentation:

```bash
# Check links in current directory
spec-tools check-links

# Check links in a specific directory
spec-tools check-links /path/to/docs

# Skip external URL validation (faster)
spec-tools check-links --no-external

# Use a custom config file for private URLs
spec-tools check-links --config .myconfigfile

# Set timeout for external URLs (default: 10 seconds)
spec-tools check-links --timeout 30

# Limit concurrent requests (default: 10)
spec-tools check-links --max-concurrent 5

# Verbose output
spec-tools check-links --verbose
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
  run: spec-tools check-links --no-external  # Skip external URLs in CI
```

### Check Coverage Command

Ensure all spec requirements have corresponding tests:

```bash
# Check coverage in current directory
spec-tools check-coverage

# Check coverage in a specific directory
spec-tools check-coverage /path/to/project

# Use custom specs and tests directories
spec-tools check-coverage --specs-dir my-specs --tests-dir my-tests
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
  run: spec-tools check-coverage
```

### Check Structure Command

Validate spec-to-test structure alignment:

```bash
# Check structure in current directory
spec-tools check-structure

# Check structure in a specific directory
spec-tools check-structure /path/to/project

# Use custom specs and tests directories
spec-tools check-structure --specs-dir my-specs --tests-dir my-tests
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
  run: spec-tools check-structure
```

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
pytest tests/ -v --cov=spec_tools --cov-report=term-missing
```

### Linting

```bash
# Check code with ruff
ruff check spec_tools/ tests/

# Format code with ruff
ruff format spec_tools/ tests/
```

### Building

```bash
# Build with flit
uv pip install flit
flit build
```

## Roadmap

Future tools planned for spec-tools:

- **spec-graph**: Visualize dependencies between spec files
- **spec-init**: Initialize new spec-driven projects
- **spec-sync**: Keep specs in sync with implementation
- **spec-extract**: Extract requirements from code comments into spec files

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
