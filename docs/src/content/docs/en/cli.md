---
title: CLI Reference
description: Complete command-line interface reference
---

gml2step provides a Typer-based CLI with four commands. The entry point is `gml2step`.

## `gml2step convert`

Convert CityGML to STEP format.

```
gml2step convert INPUT_GML OUTPUT_STEP [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--limit N` | int | None | Maximum number of buildings to convert |
| `--method` | str | `solid` | Conversion method: `solid`, `sew`, `extrude`, `auto` |
| `--debug` | flag | False | Enable debug logging |
| `--use-streaming / --no-use-streaming` | flag | True | Use streaming parser for lower memory usage |

**Requires pythonocc-core (OpenCASCADE).**

### Examples

```bash
# Convert with default settings (solid method, streaming on)
gml2step convert building.gml output.step

# Try all methods in sequence
gml2step convert building.gml output.step --method auto

# Convert only the first 50 buildings
gml2step convert building.gml output.step --limit 50

# Disable streaming (loads entire DOM)
gml2step convert building.gml output.step --no-use-streaming
```

---

## `gml2step parse`

Parse a CityGML file and print a JSON summary.

```
gml2step parse INPUT_GML [--limit N]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--limit N` | int | None | Maximum number of buildings to list |

Does **not** require OCCT.

### Output format

```json
{
  "path": "building.gml",
  "detected_source_crs": "EPSG:6677",
  "sample_latitude": 35.6812,
  "sample_longitude": 139.7671,
  "total_buildings": 1234,
  "listed_building_ids": ["bldg_001", "bldg_002", "..."]
}
```

---

## `gml2step stream-parse`

Stream building IDs from a CityGML file using constant memory.

```
gml2step stream-parse INPUT_GML [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--limit N` | int | None | Maximum number of buildings to output |
| `--building-id ID` | str (repeatable) | None | Filter to specific building IDs |
| `--filter-attribute` | str | `gml:id` | Attribute to match building IDs against |

Does **not** require OCCT.

### Output

One building ID per line, followed by a total count:

```
bldg_001
bldg_002
bldg_003
total=3
```

---

## `gml2step extract-footprints`

Extract 2D building footprints with height estimates.

```
gml2step extract-footprints INPUT_GML [OPTIONS]
```

| Option | Type | Default | Description |
|---|---|---|---|
| `--output-json PATH` | path | None | Write results to a JSON file |
| `--limit N` | int | None | Maximum number of buildings |
| `--default-height` | float | `10.0` | Default height when no measurement is available |

Does **not** require OCCT.

### Height estimation priority

1. `measuredHeight` attribute from CityGML
2. Z-coordinate range (max - min)
3. `--default-height` value (fallback)

### Output format

JSON array of footprint objects:

```json
[
  {
    "building_id": "bldg_001",
    "height": 25.3,
    "exterior": [[139.767, 35.681], [139.768, 35.681], ...],
    "holes": []
  }
]
```
