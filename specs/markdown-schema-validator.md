# Specification: Markdown Schema Validator

**ID**: SPEC-002
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

This specification defines the requirements for a markdown schema validator tool that validates markdown files against a defined structural schema, ensuring documents conform to required heading hierarchies, metadata fields, and content format patterns such as EARS (Easy Approach to Requirements Syntax).

## Requirements (EARS Format)

### File Discovery

**REQ-001**  The system shall scan the specified directory to find markdown files matching configured path patterns.

**REQ-002**  WHEN no configuration file is present, the system shall use a default schema that validates files matching the pattern `specs/*.md`.

**REQ-003**  The system shall support gitignore-style glob patterns for file matching (e.g., `specs/*.md`, `docs/**/*.md`).

**REQ-004**  The system shall respect `.gitignore` patterns when discovering markdown files.

**REQ-005**  The system shall accept a command-line option to disable `.gitignore` pattern matching.

**REQ-006**  The system shall always exclude files within the `.git` directory from validation.

### Markdown Parsing

**REQ-007**  The system shall parse markdown files to extract headings, metadata fields, and body content.

**REQ-008**  WHEN parsing headings, the system shall identify heading level (H1 through H6) and text content.

**REQ-009**  The system shall construct a hierarchical tree of headings based on their levels.

**REQ-010**  The system shall parse metadata fields in the format `**Key**: Value` appearing after the H1 heading.

**REQ-011**  The system shall also support metadata fields appearing before the first heading.

**REQ-012**  The system shall associate body content lines with their parent heading.

**REQ-013**  The system shall preserve line numbers for all parsed elements to enable accurate error reporting.

### Metadata Validation

**REQ-014**  The system shall validate that all required metadata fields are present in markdown files.

**REQ-015**  WHEN a required metadata field is missing, the system shall report a violation with severity "error".

**REQ-016**  The system shall support configuration of required and optional metadata fields.

**REQ-017**  WHEN using the default schema, the system shall require the following metadata fields: ID, Version, Date, and Status.

### Heading Structure Validation

**REQ-018**  The system shall validate that all required headings are present in markdown files.

**REQ-019**  The system shall support exact text matching for required headings (e.g., "Overview").

**REQ-020**  The system shall support regex pattern matching for required headings (e.g., `^Specification:\s+.+$`).

**REQ-021**  WHEN a required heading is missing, the system shall report a violation with severity "error".

**REQ-022**  WHEN using the default schema, the system shall require an H1 heading matching the pattern `^Specification:\s+.+$`.

**REQ-023**  WHEN using the default schema, the system shall require an H2 heading with text "Overview".

**REQ-024**  WHEN using the default schema, the system shall require an H2 heading matching the pattern `^Requirements\s+\(EARS Format\)$`.

### EARS Format Validation

**REQ-025**  The system shall validate requirement statements follow EARS (Easy Approach to Requirements Syntax) format.

**REQ-026**  The system shall identify requirement statements by the pattern `**REQ-XXX**:`, `**NFR-XXX**:`, or `**TEST-XXX**:` where XXX is a number.

**REQ-027**  WHEN validating EARS compliance, the system shall accept unconditional requirements in the format "[Subject] shall [action]".

**REQ-028**  WHEN validating EARS compliance, the system shall accept event-driven requirements in the format "WHEN [condition], [subject] shall [action]".

**REQ-029**  WHEN validating EARS compliance, the system shall accept conditional requirements in the format "IF [condition], THEN [subject] shall [action]".

**REQ-030**  WHEN validating EARS compliance, the system shall accept optional requirements in the format "WHERE [condition], [subject] shall [action]".

**REQ-031**  The system shall accept various subjects in EARS requirements including "The system", "The application", "Unit tests", "Integration tests", and similar patterns.

**REQ-032**  WHEN a requirement statement does not follow EARS format, the system shall report a violation with severity "error".

**REQ-033**  The system shall validate EARS format only within configured sections (e.g., "Requirements (EARS Format)", "Non-Functional Requirements", "Test Coverage").

**REQ-034**  WHEN EARS validation is enabled in the schema, the system shall check all requirement statements in relevant sections.

### Schema Configuration

**REQ-035**  The system shall support loading schema configuration from a file.

**REQ-036**  WHEN a configuration file path is specified via command-line option, the system shall use that file.

**REQ-037**  WHERE no configuration file is specified, the system shall look for a `.specschemaconfig` file in the root directory.

**REQ-038**  WHERE no configuration file exists, the system shall use a built-in default schema for EARS specification files.

**REQ-039**  The schema configuration shall define file matching patterns.

