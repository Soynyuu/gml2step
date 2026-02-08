"""Shared fixtures for gml2step tests."""

import tempfile
import xml.etree.ElementTree as ET

import pytest


# CityGML 2.0 namespaces (mirrors src/gml2step/citygml/core/constants.py)
NS = {
    "gml": "http://www.opengis.net/gml",
    "bldg": "http://www.opengis.net/citygml/building/2.0",
    "core": "http://www.opengis.net/citygml/2.0",
    "uro": "https://www.geospatial.jp/iur/uro/3.1",
    "gen": "http://www.opengis.net/citygml/generics/2.0",
    "xlink": "http://www.w3.org/1999/xlink",
}

# Register namespaces so ET.tostring() produces clean output
for prefix, uri in NS.items():
    ET.register_namespace(prefix, uri)


# ---------------------------------------------------------------------------
# Sample GML with rich geometry (2 buildings, lod0FootPrint polygon, generic attrs)
# ---------------------------------------------------------------------------
SAMPLE_GML_RICH = """\
<?xml version="1.0" encoding="UTF-8"?>
<CityModel xmlns="http://www.opengis.net/citygml/2.0"
           xmlns:bldg="http://www.opengis.net/citygml/building/2.0"
           xmlns:gml="http://www.opengis.net/gml"
           xmlns:gen="http://www.opengis.net/citygml/generics/2.0"
           xmlns:uro="https://www.geospatial.jp/iur/uro/3.1"
           xmlns:xlink="http://www.w3.org/1999/xlink"
           gml:id="CM_001">
  <cityObjectMember>
    <bldg:Building gml:id="BLD_001">
      <gen:stringAttribute name="address">
        <gen:value>Tokyo</gen:value>
      </gen:stringAttribute>
      <gen:intAttribute name="floors">
        <gen:value>10</gen:value>
      </gen:intAttribute>
      <uro:buildingIDAttribute>
        <uro:BuildingIDAttribute>
          <uro:buildingID>ID_001</uro:buildingID>
        </uro:BuildingIDAttribute>
      </uro:buildingIDAttribute>
      <bldg:lod0FootPrint>
        <gml:MultiSurface>
          <gml:surfaceMember>
            <gml:Polygon gml:id="POLY_001">
              <gml:exterior>
                <gml:LinearRing>
                  <gml:posList>139.0 35.0 0.0 139.1 35.0 0.0 139.1 35.1 10.0 139.0 35.1 10.0 139.0 35.0 0.0</gml:posList>
                </gml:LinearRing>
              </gml:exterior>
              <gml:interior>
                <gml:LinearRing>
                  <gml:posList>139.02 35.02 0.0 139.08 35.02 0.0 139.08 35.08 5.0 139.02 35.08 5.0 139.02 35.02 0.0</gml:posList>
                </gml:LinearRing>
              </gml:interior>
            </gml:Polygon>
          </gml:surfaceMember>
        </gml:MultiSurface>
      </bldg:lod0FootPrint>
    </bldg:Building>
  </cityObjectMember>
  <cityObjectMember>
    <bldg:Building gml:id="BLD_002">
      <bldg:lod0FootPrint>
        <gml:MultiSurface>
          <gml:surfaceMember>
            <gml:Polygon gml:id="POLY_002">
              <gml:exterior>
                <gml:LinearRing>
                  <gml:posList>140.0 36.0 0.0 140.1 36.0 0.0 140.1 36.1 0.0 140.0 36.1 0.0 140.0 36.0 0.0</gml:posList>
                </gml:LinearRing>
              </gml:exterior>
            </gml:Polygon>
          </gml:surfaceMember>
        </gml:MultiSurface>
      </bldg:lod0FootPrint>
    </bldg:Building>
  </cityObjectMember>
</CityModel>
"""


@pytest.fixture
def sample_gml_path(tmp_path):
    """Write rich sample GML to a temp file and return its path."""
    p = tmp_path / "sample.gml"
    p.write_text(SAMPLE_GML_RICH, encoding="utf-8")
    return str(p)


@pytest.fixture
def sample_gml_root():
    """Parse the rich sample GML and return the root Element."""
    return ET.fromstring(SAMPLE_GML_RICH)


def gml_elem(
    tag: str, text: str = "", attrib: dict | None = None, ns: str = "gml"
) -> ET.Element:
    """Helper to create a namespaced GML element."""
    full_tag = f"{{{NS[ns]}}}{tag}" if ns else tag
    elem = ET.Element(full_tag, attrib or {})
    if text:
        elem.text = text
    return elem
