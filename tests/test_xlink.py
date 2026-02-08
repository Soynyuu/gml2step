"""Tests for xlink resolution — xlink_resolver and xlink_cache."""

import xml.etree.ElementTree as ET

import pytest

from gml2step.citygml.core.constants import NS
from gml2step.citygml.utils.xlink_resolver import (
    build_id_index,
    extract_polygon_with_xlink,
    resolve_xlink,
)
from gml2step.citygml.streaming.xlink_cache import (
    GlobalXLinkCache,
    LocalXLinkCache,
    build_local_index_from_dict,
    resolve_xlink_from_dict,
    resolve_xlink_lazy,
)


# ── Helper ────────────────────────────────────────────────────

XLINK_DOC = f"""\
<CityModel xmlns="{NS["core"]}"
           xmlns:gml="{NS["gml"]}"
           xmlns:bldg="{NS["bldg"]}"
           xmlns:xlink="{NS["xlink"]}">
  <cityObjectMember>
    <bldg:Building gml:id="BLD_001">
      <bldg:lod2MultiSurface>
        <gml:MultiSurface>
          <gml:surfaceMember xlink:href="#POLY_A"/>
        </gml:MultiSurface>
      </bldg:lod2MultiSurface>
    </bldg:Building>
  </cityObjectMember>
  <gml:Polygon gml:id="POLY_A">
    <gml:exterior>
      <gml:LinearRing>
        <gml:posList>0 0 0 1 0 0 1 1 0 0 0 0</gml:posList>
      </gml:LinearRing>
    </gml:exterior>
  </gml:Polygon>
</CityModel>
"""


@pytest.fixture
def xlink_root():
    return ET.fromstring(XLINK_DOC)


# ── build_id_index ────────────────────────────────────────────


class TestBuildIdIndex:
    def test_indexes_all_gml_ids(self, xlink_root):
        idx = build_id_index(xlink_root)
        assert "BLD_001" in idx
        assert "POLY_A" in idx

    def test_empty_document(self):
        root = ET.fromstring(f'<CityModel xmlns="{NS["core"]}"/>')
        idx = build_id_index(root)
        assert len(idx) == 0


# ── resolve_xlink ─────────────────────────────────────────────


class TestResolveXlink:
    def test_resolve_with_hash(self, xlink_root):
        idx = build_id_index(xlink_root)
        surf = xlink_root.find(f".//{{{NS['gml']}}}surfaceMember")
        result = resolve_xlink(surf, idx)
        assert result is not None
        assert result.get(f"{{{NS['gml']}}}id") == "POLY_A"

    def test_resolve_missing_ref(self, xlink_root):
        idx = build_id_index(xlink_root)
        # Element with non-existent xlink:href
        elem = ET.Element("foo", {f"{{{NS['xlink']}}}href": "#DOES_NOT_EXIST"})
        result = resolve_xlink(elem, idx)
        assert result is None

    def test_no_href_returns_none(self, xlink_root):
        idx = build_id_index(xlink_root)
        elem = ET.Element("foo")
        assert resolve_xlink(elem, idx) is None


# ── extract_polygon_with_xlink ────────────────────────────────


class TestExtractPolygonWithXlink:
    def test_direct_polygon(self):
        """Polygon directly embedded → return it."""
        xml = f"""\
<gml:surfaceMember xmlns:gml="{NS["gml"]}">
  <gml:Polygon gml:id="P1">
    <gml:exterior><gml:LinearRing><gml:posList>0 0 0 1 0 0 1 1 0 0 0 0</gml:posList></gml:LinearRing></gml:exterior>
  </gml:Polygon>
</gml:surfaceMember>"""
        elem = ET.fromstring(xml)
        result = extract_polygon_with_xlink(elem, {})
        assert result is not None
        assert result.get(f"{{{NS['gml']}}}id") == "P1"

    def test_xlink_reference(self, xlink_root):
        idx = build_id_index(xlink_root)
        surf = xlink_root.find(f".//{{{NS['gml']}}}surfaceMember")
        result = extract_polygon_with_xlink(surf, idx)
        assert result is not None
        assert result.tag == f"{{{NS['gml']}}}Polygon"

    def test_neither(self):
        """No polygon and no xlink → None."""
        elem = ET.Element("foo")
        assert extract_polygon_with_xlink(elem, {}) is None


# ── LocalXLinkCache ───────────────────────────────────────────


