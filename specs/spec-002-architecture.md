# Spec 002: spec-tools Architecture

**Status**: Implemented
**Version**: 1.0
**Author**: spec-tools contributors
**Created**: 2025-10-22
**Updated**: 2025-10-22

## Overview

This document describes the architecture of spec-tools, a toolkit for spec-driven development. It covers the package structure, design patterns, and architectural decisions that guide development.

## Motivation

spec-tools is designed as a **toolkit** rather than a single tool. It needs an architecture that:

1. Supports multiple tools under one umbrella
2. Allows tools to share common functionality
3. Makes it easy to add new tools
4. Provides both programmatic and CLI interfaces
5. Maintains clean separation of concerns

## Architecture Principles

### 1. Modular Tool Design

Each tool is a self-contained module:
- Independent functionality
- Clear responsibilities
- Minimal coupling between tools
- Can be used independently or together

### 2. CLI with Subcommands

Use a hierarchical CLI structure:

```
spec-tools <command> [args]
  ├── lint [directory] [options]
  ├── graph [directory] [options]    (future)
  ├── check [files] [options]        (future)
  └── init [directory] [options]     (future)
```

Benefits:
- Familiar pattern (git, docker, kubectl)
- Easy to discover available tools
- Clean help system
- Extensible for new tools

### 3. Library-First Design

Every tool should be usable as:
1. **CLI**: Command-line interface for users
2. **Library**: Python API for programmatic use
3. **Module**: Importable components for other tools

Example:
```python
# As a library
from spec_tools import SpecLinter
linter = SpecLinter(root_dir=".")
result = linter.lint()

# As a CLI
$ spec-tools lint
```

### 4. Dependency Management

- **Minimal core dependencies**: Keep base requirements light
- **Optional dependencies**: Use extras for tool-specific needs
- **Modern tooling**: Use uv, flit, ruff for development

## Package Structure

```
spec-tools/
├── spec_tools/              # Main package
│   ├── __init__.py         # Package exports (SpecLinter, etc.)
│   ├── __main__.py         # Entry point for python -m spec_tools
│   ├── cli.py              # Main CLI with subcommand dispatcher
│   ├── linter.py           # Linter tool implementation
│   ├── graph.py            # (future) Graph visualizer
│   ├── checker.py          # (future) Spec content validator
│   └── common/             # (future) Shared utilities
│       ├── patterns.py     # Pattern matching utilities
│       └── files.py        # File system utilities
├── tests/                  # Test suite
│   ├── __init__.py
│   ├── test_linter.py      # Linter tests
│   ├── test_cli.py         # (future) CLI integration tests
│   └── conftest.py         # (future) Shared fixtures
├── specs/                  # Specifications
│   ├── spec-000-*.md       # Process and methodology specs
│   ├── spec-001-*.md       # Feature specs
│   └── README.md           # Specs index
├── docs/                   # (future) Additional documentation
├── .github/
│   └── workflows/
│       └── ci.yml          # CI/CD pipeline
├── pyproject.toml          # Package configuration
├── .specallowlist          # Allowlist for linter
├── .gitignore              # Git ignore patterns
├── LICENSE                 # MIT license
└── README.md               # Project README
```

## Component Architecture

### Core Components

#### 1. CLI Module (`cli.py`)

**Responsibility**: Command-line interface and argument parsing

**Design**:
- Uses argparse for argument parsing
- Subparsers for each tool (lint, graph, check, init)
- Each subcommand has a handler function
- Main function dispatches to appropriate handler

**Structure**:
```python
def main(argv):
    parser = argparse.ArgumentParser(prog="spec-tools")
    subparsers = parser.add_subparsers(dest="command")

    # Lint subcommand
    lint_parser = subparsers.add_parser("lint")
    lint_parser.add_argument(...)
    lint_parser.set_defaults(func=cmd_lint)

    # Parse and execute
    args = parser.parse_args(argv)
    return args.func(args)

def cmd_lint(args):
    # Create linter and run
    linter = SpecLinter(...)
    result = linter.lint()
    # Format and print output
    return 0 if result.is_valid else 1
```

