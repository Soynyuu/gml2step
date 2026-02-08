"""Tests for plateau/fetcher.py — Pure Python utility functions only.

Tests only functions that do NOT require network access (requests/shapely).
Network-calling functions are NOT tested here.
"""

import xml.etree.ElementTree as ET

import pytest

from gml2step.plateau.fetcher import (
    calculate_name_similarity,
    _levenshtein_distance,
    _tokenize,
    BuildingInfo,
    GeocodingResult,
    _parse_poslist,
    _extract_building_height,
    _detect_lod_levels,
    _extract_building_coordinates,
    extract_municipality_code,
    _get_municipality_name_from_code,
)

# Namespace for building XML fixtures (fetcher.py uses its own NS dict)
_NS_DECL = (
    'xmlns:gml="http://www.opengis.net/gml" '
    'xmlns:bldg="http://www.opengis.net/citygml/building/2.0" '
    'xmlns:uro="http://www.opengis.net/uro/1.0"'
)


class TestLevenshteinDistance:
    """Tests for _levenshtein_distance()."""

    def test_identical_strings(self):
        assert _levenshtein_distance("abc", "abc") == 0

    def test_empty_strings(self):
        assert _levenshtein_distance("", "") == 0

    def test_one_empty(self):
        assert _levenshtein_distance("abc", "") == 3
        assert _levenshtein_distance("", "abc") == 3

    def test_single_insertion(self):
        assert _levenshtein_distance("ab", "abc") == 1

    def test_single_deletion(self):
        assert _levenshtein_distance("abc", "ab") == 1

    def test_single_substitution(self):
        assert _levenshtein_distance("abc", "axc") == 1

    def test_completely_different(self):
        assert _levenshtein_distance("abc", "xyz") == 3

    def test_symmetric(self):
        assert _levenshtein_distance("abc", "xyz") == _levenshtein_distance(
            "xyz", "abc"
        )

    def test_japanese_characters(self):
        assert _levenshtein_distance("東京", "東京") == 0
        assert _levenshtein_distance("東京", "大阪") == 2

    def test_longer_strings(self):
        d = _levenshtein_distance("kitten", "sitting")
        assert d == 3  # Known standard example


class TestTokenize:
    """Tests for _tokenize()."""

    def test_simple_spaces(self):
        assert _tokenize("hello world") == ["hello", "world"]

    def test_hyphens(self):
        assert _tokenize("tokyo-tower") == ["tokyo", "tower"]

    def test_underscores(self):
        assert _tokenize("building_name") == ["building", "name"]

    def test_japanese_middle_dot(self):
        assert _tokenize("東京・タワー") == ["東京", "タワー"]

    def test_empty_string(self):
        assert _tokenize("") == []

    def test_single_word(self):
        assert _tokenize("word") == ["word"]

    def test_multiple_separators(self):
        result = _tokenize("a - b _ c")
        assert result == ["a", "b", "c"]

    def test_no_empty_tokens(self):
        result = _tokenize("  hello  ")
        assert "" not in result


class TestCalculateNameSimilarity:
    """Tests for calculate_name_similarity()."""

    def test_exact_match(self):
        assert calculate_name_similarity("東京駅", "東京駅") == 1.0

    def test_case_insensitive_exact(self):
        assert calculate_name_similarity("Tokyo", "tokyo") == 1.0

    def test_none_building_name(self):
        assert calculate_name_similarity(None, "query") == 0.0

    def test_none_query(self):
        assert calculate_name_similarity("name", None) == 0.0

    def test_both_none(self):
        assert calculate_name_similarity(None, None) == 0.0

    def test_empty_strings(self):
        assert calculate_name_similarity("", "") == 0.0

    def test_substring_match(self):
        score = calculate_name_similarity("東京国際フォーラム", "東京")
        assert 0 < score < 1.0

    def test_reverse_substring(self):
        score = calculate_name_similarity("東京", "東京国際フォーラム")
        assert 0 < score < 1.0

    def test_no_match(self):
        score = calculate_name_similarity("abcdef", "xyz123")
        assert 0 <= score < 0.5

    def test_returns_float(self):
        score = calculate_name_similarity("test", "test")
        assert isinstance(score, float)

    def test_score_range(self):
        """Score should always be between 0 and 1."""
        test_pairs = [
            ("a", "b"),
            ("東京駅", "大阪駅"),
            ("Tokyo Tower", "Eiffel Tower"),
            ("abc", "abcdef"),
        ]
        for name, query in test_pairs:
            score = calculate_name_similarity(name, query)
            assert 0.0 <= score <= 1.0, (
                f"Score {score} out of range for ({name}, {query})"
            )


