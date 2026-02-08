"""Tests for citygml.parsers.coordinates — parse_poslist, extract_polygon_xy, extract_polygon_xyz."""

import math
import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.parsers.coordinates import (
    extract_polygon_xy,
    extract_polygon_xyz,
    parse_poslist,
)

NS = {"gml": "http://www.opengis.net/gml"}


def _poslist_elem(text: str) -> ET.Element:
    """Create a gml:posList element with given text."""
    elem = ET.Element(f"{{{NS['gml']}}}posList")
    elem.text = text
    return elem


# ── parse_poslist ──────────────────────────────────────────────


class TestParsePoslist:
    def test_3d_coordinates(self):
        elem = _poslist_elem("1.0 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist(elem)
        assert len(result) == 2
        assert result[0] == pytest.approx((1.0, 2.0, 3.0))
        assert result[1] == pytest.approx((4.0, 5.0, 6.0))

    def test_2d_coordinates(self):
        # 4 values → 2D (not divisible by 3)
        elem = _poslist_elem("1.0 2.0 3.0 4.0")
        result = parse_poslist(elem)
        assert len(result) == 2
        assert result[0] == (1.0, 2.0, None)
        assert result[1] == (3.0, 4.0, None)

    def test_empty_text(self):
        elem = _poslist_elem("")
        assert parse_poslist(elem) == []

    def test_none_text(self):
        elem = ET.Element(f"{{{NS['gml']}}}posList")
        elem.text = None
        assert parse_poslist(elem) == []

    def test_whitespace_only(self):
        elem = _poslist_elem("   \t  \n  ")
        assert parse_poslist(elem) == []

    def test_extra_whitespace(self):
        elem = _poslist_elem("  1.0   2.0   3.0  ")
        result = parse_poslist(elem)
        assert len(result) == 1
        assert result[0] == pytest.approx((1.0, 2.0, 3.0))

    def test_single_value_returns_empty(self):
        elem = _poslist_elem("42.0")
        assert parse_poslist(elem) == []

    def test_five_values_returns_empty(self):
        # Not divisible by 2 or 3
        elem = _poslist_elem("1.0 2.0 3.0 4.0 5.0")
        assert parse_poslist(elem) == []

    def test_six_values_detected_as_3d(self):
        # 6 values: divisible by both 2 and 3, but 3D takes priority
        elem = _poslist_elem("1.0 2.0 3.0 4.0 5.0 6.0")
        result = parse_poslist(elem)
        assert len(result) == 2
        for coord in result:
            assert len(coord) == 3
            assert coord[2] is not None  # 3D, not None

    def test_large_coordinates(self):
        """PLATEAU coordinates are typically large (e.g., 139.xxx / 35.xxx)."""
        elem = _poslist_elem("139.681 35.689 25.5 139.682 35.690 30.0")
        result = parse_poslist(elem)
        assert len(result) == 2
        assert result[0] == pytest.approx((139.681, 35.689, 25.5))

    def test_negative_coordinates(self):
        elem = _poslist_elem("-100.5 -200.3 -10.0")
        result = parse_poslist(elem)
        assert len(result) == 1
        assert result[0] == pytest.approx((-100.5, -200.3, -10.0))

    def test_invalid_token_in_poslist(self):
        """Non-numeric tokens should be silently skipped (fallback path)."""
        elem = _poslist_elem("1.0 abc 2.0 3.0")
        result = parse_poslist(elem)
        # After skipping "abc": [1.0, 2.0, 3.0] → 3 values → 1 3D point
        assert len(result) == 1
        assert result[0] == pytest.approx((1.0, 2.0, 3.0))


# ── extract_polygon_xy ──────────────────────────────────────────


def _make_polygon_xml(ext_coords: str, hole_coords: str | None = None) -> ET.Element:
    """Build a gml:Polygon element from coordinate strings."""
    gml = NS["gml"]
    poly = ET.Element(f"{{{gml}}}Polygon")

    # Exterior
    ext = ET.SubElement(poly, f"{{{gml}}}exterior")
    lr = ET.SubElement(ext, f"{{{gml}}}LinearRing")
    pl = ET.SubElement(lr, f"{{{gml}}}posList")
    pl.text = ext_coords

    # Interior (hole)
    if hole_coords:
        interior = ET.SubElement(poly, f"{{{gml}}}interior")
        lr2 = ET.SubElement(interior, f"{{{gml}}}LinearRing")
        pl2 = ET.SubElement(lr2, f"{{{gml}}}posList")
        pl2.text = hole_coords

    return poly


class TestExtractPolygonXY:
    def test_basic_rectangle(self):
        poly = _make_polygon_xml("0.0 0.0 10.0 10.0 0.0 20.0 20.0 0.0 5.0 0.0 0.0 10.0")
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext) == 4  # 4 points (12 values / 3)
        # Check z values collected
        assert 10.0 in z_vals
        assert 20.0 in z_vals
        assert 5.0 in z_vals

    def test_with_hole(self):
        ext_str = "0.0 0.0 0.0 10.0 0.0 0.0 10.0 10.0 0.0 0.0 10.0 0.0 0.0 0.0 0.0"
        hole_str = "2.0 2.0 0.0 8.0 2.0 0.0 8.0 8.0 0.0 2.0 8.0 0.0 2.0 2.0 0.0"
        poly = _make_polygon_xml(ext_str, hole_str)
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext) == 5
        assert len(holes) == 1
        assert len(holes[0]) == 5

    def test_empty_polygon(self):
        poly = _make_polygon_xml("")
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert ext == []
        assert holes == []
        assert z_vals == []


