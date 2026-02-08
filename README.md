# gml2step

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

**[日本語版 README はこちら (Japanese)](README.ja.md)**

A standalone toolkit for parsing [CityGML](https://www.ogc.org/standard/citygml/) files and converting 3D building geometry to the [STEP](https://en.wikipedia.org/wiki/ISO_10303-21) (ISO 10303-21) CAD format. Originally extracted from [Paper-CAD](https://github.com/Soynyuu/Paper-CAD).

## Overview

gml2step reads CityGML 2.0 files — including large-scale datasets from Japan's [PLATEAU](https://www.mlit.go.jp/plateau/) project — and produces STEP files suitable for CAD/CAM/BIM workflows.

**Key capabilities:**

- **CityGML parsing** with streaming support for files of any size
- **STEP conversion** via OpenCASCADE with automatic LoD fallback (LoD3 -> LoD2 -> LoD1 -> LoD0)
- **4 conversion methods**: solid, sew, extrude, and auto (tries all in sequence)
- **7-phase geometry pipeline** with progressive auto-repair
- **PLATEAU integration** for fetching CityGML data from Japan's national 3D city model
- **Footprint extraction** for 2D analysis without requiring OCCT
- **CRS auto-detection** with built-in support for all 19 Japan Plane Rectangular CS zones

## Installation

### Core (parsing, footprint extraction)

```bash
pip install gml2step
```

### With PLATEAU integration

```bash
pip install "gml2step[plateau]"
```

### With STEP conversion (requires OpenCASCADE)

STEP conversion depends on [pythonocc-core](https://github.com/tpaviot/pythonocc-core), which is not reliably pip-installable on all platforms. Use conda or Docker:

```bash
# conda
conda install -c conda-forge pythonocc-core
pip install gml2step

# Docker (recommended for full conversion)
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

> **Note:** Parsing, streaming, and footprint extraction work without OCCT. Only the `convert` command requires it.

## Quick Start

### CLI

```bash
# Parse a CityGML file and print summary as JSON
gml2step parse ./input.gml

# Stream-parse buildings one at a time (constant memory)
gml2step stream-parse ./input.gml --limit 100

# Extract 2D footprints with height estimates
gml2step extract-footprints ./input.gml --output-json ./footprints.json

# Convert CityGML to STEP
gml2step convert ./input.gml ./output.step --method solid
```

### Python API

```python
from gml2step import parse, stream_parse, extract_footprints, convert

# Lightweight summary (no OCCT required)
summary = parse("input.gml")
print(summary["total_buildings"])
print(summary["detected_source_crs"])

# Stream buildings with constant memory usage
for building, xlink_index in stream_parse("input.gml", limit=10):
    bid = building.get("{http://www.opengis.net/gml}id")
    print(bid)

# Extract 2D footprints with height
footprints = extract_footprints("input.gml", limit=100)
for fp in footprints:
    print(fp.building_id, fp.height, len(fp.exterior))

# Full CityGML -> STEP conversion
ok, result = convert("input.gml", "output.step", method="auto")
```

## CLI Reference

### `gml2step convert`

```
gml2step convert INPUT_GML OUTPUT_STEP [OPTIONS]
```

| Option | Default | Description |
|---|---|---|
| `--limit N` | None | Maximum number of buildings to convert |
| `--method` | `solid` | Conversion method: `solid`, `sew`, `extrude`, `auto` |
| `--debug` | False | Enable debug logging |
| `--use-streaming / --no-use-streaming` | True | Use streaming parser for lower memory usage |

### `gml2step parse`

```
gml2step parse INPUT_GML [--limit N]
```

Outputs a JSON summary with detected CRS, building count, and building IDs.

### `gml2step stream-parse`

```
gml2step stream-parse INPUT_GML [--limit N] [--building-id ID ...] [--filter-attribute gml:id]
```

Streams building IDs one per line using constant memory. Supports filtering by building ID.

### `gml2step extract-footprints`

```
gml2step extract-footprints INPUT_GML [--output-json PATH] [--limit N] [--default-height 10.0]
```

Extracts 2D footprints with estimated building heights. Height is derived from `measuredHeight`, Z-coordinate range, or the specified default.

## Conversion Methods

| Method | Description |
|---|---|
| **solid** | Primary method. Extracts LoD surfaces, builds shells, validates solids, auto-repairs. Best for LoD2/LoD3. |
| **sew** | Collects WallSurface/RoofSurface/GroundSurface polygons, sews faces, and attempts to form a solid. |
| **extrude** | Extrudes LoD0 footprint to estimated height. Fallback for files with only 2D data. |
| **auto** | Tries solid -> sew -> extrude in sequence until one succeeds. |

## Processing Pipeline

The `convert` command processes each building through 7 phases:

| Phase | Description |
|---|---|
| **0. Recentering** | Translates coordinates near the origin for OCCT numerical stability |
| **1. LoD Selection** | Selects the best available LoD (LoD3 -> LoD2 -> LoD1 fallback) |
| **1.5. CRS Detection** | Auto-detects source CRS and reprojects if needed |
| **2. Geometry Extraction** | Extracts faces using the selected conversion method |
| **3. Shell Construction** | Builds OCCT shells from faces with multi-pass sewing |
| **4. Solid Validation** | Validates geometry and constructs solids |
| **5. Auto-Repair** | 4-level progressive repair: minimal -> standard -> aggressive -> ultra |
| **6. Part Merging** | Fuses BuildingParts via Boolean union (with compound fallback) |
| **7. STEP Export** | Writes AP214CD STEP file with millimeter units |

### Precision Modes

The `precision_mode` parameter controls coordinate tolerance:

| Mode | Relative tolerance | Use case |
|---|---|---|
| `standard` | 0.01% | General use |
| `high` | 0.001% | Detailed models |
| `maximum` | 0.0001% | High-precision CAD |
| `ultra` | 0.00001% | Maximum fidelity |

### Shape Fix Levels

The `shape_fix_level` parameter controls auto-repair aggressiveness. When repair fails at the specified level, it automatically escalates:

1. **minimal** — ShapeFix_Solid only
2. **standard** — + ShapeUpgrade_UnifySameDomain
3. **aggressive** — + Rebuild with relaxed tolerance
4. **ultra** — + ShapeFix_Shape (full repair)

## LoD Support

gml2step supports CityGML Level of Detail 0 through 3:

| LoD | Description | Surfaces supported |
|---|---|---|
| **LoD3** | Architectural detail models | lod3Solid, lod3MultiSurface, lod3Geometry |
| **LoD2** | Standard building models (PLATEAU primary) | lod2Solid, lod2MultiSurface, lod2Geometry, boundedBy |
| **LoD1** | Simple block models | lod1Solid |
| **LoD0** | 2D footprints | lod0FootPrint, lod0RoofEdge, GroundSurface |

All 6 CityGML 2.0 boundary surface types are recognized: WallSurface, RoofSurface, GroundSurface, OuterCeilingSurface, OuterFloorSurface, ClosureSurface.

## Streaming Parser

For large CityGML files (common in PLATEAU datasets), gml2step provides a SAX-style streaming parser:

- **O(1 building) memory** vs O(entire file) for DOM parsing
- **~98% memory reduction** on typical PLATEAU datasets
- **3-5x faster** than full DOM parsing
- Two-tier XLink resolution cache (local per-building + global LRU)
- Optional NumPy-accelerated coordinate parsing (10-20x faster)

```python
# Process a 20GB PLATEAU file with ~100MB memory
for building, xlinks in stream_parse("huge_plateau_file.gml"):
    process(building)
```

## CRS and Coordinate Handling

- **Auto-detection** of source CRS from GML `srsName` attributes
- **All 19 Japan Plane Rectangular CS zones** (EPSG:6669–6687) with automatic zone selection by latitude/longitude
- **Automatic reprojection** from geographic CRS (WGS84, JGD2000, JGD2011) to an appropriate projected CRS
- **Coordinate recentering** near the origin to prevent floating-point precision loss in OCCT

## PLATEAU Integration

[PLATEAU](https://www.mlit.go.jp/plateau/) is a project by Japan's Ministry of Land, Infrastructure, Transport and Tourism (MLIT) that provides open 3D city models for the entire country in CityGML format.

gml2step provides optional integration with PLATEAU (`pip install "gml2step[plateau]"`):

### Building Search

```python
from gml2step.plateau.fetcher import search_buildings_by_address

# Search by address — geocodes, fetches CityGML, parses, and ranks
buildings = search_buildings_by_address(
    "東京都千代田区霞が関3-2-1",
    ranking_mode="hybrid",  # "distance", "name", or "hybrid"
    limit=10,
)
for b in buildings:
    print(b.building_id, b.name, b.height, b.lod_level)
```

### Mesh Code Utilities

PLATEAU data is organized by [JIS X 0410 standard mesh codes](https://www.stat.go.jp/data/mesh/m_tuite.html). gml2step provides conversion functions for all 5 mesh levels:

```python
from gml2step.plateau.mesh_utils import (
    latlon_to_mesh_1st,    # 80km grid (4-digit)
    latlon_to_mesh_2nd,    # 10km grid (6-digit)
    latlon_to_mesh_3rd,    # 1km grid (8-digit)
    latlon_to_mesh_half,   # 500m grid (9-digit)
    latlon_to_mesh_quarter # 250m grid (10-digit)
)

mesh = latlon_to_mesh_3rd(35.6812, 139.7671)  # Tokyo Station
```

### Async API Client

```python
import asyncio
from gml2step.plateau.api_client import fetch_plateau_datasets_by_mesh

# Fetch PLATEAU dataset URLs by mesh code
result = asyncio.run(fetch_plateau_datasets_by_mesh("53394525"))
```

### Features

- **Geocoding** via Nominatim with Japan-specific validation and relevance scoring
- **Building search** with 3 ranking modes: distance, name similarity (Levenshtein + token matching), hybrid
- **JIS X 0410 mesh code** conversion (1st through quarter mesh)
- **Neighboring mesh enumeration** (3x3 grid) for boundary searches
- **Async batch resolution** of mesh codes with concurrency control
- **CityGML caching** (opt-in via `CITYGML_CACHE_ENABLED` / `CITYGML_CACHE_DIR` env vars)
- **Nationwide mesh-to-municipality mapping** included as package data

## Architecture

```
src/gml2step/
├── __init__.py              # Public API: convert, parse, stream_parse, extract_footprints
├── api.py                   # API implementation
├── cli.py                   # Typer CLI
├── coordinate_utils.py      # CRS utilities, Japan zone definitions
├── data/
│   └── mesh2_municipality.json  # Nationwide mesh-to-municipality mapping
├── citygml/
│   ├── core/                # Types, constants, CityGML namespaces
│   ├── parsers/             # Coordinate and polygon extraction
│   ├── streaming/           # SAX-style streaming parser, XLink cache, coordinate optimizer
│   ├── lod/                 # LoD0–LoD3 extraction strategies, footprint extractor
│   ├── geometry/            # OCCT geometry builders, shell/solid construction, auto-repair
│   ├── transforms/          # CRS detection, reprojection, recentering
│   ├── utils/               # XLink resolver, XML parser, logging
│   └── pipeline/            # Orchestrator (7-phase conversion pipeline)
└── plateau/                 # PLATEAU API client, geocoding, mesh utilities, building search
```

## Development

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
pytest
```

## License

This project is licensed under the [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0-or-later).

gml2step was originally developed as part of [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) and extracted as a standalone library. See [NOTICE](NOTICE) for full attribution.

## Acknowledgments

- [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) — The parent project from which gml2step was extracted
- [PLATEAU](https://www.mlit.go.jp/plateau/) — Japan's national 3D city model project (MLIT)
- [OpenCASCADE](https://www.opencascade.com/) / [pythonocc-core](https://github.com/tpaviot/pythonocc-core) — 3D CAD kernel for STEP conversion
- [pyproj](https://pyproj4.github.io/pyproj/) — Coordinate reference system transformations
