"""Tests for the structure linter."""

from spec_check.structure_linter import StructureLinter


class TestStructureLinter:
    """Test suite for StructureLinter."""

    def test_valid_single_file_structure(self, tmp_path):
        """Test valid structure with spec and test file."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("# Feature Spec")

        # Create corresponding test file
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text("def test_something(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_specs == 1
        assert result.specs_with_tests == 1
        assert len(result.specs_without_tests) == 0

    def test_valid_directory_structure(self, tmp_path):
        """Test valid structure with spec and test directory."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("# Feature Spec")

        # Create corresponding test directory
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        feature_tests_dir = tests_dir / "feature"
        feature_tests_dir.mkdir()
        (feature_tests_dir / "test_main.py").write_text("def test_something(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_specs == 1
        assert result.specs_with_tests == 1

    def test_kebab_case_to_snake_case(self, tmp_path):
        """Test conversion from kebab-case spec to snake_case test."""
        # Create spec with kebab-case name
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "my-feature-spec.md").write_text("# My Feature")

        # Create test with snake_case name
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_my_feature_spec.py").write_text("def test_something(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_specs == 1
        assert result.specs_with_tests == 1

    def test_spec_without_test(self, tmp_path):
        """Test spec without corresponding test file."""
        # Create spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("# Feature Spec")

        # Create tests dir but no matching test
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert not result.is_valid
        assert result.total_specs == 1
        assert result.specs_with_tests == 0
        assert "feature.md" in result.specs_without_tests

    def test_test_without_spec(self, tmp_path):
        """Test file without corresponding spec (allowed for unit tests)."""
        # Create empty specs dir
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        # Create test file without spec
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_utils.py").write_text("def test_helper(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        # Should pass because all specs have tests (there are no specs)
        assert result.is_valid
        assert result.total_specs == 0
        # But should report test without spec
        assert "test_utils.py" in result.test_dirs_without_specs

    def test_multiple_specs_all_valid(self, tmp_path):
        """Test multiple specs all with corresponding tests."""
        # Create specs
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature1.md").write_text("# Feature 1")
        (spec_dir / "feature2.md").write_text("# Feature 2")

        # Create corresponding test files
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature1.py").write_text("def test_1(): pass")
        (tests_dir / "test_feature2.py").write_text("def test_2(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert result.is_valid
        assert result.total_specs == 2
        assert result.specs_with_tests == 2

    def test_multiple_specs_some_missing(self, tmp_path):
        """Test multiple specs with some missing tests."""
        # Create specs
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature1.md").write_text("# Feature 1")
        (spec_dir / "feature2.md").write_text("# Feature 2")

        # Create test for only one
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature1.py").write_text("def test_1(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert not result.is_valid
        assert result.total_specs == 2
        assert result.specs_with_tests == 1
        assert "feature2.md" in result.specs_without_tests

    def test_nested_spec_paths(self, tmp_path):
        """Test specs in subdirectories."""
        # Create nested spec
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        api_spec_dir = spec_dir / "api"
        api_spec_dir.mkdir()
        (api_spec_dir / "endpoints.md").write_text("# API Endpoints")

        # This should work if we have tests/api/test_endpoints.py
        # or tests/api/endpoints/ structure
        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        # Should find the nested spec but not find matching test
        assert not result.is_valid
        assert result.total_specs >= 1

    def test_spec_to_test_mapping(self, tmp_path):
        """Test the spec-to-test mapping."""
        # Create spec and test
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("# Feature")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text("def test(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        assert "feature.md" in result.spec_to_test_mapping
        assert result.spec_to_test_mapping["feature.md"] == "test_feature.py"

    def test_result_string_representation(self, tmp_path):
        """Test the string representation of results."""
        # Create minimal setup
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("# Feature")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        result_str = str(result)
        assert "SPEC-TEST STRUCTURE REPORT" in result_str
        assert "Specs with tests:" in result_str
        assert "feature.md" in result_str

    def test_get_expected_test_paths(self, tmp_path):
        """Test getting expected test paths for a spec."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "my-feature.md"

        linter = StructureLinter(root_dir=tmp_path)
        expected_paths = linter.get_expected_test_paths(spec_file)

        # Should return both possible paths
        assert len(expected_paths) == 2
        # Should include test file
        assert any(p.name == "test_my_feature.py" for p in expected_paths)
        # Should include test directory
        assert any(p.name == "my_feature" and p.parent.name == "tests" for p in expected_paths)

    def test_find_test_for_spec(self, tmp_path):
        """Test finding the test for a spec."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "feature.md"
        spec_file.write_text("# Feature")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_feature.py"
        test_file.write_text("def test(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        found_test = linter.find_test_for_spec(spec_file)

        assert found_test is not None
        assert found_test == test_file

    def test_get_spec_for_test(self, tmp_path):
        """Test finding the spec for a test file."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        spec_file = spec_dir / "my-feature.md"
        spec_file.write_text("# Feature")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        test_file = tests_dir / "test_my_feature.py"
        test_file.write_text("def test(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        found_spec = linter.get_spec_for_test(test_file)

        assert found_spec is not None
        assert found_spec == spec_file

    def test_init_file_ignored(self, tmp_path):
        """Test that __init__.py files are ignored."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "__init__.py").write_text("")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        # __init__.py should not be considered a test file
        assert "__init__.py" not in str(result.test_dirs_without_specs)

    def test_all_valid_structure_shows_passed(self, tmp_path):
        """Test that fully valid structure shows PASSED message."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()
        (spec_dir / "feature.md").write_text("# Feature")

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_feature.py").write_text("def test_something(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        # Should show valid mappings and PASSED message
        assert result.is_valid
        result_str = str(result)
        assert "✅ Valid Spec-Test Mappings:" in result_str
        assert "feature.md → test_feature.py" in result_str
        assert "✅ Structure validation PASSED" in result_str

    def test_tests_without_specs_shown(self, tmp_path):
        """Test that tests without corresponding specs are shown in output."""
        spec_dir = tmp_path / "specs"
        spec_dir.mkdir()

        tests_dir = tmp_path / "tests"
        tests_dir.mkdir()
        (tests_dir / "test_orphan.py").write_text("def test_something(): pass")

        linter = StructureLinter(root_dir=tmp_path)
        result = linter.lint()

        # Should show tests without specs warning
        result_str = str(result)
        assert "⚠️  Test Files/Directories Without Corresponding Specs:" in result_str
        assert "test_orphan.py" in result_str