class TestBuildingInfoDataclass:
    """Tests for BuildingInfo dataclass."""

    def test_creation(self):
        bi = BuildingInfo(
            building_id="13101-bldg-123",
            gml_id="BLD_uuid",
            latitude=35.681,
            longitude=139.767,
            distance_meters=50.0,
        )
        assert bi.building_id == "13101-bldg-123"
        assert bi.latitude == 35.681
        assert bi.distance_meters == 50.0


class TestGeocodingResultDataclass:
    """Tests for GeocodingResult dataclass."""

    def test_creation(self):
        gr = GeocodingResult(
            query="東京駅",
            latitude=35.681,
            longitude=139.767,
            display_name="東京都千代田区丸の内",
        )
        assert gr.latitude == 35.681
        assert gr.display_name == "東京都千代田区丸の内"
        assert gr.query == "東京駅"

    def test_optional_fields(self):
        gr = GeocodingResult(
            query="test",
            latitude=35.0,
            longitude=139.0,
            display_name="test",
            osm_type="node",
            osm_id=12345,
        )
        assert gr.osm_type == "node"
        assert gr.osm_id == 12345


class TestParsePoslist:
    """Tests for _parse_poslist()."""

    def test_3d_coordinates(self):
        elem = ET.fromstring(
            '<gml:posList xmlns:gml="http://www.opengis.net/gml">1.0 2.0 3.0 4.0 5.0 6.0</gml:posList>'
        )
        result = _parse_poslist(elem)
        assert len(result) == 2
        assert result[0] == (1.0, 2.0, 3.0)
        assert result[1] == (4.0, 5.0, 6.0)

    def test_2d_coordinates(self):
        elem = ET.fromstring(
            '<gml:posList xmlns:gml="http://www.opengis.net/gml">1.0 2.0 3.0 4.0</gml:posList>'
        )
        result = _parse_poslist(elem)
        assert len(result) == 2
        assert result[0] == (1.0, 2.0, None)
        assert result[1] == (3.0, 4.0, None)

    def test_empty_poslist(self):
        elem = ET.fromstring(
            '<gml:posList xmlns:gml="http://www.opengis.net/gml"></gml:posList>'
        )
        result = _parse_poslist(elem)
        assert result == []

    def test_none_text(self):
        elem = ET.fromstring('<gml:posList xmlns:gml="http://www.opengis.net/gml"/>')
        result = _parse_poslist(elem)
        assert result == []

    def test_whitespace_only(self):
        elem = ET.fromstring(
            '<gml:posList xmlns:gml="http://www.opengis.net/gml">   </gml:posList>'
        )
        result = _parse_poslist(elem)
        assert result == []

    def test_invalid_values_skipped(self):
        elem = ET.fromstring(
            '<gml:posList xmlns:gml="http://www.opengis.net/gml">1.0 abc 2.0 3.0 4.0 5.0</gml:posList>'
        )
        result = _parse_poslist(elem)
        # Invalid 'abc' is skipped, remaining 5 values → 3 not divisible by 3,
        # but 5 values: parsed as 2D (5 values, 5%3!=0 so dim=2, 5//2=2 pairs + remainder)
        assert len(result) >= 1