#### 2. Tool Modules (`linter.py`, etc.)

**Responsibility**: Implement tool logic

**Design**:
- Each tool is a class with clear interface
- Returns structured results (dataclasses)
- No CLI-specific code (separation of concerns)
- Can be used programmatically

**Pattern**:
```python
from dataclasses import dataclass

@dataclass
class ToolResult:
    """Result from running the tool."""
    success: bool
    message: str
    details: dict

class Tool:
    """Tool implementation."""

    def __init__(self, config):
        """Initialize tool with config."""
        pass

    def run(self):
        """Run tool and return result."""
        return ToolResult(...)
```

#### 3. Package Exports (`__init__.py`)

**Responsibility**: Define public API

**Design**:
- Export main classes and functions
- Keep internal implementation private
- Use `__all__` to control exports

**Example**:
```python
"""spec-tools: Tools for spec-driven development."""

__version__ = "0.1.0"

from .linter import SpecLinter, LintResult

__all__ = ["SpecLinter", "LintResult", "__version__"]
```

### Current Tools

#### 1. Linter Tool

**Module**: `spec_tools/linter.py`

**Classes**:
- `SpecLinter`: Main linter class
- `LintResult`: Result dataclass

**Flow**:
1. Load patterns from allowlist and gitignore
2. Compile patterns into PathSpec objects
3. Discover files recursively
4. Match each file against patterns
5. Return structured result

**See**: `specs/spec-001-linter-tool.md` for detailed spec

### Future Tools

#### 2. Graph Visualizer (planned)

**Purpose**: Visualize dependencies between spec files

**Module**: `spec_tools/graph.py`

**Features**:
- Parse spec file references
- Build dependency graph
- Output as DOT, SVG, or interactive HTML

#### 3. Spec Checker (planned)

**Purpose**: Validate spec file structure and content

**Module**: `spec_tools/checker.py`

**Features**:
- Check required sections present
- Validate metadata (status, version, dates)
- Lint markdown formatting
- Check for broken links

#### 4. Project Initializer (planned)

**Purpose**: Bootstrap new spec-driven projects

**Module**: `spec_tools/init.py`

**Features**:
- Create directory structure
- Generate initial specs
- Set up .specallowlist
- Configure CI/CD templates

## Design Patterns

### 1. Command Pattern

Each tool implements a command:
- Encapsulates an action
- Has clear input (config) and output (result)
- Can be undone/logged/queued

### 2. Factory Pattern

CLI creates tool instances:
- Parses arguments
- Constructs tool with config
- Returns tool instance

### 3. Strategy Pattern

Tools can use different strategies:
- Pattern matching: PathSpec vs regex vs custom
- Output formatting: Text vs JSON vs SARIF
- File discovery: Recursive vs filtered

### 4. Result Objects

Tools return structured results:
- Success/failure status
- Detailed information
- Can be formatted for different outputs

## Data Flow

### Linter Tool Flow

```
┌─────────────┐
│ User Input  │
│ (CLI args)  │
└──────┬──────┘
       │
       v
┌─────────────────┐
│  CLI Parser     │
│  - Parse args   │
│  - Validate     │
└──────┬──────────┘
       │
       v
┌─────────────────────┐
│  SpecLinter         │
│  - __init__(config) │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Load Patterns      │
│  - Read files       │
│  - Parse patterns   │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Compile Specs      │
│  - PathSpec from    │
│    patterns         │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Get All Files      │
│  - Walk directory   │
│  - Apply filters    │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Validate Files     │
│  - Match patterns   │
│  - Collect results  │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Return Result      │
│  - LintResult obj   │
└──────┬──────────────┘
       │
       v
┌─────────────────────┐
│  Format Output      │
│  - Print summary    │
│  - Exit with code   │
└─────────────────────┘
```

## Technology Stack

### Core Dependencies

- **Python**: >=3.8 for broad compatibility
- **pathspec**: Gitignore-style pattern matching

### Development Dependencies

