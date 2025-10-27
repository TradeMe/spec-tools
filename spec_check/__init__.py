"""spec-check: Tools for spec-driven development."""

__version__ = "0.1.0"

from .linter import LintResult, SpecLinter
from .markdown_link_validator import (
    Link,
    LinkValidationResult,
    MarkdownLinkValidator,
)
from .markdown_schema_validator import (
    MarkdownSchemaValidator,
    SchemaValidationResult,
    SchemaViolation,
)

__all__ = [
    "SpecLinter",
    "LintResult",
    "MarkdownLinkValidator",
    "LinkValidationResult",
    "Link",
    "MarkdownSchemaValidator",
    "SchemaValidationResult",
    "SchemaViolation",
    "__version__",
]
