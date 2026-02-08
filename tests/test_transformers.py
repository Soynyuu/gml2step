"""Tests for citygml/transforms/transformers.py — make_xy_transformer, make_xyz_transformer.

These functions depend only on pyproj (a core dependency), no OCC needed.
"""

import pytest

from gml2step.citygml.transforms.transformers import (
    make_xy_transformer,
    make_xyz_transformer,
)


# ── make_xy_transformer ──────────────────────────────────────────


class TestMakeXyTransformer:
    """Tests for make_xy_transformer()."""

    def test_geographic_to_projected(self):
        """Geographic CRS → projected CRS (Japan Plane CS VIII)."""
        tx = make_xy_transformer("EPSG:6668", "EPSG:6676")
        # JGD2011 geographic → JGD2011 Japan Plane CS IX
        x, y = tx(35.6811, 139.7670)
        # Should produce finite meter-scale values
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert abs(x) < 1_000_000
        assert abs(y) < 1_000_000

    def test_projected_to_projected(self):
        """Projected CRS → projected CRS (no lat/lon swap)."""
        tx = make_xy_transformer("EPSG:6677", "EPSG:6676")
        x, y = tx(0.0, 0.0)
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_identity_transform(self):
        """Same CRS in and out → values unchanged."""
        tx = make_xy_transformer("EPSG:6676", "EPSG:6676")
        x, y = tx(1000.0, 2000.0)
        assert x == pytest.approx(1000.0, abs=0.01)
        assert y == pytest.approx(2000.0, abs=0.01)

    def test_returns_callable(self):
        """make_xy_transformer returns a callable."""
        tx = make_xy_transformer("EPSG:4326", "EPSG:6676")
        assert callable(tx)

    def test_wgs84_to_japan_plane(self):
        """WGS84 (EPSG:4326) → Japan Plane CS IX.

        Tokyo Station approx: lat=35.6812, lon=139.7671
        """
        tx = make_xy_transformer("EPSG:4326", "EPSG:6677")
        x, y = tx(35.6812, 139.7671)
        # Should return reasonable Y/X values in meters
        assert abs(x) < 500_000
        assert abs(y) < 500_000

    def test_swap_for_geographic_crs(self):
        """Geographic CRS should swap lat/lon (CityGML stores as lat,lon)."""
        tx_geo = make_xy_transformer("EPSG:4326", "EPSG:6677")
        # Pass (lat, lon) as CityGML does
        x1, y1 = tx_geo(35.6812, 139.7671)

        # Non-geographic CRS should not swap
        tx_proj = make_xy_transformer("EPSG:6677", "EPSG:6677")
        x2, y2 = tx_proj(1000.0, 2000.0)
        assert x2 == pytest.approx(1000.0, abs=0.01)
        assert y2 == pytest.approx(2000.0, abs=0.01)

    def test_float_conversion(self):
        """Input values are cast to float (handles int input)."""
        tx = make_xy_transformer("EPSG:6676", "EPSG:6676")
        x, y = tx(1000, 2000)  # int inputs
        assert isinstance(x, float)
        assert isinstance(y, float)

    def test_invalid_crs_raises(self):
        """Invalid CRS string should raise an exception."""
        with pytest.raises(Exception):
            make_xy_transformer("EPSG:99999999", "EPSG:6676")


# ── make_xyz_transformer ──────────────────────────────────────────


class TestMakeXyzTransformer:
    """Tests for make_xyz_transformer()."""

    def test_geographic_to_projected_3d(self):
        """Geographic CRS → projected CRS with Z passthrough."""
        tx = make_xyz_transformer("EPSG:6668", "EPSG:6676")
        x, y, z = tx(35.6811, 139.7670, 50.0)
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)
        assert abs(x) < 1_000_000
        assert abs(y) < 1_000_000

    def test_z_preserved(self):
        """Z coordinate should be preserved or transformed consistently."""
        tx = make_xyz_transformer("EPSG:6676", "EPSG:6676")
        x, y, z = tx(1000.0, 2000.0, 50.0)
        assert x == pytest.approx(1000.0, abs=0.01)
        assert y == pytest.approx(2000.0, abs=0.01)
        assert z == pytest.approx(50.0, abs=0.1)

    def test_returns_callable(self):
        """make_xyz_transformer returns a callable."""
        tx = make_xyz_transformer("EPSG:4326", "EPSG:6676")
        assert callable(tx)

    def test_returns_3_values(self):
        """Transformer returns a 3-tuple."""
        tx = make_xyz_transformer("EPSG:4326", "EPSG:6677")
        result = tx(35.6812, 139.7671, 10.0)
        assert len(result) == 3

    def test_projected_no_swap(self):
        """Projected CRS should not swap coordinates."""
        tx = make_xyz_transformer("EPSG:6677", "EPSG:6677")
        x, y, z = tx(1000.0, 2000.0, 30.0)
        assert x == pytest.approx(1000.0, abs=0.01)
        assert y == pytest.approx(2000.0, abs=0.01)

    def test_float_conversion_3d(self):
        """Input values are cast to float (handles int input)."""
        tx = make_xyz_transformer("EPSG:6676", "EPSG:6676")
        x, y, z = tx(1000, 2000, 50)  # int inputs
        assert isinstance(x, float)
        assert isinstance(y, float)
        assert isinstance(z, float)

    def test_zero_altitude(self):
        """Z=0 should work without issues."""
        tx = make_xyz_transformer("EPSG:4326", "EPSG:6677")
        x, y, z = tx(35.6812, 139.7671, 0.0)
        assert isinstance(z, float)

    def test_invalid_crs_raises(self):
        """Invalid CRS string should raise an exception."""
        with pytest.raises(Exception):
            make_xyz_transformer("EPSG:99999999", "EPSG:6676")
