"""
Reference extraction from markdown documents.

This is Pass 6 of the multi-pass validation architecture.
Extracts links from markdown and classifies them as module references,
class references, or external references based on link targets.
"""

import re
from dataclasses import dataclass
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from spec_tools.ast_parser import Position
from spec_tools.dsl.type_definitions import GlobalConfig, ModuleDefinition


@dataclass
class Reference:
    """Represents a reference extracted from a document."""

    source_file: Path
    """Source file containing the reference."""

    source_module_id: str | None
    """Module ID of the source document."""

    source_section: str | None
    """Section path where reference appears."""

    link_text: str
    """The link text (what the user sees)."""

    link_target: str
    """The link target (href)."""

    reference_type: str
    """Type: module_reference, class_reference, or external_reference."""

    position: Position
    """Source position of the link."""

    relationship: str | None = None
    """Inferred relationship type (e.g., 'implements', 'depends_on')."""

    context: str | None = None
    """Surrounding text for better error messages."""


class ReferenceExtractor:
    """
    Extracts references from markdown documents.

    This implements Pass 6 of the multi-pass validation architecture.
    """

    def __init__(self, config: GlobalConfig):
        """
        Initialize the reference extractor.

        Args:
            config: Global DSL configuration
        """
        self.config = config
        self.md = MarkdownIt()

    def extract_references(
        self,
        file_path: Path,
        content: str,
        module_id: str | None,
        module_def: ModuleDefinition | None,
    ) -> list[Reference]:
        """
        Extract all references from a markdown document.

        Args:
            file_path: Path to the markdown file
            content: Markdown content
            module_id: Module ID of this document
            module_def: Module definition for type-aware extraction

        Returns:
            List of extracted references
        """
        references = []

        # Parse markdown to get tokens
        tokens = self.md.parse(content)

        # Track current section for context
        current_section = None

        # Recursively extract links from tokens
        for token in tokens:
            # Update current section when we see headings
            if token.type == "heading_open":
                # Find the next inline token to get heading text
                idx = tokens.index(token)
                if idx + 1 < len(tokens) and tokens[idx + 1].type == "inline":
                    current_section = self._extract_text(tokens[idx + 1])

            # Extract links from inline tokens
            if token.type == "inline":
                refs = self._extract_from_inline(
                    token, file_path, module_id, current_section, module_def
                )
                references.extend(refs)

        return references

    def _extract_from_inline(
        self,
        token: Token,
        file_path: Path,
        module_id: str | None,
        section: str | None,
        module_def: ModuleDefinition | None,
    ) -> list[Reference]:
        """Extract references from an inline token (which may contain links)."""
        references = []

        if token.children:
            for child in token.children:
                if child.type == "link_open":
                    # Get link target
                    link_target = child.attrGet("href") or ""

                    # Find the text token
                    idx = token.children.index(child)
                    link_text = ""
                    if idx + 1 < len(token.children) and token.children[idx + 1].type == "text":
                        link_text = token.children[idx + 1].content

                    # Get position
                    position = Position(
                        line=child.map[0] + 1 if child.map else 1,
                        column=0,
                    )

                    # Classify reference type
                    ref_type = self._classify_reference(link_target)

                    # Infer relationship if possible
                    relationship = self._infer_relationship(
                        link_text, link_target, section, module_def
                    )

                    # Extract context
                    context = self._extract_text(token)

                    references.append(
                        Reference(
                            source_file=file_path,
                            source_module_id=module_id,
                            source_section=section,
                            link_text=link_text,
                            link_target=link_target,
                            reference_type=ref_type,
                            position=position,
                            relationship=relationship,
                            context=context,
                        )
                    )

        return references

    def _classify_reference(self, link_target: str) -> str:
        """
        Classify a link target as module, class, or external reference.

        Args:
            link_target: The link href

        Returns:
            Reference type: module_reference, class_reference, or external_reference
        """
        # External reference?
        if link_target.startswith(("http://", "https://", "mailto:", "ftp://")):
            return "external_reference"

        # Class reference (has fragment)?
        if "#" in link_target:
            return "class_reference"

        # Remove .md extension if present
        clean_target = link_target.replace(".md", "")

        # Check if looks like an ID
        if re.match(r"^[A-Z]+-\d+", clean_target):
            return "module_reference"

        # Check against configured link formats
        link_formats = self.config.link_formats

        if "id_reference" in link_formats:
            pattern = link_formats["id_reference"].get("pattern", "")
            if pattern and re.match(pattern, clean_target):
                return "module_reference"

        if "class_reference" in link_formats:
            pattern = link_formats["class_reference"].get("pattern", "")
            if pattern and re.match(pattern, link_target):
                return "class_reference"

        # Default to module reference for non-external, non-fragment links
        return "module_reference"

    def _infer_relationship(
        self,
        link_text: str,
        link_target: str,
        section: str | None,
        module_def: ModuleDefinition | None,
    ) -> str | None:
        """
        Infer the relationship type from context.

        Uses heuristics based on:
        - Link text keywords
        - Section name
        - Module definition reference constraints

        Args:
            link_text: The visible link text
            link_target: The link href
            section: Current section name
            module_def: Module definition

        Returns:
            Inferred relationship name or None
        """
        # Keyword-based heuristics
        text_lower = link_text.lower()

        if any(kw in text_lower for kw in ["implements", "implementation of"]):
            return "implements"
        if any(kw in text_lower for kw in ["depends on", "requires", "prerequisite"]):
            return "depends_on"
        if any(kw in text_lower for kw in ["validated by", "tested by", "test case"]):
            return "validated_by"
        if any(kw in text_lower for kw in ["supersedes", "replaces", "obsoletes"]):
            return "supersedes"
        if any(kw in text_lower for kw in ["see also", "related to", "reference"]):
            return "see_also"

        # Section-based heuristics
        if section:
            section_lower = section.lower()
            if "test" in section_lower or "validation" in section_lower:
                return "validated_by"
            if "implementation" in section_lower:
                return "implements"
            if "dependencies" in section_lower or "prerequisites" in section_lower:
                return "depends_on"

        # Check module definition for context
        if module_def and section:
            # Find section definition
            for sect_def in module_def.sections:
                if sect_def.heading == section:
                    # If section has only one reference type defined, use it
                    section_refs = [
                        ref
                        for ref in module_def.references
                        if not ref.allowed_sections or section in ref.allowed_sections
                    ]
                    if len(section_refs) == 1:
                        return section_refs[0].name

        return None

    def _extract_text(self, token: Token) -> str:
        """Extract plain text from a token and its children."""
        if token.type == "text":
            return token.content

        if token.children:
            return "".join(self._extract_text(child) for child in token.children)

        return ""


