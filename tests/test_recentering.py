"""Tests for citygml/transforms/recentering.py — Coordinate recentering."""

import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.transforms.recentering import (
    compute_offset_and_wrap_transform,
)
from gml2step.citygml.core.constants import NS, RECENTERING_DISTANCE_THRESHOLD

_NS_DECL = (
    'xmlns:gml="http://www.opengis.net/gml" '
    'xmlns:bldg="http://www.opengis.net/citygml/building/2.0"'
)


def _make_building_with_coords(coords_3d):
    """Create a Building element with a gml:Polygon containing coords."""
    poslist = " ".join(f"{x} {y} {z}" for x, y, z in coords_3d)
    xml_str = f"""<bldg:Building {_NS_DECL}>
        <gml:Polygon>
            <gml:exterior>
                <gml:LinearRing>
                    <gml:posList>{poslist}</gml:posList>
                </gml:LinearRing>
            </gml:exterior>
        </gml:Polygon>
    </bldg:Building>"""
    return ET.fromstring(xml_str)


class TestComputeOffsetAndWrapTransform:
    """Tests for compute_offset_and_wrap_transform()."""

    def test_no_buildings_returns_original_transform(self, capsys):
        result_transform, offset = compute_offset_and_wrap_transform([], None)
        assert result_transform is None
        assert offset is None

    def test_near_origin_no_offset(self, capsys):
        """Coordinates near origin should not trigger recentering."""
        building = _make_building_with_coords(
            [
                (0.1, 0.1, 0.1),
                (0.2, 0.1, 0.1),
                (0.2, 0.2, 0.1),
                (0.1, 0.2, 0.1),
            ]
        )
        result_transform, offset = compute_offset_and_wrap_transform([building], None)
        assert offset is None

    def test_far_from_origin_applies_offset(self, capsys):
        """Coordinates far from origin should trigger recentering."""
        building = _make_building_with_coords(
            [
                (40000.0, 5000.0, 10.0),
                (40010.0, 5000.0, 10.0),
                (40010.0, 5010.0, 10.0),
                (40000.0, 5010.0, 10.0),
            ]
        )
        result_transform, offset = compute_offset_and_wrap_transform([building], None)
        assert offset is not None
        # Offset should be negative of center
        assert offset[0] == pytest.approx(-40005.0, abs=0.1)
        assert offset[1] == pytest.approx(-5005.0, abs=0.1)
        assert offset[2] == pytest.approx(-10.0, abs=0.1)

    def test_offset_transform_recenters(self, capsys):
        """Wrapped transform should produce coordinates near origin."""
        building = _make_building_with_coords(
            [
                (40000.0, 5000.0, 10.0),
                (40010.0, 5000.0, 10.0),
                (40010.0, 5010.0, 10.0),
                (40000.0, 5010.0, 10.0),
            ]
        )
        result_transform, offset = compute_offset_and_wrap_transform([building], None)
        assert result_transform is not None

        # Apply the transform — should be near origin
        rx, ry, rz = result_transform(40000.0, 5000.0, 10.0)
        assert abs(rx) < 10.0
        assert abs(ry) < 10.0
        assert abs(rz) < 1.0

    def test_wraps_existing_transform(self, capsys):
        """Should wrap an existing xyz_transform with offset."""
        building = _make_building_with_coords(
            [
                (35.0, 139.0, 0.0),
                (35.001, 139.0, 0.0),
                (35.001, 139.001, 0.0),
                (35.0, 139.001, 0.0),
            ]
        )

        # Mock transform that converts to planar (large offset from origin)
        def mock_xyz_transform(x, y, z):
            return (x * 1000, y * 1000, z)

        result_transform, offset = compute_offset_and_wrap_transform(
            [building], mock_xyz_transform
        )
        # Distance from origin = sqrt((35000.5)^2 + (139000.5)^2 + ...) >> 1.0
        assert offset is not None
        assert result_transform is not None

        # Apply wrapped transform — should be near origin
        rx, ry, rz = result_transform(35.0, 139.0, 0.0)
        assert abs(rx) < 1.0
        assert abs(ry) < 1.0

    def test_multiple_buildings(self, capsys):
        """Should scan all buildings to compute center."""
        b1 = _make_building_with_coords(
            [
                (1000.0, 2000.0, 5.0),
                (1010.0, 2000.0, 5.0),
                (1010.0, 2010.0, 5.0),
                (1000.0, 2010.0, 5.0),
            ]
        )
        b2 = _make_building_with_coords(
            [
                (3000.0, 4000.0, 15.0),
                (3010.0, 4000.0, 15.0),
                (3010.0, 4010.0, 15.0),
                (3000.0, 4010.0, 15.0),
            ]
        )
        result_transform, offset = compute_offset_and_wrap_transform([b1, b2], None)
        assert offset is not None
        # Center should be approx midpoint
        assert offset[0] == pytest.approx(-2005.0, abs=10.0)
        assert offset[1] == pytest.approx(-3005.0, abs=10.0)

    def test_empty_polygon_building(self, capsys):
        """Building with no polygon coordinates should not crash."""
        xml_str = f"<bldg:Building {_NS_DECL}></bldg:Building>"
        building = ET.fromstring(xml_str)
        result_transform, offset = compute_offset_and_wrap_transform([building], None)
        assert offset is None

    def test_debug_mode(self, capsys):
        """Debug mode should produce additional log output."""
        building = _make_building_with_coords(
            [
                (10000.0, 20000.0, 50.0),
                (10010.0, 20000.0, 50.0),
                (10010.0, 20010.0, 50.0),
                (10000.0, 20010.0, 50.0),
            ]
        )

        def mock_transform(x, y, z):
            return (x, y, z)

        result_transform, offset = compute_offset_and_wrap_transform(
            [building], mock_transform, debug=True
        )
        captured = capsys.readouterr()
        assert "DEBUG" in captured.out
