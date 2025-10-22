# Spec 001: Allowlist Linter Tool

**Status**: Implemented
**Version**: 1.0
**Author**: spec-tools contributors
**Created**: 2025-10-22
**Updated**: 2025-10-22

## Overview

The allowlist linter is a tool that validates all files in a repository match patterns defined in an allowlist file. It's the inverse of `.gitignore` - instead of specifying what to ignore, you specify what files are allowed.

## Motivation

In spec-driven development and well-organized projects, it's important to ensure all files follow expected patterns and naming conventions. Traditional tools like `.gitignore` help exclude unwanted files, but there's no standard tool to validate that all tracked files match expected patterns.

Use cases:
- **Enforce file organization**: Ensure all files follow project structure
- **Validate naming conventions**: e.g., `specs/spec-[0-9]{3}-*.md`
- **CI/CD validation**: Catch unexpected files in pull requests
- **Documentation enforcement**: Ensure all code has matching docs
- **Research repositories**: Validate papers follow naming standards

## Requirements

### Functional Requirements

1. **Pattern Matching**
   - SHALL use gitignore-style glob patterns via the `pathspec` library
   - SHALL support wildcards (`*`, `**`, `?`)
   - SHALL support character classes (`[abc]`, `[0-9]`)
   - SHALL support brace expansion (`*.{yml,yaml}`)
   - SHALL support negation patterns (`!pattern`)

2. **Allowlist File**
   - SHALL read patterns from `.specallowlist` by default
   - SHALL support custom allowlist filenames via `--allowlist` flag
   - SHALL ignore lines starting with `#` (comments)
   - SHALL ignore inline comments (e.g., `*.md # markdown files`)
   - SHALL ignore empty lines
   - SHALL automatically exclude the allowlist file itself from validation

3. **Gitignore Integration**
   - SHALL respect `.gitignore` patterns by default
   - SHALL provide `--no-gitignore` flag to disable gitignore filtering
   - SHALL automatically ignore `.git/` directory
   - SHALL automatically exclude `.gitignore` file from validation

4. **File Discovery**
   - SHALL recursively scan all files in the target directory
   - SHALL exclude directories matched by gitignore patterns
   - SHALL report relative paths from the repository root

5. **Validation**
   - SHALL check each file against all allowlist patterns
   - SHALL report files that don't match any pattern
   - SHALL exit with code 0 if all files match
   - SHALL exit with code 1 if any files don't match or errors occur

6. **Output**
   - SHALL provide summary of total files, matched, and unmatched
   - SHALL list all unmatched files
   - SHALL provide `--verbose` flag for detailed output
   - SHALL display success message when all files match

### Non-Functional Requirements

1. **Performance**
   - SHALL handle repositories with thousands of files efficiently
   - SHALL use pathspec library for optimized pattern matching

2. **Usability**
   - SHALL provide clear, actionable error messages
   - SHALL support both `spec-tools lint` and standalone `spec-lint` commands
   - SHALL include helpful examples in `--help` output

3. **Reliability**
   - SHALL have comprehensive test coverage
   - SHALL handle edge cases (empty patterns, missing files, etc.)

## Design

### Architecture

```
┌─────────────────┐
│   CLI (cli.py)  │
│  - Argument     │
│    parsing      │
│  - Subcommands  │
└────────┬────────┘
         │
         v
┌─────────────────────────┐
│  SpecLinter (linter.py) │
│  - Pattern loading      │
│  - File discovery       │
│  - Validation logic     │
└─────────┬───────────────┘
          │
          v
┌─────────────────────────┐
│  pathspec library       │
│  - GitWildMatchPattern  │
│  - PathSpec matching    │
└─────────────────────────┘
```

### Core Components

#### 1. SpecLinter Class

**Responsibilities**:
- Load patterns from allowlist and gitignore files
- Compile patterns into PathSpec objects
- Discover all files in repository
- Validate files against patterns
- Return structured results

**Key Methods**:
- `__init__(root_dir, allowlist_file, use_gitignore)`: Initialize linter
- `load_patterns()`: Read and parse pattern files
- `compile_specs()`: Compile patterns into PathSpec objects
- `get_all_files()`: Recursively discover files
- `lint()`: Run validation and return LintResult

#### 2. LintResult Dataclass

