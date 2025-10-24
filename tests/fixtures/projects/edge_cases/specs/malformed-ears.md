# Specification: Malformed EARS Examples

**ID**: SPEC-302
**Version**: 1.0
**Date**: 2025-10-24
**Status**: Draft

## Overview

This spec contains requirements that don't follow EARS format to test validation.

## Requirements (EARS Format)

**REQ-001**: This requirement is missing the "shall" keyword.

**REQ-002**: The system should do something (uses "should" instead of "shall").

**REQ-003**: The system will perform an action (uses "will" instead of "shall").

**REQ-004**: WHEN condition is present but system will do something (wrong modal verb).

**REQ-005**: IF there is a condition, THEN the system should respond (wrong modal verb in consequent).

**REQ-006**: The system shall do something correctly (valid EARS ubiquitous).

**REQ-007**: WHEN a user clicks the button, the system shall respond (valid EARS event-driven).

**REQ-008**: WHERE the user is on mobile, the system shall adapt the layout (valid EARS state-driven).

**REQ-009**: IF the temperature exceeds 100°C, THEN the system shall shut down (valid EARS conditional).

**REQ-010**: WHILE processing data, the system shall display a progress indicator (valid EARS unwanted behavior).
