# Specification: Markdown Specification DSL

**ID**: SPEC-004
**Version**: 1.0
**Date**: 2025-10-24
**Status**: Proposal
**Milestone**: TBD

## Overview

This specification defines a domain-specific language (DSL) for defining and validating structured markdown specifications. The system provides a schema layer for markdown documents, enabling machine-enforceable structure while preserving the human-readability and standard tooling compatibility of markdown.

This represents a significant evolution of spec-tools from a validation toolkit into a comprehensive specification management system with formal type definitions, multi-pass AST validation, and extensible content validators.

## Problem Statement

Organizations maintain technical specifications, requirements, contracts, and architectural documents in markdown format. These documents follow implicit conventions around structure, naming, cross-references, and content patterns. Currently, these conventions exist only in documentation and tribal knowledge, leading to inconsistency and manual review overhead.

The goal is to formalize these conventions as explicit, machine-validated type definitions while keeping the actual specification documents as standard markdown that renders correctly in any markdown viewer.

## Architecture Overview

The system operates as a two-layer architecture:

**Type Definition Layer** - YAML documents that define schemas for specification document types. These schemas describe file naming patterns, section structure, required fields, identifier patterns, and allowed cross-references.

**Document Layer** - Standard markdown files that conform to the defined types. These remain fully compatible with standard markdown parsers and viewers, but can be validated against their type definitions for correctness.

This separation ensures that specifications remain human-readable first-class markdown while gaining the benefits of machine-enforced structure.

## Core Requirements

### Module Type Definitions

**REQ-001**: The system shall support defining module types in YAML format that describe entire specification document classes.

**REQ-002**: Module type definitions shall specify file naming patterns and allowed repository locations.

**REQ-003**: Module type definitions shall define identifier patterns for documents of that type.

**REQ-004**: Module type definitions shall specify required and optional section structure.

**REQ-005**: Module type definitions shall declare allowed cross-references to other module types with cardinality constraints.

### Class Type Definitions

**REQ-006**: The system shall support defining class types that describe repeatable structural patterns within documents.

**REQ-007**: Class type definitions shall specify heading patterns and nesting levels.

**REQ-008**: Class type definitions shall define required fields and content validation rules.

**REQ-009**: Classes shall be definable inline within modules (private) or as shared definitions (reusable).

### AST Processing

**REQ-010**: The system shall parse markdown files using a GitHub/GitLab Flavored Markdown parser.

**REQ-011**: The system shall maintain precise source position information for all AST nodes to enable high-quality error reporting.

**REQ-012**: The system shall transform flat AST representations into hierarchical section trees.

**REQ-013**: WHEN transforming to section trees, each heading shall become the root of a section containing all subsequent content until the next heading of equal or higher level.

### Multi-Pass Validation

**REQ-014**: The system shall implement a multi-pass validation architecture with the following passes:
- Pass 1: AST Construction
- Pass 2: Section Hierarchy
- Pass 3: Type Assignment
- Pass 4: Structural Validation
- Pass 5: Content Validation
- Pass 6: Reference Extraction
- Pass 7: Reference Resolution

**REQ-015**: WHEN type assignment is ambiguous (multiple types match), the system shall report an error.

**REQ-016**: WHEN structural validation fails, the system shall report the specific constraint violated with file, line, and column information.

### Reference Validation

**REQ-017**: The system shall extract and validate cross-document references as typed relationships.

**REQ-018**: Reference validation shall check that link targets exist and are of the expected type.

**REQ-019**: Reference validation shall enforce cardinality constraints on relationships.

**REQ-020**: The system shall build a graph of relationships between documents.

**REQ-021**: WHEN circular dependencies exist and are disallowed by type definitions, the system shall report an error.

### Content Type System

**REQ-022**: The system shall support strongly-typed content validation within sections through an extensible content type system.

**REQ-023**: Content validators shall operate on parsed expression structures rather than raw text strings.

**REQ-024**: The system shall provide built-in content validators for common patterns.

**REQ-025**: Users shall be able to define custom content type validators for domain-specific patterns.

**REQ-026**: Type definitions shall specify which content validator applies to each section.

### Identifier Management

**REQ-027**: The system shall validate that identifiers follow defined patterns.

**REQ-028**: The system shall enforce identifier uniqueness within the appropriate scope (global, directory, module type).

**REQ-029**: The system shall validate that identifiers appear in expected locations (title, frontmatter, first heading).

**REQ-030**: The system shall validate that cross-references use correct identifier formats.

### Markdown Flavor Support

**REQ-031**: The system shall parse both GitHub Flavored Markdown and GitLab Flavored Markdown.

**REQ-032**: Type definitions shall be able to constrain which markdown features are allowed.

**REQ-033**: The system shall support validation of flavor-specific constructs such as task lists and tables.

### Error Reporting

**REQ-034**: Validation errors shall include file path, line number, column offset, and constraint violated.

**REQ-035**: Error messages shall provide actionable guidance on how to fix violations.

**REQ-036**: The system shall support different severity levels (error, warning) for validation rules.

