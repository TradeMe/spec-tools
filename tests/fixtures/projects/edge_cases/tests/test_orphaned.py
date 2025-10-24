"""Tests with orphaned requirement references."""

import pytest


class TestOrphanedRequirements:
    """Tests that reference non-existent requirements."""

    @pytest.mark.req("SPEC-304/REQ-001")
    def test_existing_requirement(self):
        """Test for an existing requirement."""
        assert True

    @pytest.mark.req("SPEC-304/REQ-003")
    def test_missing_requirement_1(self):
        """Test references SPEC-304/REQ-003 which doesn't exist in the spec."""
        assert True

    @pytest.mark.req("SPEC-304/REQ-004")
    def test_missing_requirement_2(self):
        """Test references SPEC-304/REQ-004 which doesn't exist in the spec."""
        assert True

    @pytest.mark.req("SPEC-999/REQ-001")
    def test_completely_missing_spec(self):
        """Test references SPEC-999 which doesn't exist at all."""
        assert True

    @pytest.mark.req("SPEC-304/NFR-001")
    def test_non_existent_nfr(self):
        """Test references a non-functional requirement that doesn't exist."""
        assert True


class TestUncoveredRequirements:
    """Note: SPEC-304/REQ-002 and REQ-005 have no tests at all."""

    def test_unrelated_functionality(self):
        """This test has no requirement marker."""
        assert True
