# Jobs to be Done: Markdown Schema Validator

**Spec ID**: SPEC-002
**Version**: 1.0
**Date**: 2025-10-23
**Status**: Draft

## Overview

This document defines the high-level jobs to be done that are addressed by the Markdown Schema Validator specification ([SPEC-002](../markdown-schema-validator.md)). These jobs represent the key capabilities users need to enforce consistent structure and format in their markdown specification documents.

## Jobs

### SPEC-002/JOB-001: Discover and Parse Markdown Files

**Description:** Users need to automatically find and parse markdown files according to configured patterns, extracting their structural elements (headings, metadata, content) for validation.

**Why It Matters:** Accurate parsing of markdown structure is the foundation for all validation. The system must understand document organization before it can validate compliance with schemas.

**Related Requirements:**
- [SPEC-002/REQ-001](../markdown-schema-validator.md#req-001) - Scan directory for markdown files
- [SPEC-002/REQ-002](../markdown-schema-validator.md#req-002) - Use default schema if no config
- [SPEC-002/REQ-003](../markdown-schema-validator.md#req-003) - Support glob patterns
- [SPEC-002/REQ-004](../markdown-schema-validator.md#req-004) - Respect .gitignore
- [SPEC-002/REQ-005](../markdown-schema-validator.md#req-005) - Disable .gitignore option
- [SPEC-002/REQ-006](../markdown-schema-validator.md#req-006) - Exclude .git directory
- [SPEC-002/REQ-007](../markdown-schema-validator.md#req-007) - Parse headings, metadata, content
- [SPEC-002/REQ-008](../markdown-schema-validator.md#req-008) - Identify heading levels
- [SPEC-002/REQ-009](../markdown-schema-validator.md#req-009) - Build heading hierarchy
- [SPEC-002/REQ-010](../markdown-schema-validator.md#req-010) - Parse metadata after H1
- [SPEC-002/REQ-011](../markdown-schema-validator.md#req-011) - Parse metadata before H1
- [SPEC-002/REQ-012](../markdown-schema-validator.md#req-012) - Associate content with headings
- [SPEC-002/REQ-013](../markdown-schema-validator.md#req-013) - Preserve line numbers

**Success Criteria:**
- All markdown files matching configured patterns are discovered
- Heading hierarchy accurately reflects document structure (H1-H6)
- Metadata fields are extracted from document headers
- Body content is associated with correct parent headings
- Line numbers are tracked for accurate error reporting
- File discovery respects .gitignore when configured

### SPEC-002/JOB-002: Validate Document Metadata

**Description:** Users need to ensure all specification documents contain required metadata fields (ID, Version, Date, Status) to maintain consistent document identification and tracking.

**Why It Matters:** Metadata provides essential document identification, versioning, and status tracking. Missing metadata makes specifications harder to reference, track, and manage over time.

**Related Requirements:**
- [SPEC-002/REQ-014](../markdown-schema-validator.md#req-014) - Validate required metadata present
- [SPEC-002/REQ-015](../markdown-schema-validator.md#req-015) - Report missing metadata errors
- [SPEC-002/REQ-016](../markdown-schema-validator.md#req-016) - Configure required/optional fields
- [SPEC-002/REQ-017](../markdown-schema-validator.md#req-017) - Default required fields

**Success Criteria:**
- All required metadata fields are validated
- Missing metadata triggers clear error messages
- Required fields are configurable via schema
- Default schema requires: ID, Version, Date, Status

### SPEC-002/JOB-003: Validate Heading Structure

**Description:** Users need to enforce that specification documents follow a consistent heading structure with required sections (e.g., "Overview", "Requirements") to maintain document readability and organization.

**Why It Matters:** Consistent heading structure makes specifications predictable and easier to navigate, ensuring all necessary sections are present and properly organized.

**Related Requirements:**
- [SPEC-002/REQ-018](../markdown-schema-validator.md#req-018) - Validate required headings present
- [SPEC-002/REQ-019](../markdown-schema-validator.md#req-019) - Support exact text matching
- [SPEC-002/REQ-020](../markdown-schema-validator.md#req-020) - Support regex patterns
- [SPEC-002/REQ-021](../markdown-schema-validator.md#req-021) - Report missing headings
- [SPEC-002/REQ-022](../markdown-schema-validator.md#req-022) - Default H1 pattern requirement
- [SPEC-002/REQ-023](../markdown-schema-validator.md#req-023) - Default Overview requirement
- [SPEC-002/REQ-024](../markdown-schema-validator.md#req-024) - Default Requirements section requirement

**Success Criteria:**
- Required headings are validated using exact or pattern matching
- Missing headings trigger clear error messages
- Default schema requires: H1 matching "Specification: *", H2 "Overview", H2 "Requirements (EARS Format)"
- Schema can define both required and optional headings

### SPEC-002/JOB-004: Validate EARS Format Compliance

**Description:** Users need to ensure requirement statements follow EARS (Easy Approach to Requirements Syntax) format to maintain consistent, unambiguous requirement specification.

**Why It Matters:** EARS format ensures requirements are clear, testable, and unambiguous by using standardized patterns (unconditional, event-driven, conditional, optional, state-driven).

**Related Requirements:**
- [SPEC-002/REQ-025](../markdown-schema-validator.md#req-025) - Validate EARS format
- [SPEC-002/REQ-026](../markdown-schema-validator.md#req-026) - Identify requirement statements
- [SPEC-002/REQ-027](../markdown-schema-validator.md#req-027) - Accept unconditional format
- [SPEC-002/REQ-028](../markdown-schema-validator.md#req-028) - Accept event-driven format
- [SPEC-002/REQ-029](../markdown-schema-validator.md#req-029) - Accept conditional format
- [SPEC-002/REQ-030](../markdown-schema-validator.md#req-030) - Accept optional format
- [SPEC-002/REQ-031](../markdown-schema-validator.md#req-031) - Accept various subjects
- [SPEC-002/REQ-032](../markdown-schema-validator.md#req-032) - Report EARS violations
- [SPEC-002/REQ-033](../markdown-schema-validator.md#req-033) - Validate in configured sections
- [SPEC-002/REQ-034](../markdown-schema-validator.md#req-034) - Check enabled sections

**Success Criteria:**
- Requirement statements are validated against EARS patterns
- Supported formats: unconditional, event-driven (WHEN), conditional (IF/THEN), optional (WHERE)
- Non-compliant requirements trigger clear error messages
- EARS validation applies only to configured sections
- Various subjects are accepted (system, application, tests, etc.)

### SPEC-002/JOB-005: Configure Schema Validation

**Description:** Users need to customize validation rules through configuration files to support different document types beyond the default EARS specification schema.

**Why It Matters:** Different projects may have different documentation standards. Configuration flexibility allows the tool to adapt to various schema requirements while maintaining validation rigor.

**Related Requirements:**
- [SPEC-002/REQ-035](../markdown-schema-validator.md#req-035) - Support schema config files
- [SPEC-002/REQ-036](../markdown-schema-validator.md#req-036) - Use specified config path
- [SPEC-002/REQ-037](../markdown-schema-validator.md#req-037) - Look for .specschemaconfig
- [SPEC-002/REQ-038](../markdown-schema-validator.md#req-038) - Fall back to default schema
- [SPEC-002/REQ-039](../markdown-schema-validator.md#req-039) - Define file patterns
- [SPEC-002/REQ-040](../markdown-schema-validator.md#req-040) - Define metadata fields
- [SPEC-002/REQ-041](../markdown-schema-validator.md#req-041) - Define heading requirements
- [SPEC-002/REQ-042](../markdown-schema-validator.md#req-042) - Define EARS settings

**Success Criteria:**
- Schema configuration can be loaded from custom file
- Configuration specifies: file patterns, metadata fields, headings, EARS settings
- Built-in default schema validates EARS specifications
- Missing configuration falls back to sensible defaults

### SPEC-002/JOB-006: Provide Command-Line Interface

**Description:** Users need a command-line interface to run validation, configure options, and integrate the tool into CI/CD pipelines.

**Why It Matters:** CLI access enables developers to validate locally and integrate validation into automated workflows for continuous quality enforcement.

**Related Requirements:**
- [SPEC-002/REQ-043](../markdown-schema-validator.md#req-043) - Root directory option
- [SPEC-002/REQ-044](../markdown-schema-validator.md#req-044) - Default to current directory
- [SPEC-002/REQ-045](../markdown-schema-validator.md#req-045) - Config file option
- [SPEC-002/REQ-046](../markdown-schema-validator.md#req-046) - Verbose option
- [SPEC-002/REQ-047](../markdown-schema-validator.md#req-047) - No-gitignore option

**Success Criteria:**
- Command accepts root directory specification
- Configuration file path is customizable
- Verbose mode provides detailed output
- Gitignore handling can be disabled
- Sensible defaults minimize required options

### SPEC-002/JOB-007: Report Validation Results

**Description:** Users need clear reporting of validation results including file counts, violation details, and appropriate exit codes for automation.

**Why It Matters:** Effective reporting enables quick identification of issues, while proper exit codes allow CI/CD pipelines to enforce validation requirements automatically.

**Related Requirements:**
- [SPEC-002/REQ-048](../markdown-schema-validator.md#req-048) - Report files checked
- [SPEC-002/REQ-049](../markdown-schema-validator.md#req-049) - Report valid/invalid counts
- [SPEC-002/REQ-050](../markdown-schema-validator.md#req-050) - Report violation counts
- [SPEC-002/REQ-051](../markdown-schema-validator.md#req-051) - List violation details
- [SPEC-002/REQ-052](../markdown-schema-validator.md#req-052) - Verbose mode details
- [SPEC-002/REQ-053](../markdown-schema-validator.md#req-053) - Quiet mode summary
- [SPEC-002/REQ-054](../markdown-schema-validator.md#req-054) - Exit 0 on success
- [SPEC-002/REQ-055](../markdown-schema-validator.md#req-055) - Exit 1 on failures
- [SPEC-002/REQ-056](../markdown-schema-validator.md#req-056) - Handle file read errors
- [SPEC-002/REQ-057](../markdown-schema-validator.md#req-057) - Handle config load errors
- [SPEC-002/REQ-058](../markdown-schema-validator.md#req-058) - Report unexpected errors
- [SPEC-002/REQ-059](../markdown-schema-validator.md#req-059) - Include stack traces in verbose

**Success Criteria:**
- Summary shows files checked and validation results
- Violations include file path, line number, severity, and message
- Exit codes enable CI/CD integration (0=success, 1=failure)
- Verbose mode provides detailed debugging information
- Errors are handled gracefully without data loss
