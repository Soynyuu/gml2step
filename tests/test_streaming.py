"""Tests for citygml.streaming.parser — estimate_memory_savings, StreamingConfig."""

import tempfile

import pytest

from gml2step.citygml.streaming.parser import (
    StreamingConfig,
    estimate_memory_savings,
    stream_parse_buildings,
)
from tests.conftest import SAMPLE_GML_RICH


# ── StreamingConfig ───────────────────────────────────────────


class TestStreamingConfig:
    def test_defaults(self):
        cfg = StreamingConfig()
        assert cfg.limit is None
        assert cfg.building_ids is None
        assert cfg.filter_attribute == "gml:id"
        assert cfg.debug is False
        assert cfg.enable_gc_per_building is True
        assert cfg.max_xlink_cache_size == 10000

    def test_custom_values(self):
        cfg = StreamingConfig(limit=10, debug=True)
        assert cfg.limit == 10
        assert cfg.debug is True


# ── estimate_memory_savings ───────────────────────────────────


class TestEstimateMemorySavings:
    def test_basic_estimates(self):
        result = estimate_memory_savings(5.0, 50000)
        assert result["legacy_memory"] > 0
        assert result["streaming_memory"] > 0
        assert result["reduction_percent"] > 0
        assert result["streaming_memory"] < result["legacy_memory"]

    def test_with_limit(self):
        no_limit = estimate_memory_savings(5.0, 50000)
        with_limit = estimate_memory_savings(5.0, 50000, limit=100)
        assert with_limit["streaming_memory"] <= no_limit["streaming_memory"]

    def test_reduction_positive(self):
        result = estimate_memory_savings(1.0, 1000)
        assert result["reduction_percent"] > 50  # Should be significant


# ── stream_parse_buildings ────────────────────────────────────


class TestStreamParseBuildings:
    def _write_gml(self, tmp_path):
        p = tmp_path / "test.gml"
        p.write_text(SAMPLE_GML_RICH, encoding="utf-8")
        return str(p)

    def test_yields_all_buildings(self, tmp_path):
        path = self._write_gml(tmp_path)
        buildings = list(stream_parse_buildings(path))
        assert len(buildings) == 2

    def test_limit(self, tmp_path):
        path = self._write_gml(tmp_path)
        buildings = list(stream_parse_buildings(path, limit=1))
        assert len(buildings) == 1

    def test_building_ids_filter(self, tmp_path):
        path = self._write_gml(tmp_path)
        buildings = list(stream_parse_buildings(path, building_ids=["BLD_002"]))
        assert len(buildings) == 1
        from gml2step.citygml.core.constants import NS

        bid = buildings[0][0].get(f"{{{NS['gml']}}}id")
        assert bid == "BLD_002"

    def test_yields_xlink_index(self, tmp_path):
        path = self._write_gml(tmp_path)
        for building, xlink_idx in stream_parse_buildings(path, limit=1):
            # Should have at least the building's own gml:id
            assert isinstance(xlink_idx, dict)
            assert len(xlink_idx) >= 1

    def test_with_config(self, tmp_path):
        path = self._write_gml(tmp_path)
        cfg = StreamingConfig(limit=1, debug=False)
        buildings = list(stream_parse_buildings(path, config=cfg))
        assert len(buildings) == 1

    def test_invalid_file(self, tmp_path):
        p = tmp_path / "bad.gml"
        p.write_text("not xml", encoding="utf-8")
        with pytest.raises(ValueError, match="Invalid CityGML XML"):
            list(stream_parse_buildings(str(p)))

    def test_missing_file(self):
        with pytest.raises(FileNotFoundError):
            list(stream_parse_buildings("/nonexistent/file.gml"))
