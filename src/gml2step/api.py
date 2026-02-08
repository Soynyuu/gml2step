"""Minimal public API wrappers for gml2step."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple
import xml.etree.ElementTree as ET

from .citygml.streaming.parser import stream_parse_buildings
from .citygml.transforms.crs_detection import detect_source_crs
from .citygml.core.constants import NS


def convert(
    gml_path: str,
    out_step: str,
    limit: Optional[int] = None,
    debug: bool = False,
    method: str = "solid",
    sew_tolerance: Optional[float] = None,
    reproject_to: Optional[str] = None,
    source_crs: Optional[str] = None,
    auto_reproject: bool = True,
    precision_mode: str = "standard",
    shape_fix_level: str = "minimal",
    building_ids: Optional[List[str]] = None,
    filter_attribute: str = "gml:id",
    merge_building_parts: bool = True,
    target_latitude: Optional[float] = None,
    target_longitude: Optional[float] = None,
    radius_meters: float = 100,
    use_streaming: bool = True,
) -> Tuple[bool, str]:
    """Thin wrapper around export_step_from_citygml.

    Note: This function requires pythonocc-core for STEP conversion.
    Install it with: conda install -c conda-forge pythonocc-core
    """
    from .citygml.pipeline.orchestrator import export_step_from_citygml

    return export_step_from_citygml(
        gml_path=gml_path,
        out_step=out_step,
        limit=limit,
        debug=debug,
        method=method,
        sew_tolerance=sew_tolerance,
        reproject_to=reproject_to,
        source_crs=source_crs,
        auto_reproject=auto_reproject,
        precision_mode=precision_mode,
        shape_fix_level=shape_fix_level,
        building_ids=building_ids,
        filter_attribute=filter_attribute,
        merge_building_parts=merge_building_parts,
        target_latitude=target_latitude,
        target_longitude=target_longitude,
        radius_meters=radius_meters,
        use_streaming=use_streaming,
    )


def parse(gml_path: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Parse CityGML and return a lightweight summary.

    This function does not create 3D geometry and works without OCCT.
    """
    tree = ET.parse(gml_path)
    root = tree.getroot()
    source_crs, sample_lat, sample_lon = detect_source_crs(root)
    buildings = root.findall(".//bldg:Building", NS)
    building_ids: List[str] = []

    for idx, b in enumerate(buildings):
        if limit is not None and idx >= limit:
            break
        bid = b.get(f"{{{NS['gml']}}}id") or b.get("id")
        if bid:
            building_ids.append(bid)

    return {
        "path": str(Path(gml_path)),
        "detected_source_crs": source_crs,
        "sample_latitude": sample_lat,
        "sample_longitude": sample_lon,
        "total_buildings": len(buildings),
        "listed_building_ids": building_ids,
    }


def stream_parse(
    gml_path: str,
    limit: Optional[int] = None,
    building_ids: Optional[List[str]] = None,
    filter_attribute: str = "gml:id",
    debug: bool = False,
) -> Iterator[Tuple[ET.Element, Dict[str, ET.Element]]]:
    """Thin wrapper around stream_parse_buildings."""
    return stream_parse_buildings(
        gml_path=gml_path,
        limit=limit,
        building_ids=building_ids,
        filter_attribute=filter_attribute,
        debug=debug,
    )


def extract_footprints(
    gml_path: str,
    default_height: float = 10.0,
    limit: Optional[int] = None,
) -> List[Any]:
    """Thin wrapper around parse_citygml_footprints.

    Returns a list of Footprint dataclass instances.
    """
    from .citygml.lod.footprint_extractor import parse_citygml_footprints

    return parse_citygml_footprints(
        gml_path=gml_path,
        default_height=default_height,
        limit=limit,
    )
