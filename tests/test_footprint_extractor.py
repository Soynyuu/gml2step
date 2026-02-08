"""Tests for citygml/lod/footprint_extractor.py — Pure Python functions only.

Tests only the functions that do NOT require OpenCASCADE:
- Footprint dataclass
- extract_polygon_xy()
- find_footprint_polygons()
- estimate_building_height()
- parse_citygml_footprints()
"""

import math
import os
import tempfile
import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.lod.footprint_extractor import (
    Footprint,
    extract_polygon_xy,
    find_footprint_polygons,
    estimate_building_height,
    parse_citygml_footprints,
)
from gml2step.citygml.core.constants import NS

# XML namespace prefix for building test fixtures
_NS_DECL = (
    'xmlns:gml="http://www.opengis.net/gml" '
    'xmlns:bldg="http://www.opengis.net/citygml/building/2.0" '
    'xmlns:core="http://www.opengis.net/citygml/2.0" '
    'xmlns:uro="https://www.geospatial.jp/iur/uro/3.1"'
)


def _make_polygon_xml(coords_3d, interior_coords=None):
    """Create a gml:Polygon element from 3D coordinate list."""
    poslist = " ".join(f"{x} {y} {z}" for x, y, z in coords_3d)
    interior_xml = ""
    if interior_coords:
        for ring in interior_coords:
            ring_poslist = " ".join(f"{x} {y} {z}" for x, y, z in ring)
            interior_xml += f"""
            <gml:interior>
                <gml:LinearRing>
                    <gml:posList>{ring_poslist}</gml:posList>
                </gml:LinearRing>
            </gml:interior>"""

    xml_str = f"""<gml:Polygon xmlns:gml="http://www.opengis.net/gml">
        <gml:exterior>
            <gml:LinearRing>
                <gml:posList>{poslist}</gml:posList>
            </gml:LinearRing>
        </gml:exterior>
        {interior_xml}
    </gml:Polygon>"""
    return ET.fromstring(xml_str)


def _make_building_xml(
    footprint_type="lod0FootPrint",
    coords_3d=None,
    measured_height=None,
    uro_height=None,
    uro_building_height=None,
):
    """Create a bldg:Building element."""
    coords_3d = coords_3d or [
        (100.0, 200.0, 10.0),
        (110.0, 200.0, 10.0),
        (110.0, 210.0, 10.0),
        (100.0, 210.0, 10.0),
    ]
    poslist = " ".join(f"{x} {y} {z}" for x, y, z in coords_3d)

    height_xml = ""
    if measured_height is not None:
        height_xml += f"<bldg:measuredHeight>{measured_height}</bldg:measuredHeight>"
    if uro_height is not None:
        height_xml += f"<uro:measuredHeight>{uro_height}</uro:measuredHeight>"
    if uro_building_height is not None:
        height_xml += f"<uro:buildingHeight>{uro_building_height}</uro:buildingHeight>"

    footprint_xml = ""
    if footprint_type == "lod0FootPrint":
        footprint_xml = f"""
        <bldg:lod0FootPrint>
            <gml:MultiSurface>
                <gml:surfaceMember>
                    <gml:Polygon>
                        <gml:exterior>
                            <gml:LinearRing>
                                <gml:posList>{poslist}</gml:posList>
                            </gml:LinearRing>
                        </gml:exterior>
                    </gml:Polygon>
                </gml:surfaceMember>
            </gml:MultiSurface>
        </bldg:lod0FootPrint>"""
    elif footprint_type == "lod0RoofEdge":
        footprint_xml = f"""
        <bldg:lod0RoofEdge>
            <gml:MultiSurface>
                <gml:surfaceMember>
                    <gml:Polygon>
                        <gml:exterior>
                            <gml:LinearRing>
                                <gml:posList>{poslist}</gml:posList>
                            </gml:LinearRing>
                        </gml:exterior>
                    </gml:Polygon>
                </gml:surfaceMember>
            </gml:MultiSurface>
        </bldg:lod0RoofEdge>"""
    elif footprint_type == "groundSurface":
        footprint_xml = f"""
        <bldg:boundedBy>
            <bldg:GroundSurface>
                <bldg:lod2MultiSurface>
                    <gml:MultiSurface>
                        <gml:surfaceMember>
                            <gml:Polygon>
                                <gml:exterior>
                                    <gml:LinearRing>
                                        <gml:posList>{poslist}</gml:posList>
                                    </gml:LinearRing>
                                </gml:exterior>
                            </gml:Polygon>
                        </gml:surfaceMember>
                    </gml:MultiSurface>
                </bldg:lod2MultiSurface>
            </bldg:GroundSurface>
        </bldg:boundedBy>"""
    elif footprint_type == "none":
        footprint_xml = ""

    xml_str = f"""<bldg:Building {_NS_DECL} gml:id="test_bldg_1">
        {height_xml}
        {footprint_xml}
    </bldg:Building>"""
    return ET.fromstring(xml_str)


