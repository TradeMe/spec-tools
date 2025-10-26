# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- PyPI publishing configuration with automated workflows
- Comprehensive PyPI metadata (keywords, classifiers, project URLs)
- GitHub Actions workflow for automated PyPI publishing using trusted publishing (OIDC)
- TestPyPI publishing support for testing releases
- PUBLISHING.md with detailed publishing guide
- CHANGELOG.md following Keep a Changelog format
- Version check workflow to prevent unauthorized version changes
- Automated TestPyPI publishing for PRs
- Pre-release publishing support

### Changed
- Development status updated to Alpha
- Added flit as dev dependency for building distributions

## [0.1.0] - Initial Release

### Added
- File allowlist linter (`spec-tools lint`)
  - Validates all files match gitignore-style patterns
  - Respects `.gitignore` by default
  - Supports complex patterns including character classes
- Markdown link validator (`spec-tools check-links`)
  - Validates internal links and anchors
  - Checks external URLs for accessibility
  - Supports private URL patterns
  - Concurrent external URL checking
- Spec coverage validator (`spec-tools check-coverage`)
  - Extracts requirements from spec files
  - Validates test coverage using pytest markers
  - Reports coverage percentage and uncovered requirements
- Structure validator (`spec-tools check-structure`)
  - Enforces consistent spec-to-test structure alignment
  - Supports flexible naming conventions
  - Allows unit tests without corresponding specs
- Unique spec ID validator (`spec-tools check-unique-specs`)
  - Validates spec IDs are unique across files
  - Validates requirement IDs are unique within specs
- Markdown schema validator (`spec-tools check-schema`)
  - Validates markdown files against configurable schemas
  - Supports EARS requirement validation
  - Configurable metadata and heading requirements
- Configuration via `pyproject.toml`
- CLI with comprehensive help text
- Support for Python 3.10, 3.11, 3.12, 3.13

[Unreleased]: https://github.com/TradeMe/spec-tools/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/TradeMe/spec-tools/releases/tag/v0.1.0