**REQ-040**  The schema configuration shall define required and optional metadata fields.

**REQ-041**  The schema configuration shall define required and optional headings with text or pattern matching.

**REQ-042**  The schema configuration shall define EARS validation settings including enabled/disabled status and target sections.

### Command-Line Interface

**REQ-043**  The system shall accept a command-line option to specify the root directory to scan.

**REQ-044**  WHERE the root directory is not specified, the system shall default to the current working directory.

**REQ-045**  The system shall accept a `--config` option to specify a custom schema configuration file.

**REQ-046**  The system shall accept a `--verbose` option to enable detailed output.

**REQ-047**  The system shall accept a `--no-gitignore` option to disable `.gitignore` pattern matching.

### Reporting

**REQ-048**  WHEN validation completes, the system shall report the total number of files checked.

**REQ-049**  WHEN validation completes, the system shall report the number of valid and invalid files.

**REQ-050**  WHEN validation completes, the system shall report the total number of violations found.

**REQ-051**  WHEN violations are detected, the system shall list each violation with file path, line number, severity, and message.

**REQ-052**  WHEN verbose mode is enabled, the system shall display detailed validation results even if all files are valid.

**REQ-053**  WHEN verbose mode is disabled and all files are valid, the system shall display a summary message.

**REQ-054**  IF all files conform to the schema, THEN the system shall exit with code 0.

**REQ-055**  IF any files have schema violations, THEN the system shall exit with code 1.

### Error Handling

**REQ-056**  IF a markdown file cannot be read, THEN the system shall report a violation with severity "error" and continue processing other files.

**REQ-057**  IF a configuration file cannot be loaded, THEN the system shall report the error and exit with code 1.

**REQ-058**  WHEN unexpected errors occur, the system shall report the error to stderr.

**REQ-059**  WHEN verbose mode is enabled and unexpected errors occur, the system shall include the full stack trace.

## Default Schema Definition

The default schema (used when no configuration file is present) validates EARS specification files:

### File Patterns
```
specs/*.md
```

### Required Metadata Fields
- ID
- Version
- Date
- Status

### Required Headings
1. H1: Pattern `^Specification:\s+.+$`
2. H2: Text "Overview"
3. H2: Pattern `^Requirements\s+\(EARS Format\)$`

### Optional Headings
- H2: "Configuration File Format"
- H2: "Examples"
- H2: "Non-Functional Requirements"
- H2: "Test Coverage"

### EARS Validation
- Enabled: Yes
- Target sections:
  - "Requirements (EARS Format)"
  - "Non-Functional Requirements"
  - "Test Coverage"

## Examples

### Valid Specification File

```markdown
# Specification: User Authentication

**ID**: SPEC-042
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

This specification defines user authentication requirements.

## Requirements (EARS Format)

### Authentication

**REQ-901**: The system shall authenticate users via username and password.

**REQ-902**: WHEN a user enters invalid credentials, the system shall reject the login attempt.

**REQ-903**: IF three consecutive login attempts fail, THEN the system shall lock the account.
```

### Invalid: Missing Metadata

```markdown
# Specification: User Authentication

## Overview

Content without required metadata fields.
```

Violation: Missing required metadata fields (ID, Version, Date, Status)

### Invalid: Wrong H1 Format

```markdown
# User Authentication

**ID**: SPEC-042
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

Content here.
```

Violation: H1 heading does not match pattern `^Specification:\s+.+$`

### Invalid: Non-EARS Requirement

```markdown
# Specification: User Authentication

**ID**: SPEC-042
**Version**: 1.0
**Date**: 2025-10-22
**Status**: Draft

## Overview

Content here.

## Requirements (EARS Format)

**REQ-904**: The system authenticates users.
```

Violation: Requirement does not follow EARS format (missing "shall")

## Non-Functional Requirements

**NFR-001**: The system shall process markdown files at a rate of at least 50 files per second.

**NFR-002**: The system shall provide clear, actionable error messages for all validation failures.

**NFR-003**: The system shall have minimal dependencies, reusing existing pathspec library from other linters.

## Test Coverage

**TEST-001**: Unit tests shall cover markdown parsing including headings, metadata, and body content.

**TEST-002**: Unit tests shall cover metadata validation for required and optional fields.

**TEST-003**: Unit tests shall cover heading structure validation with exact and pattern matching.

**TEST-004**: Unit tests shall cover EARS format validation for all requirement types.

**TEST-005**: Unit tests shall cover file discovery with gitignore patterns enabled and disabled.

**TEST-006**: Unit tests shall cover validation of multiple files with mixed valid and invalid results.

**TEST-007**: Integration tests shall validate the tool against real specification files.
