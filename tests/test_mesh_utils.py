"""Tests for plateau/mesh_utils.py — JIS X 0410 mesh code calculation."""

import pytest

from gml2step.plateau.mesh_utils import (
    latlon_to_mesh_1st,
    latlon_to_mesh_2nd,
    latlon_to_mesh_3rd,
    latlon_to_mesh_half,
    latlon_to_mesh_quarter,
    get_neighboring_meshes_3rd,
)

# Known reference points (verified against official mesh code databases)
# Tokyo Station: 35.681236, 139.767125
TOKYO_STATION_LAT = 35.681236
TOKYO_STATION_LON = 139.767125

# Osaka Station: 34.702485, 135.495951
OSAKA_STATION_LAT = 34.702485
OSAKA_STATION_LON = 135.495951

# Sapporo Station: 43.068625, 141.350769
SAPPORO_STATION_LAT = 43.068625
SAPPORO_STATION_LON = 141.350769


class TestMesh1st:
    """Tests for 1st mesh code (80km grid, 4 digits)."""

    def test_tokyo_station(self):
        result = latlon_to_mesh_1st(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert len(result) == 4
        assert result == "5339"

    def test_osaka_station(self):
        result = latlon_to_mesh_1st(OSAKA_STATION_LAT, OSAKA_STATION_LON)
        assert len(result) == 4
        assert result == "5235"

    def test_sapporo_station(self):
        result = latlon_to_mesh_1st(SAPPORO_STATION_LAT, SAPPORO_STATION_LON)
        assert len(result) == 4
        assert result == "6441"

    def test_returns_string(self):
        result = latlon_to_mesh_1st(35.0, 135.0)
        assert isinstance(result, str)


class TestMesh2nd:
    """Tests for 2nd mesh code (10km grid, 6 digits)."""

    def test_tokyo_station(self):
        result = latlon_to_mesh_2nd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert len(result) == 6
        # Should start with 1st mesh code
        assert result.startswith("5339")

    def test_starts_with_1st_mesh(self):
        mesh1 = latlon_to_mesh_1st(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        mesh2 = latlon_to_mesh_2nd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert mesh2.startswith(mesh1)

    def test_osaka_station(self):
        result = latlon_to_mesh_2nd(OSAKA_STATION_LAT, OSAKA_STATION_LON)
        assert len(result) == 6
        assert result.startswith("5235")


class TestMesh3rd:
    """Tests for 3rd mesh code (1km grid, 8 digits)."""

    def test_tokyo_station(self):
        result = latlon_to_mesh_3rd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert len(result) == 8
        assert result.startswith("5339")

    def test_starts_with_2nd_mesh(self):
        mesh2 = latlon_to_mesh_2nd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        mesh3 = latlon_to_mesh_3rd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert mesh3.startswith(mesh2)

    def test_osaka_station(self):
        result = latlon_to_mesh_3rd(OSAKA_STATION_LAT, OSAKA_STATION_LON)
        assert len(result) == 8

    def test_all_digits(self):
        result = latlon_to_mesh_3rd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert result.isdigit()


class TestMeshHalf:
    """Tests for 1/2 mesh code (500m grid, 9 digits)."""

    def test_tokyo_station(self):
        result = latlon_to_mesh_half(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert len(result) == 9

    def test_starts_with_3rd_mesh(self):
        mesh3 = latlon_to_mesh_3rd(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        mesh_half = latlon_to_mesh_half(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert mesh_half.startswith(mesh3)

    def test_last_digit_1_to_4(self):
        result = latlon_to_mesh_half(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert result[-1] in "1234"


class TestMeshQuarter:
    """Tests for 1/4 mesh code (250m grid, 10 digits)."""

    def test_tokyo_station(self):
        result = latlon_to_mesh_quarter(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert len(result) == 10

    def test_starts_with_half_mesh(self):
        mesh_half = latlon_to_mesh_half(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        mesh_quarter = latlon_to_mesh_quarter(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert mesh_quarter.startswith(mesh_half)

    def test_last_digit_1_to_4(self):
        result = latlon_to_mesh_quarter(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        assert result[-1] in "1234"


class TestMeshHierarchy:
    """Tests for mesh code hierarchy consistency."""

    def test_hierarchy_nesting(self):
        """Each level should be a prefix of the next."""
        lat, lon = TOKYO_STATION_LAT, TOKYO_STATION_LON
        m1 = latlon_to_mesh_1st(lat, lon)
        m2 = latlon_to_mesh_2nd(lat, lon)
        m3 = latlon_to_mesh_3rd(lat, lon)
        m_half = latlon_to_mesh_half(lat, lon)
        m_quarter = latlon_to_mesh_quarter(lat, lon)

        assert m2.startswith(m1)
        assert m3.startswith(m2)
        assert m_half.startswith(m3)
        assert m_quarter.startswith(m_half)

    def test_nearby_points_same_3rd_mesh(self):
        """Two very close points should have the same 3rd mesh code."""
        m1 = latlon_to_mesh_3rd(35.681236, 139.767125)
        m2 = latlon_to_mesh_3rd(35.681300, 139.767200)
        assert m1 == m2

    def test_distant_points_different_1st_mesh(self):
        """Tokyo and Osaka should be in different 1st mesh codes."""
        m_tokyo = latlon_to_mesh_1st(TOKYO_STATION_LAT, TOKYO_STATION_LON)
        m_osaka = latlon_to_mesh_1st(OSAKA_STATION_LAT, OSAKA_STATION_LON)
        assert m_tokyo != m_osaka


class TestGetNeighboringMeshes:
    """Tests for get_neighboring_meshes_3rd()."""

    def test_returns_list(self):
        result = get_neighboring_meshes_3rd("53394511")
        assert isinstance(result, list)

    def test_contains_center(self):
        result = get_neighboring_meshes_3rd("53394511")
        assert "53394511" in result

    def test_returns_9_for_interior_mesh(self):
        """Interior meshes should have 9 neighbors (including self)."""
        result = get_neighboring_meshes_3rd("53394555")
        assert len(result) == 9

    def test_all_8_digit_codes(self):
        result = get_neighboring_meshes_3rd("53394511")
        for code in result:
            assert len(code) == 8
            assert code.isdigit()

    def test_no_duplicates(self):
        result = get_neighboring_meshes_3rd("53394555")
        assert len(result) == len(set(result))

    def test_invalid_length_raises(self):
        with pytest.raises(ValueError, match="8-digit"):
            get_neighboring_meshes_3rd("5339")

    def test_invalid_too_long_raises(self):
        with pytest.raises(ValueError, match="8-digit"):
            get_neighboring_meshes_3rd("533945111")

    def test_edge_mesh_fewer_neighbors(self):
        """Mesh at 2nd-mesh boundary may have fewer than 9 neighbors."""
        # Mesh with t=0, u=0 within 2nd mesh (r=0, s=0)
        # Neighbors reaching r<0 or s<0 should be skipped
        result = get_neighboring_meshes_3rd("53390000")
        # Should still contain the center
        assert "53390000" in result
        # May have fewer than 9 due to boundary clipping
        assert len(result) <= 9

    def test_overflow_wraps_correctly(self):
        """When 3rd mesh t/u overflows, should increment 2nd mesh r/s."""
        result = get_neighboring_meshes_3rd("53394599")
        # The neighbor (t+1, u+1) would overflow to next 2nd mesh
        # Check that we still get valid results
        for code in result:
            assert len(code) == 8
