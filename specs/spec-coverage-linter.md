# Specification: Spec Coverage Linter

**ID**: SPEC-003
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

This specification defines the requirements for a spec coverage linter tool that validates test-to-requirement traceability by ensuring all specification requirements have corresponding test cases.

## Requirements (EARS Format)

### Requirement Extraction

**REQ-001**: The system shall scan the specs directory to find all markdown files containing requirement definitions.

**REQ-002**: The system shall extract requirement IDs from spec files using the pattern `**REQ-XXX**:`, `**NFR-XXX**:`, or `**TEST-XXX**:` where XXX is a three-digit number.

**REQ-003**: The system shall support custom requirement ID prefixes beyond REQ, NFR, and TEST.

### Test Discovery

**REQ-004**: The system shall scan the tests directory to find all Python test files matching the pattern `test_*.py`.

**REQ-005**: The system shall parse test files using AST to extract test function definitions.

**REQ-006**: The system shall identify test functions by the naming pattern starting with `test_`.

**REQ-007**: The system shall extract requirement markers from test decorators in the format `@pytest.mark.req("REQ-XXX")`.

**REQ-008**: The system shall support test functions with multiple requirement markers.

**REQ-009**: WHEN a test function is defined within a class, the system shall construct the full test name as `ClassName::test_function_name`.

### Coverage Analysis

**REQ-010**: The system shall create a mapping from requirement IDs to test names that cover them.

**REQ-011**: The system shall identify all requirements that have no corresponding test coverage.

**REQ-012**: The system shall calculate the coverage percentage as (covered requirements / total requirements) × 100.

**REQ-013**: The system shall identify all test functions that have no requirement markers.

### Configuration

**REQ-014**: The system shall support loading configuration from `pyproject.toml` under the section `[tool.spec-tools.check-coverage]`.

**REQ-015**: The system shall accept a `min_coverage` configuration option to specify the minimum acceptable coverage percentage.

**REQ-016**: WHERE no `min_coverage` is configured, the system shall default to requiring 100% coverage.

**REQ-017**: The system shall accept `min_coverage` values from 0 to 100 representing the percentage threshold.

**REQ-018**: WHEN coverage percentage is greater than or equal to `min_coverage`, the system shall report validation as passed.

**REQ-019**: WHEN coverage percentage is less than `min_coverage`, the system shall report validation as failed.

### Command-Line Interface

**REQ-020**: The system shall accept a command-line option to specify the root directory to scan.

**REQ-021**: WHERE the root directory is not specified, the system shall default to the current working directory.

**REQ-022**: The system shall accept a `--specs-dir` option to specify a custom specs directory.

**REQ-023**: WHERE specs directory is not specified, the system shall default to `<root-dir>/specs`.

**REQ-024**: The system shall accept a `--tests-dir` option to specify a custom tests directory.

**REQ-025**: WHERE tests directory is not specified, the system shall default to `<root-dir>/tests`.

**REQ-026**: The system shall accept a `--verbose` option to enable detailed output.

**REQ-027**: The system shall accept a `--min-coverage` option to override the configured minimum coverage percentage.

**REQ-028**: WHEN both pyproject.toml configuration and command-line option are provided, the system shall use the command-line option value.

### Reporting

**REQ-029**: The system shall display a coverage report showing the coverage percentage.

**REQ-030**: The system shall display the number of covered requirements out of total requirements.

**REQ-031**: The system shall display the number of tests linked to requirements out of total tests.

**REQ-032**: WHEN uncovered requirements exist, the system shall list each uncovered requirement ID.

**REQ-033**: WHEN tests without requirement markers exist, the system shall list each test name.

**REQ-034**: The system shall display a validation status indicating whether coverage meets the minimum threshold.

**REQ-035**: IF coverage meets or exceeds the minimum threshold, THEN the system shall exit with code 0.

**REQ-036**: IF coverage is below the minimum threshold, THEN the system shall exit with code 1.

### Error Handling

**REQ-037**: IF a spec file cannot be read, THEN the system shall print a warning and continue processing other files.

**REQ-038**: IF a test file cannot be parsed, THEN the system shall print a warning and continue processing other files.

**REQ-039**: WHEN unexpected errors occur, the system shall report the error to stderr.

**REQ-040**: WHEN verbose mode is enabled and unexpected errors occur, the system shall include the full stack trace.

## Configuration File Format

The spec coverage linter supports configuration via `pyproject.toml`:

```toml
[tool.spec-tools.check-coverage]
min_coverage = 88.4  # Minimum acceptable coverage percentage (0-100)
```

### Configuration Options

- `min_coverage` (float, default: 100.0): Minimum acceptable coverage percentage
  - Valid range: 0.0 to 100.0
  - Validation passes when coverage >= min_coverage
  - Can be overridden via `--min-coverage` command-line option

## Examples

### Running with Default 100% Coverage

```bash
spec-tools check-coverage
```

Expected output when coverage is below 100%:
```
============================================================
SPEC COVERAGE REPORT
============================================================
Coverage: 88.4%
Requirements: 61/69 covered
Tests: 65/119 linked to requirements

❌ Uncovered Requirements:
  - NFR-001
  - REQ-036
  - REQ-037

❌ Spec coverage validation FAILED
============================================================
```

Exit code: 1

### Running with Configured Minimum Coverage

With `pyproject.toml`:
```toml
[tool.spec-tools.check-coverage]
min_coverage = 85.0
```

```bash
spec-tools check-coverage
```

Expected output:
```
============================================================
SPEC COVERAGE REPORT
============================================================
Coverage: 88.4%
Requirements: 61/69 covered
Tests: 65/119 linked to requirements

✅ Spec coverage validation PASSED
============================================================
```

Exit code: 0

### Overriding via Command Line

```bash
spec-tools check-coverage --min-coverage 90.0
```

This overrides any pyproject.toml configuration.

## Non-Functional Requirements

**NFR-001**: The system shall parse test files efficiently using AST without executing them.

**NFR-002**: The system shall provide clear, actionable reports identifying which requirements lack coverage.

**NFR-003**: The system shall support gradual coverage improvement by allowing configurable thresholds.

## Test Coverage

**TEST-001**: Unit tests shall cover requirement extraction from spec files with various ID formats.

**TEST-002**: Unit tests shall cover test function discovery and requirement marker extraction.

**TEST-003**: Unit tests shall cover coverage calculation with full, partial, and zero coverage scenarios.

**TEST-004**: Unit tests shall cover configuration loading from pyproject.toml.

**TEST-005**: Unit tests shall cover command-line argument parsing and precedence.

**TEST-006**: Unit tests shall cover validation logic with various threshold values.

**TEST-007**: Integration tests shall validate the tool against real spec and test files.
