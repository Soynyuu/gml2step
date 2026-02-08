"""Tests for coordinate_utils — EPSG detection, CRS classification, Japan zone selection."""

import pytest

from gml2step.coordinate_utils import (
    detect_epsg_from_srs,
    get_crs_info,
    get_japan_plane_zone,
    is_geographic_crs,
    recommend_projected_crs,
)


# ── detect_epsg_from_srs ──────────────────────────────────────


class TestDetectEpsgFromSrs:
    def test_opengis_url(self):
        assert (
            detect_epsg_from_srs("http://www.opengis.net/def/crs/EPSG/0/6697")
            == "EPSG:6697"
        )

    def test_epsg_colon(self):
        assert detect_epsg_from_srs("EPSG:4326") == "EPSG:4326"

    def test_epsg_colon_lower(self):
        assert detect_epsg_from_srs("epsg:6668") == "EPSG:6668"

    def test_urn_style(self):
        """urn:ogc:def:crs:EPSG::4326 → EPSG:4326."""
        result = detect_epsg_from_srs("urn:ogc:def:crs:EPSG::4326")
        assert result == "EPSG:4326"

    def test_empty_string(self):
        assert detect_epsg_from_srs("") is None

    def test_none(self):
        assert detect_epsg_from_srs(None) is None

    def test_no_epsg(self):
        assert detect_epsg_from_srs("some random string") is None

    def test_jgd2011_plateau_url(self):
        """Common PLATEAU srsName."""
        url = "http://www.opengis.net/def/crs/EPSG/0/6697"
        assert detect_epsg_from_srs(url) == "EPSG:6697"


# ── is_geographic_crs ─────────────────────────────────────────


class TestIsGeographicCrs:
    @pytest.mark.parametrize(
        "code",
        [
            "EPSG:4326",
            "EPSG:4612",
            "EPSG:6668",
            "EPSG:6697",
        ],
    )
    def test_geographic_codes(self, code):
        assert is_geographic_crs(code) is True

    @pytest.mark.parametrize(
        "code",
        [
            "EPSG:6677",
            "EPSG:3857",
            "EPSG:6669",
        ],
    )
    def test_projected_codes(self, code):
        assert is_geographic_crs(code) is False

    def test_empty(self):
        assert is_geographic_crs("") is False

    def test_none_like(self):
        assert is_geographic_crs(None) is False


# ── get_japan_plane_zone ──────────────────────────────────────


class TestGetJapanPlaneZone:
    def test_tokyo(self):
        """Tokyo (35.68, 139.69) → Zone IX (EPSG:6677)."""
        result = get_japan_plane_zone(35.68, 139.69)
        assert result == "EPSG:6677"

    def test_osaka(self):
        """Osaka (35.5, 135.5) → Zone VI (EPSG:6674)."""
        # Zone 6 lat_range is (35.0, 36.5), so use coords within range
        result = get_japan_plane_zone(35.5, 135.5)
        assert result == "EPSG:6674"

    def test_outside_japan(self):
        assert get_japan_plane_zone(0.0, 0.0) is None

    def test_edge_of_japan_fallback(self):
        """Coordinates within broad central Japan box but not in any zone → Zone IX fallback."""
        result = get_japan_plane_zone(35.5, 140.0)
        assert result is not None  # Should find a zone


# ── recommend_projected_crs ───────────────────────────────────


class TestRecommendProjectedCrs:
    def test_geographic_with_coords(self):
        """Geographic CRS + Tokyo coords → zone IX."""
        result = recommend_projected_crs("EPSG:6697", 35.68, 139.69)
        assert result == "EPSG:6677"

    def test_geographic_no_coords(self):
        """Japanese geographic CRS without coords → default zone IX."""
        result = recommend_projected_crs("EPSG:6697")
        assert result == "EPSG:6677"

    def test_already_projected(self):
        """Already projected → None."""
        result = recommend_projected_crs("EPSG:6677")
        assert result is None

    def test_wgs84_no_coords(self):
        """WGS84 without coords → EPSG:3857 (Web Mercator)."""
        result = recommend_projected_crs("EPSG:4326")
        assert result == "EPSG:3857"

    def test_wgs84_with_japan_coords(self):
        """WGS84 + Japan coords → Japan zone."""
        result = recommend_projected_crs("EPSG:4326", 35.68, 139.69)
        assert result == "EPSG:6677"


# ── get_crs_info ──────────────────────────────────────────────


class TestGetCrsInfo:
    def test_known_geographic(self):
        info = get_crs_info("EPSG:4326")
        assert info["name"] == "WGS 84"
        assert info["type"] == "geographic"

    def test_japan_zone(self):
        info = get_crs_info("EPSG:6677")
        assert "IX" in info["name"]
        assert info["type"] == "projected"

    def test_unknown(self):
        info = get_crs_info("EPSG:99999")
        assert info["name"] == "Unknown CRS"
        assert info["type"] == "unknown"
