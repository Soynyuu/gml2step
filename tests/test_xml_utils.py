"""Tests for citygml.utils.xml_parser — first_text, extract_generic_attributes, get_element_id, find_buildings."""

import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.utils.xml_parser import (
    extract_generic_attributes,
    find_buildings,
    first_text,
    get_element_id,
)
from gml2step.citygml.core.constants import NS


# ── first_text ────────────────────────────────────────────────


class TestFirstText:
    def test_normal_text(self):
        elem = ET.fromstring("<tag>Hello</tag>")
        assert first_text(elem) == "Hello"

    def test_whitespace_stripped(self):
        elem = ET.fromstring("<tag>  Hello  </tag>")
        assert first_text(elem) == "Hello"

    def test_empty_text(self):
        elem = ET.fromstring("<tag></tag>")
        assert first_text(elem) is None

    def test_none_element(self):
        assert first_text(None) is None

    def test_only_whitespace(self):
        elem = ET.fromstring("<tag>   </tag>")
        assert first_text(elem) == ""


# ── get_element_id ────────────────────────────────────────────


class TestGetElementId:
    def test_with_gml_id(self):
        xml = f'<bldg:Building xmlns:gml="{NS["gml"]}" xmlns:bldg="{NS["bldg"]}" gml:id="BLD_001"/>'
        elem = ET.fromstring(xml)
        assert get_element_id(elem) == "BLD_001"

    def test_without_gml_id(self):
        xml = f'<bldg:Building xmlns:bldg="{NS["bldg"]}"/>'
        elem = ET.fromstring(xml)
        assert get_element_id(elem) is None


# ── extract_generic_attributes ────────────────────────────────


class TestExtractGenericAttributes:
    def test_string_and_int_attributes(self):
        xml = f"""\
<bldg:Building xmlns:bldg="{NS["bldg"]}"
               xmlns:gen="{NS["gen"]}"
               xmlns:gml="{NS["gml"]}">
  <gen:stringAttribute name="address">
    <gen:value>Tokyo</gen:value>
  </gen:stringAttribute>
  <gen:intAttribute name="floors">
    <gen:value>10</gen:value>
  </gen:intAttribute>
</bldg:Building>"""
        elem = ET.fromstring(xml)
        attrs = extract_generic_attributes(elem)
        assert attrs["address"] == "Tokyo"
        assert attrs["floors"] == "10"

    def test_uro_building_id(self):
        xml = f"""\
<bldg:Building xmlns:bldg="{NS["bldg"]}"
               xmlns:uro="{NS["uro"]}"
               xmlns:gml="{NS["gml"]}">
  <uro:buildingIDAttribute>
    <uro:BuildingIDAttribute>
      <uro:buildingID>ID_001</uro:buildingID>
    </uro:BuildingIDAttribute>
  </uro:buildingIDAttribute>
</bldg:Building>"""
        elem = ET.fromstring(xml)
        attrs = extract_generic_attributes(elem)
        assert attrs["buildingID"] == "ID_001"

    def test_empty_building(self):
        xml = f'<bldg:Building xmlns:bldg="{NS["bldg"]}"/>'
        elem = ET.fromstring(xml)
        attrs = extract_generic_attributes(elem)
        assert attrs == {}

    def test_empty_value_skipped(self):
        xml = f"""\
<bldg:Building xmlns:bldg="{NS["bldg"]}"
               xmlns:gen="{NS["gen"]}">
  <gen:stringAttribute name="empty_attr">
    <gen:value></gen:value>
  </gen:stringAttribute>
</bldg:Building>"""
        elem = ET.fromstring(xml)
        attrs = extract_generic_attributes(elem)
        assert "empty_attr" not in attrs


# ── find_buildings ────────────────────────────────────────────


class TestFindBuildings:
    def test_finds_buildings(self, sample_gml_root):
        buildings = find_buildings(sample_gml_root)
        assert len(buildings) == 2

    def test_building_ids(self, sample_gml_root):
        buildings = find_buildings(sample_gml_root)
        ids = [get_element_id(b) for b in buildings]
        assert "BLD_001" in ids
        assert "BLD_002" in ids

    def test_empty_document(self):
        xml = f'<CityModel xmlns="{NS["core"]}"/>'
        root = ET.fromstring(xml)
        assert find_buildings(root) == []