class TestExtractPolygonXYZ:
    def test_basic_3d(self):
        coords = "0.0 0.0 0.0 10.0 0.0 0.0 10.0 10.0 5.0 0.0 10.0 5.0 0.0 0.0 0.0"
        poly = _make_polygon_xml(coords)
        ext, holes = extract_polygon_xyz(poly)
        assert len(ext) == 5
        assert ext[2] == pytest.approx((10.0, 10.0, 5.0))
        assert holes == []

    def test_missing_z_defaults_to_zero(self):
        """2D input → z should be 0.0."""
        # 8 values → 2D (not divisible by 3)
        coords = "1.0 2.0 3.0 4.0 5.0 6.0 7.0 8.0"
        poly = _make_polygon_xml(coords)
        ext, holes = extract_polygon_xyz(poly)
        assert len(ext) == 4
        for _, _, z in ext:
            assert z == 0.0

    def test_with_hole_3d(self):
        ext_str = "0.0 0.0 0.0 10.0 0.0 0.0 10.0 10.0 0.0 0.0 10.0 0.0 0.0 0.0 0.0"
        hole_str = "2.0 2.0 1.0 8.0 2.0 1.0 8.0 8.0 1.0 2.0 8.0 1.0 2.0 2.0 1.0"
        poly = _make_polygon_xml(ext_str, hole_str)
        ext, holes = extract_polygon_xyz(poly)
        assert len(ext) == 5
        assert len(holes) == 1
        assert len(holes[0]) == 5
        # Check hole z values
        for _, _, z in holes[0]:
            assert z == pytest.approx(1.0)


# ── Polygon with gml:pos fallback ────────────────────────────────


class TestPolygonWithPosFallback:
    def test_pos_elements_instead_of_poslist(self):
        """When posList is absent, parser should fall back to multiple gml:pos."""
        gml = NS["gml"]
        poly = ET.Element(f"{{{gml}}}Polygon")
        ext = ET.SubElement(poly, f"{{{gml}}}exterior")
        lr = ET.SubElement(ext, f"{{{gml}}}LinearRing")

        # Use gml:pos instead of gml:posList
        for coords in ["0.0 0.0 0.0", "10.0 0.0 0.0", "10.0 10.0 0.0", "0.0 0.0 0.0"]:
            pos = ET.SubElement(lr, f"{{{gml}}}pos")
            pos.text = coords

        ext_xy, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext_xy) == 4
        assert ext_xy[0] == (0.0, 0.0)
        assert ext_xy[1] == (10.0, 0.0)

        ext_xyz, _ = extract_polygon_xyz(poly)
        assert len(ext_xyz) == 4
        assert ext_xyz[0] == pytest.approx((0.0, 0.0, 0.0))