class TestLocalXLinkCache:
    def test_basic_indexing(self, xlink_root):
        bld = xlink_root.find(f".//{{{NS['bldg']}}}Building")
        cache = LocalXLinkCache(bld)
        assert cache.resolve("BLD_001") is not None
        assert cache.resolve("NONEXISTENT") is None

    def test_len(self, xlink_root):
        bld = xlink_root.find(f".//{{{NS['bldg']}}}Building")
        cache = LocalXLinkCache(bld)
        assert len(cache) >= 1

    def test_clear(self, xlink_root):
        bld = xlink_root.find(f".//{{{NS['bldg']}}}Building")
        cache = LocalXLinkCache(bld)
        cache.clear()
        assert len(cache) == 0

    def test_max_size(self):
        """Cache should stop indexing at max_size."""
        xml = f'<root xmlns:gml="{NS["gml"]}">'
        for i in range(50):
            xml += f'<elem gml:id="ID_{i}"/>'
        xml += "</root>"
        root = ET.fromstring(xml)
        cache = LocalXLinkCache(root, max_size=10)
        assert len(cache) == 10


# ── GlobalXLinkCache (LRU) ────────────────────────────────────


class TestGlobalXLinkCache:
    def test_put_and_get(self):
        cache = GlobalXLinkCache(max_size=5)
        elem = ET.Element("test")
        cache.put("id1", elem)
        assert cache.get("id1") is elem

    def test_miss(self):
        cache = GlobalXLinkCache()
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        cache = GlobalXLinkCache(max_size=3)
        for i in range(4):
            cache.put(f"id_{i}", ET.Element(f"e{i}"))
        # id_0 should be evicted (oldest)
        assert cache.get("id_0") is None
        assert cache.get("id_3") is not None

    def test_access_refreshes_lru(self):
        cache = GlobalXLinkCache(max_size=3)
        for i in range(3):
            cache.put(f"id_{i}", ET.Element(f"e{i}"))
        # Access id_0 to refresh it
        cache.get("id_0")
        # Now add id_3, which should evict id_1 (oldest unreffed)
        cache.put("id_3", ET.Element("e3"))
        assert cache.get("id_0") is not None
        assert cache.get("id_1") is None

    def test_clear(self):
        cache = GlobalXLinkCache()
        cache.put("a", ET.Element("a"))
        cache.clear()
        assert len(cache) == 0


# ── resolve_xlink_lazy ────────────────────────────────────────


class TestResolveXlinkLazy:
    def test_local_hit(self, xlink_root):
        bld = xlink_root.find(f".//{{{NS['bldg']}}}Building")
        local = LocalXLinkCache(bld)
        elem_with_href = ET.Element("ref", {f"{{{NS['xlink']}}}href": "#BLD_001"})
        result = resolve_xlink_lazy(elem_with_href, local)
        assert result is not None

    def test_global_hit(self):
        local = LocalXLinkCache.__new__(LocalXLinkCache)
        local.index = {}
        local.max_size = 100

        global_cache = GlobalXLinkCache()
        target = ET.Element("target")
        global_cache.put("TARGET_ID", target)

        elem = ET.Element("ref", {f"{{{NS['xlink']}}}href": "#TARGET_ID"})
        result = resolve_xlink_lazy(elem, local, global_cache)
        assert result is target

    def test_miss(self):
        local = LocalXLinkCache.__new__(LocalXLinkCache)
        local.index = {}
        local.max_size = 100

        elem = ET.Element("ref", {f"{{{NS['xlink']}}}href": "#MISSING"})
        result = resolve_xlink_lazy(elem, local)
        assert result is None

    def test_no_href(self):
        local = LocalXLinkCache.__new__(LocalXLinkCache)
        local.index = {}
        local.max_size = 100

        elem = ET.Element("plain")
        result = resolve_xlink_lazy(elem, local)
        assert result is None


# ── resolve_xlink_from_dict ───────────────────────────────────


class TestResolveXlinkFromDict:
    def test_basic(self):
        target = ET.Element("target")
        idx = {"MY_ID": target}
        elem = ET.Element("ref", {f"{{{NS['xlink']}}}href": "#MY_ID"})
        assert resolve_xlink_from_dict(elem, idx) is target

    def test_no_href(self):
        elem = ET.Element("ref")
        assert resolve_xlink_from_dict(elem, {}) is None


# ── build_local_index_from_dict ───────────────────────────────


class TestBuildLocalIndexFromDict:
    def test_creates_cache(self):
        elem = ET.Element("x")
        d = {"id1": elem}
        cache = build_local_index_from_dict(d)
        assert cache.resolve("id1") is elem
        assert len(cache) == 1
