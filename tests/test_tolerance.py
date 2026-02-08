"""Tests for citygml.geometry.tolerance — compute_tolerance_from_coords."""

import pytest

from gml2step.citygml.geometry.tolerance import (
    compute_tolerance_from_coords,
    get_precision_mode_description,
)


class TestComputeToleranceFromCoords:
    def test_empty_coords_standard(self):
        assert compute_tolerance_from_coords([], "standard") == 0.01

    def test_empty_coords_ultra(self):
        assert compute_tolerance_from_coords([], "ultra") == 0.00001

    def test_empty_coords_high(self):
        assert compute_tolerance_from_coords([], "high") == 0.001

    def test_empty_coords_maximum(self):
        assert compute_tolerance_from_coords([], "maximum") == 0.0001

    def test_100m_building_standard(self):
        """100m extent at standard → 0.01% = 0.01."""
        coords = [(0, 0, 0), (100, 100, 50)]
        tol = compute_tolerance_from_coords(coords, "standard")
        # extent=100, factor=0.0001 → 0.01
        assert tol == pytest.approx(0.01)

    def test_100m_building_ultra(self):
        """100m extent at ultra → 0.00001% = 0.00001."""
        coords = [(0, 0, 0), (100, 100, 50)]
        tol = compute_tolerance_from_coords(coords, "ultra")
        # extent=100, factor=0.0000001 → 0.00001
        assert tol == pytest.approx(0.00001)

    def test_tiny_geometry(self):
        """Very small extent → clamped to minimum tolerance."""
        coords = [(0, 0, 0), (0.0001, 0.0001, 0.0001)]
        tol = compute_tolerance_from_coords(coords, "standard")
        # extent≈0.0001, raw=0.0001*0.0001=1e-8, min_tol=1e-6
        assert tol >= 1e-6

    def test_huge_geometry(self):
        """Very large extent → clamped to max tolerance."""
        coords = [(0, 0, 0), (1_000_000, 1_000_000, 1_000_000)]
        tol = compute_tolerance_from_coords(coords, "standard")
        assert tol <= 10.0

    def test_single_point(self):
        """All coords same → extent=0 → min tolerance."""
        coords = [(5.0, 5.0, 5.0)]
        tol = compute_tolerance_from_coords(coords, "standard")
        assert tol >= 1e-6

    def test_unknown_precision_mode(self):
        """Unknown mode → uses 'standard' factor."""
        coords = [(0, 0, 0), (100, 100, 50)]
        tol = compute_tolerance_from_coords(coords, "nonexistent")
        standard_tol = compute_tolerance_from_coords(coords, "standard")
        assert tol == standard_tol

    def test_precision_ordering(self):
        """ultra < maximum < high < standard."""
        coords = [(0, 0, 0), (100, 100, 50)]
        ultra = compute_tolerance_from_coords(coords, "ultra")
        maximum = compute_tolerance_from_coords(coords, "maximum")
        high = compute_tolerance_from_coords(coords, "high")
        standard = compute_tolerance_from_coords(coords, "standard")
        assert ultra < maximum < high < standard


class TestGetPrecisionModeDescription:
    def test_known_modes(self):
        for mode in ["standard", "high", "maximum", "ultra"]:
            desc = get_precision_mode_description(mode)
            assert "extent" in desc
            assert mode != "unknown"

    def test_unknown_mode(self):
        assert "Unknown" in get_precision_mode_description("bogus")
