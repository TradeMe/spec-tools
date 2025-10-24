# Specification DSL Design Document

**Date**: 2025-10-24
**Status**: Proposal
**Related Spec**: SPEC-004

## Overview

This document describes the design of a domain-specific language (DSL) for defining and validating structured markdown specifications. The system provides a schema layer for markdown documents, enabling machine-enforceable structure while preserving the human-readability and standard tooling compatibility of markdown.

## Problem Statement

Organizations maintain technical specifications, requirements, contracts, and architectural documents in markdown format. These documents follow implicit conventions around structure, naming, cross-references, and content patterns. Currently, these conventions exist only in documentation and tribal knowledge, leading to inconsistency and manual review overhead.

The goal is to formalize these conventions as explicit, machine-validated type definitions while keeping the actual specification documents as standard markdown that renders correctly in any markdown viewer.

## Core Concept

The system operates as a two-layer architecture:

**Type Definition Layer** - YAML documents that define schemas for specification document types. These schemas describe file naming patterns, section structure, required fields, identifier patterns, and allowed cross-references.

**Document Layer** - Standard markdown files that conform to the defined types. These remain fully compatible with standard markdown parsers and viewers, but can be validated against their type definitions for correctness.

This separation ensures that specifications remain human-readable first-class markdown while gaining the benefits of machine-enforced structure.

## Fundamental Abstractions

### Modules

A module is a file-level type definition. It describes an entire specification document class such as a requirement, contract, or architecture decision record. Modules define:

- File naming patterns and allowed locations in the repository
- The relationship between filename conventions and document titles
- Identifier patterns and where they appear in the document
- Required and optional section structure
- Allowed cross-references to other module types
- Cardinality constraints for relationships

**Example Module Use Cases:**
- A "Requirement" module that enforces EARS format with required sections
- A "Contract" module that validates legal document structure
- An "ADR" module that ensures architectural decisions follow a template

### Classes

A class is a section-level type definition. It describes a repeatable structural pattern within a document, such as an acceptance criterion, a contract clause, or a risk assessment. Classes define:

- Heading patterns and nesting levels
- Required fields within the section
- Content validation rules
- Nested sub-structures

Classes can be defined inline within a module (private to that module) or in shared definitions (reusable across modules).

**Example Class Use Cases:**
- An "AcceptanceCriterion" class with Given/When/Then structure
- A "RiskAssessment" class with probability, impact, and mitigation fields
- A "TestCase" class with setup, execution, and verification sections

### References

References represent typed relationships between specifications. A reference from one document to another is not just a hyperlink—it carries semantic meaning about the relationship. References define:

- The source and target module types
- The relationship type (implements, depends-on, supersedes, etc.)
- Cardinality constraints
- Link pattern validation
- Whether the target must exist

**Example Reference Types:**
- Requirements → Contracts: "implements" (many-to-one, required)
- Requirements → Tests: "validated-by" (one-to-many, optional)
- ADRs → ADRs: "supersedes" (many-to-one, optional)

### Identifiers

Identifiers are unique designators for specifications and their sub-components. They follow defined patterns and appear consistently across the document ecosystem. Identifier definitions specify:

- The pattern format (regex-based)
- Where the identifier appears (title, frontmatter, first heading)
- Uniqueness scope (repository-wide, directory-scoped, etc.)
- How identifiers map to filenames

**Example Identifier Patterns:**
- Requirements: `REQ-\d{3}` (global scope, in title)
- Contracts: `CONTRACT-[A-Z]{3}-\d{4}` (directory scope, in frontmatter)
- ADRs: `ADR-\d{4}` (global scope, derived from filename)

## Markdown as a Structured Format

A key insight is that markdown is already a structured, machine-readable format with a well-defined abstract syntax tree. When markdown is parsed, it produces a tree of typed nodes: headings, paragraphs, lists, links, code blocks, tables, and so on.

The DSL operates on this AST rather than treating markdown as unstructured text. Type definitions describe constraints on the structure and content of AST nodes. This means validation is fundamentally AST pattern matching, not string parsing.

### The Section Model