class TestFootprintDataclass:
    """Tests for Footprint dataclass."""

    def test_creation(self):
        fp = Footprint(
            exterior=[(0, 0), (10, 0), (10, 10), (0, 10)],
            holes=[],
            height=25.0,
            building_id="bldg_001",
        )
        assert fp.height == 25.0
        assert fp.building_id == "bldg_001"
        assert len(fp.exterior) == 4
        assert fp.holes == []

    def test_with_holes(self):
        fp = Footprint(
            exterior=[(0, 0), (20, 0), (20, 20), (0, 20)],
            holes=[[(5, 5), (10, 5), (10, 10), (5, 10)]],
            height=15.0,
            building_id="bldg_002",
        )
        assert len(fp.holes) == 1
        assert len(fp.holes[0]) == 4


class TestExtractPolygonXY:
    """Tests for extract_polygon_xy()."""

    def test_basic_polygon(self):
        poly = _make_polygon_xml(
            [
                (100.0, 200.0, 10.0),
                (110.0, 200.0, 10.0),
                (110.0, 210.0, 10.0),
                (100.0, 210.0, 10.0),
            ]
        )
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext) == 4
        assert ext[0] == (100.0, 200.0)
        assert ext[1] == (110.0, 200.0)
        assert holes == []
        assert len(z_vals) == 4
        assert all(z == 10.0 for z in z_vals)

    def test_polygon_with_holes(self):
        poly = _make_polygon_xml(
            [(0, 0, 0), (20, 0, 0), (20, 20, 0), (0, 20, 0)],
            interior_coords=[[(5, 5, 0), (10, 5, 0), (10, 10, 0), (5, 10, 0)]],
        )
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext) == 4
        assert len(holes) == 1
        assert len(holes[0]) == 4

    def test_z_values_collected(self):
        poly = _make_polygon_xml(
            [
                (0, 0, 5.0),
                (10, 0, 10.0),
                (10, 10, 15.0),
                (0, 10, 20.0),
            ]
        )
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert sorted(z_vals) == [5.0, 10.0, 15.0, 20.0]

    def test_empty_polygon(self):
        xml_str = """<gml:Polygon xmlns:gml="http://www.opengis.net/gml">
            <gml:exterior>
                <gml:LinearRing>
                    <gml:posList></gml:posList>
                </gml:LinearRing>
            </gml:exterior>
        </gml:Polygon>"""
        poly = ET.fromstring(xml_str)
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert ext == []
        assert z_vals == []

    def test_polygon_with_pos_elements(self):
        """Test fallback to gml:pos elements."""
        xml_str = """<gml:Polygon xmlns:gml="http://www.opengis.net/gml">
            <gml:exterior>
                <gml:LinearRing>
                    <gml:pos>100 200 10</gml:pos>
                    <gml:pos>110 200 10</gml:pos>
                    <gml:pos>110 210 10</gml:pos>
                </gml:LinearRing>
            </gml:exterior>
        </gml:Polygon>"""
        poly = ET.fromstring(xml_str)
        ext, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext) == 3


