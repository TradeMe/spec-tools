"""
Tests for Pydantic-based DSL type definitions.

This test suite validates the new Pydantic-based approach to specification
type definitions, replacing the YAML-based approach.
"""

from pathlib import Path

import pytest

from spec_tools.dsl.models import Cardinality, IdentifierSpec, SpecModule
from spec_tools.dsl.registry import SpecTypeRegistry


class TestPydanticModels:
    """Test Pydantic model validation and behavior."""

    def test_cardinality_creation(self):
        """Test creating cardinality instances."""
        # Exactly one
        c1 = Cardinality(min=1, max=1)
        assert str(c1) == "1"

        # Zero or one
        c2 = Cardinality(min=0, max=1)
        assert str(c2) == "0..1"

        # One or more
        c3 = Cardinality(min=1, max=None)
        assert str(c3) == "1..*"

        # Zero or more
        c4 = Cardinality(min=0, max=None)
        assert str(c4) == "0..*"

    def test_cardinality_parse(self):
        """Test parsing cardinality from strings."""
        assert Cardinality.parse("1") == Cardinality(min=1, max=1)
        assert Cardinality.parse("0..1") == Cardinality(min=0, max=1)
        assert Cardinality.parse("1..*") == Cardinality(min=1, max=None)
        assert Cardinality.parse("0..*") == Cardinality(min=0, max=None)

    def test_cardinality_validation(self):
        """Test that cardinality validates max >= min."""
        with pytest.raises(ValueError, match="max.*must be.*min"):
            Cardinality(min=5, max=2)

    def test_identifier_spec_validation(self):
        """Test that identifier pattern is validated as regex."""
        # Valid regex
        id1 = IdentifierSpec(pattern=r"REQ-\d{3}")
        assert id1.pattern == r"REQ-\d{3}"

        # Invalid regex should raise error
        with pytest.raises(ValueError, match="Invalid regex"):
            IdentifierSpec(pattern=r"[invalid(regex")

    def test_spec_module_requires_section(self):
        """Test that modules must have at least one required section."""
        from spec_tools.dsl.models import SectionSpec

        # Valid: has required section
        module1 = SpecModule(
            name="Test",
            description="Test module",
            file_pattern=r"test\.md",
            location_pattern=r"test/",
            sections=[SectionSpec(heading="Required", heading_level=2, required=True)],
        )
        assert module1.name == "Test"

        # Invalid: no required sections
        with pytest.raises(ValueError, match="at least one required section"):
            SpecModule(
                name="Test",
                description="Test module",
                file_pattern=r"test\.md",
                location_pattern=r"test/",
                sections=[SectionSpec(heading="Optional", heading_level=2, required=False)],
            )


class TestSpecTypeRegistry:
    """Test type registry functionality."""

    def test_create_empty_registry(self):
        """Test creating an empty registry."""
        registry = SpecTypeRegistry()
        assert len(registry.modules) == 0
        assert len(registry.classes) == 0

    def test_register_module(self):
        """Test registering a module."""
        from spec_tools.dsl.builtin_types import RequirementModule

        registry = SpecTypeRegistry()
        module = RequirementModule()

        registry.register_module(module)

        assert "Requirement" in registry.modules
        assert registry.get_module("Requirement") == module

    def test_register_duplicate_module_fails(self):
        """Test that registering duplicate module names fails."""
        from spec_tools.dsl.builtin_types import RequirementModule

        registry = SpecTypeRegistry()
        module = RequirementModule()

        registry.register_module(module)

        with pytest.raises(ValueError, match="already registered"):
            registry.register_module(module)

    def test_load_builtin_types(self):
        """Test loading built-in types."""
        registry = SpecTypeRegistry.load_builtin_types()

        assert "Requirement" in registry.modules
        assert "Contract" in registry.modules
        assert "ADR" in registry.modules

    def test_get_module_for_file(self):
        """Test finding module for a file."""
        registry = SpecTypeRegistry.load_builtin_types()

        # Should match Requirement
        req_file = Path("tests/fixtures/requirements/REQ-001.md")
        module = registry.get_module_for_file(req_file)
        assert module is not None
        assert module.name == "Requirement"

        # Should match Contract
        contract_file = Path("tests/fixtures/contracts/CTR-001.md")
        module = registry.get_module_for_file(contract_file)
        assert module is not None
        assert module.name == "Contract"

        # Should not match anything
        other_file = Path("tests/fixtures/other/file.md")
        module = registry.get_module_for_file(other_file)
        assert module is None


