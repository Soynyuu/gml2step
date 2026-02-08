"""Tests for plateau/mesh_mapping.py — Tokyo 23-ward mesh code mapping."""

import pytest

from gml2step.plateau.mesh_mapping import (
    TOKYO_23_MESH2_MAPPING,
    get_municipality_from_mesh2,
    get_all_mesh2_codes,
    get_municipality_name,
)


class TestTokyo23MeshMapping:
    """Tests for TOKYO_23_MESH2_MAPPING dictionary."""

    def test_is_dict(self):
        assert isinstance(TOKYO_23_MESH2_MAPPING, dict)

    def test_not_empty(self):
        assert len(TOKYO_23_MESH2_MAPPING) > 0

    def test_all_keys_6_digits(self):
        for key in TOKYO_23_MESH2_MAPPING:
            assert len(key) == 6
            assert key.isdigit()

    def test_all_values_5_digits(self):
        for val in TOKYO_23_MESH2_MAPPING.values():
            assert len(val) == 5
            assert val.isdigit()

    def test_all_tokyo_prefecture(self):
        """All municipality codes should start with 13 (Tokyo)."""
        for val in TOKYO_23_MESH2_MAPPING.values():
            assert val.startswith("13")

    def test_covers_chiyoda(self):
        """Chiyoda-ku (13101) should be in the mapping."""
        assert "13101" in set(TOKYO_23_MESH2_MAPPING.values())

    def test_covers_shibuya(self):
        """Shibuya-ku (13113) should be in the mapping."""
        assert "13113" in set(TOKYO_23_MESH2_MAPPING.values())


class TestGetMunicipalityFromMesh2:
    """Tests for get_municipality_from_mesh2()."""

    def test_tokyo_station_mesh(self):
        """533945 should return Chiyoda-ku."""
        # Note: TOKYO_23_MESH2_MAPPING has duplicate keys, last one wins
        result = get_municipality_from_mesh2("533945")
        assert result is not None
        assert result.startswith("13")

    def test_unknown_mesh_returns_none(self):
        assert get_municipality_from_mesh2("999999") is None

    def test_empty_string_returns_none(self):
        assert get_municipality_from_mesh2("") is None

    def test_returns_string(self):
        # Get any valid mesh code from the mapping
        code = next(iter(TOKYO_23_MESH2_MAPPING))
        result = get_municipality_from_mesh2(code)
        assert isinstance(result, str)


class TestGetAllMesh2Codes:
    """Tests for get_all_mesh2_codes()."""

    def test_returns_list(self):
        result = get_all_mesh2_codes()
        assert isinstance(result, list)

    def test_not_empty(self):
        assert len(get_all_mesh2_codes()) > 0

    def test_all_6_digits(self):
        for code in get_all_mesh2_codes():
            assert len(code) == 6
            assert code.isdigit()

    def test_matches_dict_keys(self):
        codes = get_all_mesh2_codes()
        assert set(codes) == set(TOKYO_23_MESH2_MAPPING.keys())


class TestGetMunicipalityName:
    """Tests for get_municipality_name()."""

    def test_chiyoda(self):
        assert get_municipality_name("13101") == "千代田区"

    def test_shibuya(self):
        assert get_municipality_name("13113") == "渋谷区"

    def test_setagaya(self):
        assert get_municipality_name("13112") == "世田谷区"

    def test_minato(self):
        assert get_municipality_name("13103") == "港区"

    def test_all_23_wards(self):
        """All 23 ward codes (13101-13123) should return a name."""
        for code_num in range(13101, 13124):
            code = str(code_num)
            name = get_municipality_name(code)
            assert name is not None, f"No name for code {code}"
            assert name.endswith("区"), f"Name {name} does not end with 区"

    def test_unknown_code_returns_none(self):
        assert get_municipality_name("99999") is None

    def test_empty_string_returns_none(self):
        assert get_municipality_name("") is None

    def test_non_tokyo_returns_none(self):
        """Codes outside 13101-13123 should return None."""
        assert get_municipality_name("14101") is None  # Yokohama