**Fields**:
- `total_files`: Number of files checked
- `matched_files`: Number of files matching patterns
- `unmatched_files`: List of files not matching any pattern
- `ignored_files`: Number of files ignored (informational)

**Properties**:
- `is_valid`: Returns True if all files matched

**Methods**:
- `__str__()`: Human-readable summary

#### 3. CLI Interface

**Command Structure**:
```
spec-tools lint [directory] [options]
```

**Arguments**:
- `directory`: Directory to lint (default: current directory)
- `--allowlist, -a`: Custom allowlist filename
- `--no-gitignore`: Disable gitignore filtering
- `--verbose, -v`: Verbose output
- `--version`: Show version

### Pattern Processing

1. **Loading**: Read files line by line
2. **Comment Stripping**: Remove `#` comments (line and inline)
3. **Normalization**: Strip whitespace
4. **Compilation**: Convert to PathSpec via GitWildMatchPattern
5. **Matching**: Apply PathSpec.match_file() to each file path

### File Exclusion Rules

Files are excluded from validation if:
1. Path matches a gitignore pattern (when enabled)
2. Path is `.git/` or within `.git/`
3. Filename is `.specallowlist` or matches allowlist filename
4. Filename is `.gitignore`

## Implementation Details

### Dependencies

- **pathspec** (>=0.11.0): Gitignore-style pattern matching
- **pytest** (>=7.0.0): Testing framework (dev)
- **ruff** (>=0.1.0): Linting and formatting (dev)

### File Structure

```
spec_tools/
├── __init__.py          # Package initialization, exports
├── __main__.py          # Entry point for python -m spec_tools
├── cli.py               # CLI with argparse, subcommands
└── linter.py            # SpecLinter class, LintResult
```

### Error Handling

1. **Missing Allowlist**: FileNotFoundError with helpful message
2. **Empty Allowlist**: ValueError suggesting to add patterns
3. **Invalid Directory**: Handled by Path operations
4. **Pattern Errors**: Caught from pathspec library

## Testing

### Test Coverage

14 test cases covering:

1. **Basic Functionality**
   - Simple allowlist matching
   - All files matched scenario
   - Directory patterns
   - Character class patterns

2. **Gitignore Integration**
   - Gitignore respected
   - Gitignore disabled
   - .git directory ignored

3. **Comment Handling**
   - Line comments ignored
   - Inline comments stripped

4. **Edge Cases**
   - Missing allowlist file
   - Empty allowlist
   - Custom allowlist name
   - Nested directories
   - Allowlist file excluded from check

5. **Output**
   - Result string representation

### Test Strategy

- Use `tmp_path` fixtures for isolated file systems
- Test both positive and negative cases
- Verify error messages are helpful
- Check exit codes

## Usage Examples

### Basic Usage

```bash
# Lint current directory
spec-tools lint

# Lint specific directory
spec-tools lint /path/to/project

# Use custom allowlist
spec-tools lint --allowlist .myallowlist

# Disable gitignore
spec-tools lint --no-gitignore

# Verbose output
spec-tools lint --verbose
```

### Example .specallowlist

```
# Documentation
*.md
docs/**/*.rst

# Source code
spec_tools/**/*.py
tests/**/*.py

# Configuration
*.toml
*.yaml
*.yml

# Specs with naming convention
specs/spec-[0-9][0-9][0-9]-*.md

# GitHub workflows
.github/workflows/*.{yml,yaml}
```

### CI/CD Integration

```yaml
# .github/workflows/ci.yml
- name: Validate file allowlist
  run: spec-tools lint --verbose
```

## Future Enhancements

Potential improvements (not in scope for v1.0):

1. **Performance**: Parallel file scanning for large repos
2. **Reporting**: JSON/SARIF output formats for tool integration
3. **Patterns**: Import patterns from other files
4. **Auto-fix**: Suggest allowlist patterns for unmatched files
5. **Hooks**: Pre-commit hook integration
6. **Watch Mode**: Continuous validation during development

## Success Metrics

1. All 14 tests passing
2. Ruff linting passes with no errors
3. Tool successfully lints itself (dogfooding)
4. CI/CD integration working
5. Clear, helpful error messages

## References

- [pathspec library](https://github.com/cpburnz/python-pathspec)
- [gitignore pattern format](https://git-scm.com/docs/gitignore#_pattern_format)
- [Spec-driven development principles](../specs/spec-000-spec-driven-development.md)