Standard markdown parsers produce a flat list of nodes. However, human readers understand markdown as having hierarchical sections where content "belongs to" headings. A critical component is transforming the flat AST into a section tree, where each heading owns all content until the next heading of equal or higher level.

**Example Transformation:**

```
Flat AST:                    Section Tree:
- Heading(1, "Title")        - Section(1, "Title")
- Paragraph(...)               - Paragraph(...)
- Heading(2, "Sub")            - Section(2, "Sub")
- List(...)                      - List(...)
- Heading(2, "Sub2")           - Section(2, "Sub2")
- Paragraph(...)                 - Paragraph(...)
```

This section model is essential for expressing constraints like "the Acceptance Criteria section must contain at least three subsections of class AcceptanceCriterion."

### Why This Matters

Operating on the AST enables:

1. **Precise validation** - Check structure, not text patterns
2. **Better error messages** - Report exact line/column of violations
3. **Format preservation** - Validation doesn't require reformatting
4. **Tool integration** - Standard parsers provide the AST
5. **Future extensibility** - AST enables semantic analysis

## Multi-Pass Validation Architecture

Validation requires multiple passes through the document corpus because different validation concerns have different dependencies:

### Pass One: AST Construction

Parse each markdown file using a GitHub/GitLab Flavored Markdown parser. Construct the flat AST with full position tracking for error reporting. Handle frontmatter if present but do not require it.

**Inputs:** Raw markdown files
**Outputs:** Flat AST with position information
**Libraries:** Python-markdown, markdown-it-py, or similar

### Pass Two: Section Hierarchy

Transform flat ASTs into hierarchical section trees. Each heading becomes the root of a section containing all subsequent content until the next heading of equal or higher level. This creates the semantic structure needed for type validation.

**Inputs:** Flat ASTs from Pass 1
**Outputs:** Hierarchical section trees
**Algorithm:** Stack-based section nesting

### Pass Three: Type Assignment

Determine which type definition applies to each document based on file location and naming patterns. Validate that exactly one type matches or report ambiguity. Load the type definition for each document.

**Inputs:** File paths, section trees, type definitions
**Outputs:** Document-to-type mappings
**Validation:** Uniqueness of type match

### Pass Four: Structural Validation

Validate that each document's section structure matches its type definition. Check for required sections, validate heading patterns, verify section nesting, and ensure cardinality constraints are met. This pass operates purely on document structure.

**Inputs:** Section trees, type definitions
**Outputs:** Structural validation errors
**Validation:** Section presence, ordering, nesting

### Pass Five: Content Validation

Within each section, validate the content against type-specific rules. Apply content type validators for strongly-typed sections. Check for required fields, validate patterns in text content, and ensure lists and tables match expected formats.

**Inputs:** Section content, content type validators
**Outputs:** Content validation errors
**Validation:** Field presence, pattern matching, grammar compliance

### Pass Six: Reference Extraction

Extract all cross-document references (links to other specifications). Build a graph of relationships between documents. Validate link patterns against the type definitions.

**Inputs:** Section trees, type definitions
**Outputs:** Reference graph
**Validation:** Link pattern compliance

### Pass Seven: Reference Resolution

Resolve all references and validate that targets exist and are of the expected type. Check cardinality constraints on relationships. Validate that the reference graph is well-formed according to type definitions. Detect circular dependencies if relevant.

**Inputs:** Reference graph, document-to-type mappings
**Outputs:** Reference validation errors
**Validation:** Target existence, type matching, cardinality

### Why Multi-Pass?

This architecture allows each concern to build on the results of previous passes and enables validation of cross-document invariants. Each pass has clear inputs/outputs and can be tested independently.

## Content Type System

Beyond structural validation, the system supports strongly-typed content within sections. Rather than treating section content as arbitrary markdown, type definitions can specify that content must follow particular patterns or grammars.

### Expression-Based Validation

Content types are expression-based, not string-based. A Gherkin-style acceptance criterion is not validated by regex matching against raw text—it is parsed into structured components (given-clause, when-clause, then-clause) that are individually validated and can be programmatically manipulated.

**Example:**

```markdown
## Acceptance Criterion 1

Given a user is logged in
When they click the "Export" button
Then a CSV file is downloaded
```

