# Spec 000: Spec-Driven Development

**Status**: Living Document
**Version**: 1.0
**Author**: spec-tools contributors
**Created**: 2025-10-22
**Updated**: 2025-10-22

## Overview

This document defines the spec-driven development approach used in the spec-tools project and provides guidelines for writing and maintaining specifications.

## What is Spec-Driven Development?

Spec-driven development is a software development methodology where specifications are first-class artifacts that drive the design, implementation, and validation of features. Specifications are written before or alongside implementation, providing:

1. **Clear requirements**: Explicit documentation of what needs to be built
2. **Design rationale**: Why decisions were made
3. **Validation criteria**: How to verify the implementation works
4. **Living documentation**: Up-to-date reference for current and future developers

## Principles

### 1. Specs First, Code Second

Before implementing a feature:
- Write or update the specification
- Get feedback on the spec
- Use the spec to guide implementation

This doesn't mean waterfall development - specs can evolve iteratively with the code. But having a spec ensures thoughtful design before coding begins.

### 2. Specs as Source of Truth

The spec documents should be the authoritative reference for:
- Feature requirements and behavior
- Design decisions and trade-offs
- API contracts and interfaces
- Validation and testing criteria

Code comments explain *how*, specs explain *what* and *why*.

### 3. Keep Specs Updated

Specs are living documents:
- Update specs when requirements change
- Mark specs with status (Draft, Implemented, Deprecated)
- Use version numbers for tracking
- Archive old specs rather than deleting them

### 4. Make Specs Discoverable

- Use consistent naming conventions
- Maintain a specs index/README
- Reference specs from code and docs
- Include specs in code reviews

## Spec Structure

### Required Sections

Every spec should include:

```markdown
# Spec NNN: Title

**Status**: [Draft|In Progress|Implemented|Deprecated]
**Version**: X.Y
**Author**: Name or team
**Created**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

## Overview
Brief summary (2-3 sentences)

## Motivation
Why this feature is needed, what problems it solves

## Requirements
What the feature must do (functional and non-functional)

## Design
How the feature will be implemented (architecture, components, flows)

## Implementation Details
Specific details needed for implementation

## Testing
How to verify the implementation works

## [Optional] Future Enhancements
Ideas for future improvements not in current scope
```

### Optional Sections

Add as needed:
- **Alternatives Considered**: Other approaches evaluated
- **Performance Considerations**: Scalability, latency concerns
- **Security Considerations**: Threats, mitigations
- **Migration**: How to transition from old to new
- **Dependencies**: External requirements
- **References**: Links to related docs, research

## Naming Conventions

### Spec Files

Format: `spec-NNN-short-title.md`

- **NNN**: Zero-padded 3-digit number (001, 002, ...)
- **short-title**: Kebab-case description
- **Extension**: Always `.md` (Markdown)

Examples:
- `spec-000-spec-driven-development.md` (this document)
- `spec-001-linter-tool.md`
- `spec-002-graph-visualizer.md`

### Spec Numbers

- **000-099**: Process, methodology, architecture
- **100-199**: Core tools and features
- **200-299**: Integrations and extensions
- **300-399**: Research and experiments
- **900-999**: Deprecated specs

Start at 000 for foundational docs, 001+ for features.

### Status Values

- **Draft**: Spec is being written, not ready for implementation
- **In Progress**: Implementation has started
- **Implemented**: Feature is complete and matches spec
- **Deprecated**: Feature is obsolete, kept for historical reference

## Spec Workflow

### 1. Create Spec

```bash
# Create new spec file
touch specs/spec-NNN-feature-name.md

# Update .specallowlist if needed
echo "specs/spec-[0-9][0-9][0-9]-*.md" >> .specallowlist
```

### 2. Write Spec

- Start with Overview and Motivation
- Define clear Requirements
- Sketch high-level Design
- Add Implementation Details as you learn more
- Include Testing strategy

### 3. Review Spec

- Get feedback from team or stakeholders
- Iterate on requirements and design
- Mark status as "In Progress" when ready to implement

### 4. Implement Feature

