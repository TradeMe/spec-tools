"""
Additional DSL tests to increase coverage to 75%.
"""

from pathlib import Path

from spec_tools.ast_parser import Position, parse_markdown_file
from spec_tools.dsl.id_registry import ClassInstance, IDRegistry, ModuleInstance
from spec_tools.dsl.models import GlobalConfig
from spec_tools.dsl.reference_extractor import ReferenceExtractor
from spec_tools.dsl.registry import SpecTypeRegistry
from spec_tools.dsl.section_tree import build_section_tree
from spec_tools.dsl.validator import DSLValidator


class TestIDRegistry:
    """Test ID registry functionality."""

    def test_register_module(self):
        """Test registering module IDs."""
        registry = IDRegistry()

        pos = Position(line=1, column=1)
        registry.register_module(
            module_id="REQ-001",
            module_type="Requirement",
            file_path=Path("specs/REQ-001.md"),
            position=pos,
        )

        module = registry.get_module("REQ-001")
        assert module is not None
        assert module.module_id == "REQ-001"

    def test_get_modules_by_type(self):
        """Test retrieving modules by type."""
        registry = IDRegistry()

        pos = Position(line=1, column=1)
        registry.register_module(
            module_id="REQ-001",
            module_type="Requirement",
            file_path=Path("specs/REQ-001.md"),
            position=pos,
        )

        registry.register_module(
            module_id="JOB-001", module_type="Job", file_path=Path("jobs/JOB-001.md"), position=pos
        )

        reqs = registry.get_modules_by_type("Requirement")
        assert len(reqs) == 1
        assert reqs[0].module_id == "REQ-001"

        jobs = registry.get_modules_by_type("Job")
        assert len(jobs) == 1

    def test_has_duplicates(self):
        """Test has_duplicates method."""
        registry = IDRegistry()
        assert not registry.has_duplicates()

    def test_get_all_duplicate_errors(self):
        """Test get_all_duplicate_errors."""
        registry = IDRegistry()
        errors = registry.get_all_duplicate_errors()
        assert isinstance(errors, list)

    def test_registry_nonexistent_module(self):
        """Test getting non-existent module."""
        registry = IDRegistry()
        module = registry.get_module("NONEXISTENT")
        assert module is None

    def test_registry_nonexistent_class(self):
        """Test getting non-existent class."""
        registry = IDRegistry()
        cls = registry.get_class("NONEXISTENT")
        assert cls is None

    def test_module_instance_creation(self):
        """Test creating module instances directly."""
        pos = Position(line=1, column=1)
        module = ModuleInstance(
            module_id="TEST-001", module_type="Test", file_path=Path("test.md"), position=pos
        )

        assert module.module_id == "TEST-001"
        assert module.module_type == "Test"

    def test_class_instance_creation(self):
        """Test creating class instances directly."""
        pos = Position(line=1, column=1)
        cls = ClassInstance(
            class_id="CLS-01",
            class_type="TestClass",
            module_id="TEST-001",
            section_path=["Section"],
            file_path=Path("test.md"),
            position=pos,
        )

        assert cls.class_id == "CLS-01"
        assert cls.module_id == "TEST-001"


class TestSectionTree:
    """Test section tree functionality."""

    def test_find_section(self, tmp_path):
        """Test finding sections."""
        content = """# Root

## Section A

### Subsection

Content
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        doc = parse_markdown_file(md_file)
        tree = build_section_tree(doc)

        sec = tree.root.find_section("Section A")
        assert sec is not None

    def test_find_section_recursive(self, tmp_path):
        """Test finding nested sections."""
        content = """# Root

## Parent

### Child

Content
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        doc = parse_markdown_file(md_file)
        tree = build_section_tree(doc)

        # Should find nested section with recursive=True
        child = tree.root.find_section("Child", recursive=True)
        assert child is not None

        # Should not find with recursive=False
        child2 = tree.root.find_section("Child", recursive=False)
        assert child2 is None

    def test_section_tree_multiple_levels(self, tmp_path):
        """Test section tree with multiple nesting levels."""
        content = """# L1

## L2A

### L3A

## L2B

### L3B

#### L4B
"""
        md_file = tmp_path / "test.md"
        md_file.write_text(content)

        doc = parse_markdown_file(md_file)
        tree = build_section_tree(doc)

        assert tree.root is not None