Rather than validating with:
```python
if re.match(r"Given.*When.*Then.*", text):  # Bad!
```

We parse to:
```python
AcceptanceCriterion(
    given="a user is logged in",
    when="they click the 'Export' button",
    then="a CSV file is downloaded"
)
```

And validate each component individually.

### Built-In Content Validators

The core system should provide validators for common patterns:

- **Gherkin** - Given/When/Then clauses
- **EARS** - Event-driven, State-driven, Unwanted behavior patterns
- **Lists** - Ordered, unordered, with required items
- **Tables** - Column presence, type constraints
- **Code Blocks** - Language specification, syntax validation
- **Identifiers** - Pattern matching, uniqueness

### Custom Content Validators

Users can define custom content types for domain-specific needs. Type definitions specify which content validator applies to each section.

**Example Custom Validator:**
```yaml
content_validators:
  risk_assessment:
    fields:
      - name: probability
        type: enum
        values: [low, medium, high]
      - name: impact
        type: enum
        values: [low, medium, high]
      - name: mitigation
        type: text
        required: true
```

### Why Expression-Based?

This approach enables:

1. **Rich validation** - Check clause presence, ordering, relationships
2. **Data extraction** - Generate test matrices, traceability reports
3. **Semantic analysis** - Future LLM integration for meaning validation
4. **Transformation** - Convert formats while preserving semantics
5. **Tool integration** - Programmatic access to structured content

## Target Markdown Flavors

The system targets GitHub Flavored Markdown and GitLab Flavored Markdown. While these are largely compatible, they have subtle differences in table syntax, footnotes, and extension features.

### Flavor Differences

**GitHub Flavored Markdown:**
- Task lists with `- [ ]` and `- [x]`
- Tables with pipe syntax
- Strikethrough with `~~text~~`
- Auto-linking of URLs

**GitLab Flavored Markdown:**
- All of GitHub's features
- Additional emoji support
- Inline diffs
- Math with `$...$` and `$$...$$`

### Parsing Strategy

Rather than attempting to support the lowest common denominator, the system parses the superset of features and allows type definitions to constrain which features are used. This ensures maximum compatibility while still enabling validation of flavor-specific constructs.

**Example Type Constraint:**
```yaml
allowed_features:
  task_lists: true
  tables: true
  math: false  # Disable GitLab-specific math
  auto_linking: true
```

## Identifier and Naming Conventions

Type definitions enforce consistency in how documents are named and identified.

### File Naming Patterns

File naming patterns can require specific prefixes, suffixes, or formats:

```yaml
file_pattern: "^REQ-\\d{3}\\.md$"
location_pattern: "^specs/requirements/"
```

### Filename-to-Title Mapping

The relationship between filenames and document titles can be specified:

```yaml
filename_to_title:
  pattern: kebab-case
  transform: title-case
  # req-user-authentication.md → "Req User Authentication"
```

### Identifier Semantics

Identifiers are not just unique strings—they indicate document type, enable reliable cross-referencing, and support tooling integration:

```yaml
identifier:
  pattern: "^REQ-\\d{3}$"
  location: title  # or: frontmatter, first_heading
  scope: global    # or: directory, module
  unique: true
```

### Validation Examples

The system validates that:
- Identifiers are unique within their scope
- Identifiers appear in expected locations
- Cross-references use correct identifier format
- Filenames match identifier patterns

This prevents broken links and enables reliable document tracking.

## Relationship Cardinality and Validation

Not all relationships are optional or unbounded. Type definitions specify cardinality constraints on relationships.

### Cardinality Notation

Using standard notation:
- `1` - Exactly one
- `0..1` - Zero or one
- `1..*` - One or more
- `0..*` - Zero or more
- `n..m` - Between n and m

### Example Constraints

```yaml
references:
  - type: implements
    target_module: Contract
    cardinality: "1"  # Each requirement implements exactly one contract

  - type: validated_by
    target_module: Test
    cardinality: "1..*"  # Each requirement has one or more tests

  - type: depends_on
    target_module: Requirement
    cardinality: "0..*"  # Requirements may depend on other requirements
```

