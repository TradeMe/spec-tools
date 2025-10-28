"""spec-check: Tools for spec-driven development."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("spec-check")
except PackageNotFoundError:
    # Package not installed, use a default for development
    __version__ = "0.0.0-dev"

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
