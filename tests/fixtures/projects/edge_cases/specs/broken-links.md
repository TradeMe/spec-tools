# Specification: Broken Links Example

**ID**: SPEC-303
**Version**: 1.0
**Date**: 2025-10-24
**Status**: Draft

## Overview

This spec contains various types of broken links to test link validation.

## Requirements

**REQ-001**: The system shall implement [this feature](./non-existent-file.md).

**REQ-002**: See [another spec](../specs/does-not-exist.md) for details.

**REQ-003**: Refer to [section](#non-existent-heading) below.

**REQ-004**: Valid link to [another spec in this project](./duplicate-ids.md).

**REQ-005**: External link to [GitHub](https://github.com/TradeMe/spec-tools).

**REQ-006**: Broken external link to [invalid URL](https://this-domain-should-not-exist-12345.com/page).

## Related Specifications

- [SPEC-999](./spec-999.md) - This file doesn't exist
- [Malformed EARS](./malformed-ears.md) - This file exists

## References

[ref1]: https://example.com/valid "Valid reference"
[ref2]: ./missing-file.md "Broken reference"

Using reference style links:
- [Valid reference][ref1]
- [Broken reference][ref2]
