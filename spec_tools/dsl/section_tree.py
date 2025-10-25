"""
Section tree transformation for markdown AST.

Transforms flat markdown AST into hierarchical section trees where each heading
owns all subsequent content until the next heading of equal or higher level.

This is Pass 2 of the multi-pass validation architecture.
"""

from dataclasses import dataclass, field
from typing import Any

from spec_tools.ast_parser import MarkdownDocument, Position


@dataclass
class SectionNode:
    """
    Represents a hierarchical section in a markdown document.

    A section consists of a heading and all content (paragraphs, lists, code blocks,
    and subsections) until the next heading of equal or higher level.
    """

    heading: str
    """The heading text (without markdown formatting)."""

    level: int
    """The heading level (1-6)."""

    position: Position
    """Source position of the heading."""

    content: list[Any] = field(default_factory=list)
    """Content nodes (paragraphs, lists, code blocks) in this section."""

    subsections: list["SectionNode"] = field(default_factory=list)
    """Child sections (lower-level headings)."""

    section_id: str | None = None
    """Optional section identifier extracted from heading or anchor."""

    parent: "SectionNode | None" = None
    """Parent section (for traversal)."""

    def get_all_content(self) -> list[Any]:
        """Get all content nodes in this section (excluding subsections)."""
        return self.content

    def get_subsection(self, heading: str) -> "SectionNode | None":
        """Find a direct subsection by heading text."""
        for subsection in self.subsections:
            if subsection.heading == heading:
                return subsection
        return None

    def find_section(self, heading: str, recursive: bool = True) -> "SectionNode | None":
        """
        Find a section by heading text.

        Args:
            heading: The heading text to search for
            recursive: If True, search all descendants; if False, only direct subsections

        Returns:
            The found section, or None
        """
        # Check direct subsections
        for subsection in self.subsections:
            if subsection.heading == heading:
                return subsection

        # Recursively search if requested
        if recursive:
            for subsection in self.subsections:
                found = subsection.find_section(heading, recursive=True)
                if found:
                    return found

        return None

    def find_by_id(self, section_id: str, recursive: bool = True) -> "SectionNode | None":
        """
        Find a section by its ID.

        Args:
            section_id: The section ID to search for
            recursive: If True, search all descendants; if False, only direct subsections

        Returns:
            The found section, or None
        """
        # Check self
        if self.section_id == section_id:
            return self

        # Check subsections
        for subsection in self.subsections:
            if subsection.section_id == section_id:
                return subsection

        # Recursively search if requested
        if recursive:
            for subsection in self.subsections:
                found = subsection.find_by_id(section_id, recursive=True)
                if found:
                    return found

        return None

    def get_path(self) -> list[str]:
        """Get the path from root to this section as list of headings."""
        path = []
        current = self
        while current:
            path.insert(0, current.heading)
            current = current.parent
        return path

    def __repr__(self) -> str:
        """String representation for debugging."""
        id_part = f" (id={self.section_id})" if self.section_id else ""
        subsection_count = len(self.subsections)
        content_count = len(self.content)
        return (
            f"SectionNode(heading='{self.heading}', level={self.level}{id_part}, "
            f"subsections={subsection_count}, content_nodes={content_count})"
        )


@dataclass
class SectionTree:
    """
    Complete section tree for a markdown document.

    The root represents the entire document, with top-level sections as children.
    """

    root: SectionNode
    """Root section (usually the document title or a synthetic root)."""

    document_id: str | None = None
    """Document identifier (module ID) if present."""

    file_path: str | None = None
    """Source file path."""

    def find_section(self, heading: str) -> SectionNode | None:
        """Find any section in the tree by heading text."""
        return self.root.find_section(heading)

    def find_by_id(self, section_id: str) -> SectionNode | None:
        """Find any section in the tree by ID."""
        return self.root.find_by_id(section_id)

    def get_all_sections(self) -> list[SectionNode]:
        """Get all sections in the tree (depth-first traversal)."""
        result = []

        def traverse(section: SectionNode) -> None:
            result.append(section)
            for subsection in section.subsections:
                traverse(subsection)

        traverse(self.root)
        return result

    def get_sections_at_level(self, level: int) -> list[SectionNode]:
        """Get all sections at a specific heading level."""
        return [s for s in self.get_all_sections() if s.level == level]


def build_section_tree(document: MarkdownDocument) -> SectionTree:
    """
    Transform a flat markdown AST into a hierarchical section tree.

    This implements Pass 2 of the multi-pass validation architecture.

    Algorithm:
    - Use a stack to track the current section hierarchy
    - For each heading, pop sections until we find the correct parent
    - Content between headings belongs to the most recent heading

    Args:
        document: Parsed markdown document with flat AST

    Returns:
        Hierarchical section tree
    """
    # Create synthetic root section for the document
    root = SectionNode(
        heading=document.spec_id or "Document",
        level=0,
        position=Position(line=1, column=1),
        section_id=document.spec_id,
    )

    # Stack of (level, section) for tracking hierarchy
    stack: list[tuple[int, SectionNode]] = [(0, root)]

    # Process all nodes from the AST
    # For now, we work with headings from the document
    # In a full implementation, we'd iterate through all AST nodes

    for heading_node in document.headings:
        # Create section for this heading
        section = SectionNode(
            heading=heading_node.text,
            level=heading_node.level,
            position=heading_node.position,
            section_id=extract_section_id(heading_node.text),
        )

        # Pop stack until we find the correct parent level
        while stack and stack[-1][0] >= heading_node.level:
            stack.pop()

        # Parent is now the top of stack
        if stack:
            parent_level, parent_section = stack[-1]
            parent_section.subsections.append(section)
            section.parent = parent_section
        else:
            # Should not happen with synthetic root at level 0
            root.subsections.append(section)
            section.parent = root

        # Push this section onto the stack
        stack.append((heading_node.level, section))

    # Build section tree result
    file_path_str = str(document.file_path) if hasattr(document, "file_path") else None
    return SectionTree(root=root, document_id=document.spec_id, file_path=file_path_str)


def extract_section_id(heading_text: str) -> str | None:
    """
    Extract an identifier from a heading.

    Supports formats:
    - ID-001: Some Title  -> ID-001
    - Some Title (ID-001) -> ID-001
    - ID-001 Some Title   -> ID-001

    Args:
        heading_text: The heading text

    Returns:
        Extracted ID or None
    """
    import re

    # Pattern 1: ID at start with colon
    match = re.match(r"^([A-Z]+-\d+):", heading_text)
    if match:
        return match.group(1)

    # Pattern 2: ID in parentheses
    match = re.search(r"\(([A-Z]+-\d+)\)", heading_text)
    if match:
        return match.group(1)

    # Pattern 3: ID at start with space
    match = re.match(r"^([A-Z]+-\d+)\s", heading_text)
    if match:
        return match.group(1)

    # Pattern 4: ID-001/SUB-001 format
    match = re.match(r"^([A-Z]+-\d+/[A-Z]+-\d+):", heading_text)
    if match:
        return match.group(1)

    return None