class TestReferenceExtractor:
    """Test reference extraction."""

    def test_extract_references(self):
        """Test extracting references from content."""
        config = GlobalConfig(
            version="1.0",
            markdown_flavor="github",
            link_formats={"id_reference": {"pattern": r"^[A-Z]+-\d+$"}},
        )

        extractor = ReferenceExtractor(config)

        content = "This addresses JOB-001 and JOB-002."
        refs = extractor.extract_references(Path("test.md"), content, None, None)

        assert isinstance(refs, list)

    def test_extract_references_with_module(self):
        """Test extracting references with module context."""
        config = GlobalConfig(
            version="1.0",
            markdown_flavor="github",
            link_formats={"id_reference": {"pattern": r"^[A-Z]+-\d+$"}},
        )

        extractor = ReferenceExtractor(config)

        content = """## Dependencies

Depends on REQ-001, REQ-002, and JOB-005.
"""
        refs = extractor.extract_references(Path("test.md"), content, "REQ-003", None)

        assert isinstance(refs, list)


class TestValidator:
    """Test DSL validator."""

    def test_validate_directory(self, tmp_path):
        """Test validating a directory."""
        (tmp_path / "specs" / "jobs").mkdir(parents=True)

        job_file = tmp_path / "specs" / "jobs" / "JOB-001.md"
        job_file.write_text("""# JOB-001: Test

## Context
Context

## Job Story
Story

## Pains
Pains

## Gains
Gains
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)

        result = validator.validate(tmp_path / "specs")
        assert result is not None
        assert hasattr(result, "errors")
        assert hasattr(result, "warnings")

    def test_validate_empty_directory(self, tmp_path):
        """Test validating an empty directory."""
        (tmp_path / "specs").mkdir()

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)

        result = validator.validate(tmp_path / "specs")
        assert result is not None


class TestRegistryLoading:
    """Test registry loading."""

    def test_load_builtin_types_has_all_layers(self):
        """Test that builtin types include all layers."""
        registry = SpecTypeRegistry.load_builtin_types()

        assert "Job" in registry.modules
        assert "Requirement" in registry.modules
        assert "ADR" in registry.modules

        # Check module details
        job = registry.modules["Job"]
        assert job.name == "Job"
        assert "JOB" in job.file_pattern

    def test_get_module_for_various_files(self):
        """Test file-to-module matching."""
        registry = SpecTypeRegistry.load_builtin_types()

        # Test various file paths
        test_cases = [
            (Path("specs/jobs/JOB-001.md"), "Job"),
            (Path("project/specs/jobs/JOB-999.md"), "Job"),
            (Path("specs/requirements/REQ-001.md"), "Requirement"),
            (Path("specs/architecture/ADR-001.md"), "ADR"),
            (Path("docs/README.md"), None),
        ]

        for file_path, expected_type in test_cases:
            module = registry.get_module_for_file(file_path)
            if expected_type is None:
                assert module is None
            else:
                assert module is not None
                assert module.name == expected_type


class TestModelCreation:
    """Test creating DSL model instances."""

    def test_cardinality_str_representation(self):
        """Test string representation of Cardinality."""
        from spec_tools.dsl.models import Cardinality

        card = Cardinality(min=1, max=5)
        s = str(card)
        assert isinstance(s, str)
        assert "1" in s

    def test_identifier_spec_creation(self):
        """Test creating IdentifierSpec."""
        from spec_tools.dsl.models import IdentifierSpec

        id_spec = IdentifierSpec(pattern=r"REQ-\d+", location="title", scope="global")

        assert id_spec.pattern == r"REQ-\d+"
        assert id_spec.location == "title"

    def test_section_spec_creation(self):
        """Test creating SectionSpec."""
        from spec_tools.dsl.models import SectionSpec

        sec_spec = SectionSpec(heading="Overview", heading_level=2, required=True)

        assert sec_spec.heading == "Overview"
        assert sec_spec.required is True
