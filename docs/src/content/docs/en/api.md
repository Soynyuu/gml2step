---
title: Python API Reference
description: Public Python API for gml2step
---

gml2step exports four public functions from the top-level package.

```python
from gml2step import convert, parse, stream_parse, extract_footprints
```

---

## `convert()`

Convert a CityGML file to STEP format.

```python
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
) -> Tuple[bool, str]
```

**Requires pythonocc-core.**

### Parameters

| Parameter | Type | Default | Description |
|---|---|---|---|
| `gml_path` | str | (required) | Path to input CityGML file |
| `out_step` | str | (required) | Path for output STEP file |
| `limit` | int \| None | None | Max buildings to convert |
| `method` | str | `"solid"` | `"solid"`, `"sew"`, `"extrude"`, or `"auto"` |
| `debug` | bool | False | Enable debug logging |
| `sew_tolerance` | float \| None | None | Custom sewing tolerance |
| `reproject_to` | str \| None | None | Target CRS (e.g., `"EPSG:6677"`) |
| `source_crs` | str \| None | None | Override source CRS detection |
| `auto_reproject` | bool | True | Auto-detect and reproject CRS |
| `precision_mode` | str | `"standard"` | `"standard"`, `"high"`, `"maximum"`, `"ultra"` |
| `shape_fix_level` | str | `"minimal"` | `"minimal"`, `"standard"`, `"aggressive"`, `"ultra"` |
| `building_ids` | list \| None | None | Filter to specific building IDs |
| `filter_attribute` | str | `"gml:id"` | Attribute for building ID matching |
| `merge_building_parts` | bool | True | Merge BuildingParts via Boolean union |
| `target_latitude` | float \| None | None | Latitude for spatial filtering |
| `target_longitude` | float \| None | None | Longitude for spatial filtering |
| `radius_meters` | float | 100 | Radius for spatial filtering |
| `use_streaming` | bool | True | Use streaming parser |

### Returns

`Tuple[bool, str]` — `(success, message_or_output_path)`

### Example

```python
ok, result = convert(
    "input.gml",
    "output.step",
    method="auto",
    precision_mode="high",
    limit=10,
)
if ok:
    print(f"Written to {result}")
```

---

## `parse()`

Parse a CityGML file and return a summary dict.

```python
def parse(
    gml_path: str,
    limit: Optional[int] = None,
) -> Dict[str, Any]
```

Does **not** require OCCT.

### Returns

```python
{
    "path": str,
    "detected_source_crs": str | None,
    "sample_latitude": float | None,
    "sample_longitude": float | None,
    "total_buildings": int,
    "listed_building_ids": list[str],
}
```

### Example

```python
summary = parse("building.gml")
print(f"CRS: {summary['detected_source_crs']}")
print(f"Buildings: {summary['total_buildings']}")
```

---

## `stream_parse()`

Stream-parse buildings one at a time with constant memory.

```python
def stream_parse(
    gml_path: str,
    limit: Optional[int] = None,
    building_ids: Optional[List[str]] = None,
    filter_attribute: str = "gml:id",
    debug: bool = False,
) -> Iterator[Tuple[ET.Element, Dict[str, ET.Element]]]
```

Does **not** require OCCT.

### Yields

`Tuple[Element, dict]` — `(building_element, local_xlink_index)`

Each tuple contains:
- The `<bldg:Building>` XML element
- A dict of XLink targets resolved within the building's scope

### Example

```python
for building, xlinks in stream_parse("large_file.gml", limit=100):
    bid = building.get("{http://www.opengis.net/gml}id")
    print(bid)
```

---

## `extract_footprints()`

Extract 2D building footprints with height estimates.

```python
def extract_footprints(
    gml_path: str,
    default_height: float = 10.0,
    limit: Optional[int] = None,
) -> List[Footprint]
```

Does **not** require OCCT.

### Returns

`List[Footprint]` where each `Footprint` has:

| Field | Type | Description |
|---|---|---|
| `building_id` | str | GML building ID |
| `exterior` | list[tuple[float, float]] | Exterior ring coordinates |
| `holes` | list[list[tuple[float, float]]] | Interior rings (holes) |
| `height` | float | Estimated building height in meters |

### Example

```python
footprints = extract_footprints("building.gml", default_height=15.0)
for fp in footprints:
    print(f"{fp.building_id}: {fp.height}m, {len(fp.exterior)} vertices")
```

---

## Key types

### `Footprint`

```python
@dataclass
class Footprint:
    exterior: List[Tuple[float, float]]
    holes: List[List[Tuple[float, float]]]
    height: float
    building_id: str
```

Defined in `gml2step.citygml.lod.footprint_extractor`.

### `StreamingConfig`

```python
@dataclass
class StreamingConfig:
    limit: Optional[int] = None
    building_ids: Optional[List[str]] = None
    filter_attribute: str = "gml:id"
    debug: bool = False
    enable_gc_per_building: bool = True
    max_xlink_cache_size: int = 10000
```

Defined in `gml2step.citygml.streaming.parser`. Controls streaming parser behavior.
