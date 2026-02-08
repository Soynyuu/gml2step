---
title: Architecture
description: Internal structure, streaming parser, and CRS handling
---

## Codebase structure

```
src/gml2step/
├── __init__.py              # Public API exports
├── api.py                   # API implementation (convert, parse, etc.)
├── cli.py                   # Typer CLI entry point
├── coordinate_utils.py      # CRS utilities, Japan zone definitions
├── data/
│   └── mesh2_municipality.json
├── citygml/
│   ├── core/                # Types, constants, CityGML namespaces
│   ├── parsers/             # Coordinate and polygon extraction
│   ├── streaming/           # SAX-style streaming parser
│   ├── lod/                 # LoD0–LoD3 extraction, footprints
│   ├── geometry/            # OCCT geometry builders, shell/solid, repair
│   ├── transforms/          # CRS detection, reprojection, recentering
│   ├── utils/               # XLink resolver, XML parser, logging
│   └── pipeline/            # 7-phase conversion orchestrator
└── plateau/                 # PLATEAU API client, geocoding, mesh utils
```

---

## Streaming parser

For large CityGML files, gml2step provides a SAX-based streaming parser that processes one `<bldg:Building>` element at a time rather than loading the entire XML DOM into memory.

### How it works

1. The XML file is read incrementally using `iterparse`
2. When a `<bldg:Building>` opening tag is encountered, the parser starts accumulating the element
3. When the closing tag is found, the complete building element is yielded to the caller
4. After yielding, the element is cleared from memory
5. XLink references are resolved via a two-tier cache

### XLink resolution

CityGML files use XLink references (`xlink:href="#id"`) to share geometry between elements. The streaming parser handles this with two caches:

- **Local cache** — XLink targets within the current building element (cleared after each building)
- **Global LRU cache** — XLink targets referenced across buildings (bounded by `max_xlink_cache_size`, default 10,000 entries)

### Memory characteristics

The streaming parser maintains O(1 building) memory usage regardless of file size. The trade-off is that XLink targets outside the current building may need to be re-parsed if they fall out of the LRU cache.

> The streaming parser has not been formally benchmarked. The O(1) memory characteristic is architectural (one building in memory at a time), but actual memory usage depends on building complexity and XLink cache size.

### Configuration

```python
from gml2step.citygml.streaming.parser import StreamingConfig

config = StreamingConfig(
    limit=100,
    building_ids=["bldg_001", "bldg_002"],
    filter_attribute="gml:id",
    debug=False,
    enable_gc_per_building=True,   # Force GC after each building
    max_xlink_cache_size=10000,    # Global XLink cache entries
)
```

### NumPy coordinate optimization

When NumPy is available, coordinate string parsing can be accelerated by batch-converting coordinate strings to arrays rather than parsing them one at a time in pure Python.

This is an optional optimization in `gml2step.citygml.streaming.coordinate_optimizer`.

---

## CRS handling

### Auto-detection

gml2step reads the `srsName` attribute from GML elements to detect the source coordinate reference system. Common values:

- `http://www.opengis.net/def/crs/EPSG/0/6677` (Japan Plane Rectangular CS IX)
- `EPSG:4326` (WGS84)
- `urn:ogc:def:crs:EPSG::4612` (JGD2000)

### Japan Plane Rectangular Coordinate System

Japan uses 19 zones (EPSG:6669–6687) of the Plane Rectangular CS. Each zone covers a strip of the country optimized for minimal distortion.

gml2step includes zone definitions for all 19 zones and can automatically select the appropriate zone based on latitude/longitude.

### Reprojection

When the source CRS is geographic (lat/lon), gml2step automatically reprojects to the appropriate Japan Plane Rectangular CS zone using [pyproj](https://pyproj4.github.io/pyproj/). This produces metric coordinates suitable for OpenCASCADE.

### Recentering

Even with projected coordinates, values like X=140000, Y=36000 (meters) can cause floating-point precision issues in OCCT. The recentering step subtracts the centroid of the first building from all coordinates, shifting the geometry near the origin.

---

## Conversion pipeline internals

The pipeline orchestrator lives in `gml2step.citygml.pipeline`. It coordinates the 7-phase process described in the [Conversion Guide](/gml2step/en/conversion/).

The pipeline processes buildings sequentially. For each building:

1. A `ConversionContext` is created with coordinate transforms, precision settings, and method selection
2. The building element is passed through each phase
3. If a phase fails, the pipeline logs the error and moves to the next building
4. Successfully converted solids are accumulated into a STEP compound
5. After all buildings are processed, the compound is written to the output file

### `ConversionContext`

The context object carries state through the pipeline:

```python
@dataclass
class ConversionContext:
    method: str                    # "solid", "sew", "extrude", "auto"
    precision_mode: str            # Tolerance factor
    shape_fix_level: str           # Repair aggressiveness
    sew_tolerance: Optional[float]
    source_crs: Optional[str]
    target_crs: Optional[str]
    auto_reproject: bool
    merge_building_parts: bool
    debug: bool
    # ... (additional internal fields)
```

### `ExtractionResult`

Each phase produces or modifies an extraction result:

```python
@dataclass
class ExtractionResult:
    faces: List                    # OCCT face objects
    shell: Optional[object]        # Constructed shell
    solid: Optional[object]        # Validated solid
    repair_applied: str            # Which repair level was used
    method_used: str               # Which conversion method succeeded
    lod_level: int                 # LoD that was extracted
```
