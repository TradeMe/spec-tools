# spec-tools

[![CI](https://github.com/calvingiles/spec-tools/workflows/CI/badge.svg)](https://github.com/calvingiles/spec-tools/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)

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
- **spec-check**: Validate spec file contents and structure
- **spec-init**: Initialize new spec-driven projects
- **spec-sync**: Keep specs in sync with implementation

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.