- **pytest**: Testing framework
- **pytest-cov**: Coverage reporting
- **ruff**: Fast linting and formatting

### Build Tools

- **flit**: Simple PEP 517 build backend
- **uv**: Fast dependency management

### CI/CD

- **GitHub Actions**: Automated testing and linting
- **Codecov**: Coverage tracking (optional)

## Testing Strategy

### Unit Tests

- Test each tool independently
- Mock file system operations
- Use tmp_path fixtures
- Test edge cases and errors

### Integration Tests

- Test CLI end-to-end
- Test tool combinations
- Test on real repositories

### Coverage Goals

- Minimum 80% code coverage
- 100% coverage for critical paths
- Test both success and failure cases

### Test Organization

```
tests/
├── test_linter.py       # Linter unit tests
├── test_cli.py          # CLI integration tests
├── test_graph.py        # Graph tool tests (future)
└── conftest.py          # Shared fixtures
```

## Configuration Management

### pyproject.toml

Single configuration file for:
- Package metadata
- Dependencies
- Build system (flit)
- Tool configuration (ruff, pytest)
- Entry points (CLI commands)

### Environment Variables

Future support for:
- `SPEC_TOOLS_CONFIG`: Config file path
- `SPEC_TOOLS_VERBOSE`: Default verbosity
- `SPEC_TOOLS_COLOR`: Color output control

### Configuration Files

Future support for:
- `.spectools.toml`: Project-specific config
- `.specallowlist`: Linter patterns
- `.specignore`: Files to ignore

## Extension Points

### Adding a New Tool

1. Create `spec_tools/newtool.py` with tool class
2. Add result dataclass
3. Add subcommand to `cli.py`
4. Add tests in `tests/test_newtool.py`
5. Export from `__init__.py`
6. Update documentation

### Adding Tool Options

1. Add parameters to tool `__init__`
2. Add CLI arguments in subparser
3. Pass arguments to tool instance
4. Add tests for new options

### Adding Output Formats

1. Add format option to CLI
2. Implement formatter function
3. Update result `__str__` or add methods
4. Test output formatting

## Performance Considerations

### File I/O

- Use pathlib for cross-platform paths
- Avoid reading large files unnecessarily
- Use generators for large file lists

### Pattern Matching

- Compile patterns once, reuse
- Use pathspec library (C-accelerated)
- Filter directories early to prune search

### Concurrency

- Currently single-threaded
- Future: parallel file scanning for large repos
- Future: async I/O for network operations

## Security Considerations

### Input Validation

- Validate file paths (no directory traversal)
- Sanitize pattern input
- Limit file size for content operations

### Dependencies

- Pin major versions in pyproject.toml
- Regular dependency updates
- Security scanning in CI (future)

### File Operations

- Only read files, never write (for linter)
- Respect symlinks carefully
- Handle permissions errors gracefully

## Deployment

### Installation Methods

1. **PyPI**: `pip install spec-tools`
2. **uv**: `uv pip install spec-tools`
3. **Source**: `git clone && uv pip install -e .`

### Entry Points

- `spec-tools`: Main CLI command
- `spec-lint`: Convenience alias for linter

### Distribution

- Source distribution via flit
- Wheel for faster installation
- GitHub releases for versioning

## Future Architecture Enhancements

1. **Plugin System**: Load external tools
2. **Configuration Hierarchy**: User, project, CLI config
3. **Output Formatters**: JSON, SARIF, custom formats
4. **Interactive Mode**: Watch mode, prompts
5. **Language Server**: IDE integration
6. **Web UI**: Browser-based visualization

## References

- [Python Packaging Guide](https://packaging.python.org/)
- [Click vs Argparse](https://jwodder.github.io/kbits/posts/click-vs-argparse/)
- [Structuring Python Projects](https://docs.python-guide.org/writing/structure/)
- [pathspec library](https://github.com/cpburnz/python-pathspec)

## Changelog

### Version 1.0 (2025-10-22)

- Initial architecture document
- Define package structure
- Document linter tool architecture
- Establish design patterns and principles
