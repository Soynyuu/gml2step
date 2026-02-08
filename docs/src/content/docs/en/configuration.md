---
title: Configuration
description: Environment variables and settings
---

## Environment variables

### PLATEAU module

| Variable | Default | Description |
|---|---|---|
| `CITYGML_CACHE_ENABLED` | `false` | Enable local caching of downloaded CityGML files |
| `CITYGML_CACHE_DIR` | `<package>/data/citygml_cache` | Directory for cached GML files |
| `PLATEAU_API_URL` | `https://api.plateauview.mlit.go.jp/datacatalog/plateau-datasets` | PLATEAU Data Catalog API endpoint |
| `PLATEAU_MESH2_MAPPING_PATH` | `<package>/data/mesh2_municipality.json` | Path to mesh-to-municipality mapping file |
| `PLATEAU_ALLOW_TOKYO_FALLBACK` | `true` | Allow hardcoded Tokyo ward tilesets as fallback |
| `PLATEAU_DATASET_FETCH_CONCURRENCY` | `8` | Max concurrent HTTP requests for dataset fetching |

### Example

```bash
# Enable caching with a custom directory
export CITYGML_CACHE_ENABLED=true
export CITYGML_CACHE_DIR=/tmp/gml_cache

# Increase concurrency for batch operations
export PLATEAU_DATASET_FETCH_CONCURRENCY=16
```

---

## Conversion parameters

These are passed programmatically to `convert()` or set via CLI flags.

### Precision modes

| Mode | Factor | Relative tolerance |
|---|---|---|
| `standard` | 0.0001 | 0.01% |
| `high` | 0.00001 | 0.001% |
| `maximum` | 0.000001 | 0.0001% |
| `ultra` | 0.0000001 | 0.00001% |

The factor is multiplied by coordinate magnitude to determine absolute tolerance for geometry operations (sewing, validation, repair).

### Shape fix levels

Auto-repair escalates through these levels when geometry validation fails:

| Level | Operations |
|---|---|
| `minimal` | `ShapeFix_Solid` |
| `standard` | + `ShapeUpgrade_UnifySameDomain` |
| `aggressive` | + Rebuild shell with relaxed tolerance |
| `ultra` | + `ShapeFix_Shape` (full OCCT repair) |

The `shape_fix_level` parameter sets the starting level. If repair fails, it escalates to the next level automatically. The escalation chain is:

```
minimal -> standard -> aggressive -> ultra
```

### Conversion methods

| Method | Priority | Best for |
|---|---|---|
| `solid` | Default | LoD2/LoD3 with closed surfaces |
| `sew` | Fallback | Nearly-closed geometry with gaps |
| `extrude` | Last resort | LoD0 footprint-only data |
| `auto` | Tries all | Unknown data quality |

---

## Internal constants

These are defined in `gml2step.citygml.core.constants` and cannot be changed at runtime.

| Constant | Value | Description |
|---|---|---|
| `DEFAULT_BUILDING_HEIGHT` | 10.0 m | Fallback height for footprint extrusion |
| `DEFAULT_COORDINATE_FILTER_RADIUS` | 100.0 m | Default radius for spatial building filtering |

---

## Streaming parser settings

Configurable via `StreamingConfig` when using the Python API directly:

| Setting | Default | Description |
|---|---|---|
| `limit` | None | Max buildings to process |
| `building_ids` | None | Filter to specific IDs |
| `filter_attribute` | `gml:id` | XML attribute for ID matching |
| `debug` | False | Enable debug output |
| `enable_gc_per_building` | True | Force garbage collection after each building |
| `max_xlink_cache_size` | 10000 | Max entries in global XLink LRU cache |
