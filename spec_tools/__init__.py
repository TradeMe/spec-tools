"""spec-tools: Tools for spec-driven development."""

__version__ = "0.1.0"

from .linter import LintResult, SpecLinter
from .llm_provider import LiteLLMProvider, LLMProvider
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
from .semantic_test_analyzer import SemanticTestAnalyzer
from .semantic_test_result import (
    SemanticAnalysisResult,
    SemanticTestAdherenceResult,
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
    "LLMProvider",
    "LiteLLMProvider",
    "SemanticTestAnalyzer",
    "SemanticAnalysisResult",
    "SemanticTestAdherenceResult",
    "__version__",
]
