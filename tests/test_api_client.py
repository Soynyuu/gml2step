"""Tests for plateau/api_client.py — pure functions that don't require network access.

Since aiohttp is an optional dependency ([plateau] extra), all tests use
pytest.importorskip("aiohttp") to gracefully skip in CI environments
that only install core dependencies.
"""

import pytest

aiohttp = pytest.importorskip(
    "aiohttp", reason="aiohttp not installed (plateau extras)"
)

from gml2step.plateau.api_client import (
    KNOWN_CITY_TILESETS,
    _filter_building_datasets,
    _get_mesh2_mapping_path,
    _is_no_texture_dataset,
    _normalize_mesh2_mapping,
    _prefer_no_texture,
)


# ── KNOWN_CITY_TILESETS ───────────────────────────────────────


class TestKnownCityTilesets:
    def test_is_dict(self):
        assert isinstance(KNOWN_CITY_TILESETS, dict)

    def test_contains_chiyoda(self):
        assert "13101" in KNOWN_CITY_TILESETS
        assert KNOWN_CITY_TILESETS["13101"]["name"] == "千代田区"

    def test_contains_shibuya(self):
        assert "13113" in KNOWN_CITY_TILESETS
        assert KNOWN_CITY_TILESETS["13113"]["name"] == "渋谷区"

    def test_all_have_name_and_lod1(self):
        for code, data in KNOWN_CITY_TILESETS.items():
            assert "name" in data, f"{code} missing name"
            assert "lod1" in data, f"{code} missing lod1"
            assert data["lod1"].startswith("https://"), f"{code} lod1 not HTTPS"


# ── _filter_building_datasets ─────────────────────────────────


class TestFilterBuildingDatasets:
    """Tests for _filter_building_datasets()."""

    def _make_dataset(
        self, city_code="13101", dtype="建築物モデル", fmt="3D Tiles", lod="1"
    ):
        return {
            "city_code": city_code,
            "type": dtype,
            "format": fmt,
            "lod": lod,
            "url": "https://example.com/tileset.json",
            "name": "Test Dataset",
        }

    def test_basic_match(self):
        datasets = [self._make_dataset()]
        result = _filter_building_datasets(datasets, "13101")
        assert len(result) == 1

    def test_filter_by_city_code(self):
        datasets = [
            self._make_dataset(city_code="13101"),
            self._make_dataset(city_code="13102"),
        ]
        result = _filter_building_datasets(datasets, "13101")
        assert len(result) == 1

    def test_filter_by_type(self):
        datasets = [
            self._make_dataset(dtype="建築物モデル"),
            self._make_dataset(dtype="道路モデル"),
        ]
        result = _filter_building_datasets(datasets, "13101")
        assert len(result) == 1

    def test_filter_by_format(self):
        datasets = [
            self._make_dataset(fmt="3D Tiles"),
            self._make_dataset(fmt="CityGML"),
        ]
        result = _filter_building_datasets(datasets, "13101")
        assert len(result) == 1

    def test_filter_by_lod(self):
        datasets = [
            self._make_dataset(lod="1"),
            self._make_dataset(lod="2"),
        ]
        result = _filter_building_datasets(datasets, "13101", lod=1)
        assert len(result) == 1
        assert result[0]["lod"] == "1"

    def test_lod_none_returns_all(self):
        datasets = [
            self._make_dataset(lod="1"),
            self._make_dataset(lod="2"),
        ]
        result = _filter_building_datasets(datasets, "13101", lod=None)
        assert len(result) == 2

    def test_invalid_lod_string(self):
        """Dataset with non-numeric LOD is skipped when filtering by LOD."""
        datasets = [self._make_dataset(lod="invalid")]
        result = _filter_building_datasets(datasets, "13101", lod=1)
        assert len(result) == 0

    def test_none_lod_in_dataset(self):
        """Dataset with None LOD is skipped when filtering by LOD."""
        datasets = [self._make_dataset(lod=None)]
        result = _filter_building_datasets(datasets, "13101", lod=1)
        assert len(result) == 0

    def test_empty_datasets(self):
        result = _filter_building_datasets([], "13101")
        assert result == []

    def test_ward_code_fallback(self):
        """Datasets can use ward_code instead of city_code."""
        ds = {
            "ward_code": "13101",
            "type": "建築物モデル",
            "format": "3D Tiles",
            "lod": "1",
        }
        result = _filter_building_datasets([ds], "13101")
        assert len(result) == 1


# ── _is_no_texture_dataset ────────────────────────────────────


class TestIsNoTextureDataset:
    def test_no_texture_in_id(self):
        ds = {
            "id": "13101_bldg_no_texture_lod2",
            "url": "https://example.com/tileset.json",
        }
        assert _is_no_texture_dataset(ds) is True

    def test_no_texture_in_url(self):
        ds = {"id": "13101_bldg", "url": "https://example.com/no_texture/tileset.json"}
        assert _is_no_texture_dataset(ds) is True

    def test_regular_dataset(self):
        ds = {"id": "13101_bldg_lod2", "url": "https://example.com/tileset.json"}
        assert _is_no_texture_dataset(ds) is False

    def test_missing_fields(self):
        ds = {}
        assert _is_no_texture_dataset(ds) is False


