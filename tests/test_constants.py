"""Tests for citygml/core/constants.py — Conversion constants."""

from gml2step.citygml.core.constants import (
    NS,
    PRECISION_MODE_FACTORS,
    ULTRA_MODE_TOLERANCE_MULTIPLIERS,
    MAX_TOLERANCE_MULTIPLIER,
    RECENTERING_DISTANCE_THRESHOLD,
    INVALID_FACE_RATIO_THRESHOLD,
    BOUNDED_BY_PREFERENCE_THRESHOLD,
    AUTO_ESCALATION_MAP,
    BOUNDARY_SURFACE_TYPES,
    LOD_PRIORITY,
    LOD_SOLID_TAGS,
    LOD_MULTISURFACE_TAGS,
    LOD_GEOMETRY_TAGS,
    DEFAULT_BUILDING_HEIGHT,
    DEFAULT_COORDINATE_FILTER_RADIUS,
    MIN_POLYGON_POINTS,
    MIN_WIRE_LENGTH,
)


class TestXMLNamespaces:
    """Tests for NS namespace dictionary."""

    def test_required_keys_present(self):
        required = {"gml", "bldg", "core", "uro", "gen", "xlink"}
        assert required.issubset(NS.keys())

    def test_gml_namespace(self):
        assert NS["gml"] == "http://www.opengis.net/gml"

    def test_bldg_namespace(self):
        assert NS["bldg"] == "http://www.opengis.net/citygml/building/2.0"

    def test_core_namespace(self):
        assert NS["core"] == "http://www.opengis.net/citygml/2.0"

    def test_xlink_namespace(self):
        assert NS["xlink"] == "http://www.w3.org/1999/xlink"

    def test_all_values_are_strings(self):
        for key, val in NS.items():
            assert isinstance(key, str)
            assert isinstance(val, str)

    def test_all_values_are_urls(self):
        for val in NS.values():
            assert val.startswith("http")


class TestPrecisionModeFactors:
    """Tests for PRECISION_MODE_FACTORS."""

    def test_has_all_modes(self):
        expected_modes = {"standard", "high", "maximum", "ultra"}
        assert set(PRECISION_MODE_FACTORS.keys()) == expected_modes

    def test_decreasing_order(self):
        """Higher precision modes should have smaller factors."""
        assert PRECISION_MODE_FACTORS["standard"] > PRECISION_MODE_FACTORS["high"]
        assert PRECISION_MODE_FACTORS["high"] > PRECISION_MODE_FACTORS["maximum"]
        assert PRECISION_MODE_FACTORS["maximum"] > PRECISION_MODE_FACTORS["ultra"]

    def test_all_positive(self):
        for factor in PRECISION_MODE_FACTORS.values():
            assert factor > 0

    def test_standard_is_0001(self):
        assert PRECISION_MODE_FACTORS["standard"] == 0.0001


class TestUltraModeTolerance:
    """Tests for ULTRA_MODE_TOLERANCE_MULTIPLIERS."""

    def test_has_three_multipliers(self):
        assert len(ULTRA_MODE_TOLERANCE_MULTIPLIERS) == 3

    def test_descending_order(self):
        """Multipliers should be in descending order (try highest first)."""
        assert ULTRA_MODE_TOLERANCE_MULTIPLIERS == sorted(
            ULTRA_MODE_TOLERANCE_MULTIPLIERS, reverse=True
        )

    def test_all_positive(self):
        for m in ULTRA_MODE_TOLERANCE_MULTIPLIERS:
            assert m > 0


class TestAutoEscalationMap:
    """Tests for AUTO_ESCALATION_MAP."""

    def test_has_all_levels(self):
        expected = {"minimal", "standard", "aggressive", "ultra"}
        assert set(AUTO_ESCALATION_MAP.keys()) == expected

    def test_minimal_tries_all(self):
        assert AUTO_ESCALATION_MAP["minimal"] == [
            "minimal",
            "standard",
            "aggressive",
            "ultra",
        ]

    def test_ultra_only_ultra(self):
        assert AUTO_ESCALATION_MAP["ultra"] == ["ultra"]

    def test_each_starts_with_own_level(self):
        for level, path in AUTO_ESCALATION_MAP.items():
            assert path[0] == level

    def test_each_ends_with_ultra(self):
        for path in AUTO_ESCALATION_MAP.values():
            assert path[-1] == "ultra"


class TestBoundarySurfaceTypes:
    """Tests for BOUNDARY_SURFACE_TYPES."""

    def test_has_six_types(self):
        assert len(BOUNDARY_SURFACE_TYPES) == 6

    def test_contains_wall_roof_ground(self):
        assert "WallSurface" in BOUNDARY_SURFACE_TYPES
        assert "RoofSurface" in BOUNDARY_SURFACE_TYPES
        assert "GroundSurface" in BOUNDARY_SURFACE_TYPES

    def test_contains_outer_surfaces(self):
        assert "OuterCeilingSurface" in BOUNDARY_SURFACE_TYPES
        assert "OuterFloorSurface" in BOUNDARY_SURFACE_TYPES

    def test_contains_closure(self):
        assert "ClosureSurface" in BOUNDARY_SURFACE_TYPES


class TestLODPriority:
    """Tests for LOD_PRIORITY."""

    def test_lod3_first(self):
        assert LOD_PRIORITY[0] == "LOD3"

    def test_order_highest_to_lowest(self):
        assert LOD_PRIORITY == ["LOD3", "LOD2", "LOD1"]

    def test_solid_tags_match_priority(self):
        for lod in LOD_PRIORITY:
            assert lod in LOD_SOLID_TAGS


class TestLODTags:
    """Tests for LOD tag mappings."""

    def test_solid_tags(self):
        assert LOD_SOLID_TAGS["LOD3"] == "lod3Solid"
        assert LOD_SOLID_TAGS["LOD2"] == "lod2Solid"
        assert LOD_SOLID_TAGS["LOD1"] == "lod1Solid"

    def test_multisurface_tags(self):
        assert LOD_MULTISURFACE_TAGS["LOD3"] == "lod3MultiSurface"
        assert LOD_MULTISURFACE_TAGS["LOD2"] == "lod2MultiSurface"

    def test_geometry_tags(self):
        assert LOD_GEOMETRY_TAGS["LOD3"] == "lod3Geometry"
        assert LOD_GEOMETRY_TAGS["LOD2"] == "lod2Geometry"

    def test_multisurface_no_lod1(self):
        assert "LOD1" not in LOD_MULTISURFACE_TAGS

    def test_geometry_no_lod1(self):
        assert "LOD1" not in LOD_GEOMETRY_TAGS


class TestDefaultValues:
    """Tests for default configuration values."""

    def test_default_building_height(self):
        assert DEFAULT_BUILDING_HEIGHT == 10.0

    def test_default_coordinate_filter_radius(self):
        assert DEFAULT_COORDINATE_FILTER_RADIUS == 100.0

    def test_min_polygon_points(self):
        assert MIN_POLYGON_POINTS == 3

    def test_min_wire_length_positive(self):
        assert MIN_WIRE_LENGTH > 0

    def test_recentering_threshold_positive(self):
        assert RECENTERING_DISTANCE_THRESHOLD > 0

    def test_invalid_face_ratio_between_0_and_1(self):
        assert 0 < INVALID_FACE_RATIO_THRESHOLD < 1

    def test_bounded_by_preference_threshold(self):
        assert BOUNDED_BY_PREFERENCE_THRESHOLD == 1.0

    def test_max_tolerance_multiplier(self):
        assert MAX_TOLERANCE_MULTIPLIER == 1000.0
