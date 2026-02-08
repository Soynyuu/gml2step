"""Tests for citygml.streaming.coordinate_optimizer — optimized parsers."""

import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.streaming.coordinate_optimizer import (
    NUMPY_AVAILABLE,
    benchmark_parsers,
    parse_pos_numpy,
    parse_pos_optimized,
    parse_poslist_auto,
    parse_poslist_numpy,
    parse_poslist_optimized,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _elem(text: str) -> ET.Element:
    """Create a dummy element with the given text."""
    e = ET.Element("posList")
    e.text = text
    return e


# ===================================================================
# parse_poslist_optimized
# ===================================================================


class TestParsePoslistOptimized:
    """Tests for parse_poslist_optimized()."""

    def test_3d_coords(self):
        """Parses 3D coordinates correctly."""
        elem = _elem("1.0 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist_optimized(elem)
        assert result == [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]

    def test_2d_coords(self):
        """Parses 2D coordinates (6 values = 3D takes precedence)."""
        # 4 values → 2D (2 points)
        elem = _elem("1.0 2.0 3.0 4.0")
        result = parse_poslist_optimized(elem)
        assert result == [(1.0, 2.0, None), (3.0, 4.0, None)]

    def test_empty_text(self):
        """Returns empty list for empty text."""
        elem = _elem("")
        assert parse_poslist_optimized(elem) == []

    def test_none_text(self):
        """Returns empty list for None text."""
        elem = ET.Element("posList")
        elem.text = None
        assert parse_poslist_optimized(elem) == []

    def test_single_3d_point(self):
        """Single 3D coordinate."""
        elem = _elem("35.68 139.77 10.5")
        result = parse_poslist_optimized(elem)
        assert len(result) == 1
        assert result[0] == (35.68, 139.77, 10.5)

    def test_invalid_dimensionality(self):
        """5 values → not divisible by 2 or 3 → empty."""
        elem = _elem("1.0 2.0 3.0 4.0 5.0")
        # 5 values: not %3==0, not %2==0 → empty
        assert parse_poslist_optimized(elem) == []

    def test_single_value(self):
        """Single value → not divisible by 2 or 3 → empty."""
        elem = _elem("42.0")
        assert parse_poslist_optimized(elem) == []

    def test_non_numeric_tokens_filtered(self):
        """Non-numeric tokens are filtered via slow path."""
        elem = _elem("1.0 abc 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist_optimized(elem)
        # After filtering "abc": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0] → 3D
        assert result == [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]

    def test_all_invalid_tokens(self):
        """All invalid tokens → empty list."""
        elem = _elem("abc def ghi")
        assert parse_poslist_optimized(elem) == []

    def test_whitespace_handling(self):
        """Extra whitespace is handled correctly."""
        elem = _elem("  1.0  2.0  3.0  ")
        result = parse_poslist_optimized(elem)
        assert result == [(1.0, 2.0, 3.0)]

    def test_large_polygon(self):
        """Handles polygons with many vertices."""
        # 100 vertices = 300 values
        coords = " ".join(f"{i}.0 {i + 1}.0 {i + 2}.0" for i in range(100))
        elem = _elem(coords)
        result = parse_poslist_optimized(elem)
        assert len(result) == 100

    def test_negative_coordinates(self):
        """Handles negative coordinates."""
        elem = _elem("-1.5 -2.5 -3.5")
        result = parse_poslist_optimized(elem)
        assert result == [(-1.5, -2.5, -3.5)]

    def test_scientific_notation(self):
        """Handles scientific notation."""
        elem = _elem("1e2 2.5e1 3.0e0")
        result = parse_poslist_optimized(elem)
        assert result == [(100.0, 25.0, 3.0)]


# ===================================================================
# parse_poslist_numpy
# ===================================================================


class TestParsePoslistNumpy:
    """Tests for parse_poslist_numpy()."""

    def test_3d_coords(self):
        """Parses 3D coordinates correctly."""
        elem = _elem("1.0 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist_numpy(elem)
        assert len(result) == 2
        assert result[0] == pytest.approx((1.0, 2.0, 3.0))
        assert result[1] == pytest.approx((4.0, 5.0, 6.0))

    def test_2d_coords(self):
        """Parses 2D coordinates."""
        elem = _elem("1.0 2.0 3.0 4.0")
        result = parse_poslist_numpy(elem)
        assert len(result) == 2
        assert result[0][:2] == pytest.approx((1.0, 2.0))
        assert result[1][:2] == pytest.approx((3.0, 4.0))

    def test_empty_text(self):
        """Returns empty list for empty text."""
        elem = _elem("")
        assert parse_poslist_numpy(elem) == []

    def test_none_text(self):
        """Returns empty list for None text."""
        elem = ET.Element("posList")
        elem.text = None
        assert parse_poslist_numpy(elem) == []

    def test_alpha_fallback(self):
        """Falls back to optimized parser for alphabetic content."""
        elem = _elem("1.0 abc 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist_numpy(elem)
        # Should still work via optimized fallback
        assert result == [(1.0, 2.0, 3.0), (4.0, 5.0, 6.0)]

    def test_memoization_cache(self):
        """Repeated calls with same text use cache."""
        elem = _elem("1.0 2.0 3.0")
        r1 = parse_poslist_numpy(elem)
        r2 = parse_poslist_numpy(elem)
        assert r1 == r2

    def test_large_polygon(self):
        """Handles large polygons efficiently."""
        coords = " ".join(f"{i}.0 {i + 1}.0 {i + 2}.0" for i in range(100))
        elem = _elem(coords)
        result = parse_poslist_numpy(elem)
        assert len(result) == 100

    def test_matches_optimized_output(self):
        """NumPy and optimized versions produce identical results."""
        text = "35.68 139.77 10.5 35.69 139.78 11.0 35.70 139.79 12.5"
        elem = _elem(text)
        opt = parse_poslist_optimized(elem)
        npy = parse_poslist_numpy(elem)
        assert len(opt) == len(npy)
        for a, b in zip(opt, npy):
            assert a == pytest.approx(b)


# ===================================================================
# parse_pos_optimized / parse_pos_numpy
# ===================================================================


class TestParsePosOptimized:
    """Tests for parse_pos_optimized()."""

    def test_single_3d_point(self):
        """Returns single 3D coordinate."""
        elem = _elem("35.68 139.77 10.5")
        result = parse_pos_optimized(elem)
        assert result == (35.68, 139.77, 10.5)

    def test_empty_returns_none(self):
        """Returns None for empty text."""
        elem = _elem("")
        assert parse_pos_optimized(elem) is None

    def test_multi_point_returns_first(self):
        """Returns first coordinate from multi-point text."""
        elem = _elem("1.0 2.0 3.0 4.0 5.0 6.0")
        result = parse_pos_optimized(elem)
        assert result == (1.0, 2.0, 3.0)


class TestParsePosNumpy:
    """Tests for parse_pos_numpy()."""

    def test_single_3d_point(self):
        """Returns single 3D coordinate."""
        elem = _elem("35.68 139.77 10.5")
        result = parse_pos_numpy(elem)
        assert result == pytest.approx((35.68, 139.77, 10.5))

    def test_empty_returns_none(self):
        """Returns None for empty text."""
        elem = _elem("")
        assert parse_pos_numpy(elem) is None


# ===================================================================
# parse_poslist_auto
# ===================================================================


class TestAutoParser:
    """Tests for auto-selected parser."""

    def test_auto_works(self):
        """Auto parser produces valid output."""
        elem = _elem("1.0 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist_auto(elem)
        assert len(result) == 2
        assert result[0] == pytest.approx((1.0, 2.0, 3.0))

    def test_numpy_available_flag(self):
        """NUMPY_AVAILABLE is a boolean."""
        assert isinstance(NUMPY_AVAILABLE, bool)


# ===================================================================
# benchmark_parsers
# ===================================================================


class TestBenchmarkParsers:
    """Tests for benchmark_parsers()."""

    def test_returns_dict_with_optimized_key(self):
        """Benchmark returns timing results."""
        result = benchmark_parsers("1.0 2.0 3.0 4.0 5.0 6.0", iterations=10)
        assert "optimized" in result
        assert result["optimized"] > 0

    @pytest.mark.skipif(not NUMPY_AVAILABLE, reason="numpy not installed")
    def test_numpy_benchmark_present(self):
        """NumPy benchmark present when numpy available."""
        result = benchmark_parsers("1.0 2.0 3.0 4.0 5.0 6.0", iterations=1000)
        assert "numpy" in result
        assert "numpy_speedup" in result

    def test_small_iterations(self):
        """Works with minimal iterations."""
        result = benchmark_parsers("1.0 2.0 3.0", iterations=1)
        assert "optimized" in result
