"""spec-tools: Tools for spec-driven development."""

__version__ = "0.1.0"

from .linter import LintResult, SpecLinter

__all__ = ["SpecLinter", "LintResult", "__version__"]
