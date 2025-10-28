"""
Additional DSL tests to increase coverage to 75%.
"""

from pathlib import Path

from spec_check.ast_parser import Position, parse_markdown_file
from spec_check.dsl.id_registry import ClassInstance, IDRegistry, ModuleInstance
from spec_check.dsl.models import GlobalConfig
from spec_check.dsl.reference_extractor import ReferenceExtractor
from spec_check.dsl.registry import SpecTypeRegistry
from spec_check.dsl.section_tree import build_section_tree
from spec_check.dsl.validator import DSLValidator


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

    def test_validate_missing_required_section(self, tmp_path):
        """Test validating a spec with missing required sections.

        This test reproduces issue #25 where validator.py incorrectly
        accesses section_def.level instead of section_def.heading_level.
        """
        (tmp_path / "specs" / "jobs").mkdir(parents=True)

        # Create a Job spec missing the required "Context" section
        job_file = tmp_path / "specs" / "jobs" / "JOB-999.md"
        job_file.write_text("""# JOB-999: Test Job Missing Context

## Job Story
Story content

## Pains
Pains content

## Gains
Gains content
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)

        # This should trigger the code path that accesses section_def.level
        # Before the fix, this raises AttributeError: 'SectionSpec' object has no attribute 'level'
        result = validator.validate(tmp_path / "specs")

        assert result is not None
        # Should have errors for missing required section
        assert len(result.errors) > 0
        # Check that one of the errors is about missing Context section
        error_messages = [e.message for e in result.errors]
        assert any("Context" in msg for msg in error_messages)

    def test_reference_cardinality_validation(self, tmp_path):
        """Test validating reference cardinality constraints.

        This test reproduces issue #28 where reference_resolver.py calls
        ref_def.validate_count() and ref_def.parse_cardinality() which
        don't exist on the Reference model.

        The Requirement module requires at least one "addresses" reference
        to a Job (cardinality min=1). This test creates a Requirement without
        any Job references, triggering cardinality validation.
        """
        (tmp_path / "specs" / "jobs").mkdir(parents=True)
        (tmp_path / "specs" / "requirements").mkdir(parents=True)

        # Create a Job spec
        job_file = tmp_path / "specs" / "jobs" / "JOB-001.md"
        job_file.write_text("""# JOB-001: Test Job

## Context
Context content

## Job Story
Story content

## Pains
Pains content

## Gains
Gains content
""")

        # Create a Requirement spec with missing "addresses" reference
        # This violates the cardinality constraint (min=1)
        req_file = tmp_path / "specs" / "requirements" / "REQ-001.md"
        req_file.write_text("""# REQ-001: Test Requirement

## Overview
This requirement doesn't address any jobs, violating cardinality.

## Specification
Some spec content.

## Acceptance Criteria
- Criterion 1
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)

        # This should trigger cardinality validation code path
        # Before the fix, this raises:
        # AttributeError: 'Reference' object has no attribute 'validate_count'
        result = validator.validate(tmp_path / "specs")

        assert result is not None
        # Should detect the cardinality violation
        assert len(result.errors) > 0
        error_messages = [e.message for e in result.errors]
        # Should have an error about missing "addresses" reference
        assert any("addresses" in msg.lower() for msg in error_messages)

    def test_file_path_reference_resolution(self, tmp_path):
        """Test resolving cross-document references using file paths.

        This test reproduces issue #36 where validate-dsl cannot resolve
        references that use relative file paths instead of module IDs.

        ADR documents often link to each other using standard markdown
        file path links like './011-deployment-architecture.md' which should
        resolve to module ID 'ADR-011'.
        """
        (tmp_path / "specs" / "architecture").mkdir(parents=True)

        # Create first ADR with a known module ID (using correct pattern ADR-NNN.md)
        adr_011 = tmp_path / "specs" / "architecture" / "ADR-011.md"
        adr_011.write_text("""# ADR-011: Deployment Architecture

## Status
Accepted

## Context
Deployment architecture decisions.

## Decision
Use cloud infrastructure.

## Consequences
Improved scalability.
""")

        # Create second ADR that references the first using a file path
        adr_015 = tmp_path / "specs" / "architecture" / "ADR-015.md"
        adr_015.write_text("""# ADR-015: Developer Access Control Strategy

## Status
Accepted

## Context
Access control strategy.

## Decision
Implement RBAC.

## Adheres To
- [ADR-011: Deployment Architecture](./ADR-011.md)

## Consequences
Better security.
""")

        registry = SpecTypeRegistry.load_builtin_types()
        validator = DSLValidator(registry)

        # Before the fix, this fails with:
        # Module reference './ADR-011' not found
        result = validator.validate(tmp_path / "specs")

        assert result is not None

        # The file path reference should resolve successfully
        # Check that there's no error about './ADR-011' not being found
        error_messages = [e.message for e in result.errors]
        assert not any("'./ADR-011'" in msg for msg in error_messages), (
            f"File path reference should resolve, but got errors: {error_messages}"
        )


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
        from spec_check.dsl.models import Cardinality

        card = Cardinality(min=1, max=5)
        s = str(card)
        assert isinstance(s, str)
        assert "1" in s

    def test_identifier_spec_creation(self):
        """Test creating IdentifierSpec."""
        from spec_check.dsl.models import IdentifierSpec

        id_spec = IdentifierSpec(pattern=r"REQ-\d+", location="title", scope="global")

        assert id_spec.pattern == r"REQ-\d+"
        assert id_spec.location == "title"

    def test_section_spec_creation(self):
        """Test creating SectionSpec."""
        from spec_check.dsl.models import SectionSpec

        sec_spec = SectionSpec(heading="Overview", heading_level=2, required=True)

        assert sec_spec.heading == "Overview"
        assert sec_spec.required is True
