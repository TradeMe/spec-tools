# Jobs to be Done: Markdown Link Validator

**Spec ID**: SPEC-001
**Version**: 1.0
**Date**: 2025-10-23
**Status**: Draft

## Overview

This document defines the high-level jobs to be done that are addressed by the Markdown Link Validator specification ([SPEC-001](../markdown-link-validator.md)). These jobs represent the key capabilities users need to ensure their markdown documentation has valid, working hyperlinks.

## Jobs

### SPEC-001/JOB-001: Discover and Parse Links from Markdown Files

**Description:** Users need to automatically extract all hyperlinks from markdown files to identify what needs to be validated, supporting both inline and reference-style link formats.

**Why It Matters:** Before validating links, the system must accurately find and parse all link types in markdown to ensure comprehensive coverage.

**Related Requirements:**
- [SPEC-001/REQ-001](../markdown-link-validator.md#req-001) - Parse all markdown files
- [SPEC-001/REQ-002](../markdown-link-validator.md#req-002) - Identify inline links
- [SPEC-001/REQ-003](../markdown-link-validator.md#req-003) - Identify reference-style links
- [SPEC-001/REQ-004](../markdown-link-validator.md#req-004) - Extract link components

**Success Criteria:**
- All inline `[text](url)` links are discovered
- All reference-style `[text][ref]` and `[ref]: url` links are discovered
- Link text, URL/path, and anchor fragments are correctly extracted
- Link discovery works across all markdown files in the project

### SPEC-001/JOB-002: Validate Internal File and Anchor Links

**Description:** Users need to verify that all relative links to internal files and heading anchors resolve correctly, preventing broken navigation within documentation.

**Why It Matters:** Broken internal links frustrate users navigating documentation and indicate structural problems in the documentation organization.

**Related Requirements:**
- [SPEC-001/REQ-005](../markdown-link-validator.md#req-005) - Resolve relative paths
- [SPEC-001/REQ-006](../markdown-link-validator.md#req-006) - Check file existence
- [SPEC-001/REQ-007](../markdown-link-validator.md#req-007) - Report missing files
- [SPEC-001/REQ-008](../markdown-link-validator.md#req-008) - Validate file and anchor
- [SPEC-001/REQ-009](../markdown-link-validator.md#req-009) - Validate anchor-only links
- [SPEC-001/REQ-010](../markdown-link-validator.md#req-010) - Convert headings to anchor IDs

**Success Criteria:**
- All relative file paths resolve correctly from their source location
- File existence is verified for all internal links
- Anchor fragments are validated against actual headings
- Markdown heading-to-anchor conversion matches standard renderer behavior
- Clear error messages identify broken internal links with file and line number

### SPEC-001/JOB-003: Validate External URL Accessibility

**Description:** Users need to verify that external HTTP/HTTPS URLs are accessible and return valid responses, ensuring references to external resources are current.

**Why It Matters:** External links can break over time as websites change or go offline, creating poor user experience and reducing documentation credibility.

**Related Requirements:**
- [SPEC-001/REQ-011](../markdown-link-validator.md#req-011) - Classify external URLs
- [SPEC-001/REQ-012](../markdown-link-validator.md#req-012) - Send HTTP requests
- [SPEC-001/REQ-013](../markdown-link-validator.md#req-013) - Accept 2xx/3xx responses
- [SPEC-001/REQ-014](../markdown-link-validator.md#req-014) - Report 4xx/5xx errors
- [SPEC-001/REQ-015](../markdown-link-validator.md#req-015) - Report timeouts/failures
- [SPEC-001/REQ-037](../markdown-link-validator.md#req-037) - Retry failed requests
- [SPEC-001/REQ-038](../markdown-link-validator.md#req-038) - Concurrent validation
- [SPEC-001/REQ-039](../markdown-link-validator.md#req-039) - Limit concurrency
- [SPEC-001/REQ-040](../markdown-link-validator.md#req-040) - Default timeout

**Success Criteria:**
- HTTP/HTTPS URLs are identified and validated
- Successful responses (2xx, 3xx) mark links as valid
- Error responses (4xx, 5xx) mark links as invalid
- Network failures trigger retries before marking invalid
- Concurrent validation improves performance without overwhelming network
- Configurable timeouts prevent hanging on slow URLs

### SPEC-001/JOB-004: Handle Private URLs and Configuration

**Description:** Users need to configure the tool to skip validation of private/internal URLs that are not publicly accessible, while still validating public documentation links.

**Why It Matters:** Documentation often references internal resources (intranet, localhost, private services) that cannot be validated from external CI environments but should not be flagged as errors.

**Related Requirements:**
- [SPEC-001/REQ-016](../markdown-link-validator.md#req-016) - Support private URI configuration
- [SPEC-001/REQ-017](../markdown-link-validator.md#req-017) - Skip private URL validation
- [SPEC-001/REQ-018](../markdown-link-validator.md#req-018) - Report private link counts
- [SPEC-001/REQ-019](../markdown-link-validator.md#req-019) - Read .speclinkconfig file
- [SPEC-001/REQ-020](../markdown-link-validator.md#req-020) - Handle missing config file
- [SPEC-001/REQ-021](../markdown-link-validator.md#req-021) - Support domains and prefixes
- [SPEC-001/REQ-022](../markdown-link-validator.md#req-022) - Custom config path option
- [SPEC-001/REQ-023](../markdown-link-validator.md#req-023) - Timeout configuration
- [SPEC-001/REQ-024](../markdown-link-validator.md#req-024) - Disable external validation
- [SPEC-001/REQ-025](../markdown-link-validator.md#req-025) - Root directory option
- [SPEC-001/REQ-026](../markdown-link-validator.md#req-026) - Default to current directory
- [SPEC-001/REQ-027](../markdown-link-validator.md#req-027) - Respect .gitignore
- [SPEC-001/REQ-028](../markdown-link-validator.md#req-028) - Disable .gitignore option

**Success Criteria:**
- Private URLs are identified by configured domains/prefixes
- Private URLs are skipped without validation errors
- Configuration file is optional with sensible defaults
- Command-line options override configuration file settings
- File discovery respects .gitignore when enabled

### SPEC-001/JOB-005: Report Validation Results

**Description:** Users need clear, actionable reporting of link validation results including counts, error details, and exit codes for CI integration.

**Why It Matters:** Effective reporting enables users to quickly identify and fix broken links, while proper exit codes enable automated CI/CD workflows to catch link issues.

**Related Requirements:**
- [SPEC-001/REQ-029](../markdown-link-validator.md#req-029) - Report total links checked
- [SPEC-001/REQ-030](../markdown-link-validator.md#req-030) - Report valid/invalid/private counts
- [SPEC-001/REQ-031](../markdown-link-validator.md#req-031) - List invalid links with location
- [SPEC-001/REQ-032](../markdown-link-validator.md#req-032) - Verbose output option
- [SPEC-001/REQ-033](../markdown-link-validator.md#req-033) - Exit code 0 for success
- [SPEC-001/REQ-034](../markdown-link-validator.md#req-034) - Exit code 1 for failures
- [SPEC-001/REQ-035](../markdown-link-validator.md#req-035) - Handle file read errors
- [SPEC-001/REQ-036](../markdown-link-validator.md#req-036) - Handle config parse errors

**Success Criteria:**
- Summary shows total links checked and validation results
- Invalid links are listed with source file and line number
- Verbose mode provides detailed information for debugging
- Exit codes enable CI/CD integration
- Errors are handled gracefully without crashing the tool