### Directionality

Relationship validation can also enforce directionality:

```yaml
references:
  - source: Requirement
    target: Contract
    type: implements
    allowed: true

  - source: Contract
    target: Requirement
    type: implemented_by
    allowed: false  # Contracts cannot reference requirements
```

### Validation

The reference resolution pass validates:
- Cardinality constraints are met
- Only allowed reference directions are used
- Circular dependencies are detected (if configured)
- Orphaned documents are identified

## Scope and Namespacing

Documents and classes exist in scopes to enable gradual adoption and prevent naming conflicts.

### Module-Level Scoping

Classes may be private to a module type or shared:

```yaml
# Private class (only in Requirement documents)
modules:
  Requirement:
    classes:
      AcceptanceCriterion:
        private: true

# Shared class (usable in any module)
shared_classes:
  RiskAssessment:
    usable_in: [Requirement, ADR, Contract]
```

### Identifier Scoping

Identifiers may be globally unique or scoped:

```yaml
identifier:
  scope: global         # REQ-001 is unique across entire repo

identifier:
  scope: directory      # REQ-001 in specs/auth/ vs specs/ui/

identifier:
  scope: module_type    # REQ-001 for requirements, TEST-001 for tests
```

### Gradual Adoption

This scoping enables organizations to:
- Define strict types for some document classes
- Leave others loosely defined initially
- Tighten validation incrementally
- Mix validated and unvalidated specs

## AST Library Requirements

The foundation of this system is a robust markdown parser and AST manipulation library.

### Required Features

The library must support:

1. **GitHub/GitLab Flavored Markdown** - Full compatibility with both flavors
2. **Position Tracking** - Precise line/column for every AST node
3. **Extension Features** - Tables, task lists, strikethrough, math
4. **Frontmatter** - YAML frontmatter parsing
5. **Malformed Input** - Graceful handling with diagnostics

### Extensibility Needs

The library must support:

1. **Custom AST Transforms** - Building section hierarchy
2. **Efficient Traversal** - Querying and filtering nodes
3. **AST Manipulation** - Future support for document generation
4. **Serialization** - Converting AST back to markdown

### Python Library Options

Current Python markdown libraries and their limitations:

**python-markdown:**
- ✓ Mature and well-maintained
- ✓ Extension system
- ✗ Limited position tracking
- ✗ Not fully GFM compliant

**markdown-it-py:**
- ✓ Full GFM compliance
- ✓ Good position tracking
- ✓ Plugin system
- ✓ Based on markdown-it (JavaScript)

**mistune:**
- ✓ Fast parser
- ✓ GFM support
- ✗ Limited extensibility
- ✗ AST not as accessible

**CommonMark:**
- ✓ Standards-compliant
- ✓ Good AST
- ✗ Lacks GFM extensions
- ✗ Limited ecosystem

### Recommendation

**markdown-it-py** appears to be the best foundation, with custom plugins for:
- Section hierarchy transformation
- Content type validation
- Enhanced error reporting

## Error Reporting and Developer Experience

Validation errors must be actionable and integrate seamlessly into development workflows.

### Error Message Requirements

Error messages should include:

1. **Location** - File path, line number, column offset
2. **Constraint** - Which rule was violated
3. **Context** - Surrounding code/structure
4. **Guidance** - How to fix the issue
5. **Severity** - Error vs warning

**Example Error:**
```
specs/requirements/user-auth.md:42:1: error: Missing required section
  Expected section "Acceptance Criteria" not found in requirement document.

  Requirement documents must include:
    - Overview
    - Requirements (EARS Format)
    - Acceptance Criteria
    - Test Coverage

  Add a level-2 heading "## Acceptance Criteria" after the Requirements section.
```

### Severity Levels

Type definitions specify severity:

```yaml
validation_rules:
  required_sections:
    severity: error      # Must fix

  recommended_sections:
    severity: warning    # Should fix

  style_guide:
    severity: info       # Nice to fix
```

### Output Formats

The system should support:

1. **Human-readable** - Colored, formatted for terminal
2. **JSON** - Structured for tool integration
3. **GitHub Actions** - Annotated file format
4. **GitLab CI** - Code quality report format
5. **SARIF** - Static analysis results interchange format

