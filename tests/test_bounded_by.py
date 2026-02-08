"""Tests for citygml/lod/bounded_by.py — Pure Python functions only.

Tests only the functions that do NOT require OpenCASCADE:
- find_bounded_surfaces()
- count_bounded_by_faces()
"""

import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.lod.bounded_by import (
    find_bounded_surfaces,
    count_bounded_by_faces,
)
from gml2step.citygml.core.constants import NS

_NS_DECL = (
    'xmlns:gml="http://www.opengis.net/gml" '
    'xmlns:bldg="http://www.opengis.net/citygml/building/2.0"'
)

_SIMPLE_POLYGON = """
<gml:Polygon>
    <gml:exterior>
        <gml:LinearRing>
            <gml:posList>0 0 0 10 0 0 10 10 0 0 10 0</gml:posList>
        </gml:LinearRing>
    </gml:exterior>
</gml:Polygon>"""


def _make_building_with_surfaces(
    wall=0, roof=0, ground=0, outer_ceiling=0, outer_floor=0, closure=0, use_lod2=False
):
    """Build a bldg:Building element with specified bounded surfaces."""
    parts = []
    for surface_type, count in [
        ("WallSurface", wall),
        ("RoofSurface", roof),
        ("GroundSurface", ground),
        ("OuterCeilingSurface", outer_ceiling),
        ("OuterFloorSurface", outer_floor),
        ("ClosureSurface", closure),
    ]:
        for i in range(count):
            if use_lod2:
                poly_wrapper = f"""
                <bldg:lod2MultiSurface>
                    <gml:MultiSurface>
                        <gml:surfaceMember>
                            {_SIMPLE_POLYGON}
                        </gml:surfaceMember>
                    </gml:MultiSurface>
                </bldg:lod2MultiSurface>"""
            else:
                poly_wrapper = f"""
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        {_SIMPLE_POLYGON}
                    </gml:surfaceMember>
                </gml:MultiSurface>"""

            parts.append(f"""
            <bldg:boundedBy>
                <bldg:{surface_type}>
                    {poly_wrapper}
                </bldg:{surface_type}>
            </bldg:boundedBy>""")

    xml_str = f"""<bldg:Building {_NS_DECL} gml:id="test_bldg">
        {"".join(parts)}
    </bldg:Building>"""
    return ET.fromstring(xml_str)


class TestFindBoundedSurfaces:
    """Tests for find_bounded_surfaces()."""

    def test_empty_building(self):
        xml = f"<bldg:Building {_NS_DECL}></bldg:Building>"
        building = ET.fromstring(xml)
        surfaces = find_bounded_surfaces(building)
        assert surfaces == []

    def test_wall_surfaces(self):
        building = _make_building_with_surfaces(wall=3)
        surfaces = find_bounded_surfaces(building)
        assert len(surfaces) == 3

    def test_roof_surfaces(self):
        building = _make_building_with_surfaces(roof=2)
        surfaces = find_bounded_surfaces(building)
        assert len(surfaces) == 2

    def test_ground_surfaces(self):
        building = _make_building_with_surfaces(ground=1)
        surfaces = find_bounded_surfaces(building)
        assert len(surfaces) == 1

    def test_all_surface_types(self):
        building = _make_building_with_surfaces(
            wall=2,
            roof=1,
            ground=1,
            outer_ceiling=1,
            outer_floor=1,
            closure=1,
        )
        surfaces = find_bounded_surfaces(building)
        assert len(surfaces) == 7

    def test_mixed_surfaces(self):
        building = _make_building_with_surfaces(wall=4, roof=2, ground=1)
        surfaces = find_bounded_surfaces(building)
        assert len(surfaces) == 7

    def test_returns_elements(self):
        building = _make_building_with_surfaces(wall=1)
        surfaces = find_bounded_surfaces(building)
        assert all(isinstance(s, ET.Element) for s in surfaces)

    def test_surface_types_correct(self):
        building = _make_building_with_surfaces(wall=1, roof=1)
        surfaces = find_bounded_surfaces(building)
        tags = {s.tag.split("}")[-1] for s in surfaces}
        assert "WallSurface" in tags
        assert "RoofSurface" in tags


class TestCountBoundedByFaces:
    """Tests for count_bounded_by_faces()."""

    def test_empty_building(self):
        xml = f"<bldg:Building {_NS_DECL}></bldg:Building>"
        building = ET.fromstring(xml)
        assert count_bounded_by_faces(building) == 0

    def test_single_surface_single_polygon(self):
        building = _make_building_with_surfaces(wall=1)
        count = count_bounded_by_faces(building)
        assert count == 1

    def test_multiple_surfaces(self):
        building = _make_building_with_surfaces(wall=3, roof=2)
        count = count_bounded_by_faces(building)
        assert count == 5

    def test_lod2_wrapped_polygons(self):
        building = _make_building_with_surfaces(wall=2, use_lod2=True)
        count = count_bounded_by_faces(building)
        assert count == 2

    def test_all_surface_types_counted(self):
        building = _make_building_with_surfaces(
            wall=1,
            roof=1,
            ground=1,
            outer_ceiling=1,
            outer_floor=1,
            closure=1,
        )
        count = count_bounded_by_faces(building)
        assert count == 6

    def test_multi_polygon_surface(self):
        """Surface with multiple polygons in a MultiSurface."""
        xml_str = f"""<bldg:Building {_NS_DECL} gml:id="multi_poly_bldg">
            <bldg:boundedBy>
                <bldg:WallSurface>
                    <bldg:lod2MultiSurface>
                        <gml:MultiSurface>
                            <gml:surfaceMember>
                                {_SIMPLE_POLYGON}
                            </gml:surfaceMember>
                            <gml:surfaceMember>
                                {_SIMPLE_POLYGON}
                            </gml:surfaceMember>
                            <gml:surfaceMember>
                                {_SIMPLE_POLYGON}
                            </gml:surfaceMember>
                        </gml:MultiSurface>
                    </bldg:lod2MultiSurface>
                </bldg:WallSurface>
            </bldg:boundedBy>
        </bldg:Building>"""
        building = ET.fromstring(xml_str)
        count = count_bounded_by_faces(building)
        assert count == 3

    def test_lod3_priority_over_lod2(self):
        """LOD3 geometry should be counted if present."""
        xml_str = f"""<bldg:Building {_NS_DECL} gml:id="lod3_bldg">
            <bldg:boundedBy>
                <bldg:WallSurface>
                    <bldg:lod3MultiSurface>
                        <gml:MultiSurface>
                            <gml:surfaceMember>
                                {_SIMPLE_POLYGON}
                            </gml:surfaceMember>
                            <gml:surfaceMember>
                                {_SIMPLE_POLYGON}
                            </gml:surfaceMember>
                        </gml:MultiSurface>
                    </bldg:lod3MultiSurface>
                </bldg:WallSurface>
            </bldg:boundedBy>
        </bldg:Building>"""
        building = ET.fromstring(xml_str)
        count = count_bounded_by_faces(building)
        assert count == 2
