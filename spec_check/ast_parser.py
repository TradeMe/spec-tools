"""Unified AST-based markdown parser for specification documents.

This module provides a robust AST-based approach to parsing markdown specification
documents. It replaces the fragile regex-based parsing with proper Abstract Syntax
Tree traversal, enabling:

- Correct handling of code blocks (no false positives)
- Precise position tracking (line and column numbers)
- Semantic understanding of document structure
- Single source of truth for parsing logic
- Foundation for future Specification DSL

Key classes:
    - MarkdownDocument: High-level representation of a parsed spec document
    - ASTVisitor: Base class for traversing the markdown AST
    - SpecExtractor: Extracts spec IDs, requirements, and metadata from AST
"""

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from markdown_it import MarkdownIt
from markdown_it.token import Token


@dataclass
class Position:
    """Position information for an AST node."""

    line: int  # 1-indexed line number
    column: int = 0  # 0-indexed column number


@dataclass
class MarkdownNode:
    """Base class for markdown AST nodes."""

    position: Position
    raw_content: str = ""


@dataclass
class HeadingNode(MarkdownNode):
    """Represents a heading in the document."""

    level: int = 1  # 1-6
    text: str = ""
    children: list["MarkdownNode"] = field(default_factory=list)


@dataclass
class ParagraphNode(MarkdownNode):
    """Represents a paragraph with inline content."""

    inline_content: list["InlineNode"] = field(default_factory=list)


@dataclass
class CodeBlockNode(MarkdownNode):
    """Represents a code block."""

    language: str = ""
    code: str = ""


@dataclass
class InlineNode(MarkdownNode):
    """Base class for inline elements."""

    pass


@dataclass
class TextNode(InlineNode):
    """Plain text content."""

    text: str = ""


@dataclass
class BoldNode(InlineNode):
    """Bold text (**text**)."""

    text: str = ""


@dataclass
class LinkNode(InlineNode):
    """Link [text](url)."""

    text: str = ""
    url: str = ""


@dataclass
class InlineCodeNode(InlineNode):
    """Inline code `text`."""

    code: str = ""


@dataclass
class RequirementNode(MarkdownNode):
    """Represents an extracted requirement."""

    req_id: str = ""  # e.g., "REQ-001", "NFR-001"
    fully_qualified_id: str = ""  # e.g., "SPEC-100/REQ-001"
    content: str = ""  # The full requirement text
    is_in_code_block: bool = False  # Flag for validation


@dataclass
class MarkdownDocument:
    """High-level representation of a parsed markdown specification document.

    This is the main interface for working with parsed spec documents.
    It provides convenient access to extracted information without
    requiring direct AST traversal.
    """

    file_path: Path
    spec_id: str | None = None
    metadata: dict[str, str] = field(default_factory=dict)
    requirements: list[RequirementNode] = field(default_factory=list)
    headings: list[HeadingNode] = field(default_factory=list)
    raw_tokens: list[Token] = field(default_factory=list)
    raw_content: str = ""

    def get_requirement_ids(self, include_code_blocks: bool = False) -> set[str]:
        """Get all requirement IDs found in the document.

        Args:
            include_code_blocks: If True, include requirements found in code blocks.
                                If False (default), only return requirements
                                from actual markdown content.

        Returns:
            Set of fully qualified requirement IDs (e.g., {"SPEC-100/REQ-001", ...})
        """
        if include_code_blocks:
            return {req.fully_qualified_id for req in self.requirements}
        else:
            return {req.fully_qualified_id for req in self.requirements if not req.is_in_code_block}


class ASTVisitor:
    """Base class for traversing markdown AST nodes.

    Subclass this to implement custom visitors for specific extraction tasks.
    """

    def visit(self, node: MarkdownNode) -> Any:
        """Visit a node and dispatch to the appropriate visit_* method."""
        method_name = f"visit_{node.__class__.__name__}"
        method = getattr(self, method_name, self.generic_visit)
        return method(node)

    def generic_visit(self, node: MarkdownNode) -> Any:
        """Default visit method if no specific visitor is defined."""
        pass