### CI/CD Integration

The validator should:
- Provide clear exit codes (0 = pass, 1 = fail, 2 = error)
- Support quiet mode for CI (minimal output)
- Support verbose mode for debugging
- Cache validation results for performance
- Integrate with git hooks (pre-commit, pre-push)

## Frontmatter Policy

Many markdown specifications use YAML frontmatter for metadata. The system takes a flexible approach.

### No Frontmatter Required

The system does not require frontmatter. If frontmatter is absent, all metadata must be derivable from document structure and content.

**Example without frontmatter:**
```markdown
# REQ-001: User Authentication

## Overview
This requirement defines...
```

Identifier `REQ-001` is extracted from the title.

### Frontmatter Optional

When frontmatter is present, it is treated as structured metadata that can participate in validation.

**Example with frontmatter:**
```markdown
---
id: REQ-001
version: 1.2
status: approved
implements: CONTRACT-AUTH-0042
---

# User Authentication

## Overview
This requirement defines...
```

Type definitions can specify:
```yaml
frontmatter:
  optional: true
  allowed_keys:
    - id
    - version
    - status
    - implements
  required_keys: []
  validation:
    status:
      type: enum
      values: [draft, review, approved, deprecated]
```

### Benefits of Optional Frontmatter

This approach:
- Keeps specs readable as pure markdown
- Supports gradual adoption of metadata
- Allows tools to extract data from content or frontmatter
- Doesn't require special parsers for casual readers

## Versioning and Evolution

Specifications and their type definitions evolve over time. The system must support change without breaking existing documents.

### Type Definition Versioning

Type definitions can be versioned:

```yaml
module: Requirement
version: 2.0
previous_versions: [1.0, 1.1]
```

### Document Version Declaration

Documents might explicitly declare conformance:

```markdown
---
schema_version: "Requirement:2.0"
---
```

Or the system might infer version from:
- Document creation date
- Directory location
- Git history

### Migration Paths

Type definitions can express migrations:

```yaml
migrations:
  from_version: "1.0"
  to_version: "2.0"
  changes:
    - type: section_renamed
      old: "Acceptance Criteria"
      new: "Acceptance Tests"
    - type: field_added
      section: "Overview"
      field: "stakeholders"
      default: "TBD"
```

### Deprecation Warnings

The system should support deprecation without immediate failure:

```yaml
sections:
  "Rationale":
    deprecated: true
    deprecated_in: "2.0"
    replaced_by: "Decision Factors"
    message: "The 'Rationale' section is deprecated. Use 'Decision Factors' instead."
```

### Validation with Versions

The validator should:
- Detect document version
- Load appropriate type definition version
- Validate against that version's rules
- Provide migration guidance for deprecated patterns
- Support linting with "upgrade to latest" suggestions

## Future Extensibility

The design anticipates future enhancements beyond structural validation.

### Semantic Validation with LLMs

Large language models could validate:
- Whether section content makes logical sense
- Whether rationales are well-reasoned
- Whether acceptance criteria adequately cover requirements
- Whether terminology is used consistently

The expression-based content type system prepares for this. Once content is parsed into structured expressions, those expressions can be passed to semantic validators.

**Example Integration:**
```python
# Structural validation (current)
acceptance_criterion = parse_gherkin(section.content)
validate_structure(acceptance_criterion)

# Semantic validation (future)
requirement_text = get_requirement_text(document)
semantic_score = llm_validate_alignment(
    requirement=requirement_text,
    test=acceptance_criterion
)
```

### Additional Validation Passes

The multi-pass architecture supports adding new passes:

- **Pass 8: Performance Analysis** - Estimate complexity, identify bottlenecks
- **Pass 9: Completeness Checking** - Detect missing scenarios, edge cases
- **Pass 10: Impact Assessment** - Analyze change ripple effects
- **Pass 11: Semantic Coherence** - LLM-based meaning validation

### Plugin Architecture

Future plugin system could support:

