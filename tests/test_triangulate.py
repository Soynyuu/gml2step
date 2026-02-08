"""Tests for citygml.geometry.builders — triangulate_polygon_fan."""

import pytest

from gml2step.citygml.geometry.builders import triangulate_polygon_fan


class TestTriangulatePolygonFan:
    def test_less_than_3_vertices(self):
        assert triangulate_polygon_fan([]) == []
        assert triangulate_polygon_fan([(0, 0, 0)]) == []
        assert triangulate_polygon_fan([(0, 0, 0), (1, 0, 0)]) == []

    def test_triangle(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        result = triangulate_polygon_fan(verts)
        assert len(result) == 1
        assert result[0] == verts

    def test_quad(self):
        verts = [(0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0)]
        result = triangulate_polygon_fan(verts)
        assert len(result) == 2
        # Fan: pivot=v0, (v0,v1,v2) and (v0,v2,v3)
        assert result[0] == [verts[0], verts[1], verts[2]]
        assert result[1] == [verts[0], verts[2], verts[3]]

    def test_pentagon(self):
        verts = [(0, 0, 0), (1, 0, 0), (1.5, 0.5, 0), (1, 1, 0), (0, 1, 0)]
        result = triangulate_polygon_fan(verts)
        assert len(result) == 3  # n-2 = 5-2 = 3

    def test_n_vertices_gives_n_minus_2_triangles(self):
        for n in range(3, 20):
            verts = [(i, 0, 0) for i in range(n)]
            result = triangulate_polygon_fan(verts)
            assert len(result) == n - 2

    def test_all_triangles_share_pivot(self):
        verts = [(0, 0, 0), (1, 0, 0), (2, 1, 0), (1, 2, 0), (0, 1, 0)]
        result = triangulate_polygon_fan(verts)
        for tri in result:
            assert tri[0] == verts[0]

    def test_3d_coordinates_preserved(self):
        verts = [(0, 0, 5), (10, 0, 10), (10, 10, 15), (0, 10, 20)]
        result = triangulate_polygon_fan(verts)
        # All original z values should be present
        all_z = {pt[2] for tri in result for pt in tri}
        assert all_z == {5, 10, 15, 20}
