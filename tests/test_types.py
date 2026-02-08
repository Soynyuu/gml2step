"""Tests for citygml/core/types.py — Type definitions and dataclasses."""

import xml.etree.ElementTree as ET

from gml2step.citygml.core.types import (
    ConversionContext,
    LODExtractionResult,
    ExtractionResult,
    CoordinateTransform3D,
    CoordinateTransform2D,
    IDIndex,
)


class TestConversionContext:
    """Tests for ConversionContext dataclass."""

    def test_minimal_creation(self):
        ctx = ConversionContext(gml_path="test.gml", out_step="out.step")
        assert ctx.gml_path == "test.gml"
        assert ctx.out_step == "out.step"

    def test_defaults(self):
        ctx = ConversionContext(gml_path="a.gml", out_step="b.step")
        assert ctx.limit is None
        assert ctx.debug is False
        assert ctx.method == "solid"
        assert ctx.sew_tolerance is None
        assert ctx.reproject_to is None
        assert ctx.source_crs is None
        assert ctx.auto_reproject is True
        assert ctx.precision_mode == "standard"
        assert ctx.shape_fix_level == "minimal"
        assert ctx.building_ids is None
        assert ctx.filter_attribute == "gml:id"
        assert ctx.merge_building_parts is True
        assert ctx.target_latitude is None
        assert ctx.target_longitude is None
        assert ctx.radius_meters == 100.0

    def test_runtime_state_defaults(self):
        ctx = ConversionContext(gml_path="a.gml", out_step="b.step")
        assert ctx.root is None
        assert ctx.id_index == {}
        assert ctx.xyz_transform is None
        assert ctx.xy_transform is None
        assert ctx.source_crs_detected is None
        assert ctx.target_crs_selected is None
        assert ctx.coord_offset is None
        assert ctx.building_elements == []

    def test_full_creation(self):
        ctx = ConversionContext(
            gml_path="city.gml",
            out_step="city.step",
            limit=10,
            debug=True,
            method="sew",
            precision_mode="ultra",
            shape_fix_level="aggressive",
            building_ids=["b1", "b2"],
            merge_building_parts=False,
            radius_meters=200.0,
        )
        assert ctx.limit == 10
        assert ctx.debug is True
        assert ctx.method == "sew"
        assert ctx.precision_mode == "ultra"
        assert ctx.shape_fix_level == "aggressive"
        assert ctx.building_ids == ["b1", "b2"]
        assert ctx.merge_building_parts is False
        assert ctx.radius_meters == 200.0

    def test_mutable_runtime_state(self):
        ctx = ConversionContext(gml_path="a.gml", out_step="b.step")
        root = ET.Element("root")
        ctx.root = root
        assert ctx.root is root

        ctx.id_index = {"id1": root}
        assert "id1" in ctx.id_index

        ctx.coord_offset = (-100.0, -200.0, -5.0)
        assert ctx.coord_offset == (-100.0, -200.0, -5.0)

    def test_id_index_is_independent_per_instance(self):
        ctx1 = ConversionContext(gml_path="a.gml", out_step="b.step")
        ctx2 = ConversionContext(gml_path="c.gml", out_step="d.step")
        ctx1.id_index["x"] = ET.Element("x")
        assert "x" not in ctx2.id_index

    def test_building_elements_independent_per_instance(self):
        ctx1 = ConversionContext(gml_path="a.gml", out_step="b.step")
        ctx2 = ConversionContext(gml_path="c.gml", out_step="d.step")
        ctx1.building_elements.append(ET.Element("b"))
        assert len(ctx2.building_elements) == 0


class TestLODExtractionResult:
    """Tests for LODExtractionResult dataclass."""

    def test_creation(self):
        result = LODExtractionResult(
            exterior_faces=["face1", "face2"],
            interior_shells=[["face3"]],
            lod_level="LOD2",
            method="lod2Solid//gml:Solid",
        )
        assert len(result.exterior_faces) == 2
        assert len(result.interior_shells) == 1
        assert result.lod_level == "LOD2"
        assert result.method == "lod2Solid//gml:Solid"
        assert result.prefer_bounded_by is False

    def test_prefer_bounded_by(self):
        result = LODExtractionResult(
            exterior_faces=[],
            interior_shells=[],
            lod_level="LOD2",
            method="boundedBy surfaces",
            prefer_bounded_by=True,
        )
        assert result.prefer_bounded_by is True


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_creation_minimal(self):
        result = ExtractionResult(
            shape="mock_shape",
            building_id="bldg_001",
        )
        assert result.shape == "mock_shape"
        assert result.building_id == "bldg_001"
        assert result.building_name is None
        assert result.lod_level == "unknown"
        assert result.method == "unknown"
        assert result.num_faces == 0
        assert result.is_valid is False

    def test_creation_full(self):
        result = ExtractionResult(
            shape="shape",
            building_id="bldg_002",
            building_name="Tokyo Tower",
            lod_level="LOD3",
            method="solid",
            num_faces=42,
            is_valid=True,
        )
        assert result.building_name == "Tokyo Tower"
        assert result.lod_level == "LOD3"
        assert result.method == "solid"
        assert result.num_faces == 42
        assert result.is_valid is True


class TestTypeAliases:
    """Tests for type aliases (basic usage verification)."""

    def test_coordinate_transform_3d_callable(self):
        """Verify the type alias works as expected."""

        def my_transform(x: float, y: float, z: float):
            return (x + 1, y + 1, z + 1)

        # CoordinateTransform3D is just a type alias, verify the function works
        fn: CoordinateTransform3D = my_transform
        assert fn(1.0, 2.0, 3.0) == (2.0, 3.0, 4.0)

    def test_coordinate_transform_2d_callable(self):
        def my_transform(x: float, y: float):
            return (x * 2, y * 2)

        fn: CoordinateTransform2D = my_transform
        assert fn(3.0, 4.0) == (6.0, 8.0)

    def test_id_index_dict(self):
        index: IDIndex = {"id1": ET.Element("elem")}
        assert "id1" in index