class TestExtractBuildingHeight:
    """Tests for _extract_building_height()."""

    def test_measured_height(self):
        xml = f"""<bldg:Building {_NS_DECL}>
            <bldg:measuredHeight>25.5</bldg:measuredHeight>
        </bldg:Building>"""
        building = ET.fromstring(xml)
        assert _extract_building_height(building) == 25.5

    def test_uro_measured_height(self):
        xml = f"""<bldg:Building {_NS_DECL}>
            <uro:measuredHeight>30.0</uro:measuredHeight>
        </bldg:Building>"""
        building = ET.fromstring(xml)
        assert _extract_building_height(building) == 30.0

    def test_no_height(self):
        xml = f"<bldg:Building {_NS_DECL}></bldg:Building>"
        building = ET.fromstring(xml)
        assert _extract_building_height(building) is None

    def test_zero_height_returns_none(self):
        xml = f"""<bldg:Building {_NS_DECL}>
            <bldg:measuredHeight>0</bldg:measuredHeight>
        </bldg:Building>"""
        building = ET.fromstring(xml)
        assert _extract_building_height(building) is None

    def test_invalid_text(self):
        xml = f"""<bldg:Building {_NS_DECL}>
            <bldg:measuredHeight>invalid</bldg:measuredHeight>
        </bldg:Building>"""
        building = ET.fromstring(xml)
        assert _extract_building_height(building) is None


class TestExtractBuildingCoordinates:
    """Tests for _extract_building_coordinates()."""

    def test_from_footprint(self):
        xml = f"""<bldg:Building {_NS_DECL}>
            <bldg:lod0FootPrint>
                <gml:MultiSurface>
                    <gml:surfaceMember>
                        <gml:Polygon>
                            <gml:exterior>
                                <gml:LinearRing>
                                    <gml:posList>35.681 139.767 0 35.682 139.768 0</gml:posList>
                                </gml:LinearRing>
                            </gml:exterior>
                        </gml:Polygon>
                    </gml:surfaceMember>
                </gml:MultiSurface>
            </bldg:lod0FootPrint>
        </bldg:Building>"""
        building = ET.fromstring(xml)
        result = _extract_building_coordinates(building)
        assert result is not None
        lat, lon = result
        assert 20 <= lat <= 50
        assert 120 <= lon <= 155

    def test_no_coordinates(self):
        xml = f"<bldg:Building {_NS_DECL}></bldg:Building>"
        building = ET.fromstring(xml)
        assert _extract_building_coordinates(building) is None


class TestDetectLodLevels:
    """Tests for _detect_lod_levels()."""

    def test_lod2_solid(self):
        xml = f"""<bldg:Building {_NS_DECL}>
            <bldg:lod2Solid>
                <gml:Solid><gml:exterior/></gml:Solid>
            </bldg:lod2Solid>
        </bldg:Building>"""
        building = ET.fromstring(xml)
        has_lod2, has_lod3 = _detect_lod_levels(building)
        assert has_lod2 is True

    def test_no_lod(self):
        xml = f"<bldg:Building {_NS_DECL}></bldg:Building>"
        building = ET.fromstring(xml)
        has_lod2, has_lod3 = _detect_lod_levels(building)
        assert has_lod2 is False
        assert has_lod3 is False


class TestExtractMunicipalityCode:
    """Tests for extract_municipality_code()."""

    def test_standard_format(self):
        assert extract_municipality_code("13101-bldg-2287") == "13101"

    def test_different_municipality(self):
        assert extract_municipality_code("14101-bldg-100") == "14101"

    def test_no_bldg_prefix(self):
        assert extract_municipality_code("13101-something") == "13101"

    def test_empty_string(self):
        assert extract_municipality_code("") is None

    def test_none_input(self):
        assert extract_municipality_code(None) is None

    def test_no_dash(self):
        assert extract_municipality_code("13101") is None

    def test_non_5_digit_prefix(self):
        assert extract_municipality_code("123-bldg-1") is None

    def test_non_digit_prefix(self):
        assert extract_municipality_code("abcde-bldg-1") is None


class TestGetMunicipalityNameFromCode:
    """Tests for _get_municipality_name_from_code()."""

    def test_chiyoda(self):
        assert _get_municipality_name_from_code("13101") == "千代田区"

    def test_shibuya(self):
        assert _get_municipality_name_from_code("13113") == "渋谷区"

    def test_all_23_wards(self):
        for code_num in range(13101, 13124):
            name = _get_municipality_name_from_code(str(code_num))
            assert name is not None

    def test_unknown_code(self):
        assert _get_municipality_name_from_code("99999") is None