**REQ-037**: Type definitions shall specify the severity of each constraint.

**REQ-038**: The system shall provide clear exit codes and support multiple output formats.

### Frontmatter Handling

**REQ-039**: The system shall not require YAML frontmatter but shall tolerate it when present.

**REQ-040**: WHEN frontmatter is present, type definitions may specify allowed or required frontmatter keys.

**REQ-041**: WHEN frontmatter is absent, all metadata shall be derivable from document structure and content.

### Versioning and Evolution

**REQ-042**: Type definitions shall be versionable.

**REQ-043**: The system shall support validating documents against specific type definition versions.

**REQ-044**: The system shall provide deprecation warnings for outdated patterns.

**REQ-045**: Migration paths between type definition versions shall be expressible.

### Integration

**REQ-046**: The system shall integrate with continuous integration pipelines.

**REQ-047**: The system shall support JSON output for tool integration.

**REQ-048**: The system shall provide human-readable output for developer feedback.

## Non-Functional Requirements

**NFR-001**: The system shall be designed as a general-purpose tool without organization-specific assumptions.

**NFR-002**: All conventions shall be expressed through type definitions, not hardcoded.

**NFR-003**: The system shall support extensibility through plugins for content validators.

**NFR-004**: The architecture shall maintain clean separation between validation passes.

**NFR-005**: The system shall be designed for future enhancement with semantic validation capabilities.

**NFR-006**: The system shall be compatible with Python 3.10, 3.11, 3.12, and 3.13.

## Design Considerations

### AST Library Selection

The implementation will require a robust markdown parser that supports:
- Full GitHub/GitLab Flavored Markdown compatibility
- Precise source position tracking
- All extension features (tables, task lists, strikethrough)
- Extensibility for custom AST transformations

No existing Python markdown library provides all required functionality out of the box. Custom extensions will be needed for section hierarchy building and content validation.

### Expression-Based Content Validation

Rather than validating section content via regex against raw text, content should be parsed into structured expressions that can be individually validated and programmatically manipulated. This prepares the foundation for future semantic analysis with LLMs.

### Gradual Adoption Support

Organizations should be able to:
- Define strict types for some document classes while leaving others loosely defined
- Tighten validation incrementally as conventions solidify
- Mix validated and unvalidated specifications in the same repository

### Scoping and Namespacing

The type system must support:
- Module-level classes that are private or shared
- Identifiers that are globally unique or scoped to directories/types
- Clear scoping boundaries that enable gradual adoption

## Future Enhancements

The following capabilities are anticipated for future development:

**Semantic Validation**: Integration with LLMs to validate that section content makes logical sense beyond structural correctness.

**Auto-Completion**: IDE support for generating specification sections based on type definitions.

**Migration Tools**: Automated assistance in migrating documents to new type definition versions.

**Visual Schema Editors**: Graphical tools for creating and editing type definitions.

**Import/Export**: Convert between the DSL format and other specification systems.

**Analytics**: Generate metrics and visualizations from the typed specification corpus.

## Implementation Phases

This feature should be implemented in phases:

**Phase 1**: Core AST processing and section model
- Markdown parser integration
- Section tree transformation
- Basic structural validation

**Phase 2**: Type definition language
- YAML schema for type definitions
- Module and class type support
- Type assignment logic

**Phase 3**: Reference validation
- Cross-document link extraction
- Reference graph construction
- Cardinality constraint validation

**Phase 4**: Content type system
- Extensible content validator architecture
- Built-in validators for common patterns
- Plugin system for custom validators

**Phase 5**: Advanced features
- Versioning support
- Migration tools
- Enhanced error reporting
- CI/CD integration

## Dependencies

This specification depends on:
- Selection of appropriate markdown parsing library
- Design of YAML type definition schema
- Development of section tree transformation algorithms
- Implementation of multi-pass validation architecture

## Test Coverage

**TEST-001**: The test suite shall verify AST construction from various markdown flavors.

**TEST-002**: The test suite shall verify section tree transformation with nested headings.

**TEST-003**: The test suite shall verify type assignment from file patterns and locations.

**TEST-004**: The test suite shall verify structural validation against type definitions.

**TEST-005**: The test suite shall verify content validation with built-in validators.

**TEST-006**: The test suite shall verify reference extraction and resolution.

**TEST-007**: The test suite shall verify cardinality constraint enforcement.

**TEST-008**: The test suite shall verify identifier uniqueness validation.

**TEST-009**: The test suite shall verify error reporting with accurate position information.

**TEST-010**: The test suite shall verify frontmatter handling (present and absent).

## Success Criteria

This feature will be considered successful when:

1. Users can define type schemas for their specification documents in YAML
2. The system can validate arbitrary markdown documents against those schemas
3. Validation errors provide actionable, precisely-located guidance
4. The system handles both GitHub and GitLab Flavored Markdown
5. Cross-document references are validated with type checking
6. The architecture supports future semantic validation enhancements
7. Documentation and examples enable adoption by other organizations

## Related Documents

See `technical-notes/specification-dsl-design.md` for detailed design discussion and implementation considerations.
