"""spec-tools: Tools for spec-driven development."""

__version__ = "0.1.0"

from .linter import LintResult, SpecLinter
from .markdown_link_validator import (
    Link,
    LinkValidationResult,
    MarkdownLinkValidator,
)

__all__ = [
    "SpecLinter",
    "LintResult",
    "MarkdownLinkValidator",
    "LinkValidationResult",
    "Link",
    "__version__",
]