1. **Custom Passes** - User-defined validation passes
2. **Content Validators** - Domain-specific grammar validators
3. **Output Formatters** - Custom report formats
4. **Type Loaders** - Alternative schema languages
5. **AST Transformers** - Document generation, refactoring

## Open Source and General Purpose Design

While this system originates from specific needs, it is designed as a general-purpose tool.

### No Organization-Specific Assumptions

All conventions are expressed through type definitions, not hardcoded. The system should not assume:
- Specific identifier formats
- Particular section structures
- Fixed relationship types
- Predetermined document classes

### Extensibility for Diverse Use Cases

The type definition language should support:
- Requirements engineering (this project's origin)
- Contract management
- API documentation
- Architectural decision records
- Test case specifications
- Process documentation
- Regulatory compliance documents

### Community Contributions

As an open-source project:
- Plugin system enables community validators
- Clean architecture enables contribution
- Well-defined type format enables sharing schemas
- Example schemas help adoption

### Library Ecosystem

Over time, this could enable:
- Shared type definition repositories
- Industry-standard specification schemas
- Tool integration (linters, generators, analyzers)
- Educational resources for specification writing

## Implementation Strategy

### Phase 1: Core AST Processing

**Goal:** Parse markdown and build section model

**Deliverables:**
- markdown-it-py integration
- Section tree transformer
- Position tracking system
- AST query utilities

**Success Criteria:**
- Parse 1000+ line markdown files
- Accurate line/column tracking
- Correct section nesting for complex documents

### Phase 2: Type Definition Language

**Goal:** YAML schema for type definitions

**Deliverables:**
- YAML schema specification
- Type definition parser
- Module and class support
- Type assignment logic

**Success Criteria:**
- Express requirements spec structure in YAML
- Validate type definition correctness
- Assign types to documents based on patterns

### Phase 3: Structural Validation

**Goal:** Validate document structure against types

**Deliverables:**
- Section structure validator
- Required/optional section checking
- Heading pattern matching
- Cardinality enforcement

**Success Criteria:**
- Detect missing sections
- Validate section ordering
- Report precise error locations

### Phase 4: Reference System

**Goal:** Cross-document reference validation

**Deliverables:**
- Reference graph builder
- Link pattern validation
- Target resolution
- Cardinality checking

**Success Criteria:**
- Extract all cross-doc references
- Validate reference types
- Detect broken links, invalid targets

### Phase 5: Content Type System

**Goal:** Strongly-typed section content

**Deliverables:**
- Content validator plugin system
- Built-in validators (Gherkin, EARS, tables)
- Expression parsing framework
- Custom validator API

**Success Criteria:**
- Validate Gherkin acceptance criteria
- Parse and validate EARS requirements
- Support custom domain validators

### Phase 6: Production Ready

**Goal:** Polished user experience

**Deliverables:**
- Comprehensive error messages
- Multiple output formats
- CI/CD integration
- Documentation and examples
- Migration tools
- Performance optimization

**Success Criteria:**
- Error messages guide fixes
- Integrates with GitHub Actions, GitLab CI
- Documentation enables adoption
- Performance acceptable for large repos

## Success Metrics

The implementation will be considered successful when:

1. **Type Definition Authoring** - Users can define spec schemas in YAML
2. **Validation Quality** - Errors are precise and actionable
3. **Markdown Compatibility** - Works with GitHub/GitLab rendering
4. **Cross-Document Validation** - References are type-checked
5. **Extensibility** - Custom validators are straightforward
6. **Performance** - Validates large repos in reasonable time
7. **Adoption** - Other orgs successfully use the system
8. **Future-Ready** - Architecture supports semantic validation

## Conclusion

This DSL design provides a comprehensive schema language for markdown specifications. Through a two-layer architecture of YAML type definitions and standard markdown documents, validated via multi-pass AST analysis, the system brings rigor to specification management without sacrificing the simplicity that makes markdown effective.

The expression-based content type system, hierarchical section model, and typed reference graph transform markdown from a documentation format into a verifiable specification language suitable for engineering-critical documentation.

By maintaining clean abstractions, supporting extensibility, and building on standard markdown parsing, this design creates a foundation for both immediate validation needs and future semantic analysis capabilities.
