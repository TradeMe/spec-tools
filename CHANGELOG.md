# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.2] - 2025-10-28

### Fixed
- Added missing `validate_count()` and `parse_cardinality()` methods to `Reference` model (#28)
- Fixed DSL validator to use `target_type` instead of non-existent `target_module`/`target_class` attributes

## [0.1.1] - 2025-10-28

### Fixed
- Release workflow now automatically publishes to PyPI in the same workflow
- Added `pull-requests: write` permission to enable PR commenting
- Eliminated manual intervention requirement for PyPI publishing
- Fixed AttributeError in DSL validator where `section_def.level` was incorrectly used instead of `section_def.heading_level` (#25)

### Changed
- Merged release creation and PyPI publishing into single workflow for reliability
- Improved PR comments to show publishing status

## [0.1.0] - 2025-10-28

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
- File allowlist linter (`spec-check lint`)
  - Validates all files match gitignore-style patterns
  - Respects `.gitignore` by default
  - Supports complex patterns including character classes
- Markdown link validator (`spec-check check-links`)
  - Validates internal links and anchors
  - Checks external URLs for accessibility
  - Supports private URL patterns
  - Concurrent external URL checking
- Spec coverage validator (`spec-check check-coverage`)
  - Extracts requirements from spec files
  - Validates test coverage using pytest markers
  - Reports coverage percentage and uncovered requirements
- Structure validator (`spec-check check-structure`)
  - Enforces consistent spec-to-test structure alignment
  - Supports flexible naming conventions
  - Allows unit tests without corresponding specs
- Unique spec ID validator (`spec-check check-unique-specs`)
  - Validates spec IDs are unique across files
  - Validates requirement IDs are unique within specs
- Markdown schema validator (`spec-check check-schema`)
  - Validates markdown files against configurable schemas
  - Supports EARS requirement validation
  - Configurable metadata and heading requirements
- Configuration via `pyproject.toml`
- CLI with comprehensive help text
- Support for Python 3.10, 3.11, 3.12, 3.13

### Changed
- Development status updated to Alpha
- Added flit as dev dependency for building distributions

[Unreleased]: https://github.com/TradeMe/spec-check/compare/v0.1.2...HEAD
[0.1.2]: https://github.com/TradeMe/spec-check/compare/v0.1.1...v0.1.2
[0.1.1]: https://github.com/TradeMe/spec-check/compare/v0.1.0...v0.1.1
[0.1.0]: https://github.com/TradeMe/spec-check/releases/tag/v0.1.0