- Reference spec in commit messages
- Update spec if implementation differs
- Use spec for test cases
- Mark sections as done when complete

### 5. Update on Completion

- Set status to "Implemented"
- Update version number
- Add "Future Enhancements" for follow-up work
- Reference in documentation

### 6. Maintain Specs

- Review specs periodically
- Deprecate obsolete specs (don't delete)
- Keep specs in sync with major changes

## Integration with Development

### Code References

Reference specs in code:

```python
"""Allowlist linter implementation.

See specs/spec-001-linter-tool.md for design and requirements.
"""
```

### Commit Messages

Reference specs in commits:

```
Implement pattern matching for linter

Implements the pattern matching requirements from spec-001,
using the pathspec library for gitignore-style patterns.

Ref: specs/spec-001-linter-tool.md
```

### Pull Requests

- Link to relevant specs in PR description
- Update specs as part of PRs if requirements change
- Review spec changes alongside code changes

### CI/CD Integration

Validate specs are tracked:

```yaml
- name: Validate file allowlist
  run: spec-tools lint
```

This ensures all files, including specs, match expected patterns.

## Spec-Tools Integration

This project is self-hosting - we use spec-tools to validate our own specs:

### .specallowlist Example

```
# Specs with naming convention
specs/spec-[0-9][0-9][0-9]-*.md

# Other allowed files...
*.md
spec_tools/**/*.py
```

### Automated Validation

The linter validates:
- All spec files follow naming convention
- No unexpected files in specs directory
- Spec files are tracked in git

## Benefits

### For Developers

- **Clarity**: Know what to build and why
- **Focus**: Spec defines scope, reduces scope creep
- **Onboarding**: New developers can read specs to understand system
- **Reference**: Don't rely on memory or tribal knowledge

### For Projects

- **Quality**: Thoughtful design before implementation
- **Documentation**: Specs double as design docs
- **Maintenance**: Easier to modify with clear requirements
- **Validation**: Specs define success criteria

### For Teams

- **Communication**: Specs facilitate discussion
- **Alignment**: Everyone understands requirements
- **Review**: Easier to review specs than code
- **Knowledge**: Specs preserve design decisions

## Anti-Patterns to Avoid

### 1. Specs That Are Too Detailed

Don't specify every line of code. Focus on requirements, interfaces, and high-level design. Leave implementation details flexible.

**Bad**: "The function shall use a for loop from i=0 to n-1"
**Good**: "The function shall process all items in the list"

### 2. Specs That Are Never Updated

Specs drift from reality if not maintained. Update specs when implementation changes, or mark them deprecated.

### 3. Specs That Are Too Vague

Specs should be specific enough to guide implementation and testing.

**Bad**: "The tool shall be fast"
**Good**: "The tool shall process 10,000 files in under 5 seconds"

### 4. Treating Specs as Contracts

Specs are living documents, not legal contracts. They should evolve with understanding. Change them when needed.

### 5. Writing Specs After Implementation

While retroactive specs have value, writing specs first leads to better design. Don't always wait until implementation is done.

## Tools for Spec Management

### spec-tools (this project)

- **spec-tools lint**: Validate specs follow naming conventions
- **spec-tools graph**: (future) Visualize spec dependencies
- **spec-tools check**: (future) Validate spec structure and completeness

### External Tools

- **Markdown linters**: Vale, markdownlint
- **Diagram tools**: Mermaid, PlantUML, Excalidraw
- **Version control**: Git for tracking spec changes
- **Review tools**: GitHub, GitLab for spec reviews

## Examples

See other specs in this directory:

- `spec-001-linter-tool.md`: Example of a feature spec
- `spec-002-architecture.md`: Example of an architecture spec

## References

- [Design Docs at Google](https://www.industrialempathy.com/posts/design-docs-at-google/)
- [Rust RFCs](https://github.com/rust-lang/rfcs)
- [Python PEPs](https://www.python.org/dev/peps/)
- [IETF RFCs](https://www.ietf.org/standards/rfcs/)

## Changelog

### Version 1.0 (2025-10-22)

- Initial spec-driven development guide
- Define structure, naming, and workflow
- Establish principles and best practices
