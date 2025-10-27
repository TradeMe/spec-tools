# Specification: Semantic Test-Adherence Validator

**ID**: SPEC-003
**Version**: 1.0
**Date**: 2025-10-23
**Status**: Provisional
**Milestone**: milestone-001-semantic-test-adherence

## Overview

This specification defines the requirements for a semantic test-adherence validator that analyzes whether tests marked with requirement IDs actually test the behavior specified in those requirements. While the existing `check-coverage` tool ensures every requirement has associated tests, it cannot verify that the tests validate the correct behavior. This tool addresses that gap through semantic analysis.

The validator uses AI/LLM-powered analysis to understand requirement intent and compare it against test implementation logic, identifying cases where tests are incorrectly linked to requirements or fail to validate the specified behavior.

## Requirements (EARS Format)

### Requirement Discovery and Parsing

**REQ-001**: The system shall discover all requirement definitions in specification files using the pattern `**[A-Z]+-\d{3})**:`.

**REQ-002**: WHEN parsing requirements, the system shall extract the requirement ID, requirement text, and source location (file and line number).

**REQ-003**: The system shall support multiple requirement types including REQ-XXX, NFR-XXX, and TEST-XXX formats.

**REQ-004**: WHEN a requirement is written in EARS format, the system shall parse and preserve the EARS structure (conditional, event-driven, unconditional, or optional).

**REQ-005**: The system shall associate each requirement with its specification file context, including the section heading under which it appears.

### Test Discovery and Parsing

**REQ-006**: The system shall discover all test functions in Python test files that use pytest markers.

**REQ-007**: WHEN parsing test files, the system shall extract test functions decorated with `@pytest.mark.req()` markers.

**REQ-008**: The system shall extract the requirement ID(s) from each test's `@pytest.mark.req()` marker arguments.

**REQ-009**: WHEN a test is marked with multiple requirement IDs, the system shall validate the test against each requirement separately.

**REQ-010**: The system shall parse the test function source code, including the function body, assertions, and any helper function calls.

**REQ-011**: The system shall extract the test's docstring as additional context for semantic analysis.

**REQ-012**: The system shall preserve the test location (file, function name, and line number) for reporting.

### Semantic Analysis

**REQ-013**: The system shall perform semantic analysis to determine if a test validates the behavior specified in its linked requirement(s).

**REQ-014**: WHEN performing semantic analysis, the system shall use an AI/LLM model to understand the intent of both the requirement text and test implementation.

**REQ-015**: The system shall analyze the following aspects of alignment:
- Whether the test validates the action/behavior described in the requirement
- Whether the test covers the conditions/triggers specified in the requirement
- Whether the test assertions match the expected outcomes in the requirement
- Whether the test scope is appropriate for the requirement scope

**REQ-016**: WHEN a requirement is in EARS format, the system shall validate that the test includes:
- Appropriate setup for WHEN/IF/WHERE conditions (if present)
- Validation of the SHALL action/behavior
- Assertions matching the specified outcome

**REQ-017**: The system shall produce a confidence score (0.0 to 1.0) indicating the semantic alignment between each test-requirement pair.

**REQ-018**: WHEN the confidence score is below a configurable threshold, the system shall flag the test-requirement pair as potentially misaligned.

**REQ-019**: The system shall generate a textual explanation of why a test-requirement pair is considered aligned or misaligned.

**REQ-020**: WHEN analyzing non-functional requirements (NFR-XXX), the system shall recognize and validate NFR-specific characteristics such as performance, security, usability, or reliability aspects.

### AI/LLM Integration

**REQ-021**: The system shall support multiple AI/LLM backends for semantic analysis.

**REQ-022**: The system shall support the following LLM providers via configuration:
- Anthropic Claude (via API)
- OpenAI GPT models (via API)
- Local models (via Ollama or similar)

**REQ-023**: The system shall accept an API key or authentication configuration for LLM providers that require authentication.

**REQ-024**: WHEN an LLM API call fails, the system shall retry up to 3 times with exponential backoff before reporting an error.

**REQ-025**: WHEN an LLM provider is unavailable or authentication fails, the system shall report a clear error message and exit with code 1.

**REQ-026**: The system shall support a configurable prompt template for semantic analysis requests.

**REQ-027**: The system shall include in the analysis prompt:
- The requirement ID and full text
- The requirement context (specification section, related requirements)
- The test function name and full source code
- The test docstring
- Instructions for alignment analysis

**REQ-028**: The system shall limit the context sent to LLMs to avoid exceeding token limits, prioritizing the most relevant information.

**REQ-029**: WHEN multiple tests reference the same requirement, the system shall batch analyze them in a single LLM request when possible to improve efficiency.

### Configuration

**REQ-030**: The system shall read configuration from `[tool.spec-check.check-semantic-test-adherence]` section in `pyproject.toml`.

**REQ-031**: The system shall support a `--specs-dir` command-line option to specify the directory containing specification files.

**REQ-032**: WHERE the `--specs-dir` option is not provided, the system shall default to `specs/`.

**REQ-033**: The system shall support a `--tests-dir` command-line option to specify the directory containing test files.

**REQ-034**: WHERE the `--tests-dir` option is not provided, the system shall default to `tests/`.

**REQ-035**: The system shall support a `--llm-provider` option to specify which LLM backend to use (anthropic, openai, ollama).

**REQ-036**: The system shall support a `--llm-model` option to specify the model name/version for the selected provider.

**REQ-037**: The system shall support a `--threshold` option to set the minimum confidence score for alignment (default: 0.7).