class SpecExtractor:
    """Extracts spec information from markdown tokens.

    This class encapsulates all the logic for finding spec IDs, requirements,
    and metadata in a markdown document's AST.
    """

    # Patterns for extracting information
    SPEC_ID_PATTERN = re.compile(r"\*\*ID\*\*:\s*([A-Z]+-\d+)")
    REQ_ID_PATTERN = re.compile(r"\*\*([A-Z]+-\d{3})\*\*:")
    METADATA_PATTERN = re.compile(r"\*\*([^*]+)\*\*:\s*(.+)")

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.md = MarkdownIt()
        self.document = MarkdownDocument(file_path=file_path)
        self._in_code_block = False

    def parse(self, content: str) -> MarkdownDocument:
        """Parse markdown content and extract spec information.

        Args:
            content: Raw markdown content

        Returns:
            MarkdownDocument with extracted information
        """
        self.document.raw_content = content
        self.document.raw_tokens = self.md.parse(content)

        # Extract spec ID from metadata
        self.document.spec_id = self._extract_spec_id(content)

        # Extract metadata from the document header
        self.document.metadata = self._extract_metadata(self.document.raw_tokens)

        # Extract requirements, tracking code block context
        self.document.requirements = self._extract_requirements(self.document.raw_tokens, content)

        # Extract headings for structure validation
        self.document.headings = self._extract_headings(self.document.raw_tokens)

        return self.document

    def _extract_spec_id(self, content: str) -> str | None:
        """Extract the spec ID from metadata.

        Args:
            content: Raw markdown content

        Returns:
            Spec ID (e.g., "SPEC-001") or None if not found
        """
        match = self.SPEC_ID_PATTERN.search(content)
        return match.group(1) if match else None

    def _extract_metadata(self, tokens: list[Token]) -> dict[str, str]:
        """Extract metadata fields from markdown tokens.

        Metadata is expected to be **Key**: Value format in paragraphs
        near the beginning of the document.

        Args:
            tokens: List of markdown-it tokens

        Returns:
            Dictionary of metadata key-value pairs
        """
        metadata = {}
        in_metadata_section = True  # Metadata is typically at the start
        heading_count = 0

        for token in tokens:
            # Stop looking for metadata after the first major heading
            if token.type == "heading_open":
                heading_count += 1
                if heading_count > 1:  # Allow metadata after title (first heading)
                    in_metadata_section = False

            if in_metadata_section and token.type == "inline" and token.content:
                # Look for **Key**: Value pattern
                for match in self.METADATA_PATTERN.finditer(token.content):
                    key = match.group(1).strip()
                    value = match.group(2).strip()
                    metadata[key] = value

        return metadata

    def _extract_requirements(self, tokens: list[Token], content: str) -> list[RequirementNode]:
        """Extract requirement nodes from markdown tokens.

        This method properly handles code blocks to avoid false positives.

        Args:
            tokens: List of markdown-it tokens
            content: Raw markdown content for context

        Returns:
            List of RequirementNode objects
        """
        requirements = []
        spec_id = self.document.spec_id or "UNKNOWN"

        for token in tokens:
            # Handle code blocks - mark requirements as in_code_block
            if token.type == "fence" or token.type == "code_block":
                # Check if requirement patterns exist in code blocks (for tracking)
                if token.content:
                    for match in self.REQ_ID_PATTERN.finditer(token.content):
                        req_id = match.group(1)
                        fully_qualified = f"{spec_id}/{req_id}"
                        requirements.append(
                            RequirementNode(
                                position=Position(line=token.map[0] + 1 if token.map else 0),
                                raw_content=token.content,
                                req_id=req_id,
                                fully_qualified_id=fully_qualified,
                                content=token.content,
                                is_in_code_block=True,  # Mark as code block requirement
                            )
                        )
                # fence/code_block is a single token, no state tracking needed
                continue

            # Extract from inline content (regular markdown text)
            if token.type == "inline" and token.content:
                for match in self.REQ_ID_PATTERN.finditer(token.content):
                    req_id = match.group(1)
                    fully_qualified = f"{spec_id}/{req_id}"

                    # Get the full line content for context
                    line_number = token.map[0] + 1 if token.map else 0
                    req_content = token.content

                    requirements.append(
                        RequirementNode(
                            position=Position(line=line_number),
                            raw_content=req_content,
                            req_id=req_id,
                            fully_qualified_id=fully_qualified,
                            content=req_content,
                            is_in_code_block=False,
                        )
                    )

        return requirements

    def _extract_headings(self, tokens: list[Token]) -> list[HeadingNode]:
        """Extract heading nodes from markdown tokens.

        Args:
            tokens: List of markdown-it tokens

        Returns:
            List of HeadingNode objects
        """
        headings = []
        i = 0

        while i < len(tokens):
            token = tokens[i]

            if token.type == "heading_open":
                level = int(token.tag[1])  # h1 -> 1, h2 -> 2, etc.
                line_number = token.map[0] + 1 if token.map else 0

                # Next token should be inline content
                if i + 1 < len(tokens) and tokens[i + 1].type == "inline":
                    text = tokens[i + 1].content

                    headings.append(
                        HeadingNode(
                            position=Position(line=line_number),
                            level=level,
                            text=text,
                            raw_content=text,
                        )
                    )

                i += 2  # Skip inline and heading_close
            else:
                i += 1

        return headings


def parse_markdown_file(file_path: Path) -> MarkdownDocument:
    """Parse a markdown file and return a MarkdownDocument.

    This is the main entry point for parsing specification files.

    Args:
        file_path: Path to the markdown file

    Returns:
        MarkdownDocument with extracted information

    Example:
        >>> doc = parse_markdown_file(Path("specs/my-spec.md"))
        >>> print(f"Spec ID: {doc.spec_id}")
        >>> print(f"Requirements: {doc.get_requirement_ids()}")
    """
    content = file_path.read_text(encoding="utf-8")
    extractor = SpecExtractor(file_path)
    return extractor.parse(content)