class TestBuiltinTypes:
    """Test built-in type definitions."""

    def test_requirement_module(self):
        """Test Requirement module definition."""
        from spec_tools.dsl.builtin_types import RequirementModule

        module = RequirementModule()

        assert module.name == "Requirement"
        assert module.file_pattern == r"^REQ-\d{3}\.md$"
        assert module.location_pattern == r"requirements/"

        # Should have identifier
        assert module.identifier is not None
        assert module.identifier.pattern == r"REQ-\d{3}"

        # Should have required sections
        assert len(module.sections) > 0
        assert any(s.required for s in module.sections)

        # Should have references
        assert len(module.references) > 0

    def test_contract_module(self):
        """Test Contract module definition."""
        from spec_tools.dsl.builtin_types import ContractModule

        module = ContractModule()

        assert module.name == "Contract"
        assert module.file_pattern == r"^CTR-\d{3}\.md$"
        assert module.location_pattern == r"contracts/"

    def test_adr_module(self):
        """Test ADR module definition."""
        from spec_tools.dsl.builtin_types import ArchitectureDecisionModule

        module = ArchitectureDecisionModule()

        assert module.name == "ADR"
        assert module.file_pattern == r"^ADR-\d{3}\.md$"
        assert module.location_pattern == r"adrs/"


class TestPythonPackageLoading:
    """Test loading type definitions from Python packages."""

    def test_load_from_package(self):
        """Test loading types from a Python package."""
        package_path = Path("tests/fixtures/dsl_projects/valid_project_py/spec_types")

        registry = SpecTypeRegistry.load_from_package(package_path)

        # Should have loaded all three modules
        assert "Requirement" in registry.modules
        assert "Contract" in registry.modules
        assert "ADR" in registry.modules

    def test_load_from_nonexistent_package_fails(self):
        """Test that loading from non-existent path fails."""
        package_path = Path("nonexistent/path")

        with pytest.raises(FileNotFoundError):
            SpecTypeRegistry.load_from_package(package_path)

    def test_load_from_non_package_fails(self):
        """Test that loading from non-package directory fails."""
        package_path = Path("tests/fixtures")  # Has no __init__.py

        with pytest.raises(ImportError, match="Not a Python package"):
            SpecTypeRegistry.load_from_package(package_path)


class TestFileMatching:
    """Test file matching logic."""

    def test_requirement_file_matching(self):
        """Test that requirement files match correctly."""
        from spec_tools.dsl.builtin_types import RequirementModule

        module = RequirementModule()

        # Should match
        assert module.matches_file(Path("requirements/REQ-001.md"))
        assert module.matches_file(Path("project/requirements/REQ-999.md"))

        # Should not match
        assert not module.matches_file(Path("requirements/req-001.md"))  # lowercase
        assert not module.matches_file(Path("requirements/REQ-1.md"))  # wrong format
        assert not module.matches_file(Path("contracts/REQ-001.md"))  # wrong location

    def test_contract_file_matching(self):
        """Test that contract files match correctly."""
        from spec_tools.dsl.builtin_types import ContractModule

        module = ContractModule()

        # Should match
        assert module.matches_file(Path("contracts/CTR-001.md"))
        assert module.matches_file(Path("project/contracts/CTR-999.md"))

        # Should not match
        assert not module.matches_file(Path("contracts/ctr-001.md"))  # lowercase
        assert not module.matches_file(Path("requirements/CTR-001.md"))  # wrong location