**REQ-038**: The system shall support a `--use-gitignore` flag to respect `.gitignore` patterns when discovering files.

**REQ-039**: WHERE `--use-gitignore` is enabled, the system shall use the same gitignore handling as other spec-check commands.

**REQ-040**: The system shall read LLM API keys from environment variables (e.g., `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`).

**REQ-041**: The system shall support a `--max-concurrent` option to control concurrent LLM requests (default: 5).

**REQ-042**: The system shall support a `--cache-results` flag to cache analysis results and avoid re-analyzing unchanged test-requirement pairs.

**REQ-043**: WHEN `--cache-results` is enabled, the system shall invalidate cache entries when either the requirement or test source code changes.

### Reporting

**REQ-044**: WHEN analysis completes, the system shall report the total number of test-requirement pairs analyzed.

**REQ-045**: WHEN analysis completes, the system shall report the number of aligned pairs, misaligned pairs, and errors.

**REQ-046**: WHEN analysis completes, the system shall report the overall alignment percentage.

**REQ-047**: The system shall list all misaligned test-requirement pairs with:
- Requirement ID and text
- Test file, function name, and line number
- Confidence score
- Explanation of the misalignment

**REQ-048**: WHEN the verbose option is enabled, the system shall report all test-requirement pairs, including aligned ones.

**REQ-049**: WHEN the verbose option is enabled, the system shall include the full LLM analysis explanation for each pair.

**REQ-050**: The system shall support a `--format` option to control output format (text, json, markdown).

**REQ-051**: WHEN `--format json` is specified, the system shall output results as structured JSON including all analysis data.

**REQ-052**: WHEN `--format markdown` is specified, the system shall output a markdown report suitable for inclusion in documentation.

**REQ-053**: IF all test-requirement pairs are aligned (above threshold), THEN the system shall exit with code 0.

**REQ-054**: IF any test-requirement pairs are misaligned (below threshold), THEN the system shall exit with code 1.

**REQ-055**: The system shall support a `--fail-on-error` flag that causes non-zero exit when LLM errors occur (default: false).

### Error Handling

**REQ-056**: IF a specification file cannot be read, THEN the system shall report the error and continue processing other files.

**REQ-057**: IF a test file cannot be parsed, THEN the system shall report the error and continue processing other files.

**REQ-058**: IF a requirement ID in a test marker does not exist in any specification file, THEN the system shall report a warning.

**REQ-059**: IF an LLM request fails after all retries, THEN the system shall report the error and mark the test-requirement pair as "error" rather than aligned or misaligned.

**REQ-060**: WHEN network errors occur during LLM API calls, the system shall include network diagnostics in the error message.

### Integration

**REQ-061**: The system shall use the same requirement pattern matching as the `check-coverage` tool for consistency.

**REQ-062**: The system shall use the same test marker parsing as the `check-coverage` tool for consistency.

**REQ-063**: The system shall respect the same `.gitignore` handling as other spec-check commands when enabled.

**REQ-064**: The system shall support the same `--verbose` flag behavior as other spec-check commands.

**REQ-065**: The system shall follow the same exit code conventions as other spec-check commands (0 for pass, 1 for fail).

## Non-Functional Requirements

**NFR-001**: The system shall complete semantic analysis of 100 test-requirement pairs in under 5 minutes when using commercial LLM APIs with default concurrency settings.

**NFR-002**: The system shall handle specification files up to 10,000 lines without performance degradation.

**NFR-003**: The system shall handle test files up to 5,000 lines without performance degradation.

**NFR-004**: The system shall provide clear progress indicators when analyzing large numbers of test-requirement pairs.

**NFR-005**: The system shall cache LLM responses to avoid unnecessary API costs when re-running analysis on unchanged code.

**NFR-006**: The system shall minimize LLM token usage by sending only relevant context rather than entire specification or test files.

**NFR-007**: The system shall provide actionable error messages when LLM configuration is incorrect or APIs are unavailable.

**NFR-008**: The system shall be compatible with Python 3.10, 3.11, 3.12, and 3.13.

## Test Coverage

**TEST-001**: The test suite shall verify requirement discovery from specification files with various requirement types (REQ, NFR, TEST).

**TEST-002**: The test suite shall verify test discovery from Python files with pytest markers.

**TEST-003**: The test suite shall verify semantic analysis with mock LLM responses for both aligned and misaligned cases.

**TEST-004**: The test suite shall verify confidence score thresholding and reporting.

**TEST-005**: The test suite shall verify all supported output formats (text, json, markdown).

**TEST-006**: The test suite shall verify LLM provider configuration and authentication handling.

**TEST-007**: The test suite shall verify caching behavior for unchanged test-requirement pairs.

**TEST-008**: The test suite shall verify EARS format requirement parsing and validation logic.

**TEST-009**: The test suite shall verify error handling for missing requirements, parse failures, and LLM errors.

**TEST-010**: The test suite shall verify integration with existing spec-check configuration patterns.

## Future Enhancements

The following features are out of scope for the initial implementation but may be considered for future versions:

- **Batch Processing**: Analyze multiple repositories or projects in a single run
- **Trend Analysis**: Track semantic alignment over time and detect regressions
- **Auto-Correction**: Suggest test modifications to improve alignment
- **Custom Validators**: Plugin system for domain-specific semantic validation rules
- **IDE Integration**: Real-time semantic validation in IDEs and editors
- **Fine-Tuned Models**: Project-specific LLM fine-tuning for improved accuracy
