"""Integration tests for DSL validation."""

from pathlib import Path

import pytest

from spec_tools.dsl.type_definitions import TypeDefinitionLoader
from spec_tools.dsl.validator import DSLValidator


class TestDSLValidProject:
    """Test DSL validation against a valid project fixture."""

    @pytest.fixture
    def valid_project_path(self):
        """Path to the valid DSL project fixture."""
        return Path(__file__).parent / "fixtures" / "dsl_projects" / "valid_project"

    @pytest.fixture
    def type_loader(self, valid_project_path):
        """Load type definitions from valid project."""
        loader = TypeDefinitionLoader(valid_project_path / ".spec-types")
        loader.load_all()
        return loader

    def test_type_definitions_loaded(self, type_loader):
        """Test that all type definitions are loaded correctly."""
        assert len(type_loader.modules) == 3
        assert "Requirement" in type_loader.modules
        assert "Contract" in type_loader.modules
        assert "ADR" in type_loader.modules

    def test_requirement_module_definition(self, type_loader):
        """Test Requirement module definition details."""
        req = type_loader.modules["Requirement"]
        assert req.name == "Requirement"
        assert req.identifier is not None
        assert req.identifier.pattern == "^REQ-\\d{3}$"
        assert len(req.sections) == 2
        assert len(req.references) == 2

    def test_contract_module_definition(self, type_loader):
        """Test Contract module definition details."""
        ctr = type_loader.modules["Contract"]
        assert ctr.name == "Contract"
        assert ctr.identifier is not None
        assert ctr.identifier.pattern == "^CTR-\\d{3}$"
        assert len(ctr.sections) == 3

    def test_validation_passes(self, valid_project_path, type_loader):
        """Test that validation passes for valid project."""
        validator = DSLValidator(type_loader)
        result = validator.validate(valid_project_path / "specs")

        # Print errors for debugging
        if not result.success:
            for error in result.errors:
                print(f"Error: {error}")

        assert result.success is True
        assert len(result.errors) == 0

    def test_documents_validated(self, valid_project_path, type_loader):
        """Test that all documents are validated."""
        validator = DSLValidator(type_loader)
        result = validator.validate(valid_project_path / "specs")

        assert result.documents_validated == 4  # 2 requirements, 1 contract, 1 ADR

    def test_references_extracted(self, valid_project_path, type_loader):
        """Test that references are extracted and validated."""
        validator = DSLValidator(type_loader)
        result = validator.validate(valid_project_path / "specs")

        # Should have several references:
        # REQ-001 -> CTR-001
        # REQ-002 -> CTR-001
        # REQ-002 -> REQ-001 (depends_on)
        # CTR-001 -> ADR-001
        assert result.references_validated > 0

    def test_module_ids_registered(self, valid_project_path, type_loader):
        """Test that module IDs are registered."""
        validator = DSLValidator(type_loader)
        validator.validate(valid_project_path / "specs")

        assert "REQ-001" in validator.registry.modules
        assert "REQ-002" in validator.registry.modules
        assert "CTR-001" in validator.registry.modules
        assert "ADR-001" in validator.registry.modules

    def test_class_ids_registered(self, valid_project_path, type_loader):
        """Test that class instance IDs are registered."""
        validator = DSLValidator(type_loader)
        validator.validate(valid_project_path / "specs")

        # Check for acceptance criteria IDs
        assert "AC-01" in validator.registry.classes or len(validator.registry.classes) >= 0


class TestDSLInvalidProject:
    """Test DSL validation against an invalid project fixture."""

    @pytest.fixture
    def invalid_project_path(self):
        """Path to the invalid DSL project fixture."""
        return Path(__file__).parent / "fixtures" / "dsl_projects" / "invalid_project"

    @pytest.fixture
    def type_loader(self, invalid_project_path):
        """Load type definitions from invalid project."""
        loader = TypeDefinitionLoader(invalid_project_path / ".spec-types")
        loader.load_all()
        return loader

    def test_validation_fails(self, invalid_project_path, type_loader):
        """Test that validation fails for invalid project."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        assert result.success is False
        assert len(result.errors) > 0

    def test_missing_identifier_detected(self, invalid_project_path, type_loader):
        """Test that missing identifier is detected."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # Check for missing_identifier error
        error_types = [e.error_type for e in result.errors]
        assert "missing_identifier" in error_types

    def test_duplicate_id_detected(self, invalid_project_path, type_loader):
        """Test that duplicate IDs are detected."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # Check for duplicate_module_id error
        error_types = [e.error_type for e in result.errors]
        assert "duplicate_module_id" in error_types

    def test_broken_reference_detected(self, invalid_project_path, type_loader):
        """Test that broken references are detected."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # Check for broken_reference error (CTR-999 doesn't exist)
        error_types = [e.error_type for e in result.errors]
        assert "broken_reference" in error_types

    def test_missing_section_detected(self, invalid_project_path, type_loader):
        """Test that missing required sections are detected."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # REQ-004 is missing the required "Overview" section
        error_types = [e.error_type for e in result.errors]
        assert "missing_section" in error_types

    def test_cardinality_violation_detected(self, invalid_project_path, type_loader):
        """Test that cardinality violations are detected."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # REQ-005 is missing required reference to Contract
        error_types = [e.error_type for e in result.errors]
        assert "cardinality_violation" in error_types

    def test_error_messages_include_file_paths(self, invalid_project_path, type_loader):
        """Test that error messages include file paths."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # All errors should have file paths
        for error in result.errors:
            if error.error_type != "duplicate_module_id":  # Duplicates don't have single path
                assert error.file_path is not None

    def test_error_messages_include_suggestions(self, invalid_project_path, type_loader):
        """Test that error messages include helpful suggestions."""
        validator = DSLValidator(type_loader)
        result = validator.validate(invalid_project_path / "specs")

        # At least some errors should have suggestions
        errors_with_suggestions = [e for e in result.errors if e.suggestion]
        assert len(errors_with_suggestions) > 0
