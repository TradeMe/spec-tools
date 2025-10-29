# Specification: Markdown Link Validator

**ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

This specification defines the requirements for a markdown link validator tool that validates hyperlinks in markdown files, ensuring internal links resolve correctly and external links are accessible.

## Requirements (EARS Format)

### Link Discovery

**REQ-001**  The system shall parse all markdown files in the specified directory to extract hyperlinks.

**REQ-002**  WHEN parsing markdown files, the system shall identify links in the format `[text](url)`.

**REQ-003**  WHEN parsing markdown files, the system shall identify reference-style links in the format `[text][ref]` and `[ref]: url`.

**REQ-004**  The system shall extract the following link components: link text, URL/path, and optional anchor fragment.

### Internal Link Validation

**REQ-005**  WHEN a link uses a relative path (e.g., `./file.md`, `../dir/file.md`, `file.md`), the system shall resolve the path relative to the markdown file containing the link.

**REQ-006**  WHEN validating an internal link, the system shall check if the target file exists in the filesystem.

**REQ-007**  IF an internal link target does not exist, THEN the system shall report the link as invalid.

**REQ-008**  WHEN an internal link includes an anchor fragment (e.g., `file.md#heading`), the system shall validate both the file existence and the anchor target.

**REQ-009**  WHEN validating an anchor-only link (e.g., `#heading`), the system shall check if the anchor exists in the current markdown file.

**REQ-010**  WHEN checking anchor targets, the system shall convert markdown headings to anchor IDs following the same rules as standard markdown renderers (lowercase, spaces to hyphens, special characters removed).

### External URL Validation

**REQ-011**  WHEN a link uses an HTTP or HTTPS scheme, the system shall classify it as an external URL.

**REQ-012**  WHEN validating an external URL, the system shall send an HTTP request to verify the URL is accessible.

**REQ-013**  IF an external URL returns an HTTP status code in the 2xx or 3xx range, THEN the system shall consider the link valid.

**REQ-014**  IF an external URL returns an HTTP status code in the 4xx or 5xx range, THEN the system shall report the link as invalid.

**REQ-015**  IF an external URL request times out or fails to connect, THEN the system shall report the link as invalid.

### Private URL Handling

**REQ-016**  The system shall support a configuration mechanism to specify private URI domains and prefixes.

**REQ-017**  WHEN a link matches a configured private domain or prefix, the system shall mark it as private and skip validation.

**REQ-018**  WHEN reporting results, the system shall separately count private links that were not validated.

**REQ-019**  The system shall read private domain/prefix configuration from a `.speclinkconfig` file in the root directory.

**REQ-020**  WHERE a `.speclinkconfig` file is not present, the system shall proceed with no private domains configured.

**REQ-021**  The system shall support both domain patterns (e.g., `internal.company.com`) and URI prefixes (e.g., `https://internal.company.com/`, `http://localhost:`).

### Configuration

**REQ-022**  The system shall accept a command-line option to specify a custom configuration file path.

**REQ-023**  The system shall accept a command-line option to set the timeout for external URL validation (in seconds).

**REQ-024**  The system shall accept a command-line option to disable external URL validation entirely.

**REQ-025**  The system shall accept a command-line option to specify the root directory to scan.

**REQ-026**  WHERE the root directory is not specified, the system shall default to the current working directory.

**REQ-027**  The system shall respect `.gitignore` patterns when discovering markdown files.

**REQ-028**  The system shall accept a command-line option to disable `.gitignore` pattern matching.

### Reporting

**REQ-029**  WHEN validation completes, the system shall report the total number of links checked.

**REQ-030**  WHEN validation completes, the system shall report the number of valid links, invalid links, and private links.

**REQ-031**  WHEN validation completes, the system shall list all invalid links with their source file and line number.

**REQ-032**  WHEN the verbose option is enabled, the system shall report all links checked, including valid ones.

**REQ-033**  IF all links are valid or private, THEN the system shall exit with code 0.

**REQ-034**  IF any links are invalid, THEN the system shall exit with code 1.

### Error Handling

**REQ-035**  IF a markdown file cannot be read, THEN the system shall report the error and continue processing other files.

**REQ-036**  IF the configuration file cannot be parsed, THEN the system shall report the error and exit with code 1.

**REQ-037**  WHEN network errors occur during external URL validation, the system shall retry the request up to 2 additional times before marking the link as invalid.

### Performance

**REQ-038**  The system shall validate external URLs concurrently to improve performance.

**REQ-039**  The system shall limit concurrent external URL requests to prevent overwhelming network resources.

**REQ-040**  The system shall use a default timeout of 10 seconds for external URL validation.

## Configuration File Format

The `.speclinkconfig` file shall use the following YAML format:

```yaml
# Private domains and URI prefixes to skip validation
private_urls:
  # Domain patterns
  - internal.company.com
  - localhost

  # URI prefixes
  - https://private.example.com/
  - http://localhost:
  - http://127.0.0.1:

# Optional: timeout for external URL validation (seconds)
timeout: 10

# Optional: maximum concurrent requests
max_concurrent: 10
```

## Examples

### Valid Internal Link
```markdown
<!-- In docs/guide.md -->
See [installation](./installation.md) for setup instructions.
```
Validation: Check if `docs/installation.md` exists.

### Valid Anchor Link
```markdown
<!-- In docs/guide.md -->
Jump to [configuration section](#configuration).
```
Validation: Check if heading `## Configuration` exists in `docs/guide.md`.

### Valid Cross-File Anchor
```markdown
<!-- In docs/guide.md -->
See [API reference](../api/reference.md#authentication).
```
Validation: Check if `api/reference.md` exists and contains heading `## Authentication`.

### Private URL
```markdown
See [internal docs](https://internal.company.com/docs).
```
With `internal.company.com` in private_urls config, this link is marked as private and not validated.

### External URL
```markdown
Learn more at [Python.org](https://www.python.org/).
```
Validation: Send HTTP request to verify the URL is accessible.

## Non-Functional Requirements

**NFR-001**: The system shall process markdown files at a rate of at least 100 files per second (excluding network I/O).

**NFR-002**: The system shall have minimal dependencies, adding no more than 2 new required packages.

**NFR-003**: The system shall provide clear, actionable error messages for all validation failures.

## Test Coverage

**TEST-001**: Unit tests shall cover all link parsing scenarios (inline, reference-style, with anchors).

**TEST-002**: Unit tests shall cover internal link validation with various relative path formats.

**TEST-003**: Unit tests shall cover anchor validation in both same-file and cross-file scenarios.

**TEST-004**: Unit tests shall cover external URL validation with mocked HTTP responses.

**TEST-005**: Unit tests shall cover private URL detection and skipping.

**TEST-006**: Integration tests shall validate the tool against a sample repository with known link issues.
