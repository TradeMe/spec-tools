# spec-tools Specifications

This directory contains specifications for spec-tools, a toolkit for spec-driven development.

## What are Specs?

Specifications (specs) are formal documents that describe features, requirements, and design decisions. They serve as:

- **Design documents**: Guide implementation before coding
- **Living documentation**: Up-to-date reference for features
- **Decision records**: Capture why choices were made
- **Validation criteria**: Define how to verify features work

## Quick Start

### Reading Specs

1. Start with [spec-000](spec-000-spec-driven-development.md) to understand our approach
2. Check [spec-002](spec-002-architecture.md) for overall architecture
3. Read feature-specific specs as needed

### Writing Specs

1. Read [spec-000](spec-000-spec-driven-development.md) for guidelines
2. Use the naming convention: `spec-NNN-short-title.md`
3. Include required sections: Overview, Motivation, Requirements, Design
4. Update `.specallowlist` if you add new spec patterns

## Spec Index

### Process & Methodology (000-099)

| Spec | Title | Status | Description |
|------|-------|--------|-------------|
| [spec-000](spec-000-spec-driven-development.md) | Spec-Driven Development | Living Document | Guidelines for writing and maintaining specs |
| [spec-002](spec-002-architecture.md) | Architecture | Implemented | Overall architecture and design patterns |

### Features (100-199)

| Spec | Title | Status | Description |
|------|-------|--------|-------------|
| [spec-001](spec-001-linter-tool.md) | Allowlist Linter Tool | Implemented | File allowlist validation tool |

### Future Features (Planned)

| Spec | Title | Status | Description |
|------|-------|--------|-------------|
| TBD | Graph Visualizer | Planned | Visualize spec dependencies |
| TBD | Spec Checker | Planned | Validate spec structure and content |
| TBD | Project Initializer | Planned | Bootstrap spec-driven projects |

## Naming Convention

Spec files follow the pattern: `spec-NNN-short-title.md`

- **NNN**: Zero-padded 3-digit number
- **short-title**: Kebab-case description
- **Extension**: Always `.md` (Markdown)

### Number Ranges

- **000-099**: Process, methodology, architecture
- **100-199**: Core tools and features
- **200-299**: Integrations and extensions
- **300-399**: Research and experiments
- **900-999**: Deprecated specs

## Spec Status Values

- **Draft**: Being written, not ready for implementation
- **In Progress**: Implementation has started
- **Implemented**: Feature complete and matches spec
- **Living Document**: Continuously updated (process docs)
- **Deprecated**: Obsolete, kept for historical reference

## How to Use Specs

### For Developers

**Before implementing a feature**:
1. Read the spec to understand requirements
2. Check the design for architecture guidance
3. Use test criteria for validation

**While implementing**:
1. Update spec if requirements change
2. Reference spec in commit messages
3. Mark sections as done when complete

**After implementation**:
1. Update spec status to "Implemented"
2. Add "Future Enhancements" section
3. Link spec from documentation

### For Contributors

**Proposing a new feature**:
1. Create a spec in Draft status
2. Get feedback on the spec first
3. Iterate before coding
4. Move to "In Progress" when ready

**Modifying existing features**:
1. Update the relevant spec
2. Include spec changes in PR
3. Update status and version

### For Users

**Understanding a feature**:
1. Read the spec's Overview and Motivation
2. Check examples and use cases
3. See Implementation Details for advanced usage

## Spec Template

```markdown
# Spec NNN: Title

**Status**: Draft|In Progress|Implemented|Deprecated
**Version**: X.Y
**Author**: Name or team
**Created**: YYYY-MM-DD
**Updated**: YYYY-MM-DD

## Overview
Brief summary (2-3 sentences)

## Motivation
Why this feature is needed

## Requirements
What the feature must do

## Design
How it will be implemented

## Implementation Details
Specific details for implementation

## Testing
How to verify it works

## [Optional] Future Enhancements
Ideas for future improvements
```

## Validation

This directory is validated by spec-tools itself! The `.specallowlist` includes:

```
specs/spec-[0-9][0-9][0-9]-*.md
specs/README.md
```

Run the linter to verify:

```bash
spec-tools lint
```

## Contributing

When adding specs:

1. Follow the naming convention
2. Include all required sections
3. Update this README index
4. Ensure `.specallowlist` matches
5. Get spec reviewed before implementation

## Questions?

- Read [spec-000](spec-000-spec-driven-development.md) for detailed guidelines
- Check [spec-002](spec-002-architecture.md) for architecture questions
- Open an issue for clarification

---

**Note**: Specs are living documents. If you find outdated information, please submit a PR to update it!
