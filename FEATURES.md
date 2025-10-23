# Spec-Tools Features and Roadmap

This document tracks implemented features and planned milestones for the spec-tools project.

## Released Features

### Release 0.1.0 (Current)

#### File Allowlist Validation (`lint`)
- **Command**: `spec-tools lint`
- **Specification**: N/A (core utility)
- **Description**: Validates that all files in a repository match patterns in an allowlist
- **Key Features**:
  - Gitignore-style glob pattern matching
  - Supports character classes and ranges
  - Respects `.gitignore` by default
  - Configuration via `.specallowlist` or `pyproject.toml`

#### Markdown Link Validation (`check-links`)
- **Command**: `spec-tools check-links`
- **Specification**: SPEC-001 (40 requirements)
- **Description**: Validates hyperlinks in markdown files
- **Key Features**:
  - Internal link validation (relative paths)
  - Anchor link validation (heading references)
  - External URL validation with HTTP requests
  - Private URL pattern exclusion
  - Concurrent URL checking
  - Configuration via `.speclinkconfig` or `pyproject.toml`

#### Spec-to-Test Coverage Validation (`check-coverage`)
- **Command**: `spec-tools check-coverage`
- **Specification**: N/A (core utility)
- **Description**: Ensures 100% traceability between specifications and tests
- **Key Features**:
  - Extracts requirement IDs from spec files (REQ-XXX, NFR-XXX, TEST-XXX)
  - Finds pytest markers in test files (`@pytest.mark.req()`)
  - Reports coverage percentage
  - Identifies uncovered requirements
  - Lists tests without requirement markers

#### Spec-to-Test Structure Validation (`check-structure`)
- **Command**: `spec-tools check-structure`
- **Specification**: N/A (core utility)
- **Description**: Enforces consistent spec-to-test file structure alignment
- **Key Features**:
  - Verifies each spec file has corresponding test file or directory
  - Supports kebab-case to snake_case naming conversion
  - Allows unit tests without corresponding specs
  - Reports specs without tests and orphaned test files
  - Configuration via `pyproject.toml`

#### Markdown Schema Validation (`check-schema`)
- **Command**: `spec-tools check-schema`
- **Specification**: SPEC-002 (59 requirements)
- **Description**: Validates markdown files against a defined structural schema
- **Key Features**:
  - Metadata field validation (ID, Version, Date, Status)
  - Heading structure and hierarchy validation
  - EARS (Easy Approach to Requirements Syntax) format compliance
  - Requirement pattern matching
  - Supports exact text and regex pattern matching
  - Configuration via `.specschemaconfig` or `pyproject.toml`

## Planned Milestones

### Milestone 001: Semantic Test Adherence

**Status**: Future
**Target**: TBD

#### Semantic Test-Adherence Check (`check-semantic-test-adherence`)
- **Command**: `spec-tools check-semantic-test-adherence`
- **Specification**: SPEC-003 (planned)
- **Description**: Validates that tests marked with requirement IDs actually test the behavior specified in those requirements
- **Key Features** (planned):
  - Semantic analysis of requirement text vs. test implementation
  - AI/LLM-powered understanding of requirement intent
  - Detection of mismatched test-requirement pairs
  - Confidence scoring for test-requirement alignment
  - Support for multiple semantic validation strategies
  - Configuration for semantic analysis parameters
  - Integration with existing requirement markers (`@pytest.mark.req()`)
  - Reporting of semantic mismatches with explanations

**Rationale**: While `check-coverage` ensures every requirement has tests, it cannot verify that the tests actually validate the specified behavior. This semantic check fills that gap by analyzing whether the test logic aligns with the requirement semantics.

**Use Cases**:
- Detect when requirements evolve but tests don't update accordingly
- Identify tests that verify the wrong behavior despite correct markers
- Improve requirement-test quality beyond simple traceability
- Provide AI-assisted code review for requirement compliance

### Future Roadmap (Unscheduled)

The following features are documented in README.md but not yet assigned to milestones:

- **`spec-graph`**: Visualize dependencies between spec files
- **`spec-init`**: Initialize new spec-driven projects with templates
- **`spec-sync`**: Keep specs in sync with implementation (bidirectional)
- **`spec-extract`**: Extract requirements from code comments

## Milestone Naming Convention

Milestones follow the format: `milestone-XXX-short-description`

- **XXX**: Three-digit milestone number (001, 002, etc.)
- **short-description**: Brief kebab-case description of milestone focus

## Versioning Strategy

This project follows [Semantic Versioning](https://semver.org/):

- **Major version** (X.0.0): Breaking changes to CLI or API
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

**Current version**: 0.1.0 (initial release)

## Contributing to Roadmap

To propose new features or milestones:

1. Open a GitHub issue with the `enhancement` label
2. Describe the feature, use cases, and rationale
3. Discuss implementation approach and requirements
4. If approved, create a specification file (SPEC-XXX)
5. Update this FEATURES.md to reflect the new milestone

## Status Definitions

- **Released**: Feature is implemented, tested, and available in a tagged release
- **In Progress**: Feature is actively being developed
- **Future**: Feature is planned but not yet in active development
- **Deferred**: Feature is planned but postponed to later milestones
- **Cancelled**: Feature was planned but is no longer being pursued