def build_reference_graph(references: list[Reference]) -> dict[str, list[Reference]]:
    """
    Build a reference graph from extracted references.

    Args:
        references: List of extracted references

    Returns:
        Dictionary mapping source module ID to outgoing references
    """
    graph: dict[str, list[Reference]] = {}

    for ref in references:
        if ref.source_module_id:
            if ref.source_module_id not in graph:
                graph[ref.source_module_id] = []
            graph[ref.source_module_id].append(ref)

    return graph


def detect_circular_references(
    graph: dict[str, list[Reference]], allow_circular: bool = True
) -> list[list[str]]:
    """
    Detect circular dependencies in the reference graph.

    Args:
        graph: Reference graph
        allow_circular: If False, return all cycles; if True, return empty list

    Returns:
        List of circular dependency chains
    """
    if allow_circular:
        return []

    cycles = []
    visited = set()
    rec_stack = set()

    def visit(node: str, path: list[str]) -> None:
        """DFS to detect cycles."""
        visited.add(node)
        rec_stack.add(node)
        path.append(node)

        if node in graph:
            for ref in graph[node]:
                # Extract target ID from link_target
                target = _extract_target_id(ref.link_target)
                if not target:
                    continue

                if target not in visited:
                    visit(target, path[:])
                elif target in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(target)
                    cycle = path[cycle_start:] + [target]
                    cycles.append(cycle)

        rec_stack.remove(node)

    for node in graph:
        if node not in visited:
            visit(node, [])

    return cycles


def _extract_target_id(link_target: str) -> str | None:
    """Extract module or class ID from a link target."""
    # Remove .md extension
    target = link_target.replace(".md", "")

    # If has fragment, take the part before or after depending on format
    if "#" in target:
        # Format: MODULE-ID#CLASS-ID
        if not target.startswith("#"):
            return target.split("#")[0]
        # Format: #CLASS-ID (same document)
        else:
            return None

    return target