class TestFindFootprintPolygons:
    """Tests for find_footprint_polygons()."""

    def test_lod0_footprint_priority(self):
        """lod0FootPrint should be found first."""
        building = _make_building_xml(footprint_type="lod0FootPrint")
        polys = find_footprint_polygons(building)
        assert len(polys) >= 1

    def test_lod0_roof_edge_fallback(self):
        """lod0RoofEdge should be used when no FootPrint."""
        building = _make_building_xml(footprint_type="lod0RoofEdge")
        polys = find_footprint_polygons(building)
        assert len(polys) >= 1

    def test_ground_surface_fallback(self):
        """GroundSurface should be used as last resort."""
        building = _make_building_xml(footprint_type="groundSurface")
        polys = find_footprint_polygons(building)
        assert len(polys) >= 1

    def test_no_footprint_returns_empty(self):
        building = _make_building_xml(footprint_type="none")
        polys = find_footprint_polygons(building)
        assert polys == []


class TestEstimateBuildingHeight:
    """Tests for estimate_building_height()."""

    def test_measured_height(self):
        building = _make_building_xml(measured_height="25.5")
        height = estimate_building_height(building, 10.0)
        assert height == 25.5

    def test_uro_measured_height(self):
        building = _make_building_xml(uro_height="30.0")
        height = estimate_building_height(building, 10.0)
        assert height == 30.0

    def test_uro_building_height(self):
        building = _make_building_xml(uro_building_height="15.0")
        height = estimate_building_height(building, 10.0)
        assert height == 15.0

    def test_priority_order(self):
        """measuredHeight should have priority over uro height."""
        building = _make_building_xml(measured_height="20.0", uro_height="30.0")
        height = estimate_building_height(building, 10.0)
        assert height == 20.0

    def test_z_range_fallback(self):
        """When no height tags, use Z coordinate range."""
        coords = [
            (0, 0, 5.0),
            (10, 0, 5.0),
            (10, 10, 5.0),
            (0, 10, 5.0),
            (0, 0, 25.0),
            (10, 0, 25.0),
            (10, 10, 25.0),
            (0, 10, 25.0),
        ]
        building = _make_building_xml(footprint_type="lod0FootPrint", coords_3d=coords)
        height = estimate_building_height(building, 10.0)
        assert height == 20.0  # 25 - 5

    def test_default_height_fallback(self):
        building = _make_building_xml(footprint_type="none")
        height = estimate_building_height(building, 42.0)
        assert height == 42.0

    def test_zero_height_uses_default(self):
        building = _make_building_xml(measured_height="0")
        height = estimate_building_height(building, 10.0)
        assert height == 10.0

    def test_negative_height_uses_default(self):
        building = _make_building_xml(measured_height="-5")
        height = estimate_building_height(building, 10.0)
        assert height == 10.0

    def test_non_numeric_height_uses_default(self):
        building = _make_building_xml(measured_height="invalid")
        height = estimate_building_height(building, 10.0)
        assert height == 10.0


