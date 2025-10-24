# Specification: Code Block Confusion

**ID**: SPEC-305
**Version**: 1.0
**Date**: 2025-10-24
**Status**: Draft

## Overview

This spec tests that requirements inside code blocks are NOT parsed as actual requirements.

## Requirements

**REQ-001**: The system shall support code examples in specifications.

## Examples

Here's an example of documenting requirements:

```markdown
**REQ-999**: This looks like a requirement but it's in a code block!
**NFR-888**: This should NOT be extracted as a requirement.
```

Another example in a different language:

```python
# This comment mentions **REQ-777**: but it shouldn't be extracted
print("**REQ-666**: Also not a real requirement")
```

**REQ-002**: The system shall correctly ignore requirements inside code blocks.

## More Examples

Inline code like `**REQ-555**:` should also be ignored if possible.

```
Plain code block without language specified:
**REQ-444**: Should not be extracted
**TEST-333**: Also should not be extracted
```

**REQ-003**: The system shall only extract requirements from actual markdown content.