# ── _prefer_no_texture ────────────────────────────────────────


class TestPreferNoTexture:
    def test_disabled(self):
        """When prefer_no_texture=False, return datasets unchanged."""
        datasets = [{"id": "a"}, {"id": "b"}]
        result = _prefer_no_texture(datasets, False)
        assert result is datasets  # Same object, not a copy

    def test_no_texture_first(self):
        datasets = [
            {"id": "13101_bldg_lod2", "url": "https://example.com/tileset.json"},
            {
                "id": "13101_bldg_no_texture_lod2",
                "url": "https://example.com/tileset2.json",
            },
        ]
        result = _prefer_no_texture(datasets, True)
        assert "no_texture" in result[0]["id"]

    def test_no_no_texture_returns_all(self):
        """If no no_texture datasets exist, return all unchanged."""
        datasets = [
            {"id": "13101_bldg", "url": "https://example.com/tileset.json"},
        ]
        result = _prefer_no_texture(datasets, True)
        assert result is datasets

    def test_mixed_ordering(self):
        """No-texture datasets come first, then others."""
        datasets = [
            {"id": "regular_1", "url": "https://a.com"},
            {"id": "no_texture_1", "url": "https://b.com"},
            {"id": "regular_2", "url": "https://c.com"},
        ]
        result = _prefer_no_texture(datasets, True)
        assert len(result) == 3
        assert "no_texture" in result[0]["id"]


# ── _normalize_mesh2_mapping ──────────────────────────────────


class TestNormalizeMesh2Mapping:
    def test_basic_mapping(self):
        raw = {"533935": ["13113"], "533946": ["13101"]}
        result = _normalize_mesh2_mapping(raw)
        assert result["533935"] == ["13113"]
        assert result["533946"] == ["13101"]

    def test_wrapped_format(self):
        """Handles {mesh2_to_municipalities: {...}} wrapper."""
        raw = {"mesh2_to_municipalities": {"533935": ["13113"]}}
        result = _normalize_mesh2_mapping(raw)
        assert "533935" in result

    def test_string_code_normalized(self):
        """Single string code is wrapped in list."""
        raw = {"533935": "13113"}
        result = _normalize_mesh2_mapping(raw)
        assert result["533935"] == ["13113"]

    def test_invalid_mesh2_key_skipped(self):
        """Non-6-digit keys are skipped."""
        raw = {"12345": ["13113"], "533935": ["13113"]}
        result = _normalize_mesh2_mapping(raw)
        assert "12345" not in result
        assert "533935" in result

    def test_invalid_code_skipped(self):
        """Non-5-digit municipality codes are skipped."""
        raw = {"533935": ["13113", "abc", "1234567"]}
        result = _normalize_mesh2_mapping(raw)
        assert result["533935"] == ["13113"]

    def test_non_list_value_skipped(self):
        """Non-list, non-string values are skipped."""
        raw = {"533935": 12345, "533946": ["13101"]}
        result = _normalize_mesh2_mapping(raw)
        assert "533935" not in result
        assert "533946" in result

    def test_empty_raises(self):
        with pytest.raises(ValueError, match="no usable entries"):
            _normalize_mesh2_mapping({})

    def test_non_dict_raises(self):
        with pytest.raises(ValueError, match="must be an object"):
            _normalize_mesh2_mapping([1, 2, 3])

    def test_duplicates_deduplicated(self):
        raw = {"533935": ["13113", "13113", "13113"]}
        result = _normalize_mesh2_mapping(raw)
        assert result["533935"] == ["13113"]

    def test_sorted_output(self):
        raw = {"533935": ["13113", "13101"]}
        result = _normalize_mesh2_mapping(raw)
        assert result["533935"] == ["13101", "13113"]

    def test_non_digit_mesh2_key_skipped(self):
        raw = {"abcdef": ["13113"], "533935": ["13113"]}
        result = _normalize_mesh2_mapping(raw)
        assert "abcdef" not in result


# ── _get_mesh2_mapping_path ───────────────────────────────────


class TestGetMesh2MappingPath:
    def test_default_path(self, monkeypatch):
        monkeypatch.delenv("PLATEAU_MESH2_MAPPING_PATH", raising=False)
        path = _get_mesh2_mapping_path()
        assert path.name == "mesh2_municipality.json"
        assert "data" in str(path)

    def test_env_override(self, monkeypatch):
        monkeypatch.setenv("PLATEAU_MESH2_MAPPING_PATH", "/tmp/custom.json")
        path = _get_mesh2_mapping_path()
        assert str(path) == "/tmp/custom.json"