class TestParseCitygmlFootprints:
    """Tests for parse_citygml_footprints()."""

    def _write_gml(self, buildings_xml, tmpdir):
        """Write a minimal CityGML file and return its path."""
        gml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
        <core:CityModel {_NS_DECL}>
            {buildings_xml}
        </core:CityModel>"""
        path = os.path.join(tmpdir, "test.gml")
        with open(path, "w") as f:
            f.write(gml_content)
        return path

    def test_single_building(self, tmp_path):
        buildings_xml = """
        <bldg:Building gml:id="bldg_001">
            <bldg:measuredHeight>25.0</bldg:measuredHeight>
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>0 0 0 10 0 0 10 10 0 0 10 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))
        footprints = parse_citygml_footprints(path)
        assert len(footprints) == 1
        assert footprints[0].building_id == "bldg_001"
        assert footprints[0].height == 25.0
        assert len(footprints[0].exterior) >= 3

    def test_limit_parameter(self, tmp_path):
        buildings_xml = ""
        for i in range(5):
            buildings_xml += f"""
            <bldg:Building gml:id="bldg_{i}">
                <bldg:lod0FootPrint>
                    <gml:MultiSurface>
                        <gml:surfaceMember>
                            <gml:Polygon>
                                <gml:exterior>
                                    <gml:LinearRing>
                                        <gml:posList>0 0 0 10 0 0 10 10 0 0 10 0</gml:posList>
                                    </gml:LinearRing>
                                </gml:exterior>
                            </gml:Polygon>
                        </gml:surfaceMember>
                    </gml:MultiSurface>
                </bldg:lod0FootPrint>
            </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))
        footprints = parse_citygml_footprints(path, limit=2)
        assert len(footprints) == 2

    def test_xy_transform(self, tmp_path):
        buildings_xml = """
        <bldg:Building gml:id="bldg_t">
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>1 2 0 3 4 0 5 6 0 7 8 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))

        def double_transform(x, y):
            return (x * 2, y * 2)

        footprints = parse_citygml_footprints(path, xy_transform=double_transform)
        assert len(footprints) == 1
        # Coordinates should be doubled
        assert footprints[0].exterior[0] == (2.0, 4.0)

    def test_skips_building_without_footprint(self, tmp_path):
        buildings_xml = """
        <bldg:Building gml:id="no_footprint">
        </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))
        footprints = parse_citygml_footprints(path)
        assert len(footprints) == 0

    def test_default_height_parameter(self, tmp_path):
        buildings_xml = """
        <bldg:Building gml:id="bldg_no_height">
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>0 0 0 10 0 0 10 10 0 0 10 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))
        footprints = parse_citygml_footprints(path, default_height=42.0)
        # All Z values are 0, so Z range is 0. Should fall back to default.
        assert footprints[0].height == 42.0

    def test_failing_xy_transform(self, tmp_path):
        """xy_transform that raises an exception is caught (lines 294-295)."""
        buildings_xml = """
        <bldg:Building gml:id="bldg_fail_tx">
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>1 2 0 3 4 0 5 6 0 7 8 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))

        def bad_transform(x, y):
            raise RuntimeError("transform failed")

        # Should not raise — caught internally, original coords used
        footprints = parse_citygml_footprints(path, xy_transform=bad_transform)
        assert len(footprints) == 1
        # Original untransformed coordinates should remain
        assert footprints[0].exterior[0] == (1.0, 2.0)

    def test_polygon_with_too_few_vertices(self, tmp_path):
        """Polygon with < 3 exterior vertices is skipped (lines 297-298)."""
        buildings_xml = """
        <bldg:Building gml:id="bldg_tiny">
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>1 2 0 3 4 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        path = self._write_gml(buildings_xml, str(tmp_path))
        footprints = parse_citygml_footprints(path)
        assert len(footprints) == 0


class TestExtractPolygonXYInteriorPosFallback:
    """Cover extract_polygon_xy() interior ring with gml:pos fallback (lines 89-91)."""

    def test_interior_ring_pos_elements(self):
        """Interior ring using gml:pos instead of gml:posList."""
        poly = _make_polygon_xml(
            [(0, 0, 0), (20, 0, 0), (20, 20, 0), (0, 20, 0)],
        )
        gml = "http://www.opengis.net/gml"
        # Remove interior posList and add gml:pos elements instead
        interior = ET.SubElement(poly, f"{{{gml}}}interior")
        lr = ET.SubElement(interior, f"{{{gml}}}LinearRing")
        for coords in ["5 5 1", "10 5 1", "10 10 1", "5 10 1", "5 5 1"]:
            pos = ET.SubElement(lr, f"{{{gml}}}pos")
            pos.text = coords

        ext, holes, z_vals = extract_polygon_xy(poly)
        assert len(ext) == 4
        assert len(holes) == 1
        assert len(holes[0]) == 5
        assert holes[0][0] == (5.0, 5.0)


class TestEstimateBuildingHeightChildText:
    """Cover _first_text() child element text path (lines 183-186)."""

    def test_height_in_child_element(self):
        """Height value stored in a child element, not direct text."""
        xml_str = f"""<bldg:Building {_NS_DECL} gml:id="bldg_child_text">
            <bldg:measuredHeight><child>35.0</child></bldg:measuredHeight>
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>0 0 0 10 0 0 10 10 0 0 10 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        building = ET.fromstring(xml_str)
        height = estimate_building_height(building, 10.0)
        assert height == 35.0
