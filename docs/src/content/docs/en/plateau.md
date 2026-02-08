---
title: PLATEAU Integration
description: Fetching CityGML data from Japan's 3D city model
---

## What is PLATEAU?

[PLATEAU](https://www.mlit.go.jp/plateau/) is a project by Japan's Ministry of Land, Infrastructure, Transport and Tourism (MLIT) that provides open 3D city models for the entire country in CityGML format. The data covers buildings, roads, terrain, and more, organized by [JIS X 0410 standard mesh codes](https://www.stat.go.jp/data/mesh/m_tuite.html).

## What gml2step provides

gml2step's PLATEAU module (`pip install "gml2step[plateau]"`) is a convenience wrapper for fetching and searching PLATEAU building data. It calls two public APIs directly — there is no custom backend server:

- **[PLATEAU Data Catalog API](https://api.plateauview.mlit.go.jp/)** (operated by MLIT) — queried for CityGML file URLs by mesh code or municipality
- **[Nominatim](https://nominatim.openstreetmap.org/)** (OpenStreetMap) — used for geocoding Japanese addresses to latitude/longitude

---

## Address-based building search

The main entry point. Takes a Japanese address, geocodes it, fetches the surrounding CityGML data from PLATEAU, parses the buildings, and ranks them.

```python
from gml2step.plateau.fetcher import search_buildings_by_address

buildings = search_buildings_by_address(
    "東京都千代田区霞が関3-2-1",
    ranking_mode="hybrid",
    limit=10,
)
for b in buildings:
    print(b.building_id, b.name, b.height, b.lod_level)
```

### Ranking modes

| Mode | How it ranks |
|---|---|
| `distance` | By geographic distance from the geocoded point |
| `name` | By name similarity (Levenshtein distance + token matching) |
| `hybrid` | Combined distance and name score |

### `BuildingInfo` fields

| Field | Type | Description |
|---|---|---|
| `building_id` | str | CityGML building ID |
| `gml_id` | str | GML ID attribute |
| `latitude` | float | Building centroid latitude |
| `longitude` | float | Building centroid longitude |
| `distance_meters` | float | Distance from search point |
| `height` | float | Building height |
| `measured_height` | float | `measuredHeight` from CityGML |
| `name` | str | Building name (if available) |
| `usage` | str | Building usage type |
| `has_lod2` | bool | Whether LoD2 data exists |
| `has_lod3` | bool | Whether LoD3 data exists |
| `relevance_score` | float | Combined ranking score |
| `name_similarity` | float | Name match score (0-1) |
| `match_reason` | str | Why this result was ranked |

---

## Mesh code lookup

PLATEAU data is organized by JIS X 0410 mesh codes. You can fetch data by mesh code directly.

### Latitude/longitude to mesh code

```python
from gml2step.plateau.mesh_utils import (
    latlon_to_mesh_1st,     # 80km grid (4-digit)
    latlon_to_mesh_2nd,     # 10km grid (6-digit)
    latlon_to_mesh_3rd,     # 1km grid (8-digit)
    latlon_to_mesh_half,    # 500m grid (9-digit)
    latlon_to_mesh_quarter, # 250m grid (10-digit)
)

mesh = latlon_to_mesh_3rd(35.6812, 139.7671)  # Tokyo Station -> "53394525"
```

### Neighboring meshes

For searches near mesh boundaries, get the 3x3 surrounding grid:

```python
from gml2step.plateau.mesh_utils import get_neighboring_meshes_3rd

neighbors = get_neighboring_meshes_3rd("53394525")  # Returns 9 mesh codes
```

### Fetch datasets by mesh code

```python
import asyncio
from gml2step.plateau.api_client import fetch_plateau_datasets_by_mesh

datasets = asyncio.run(fetch_plateau_datasets_by_mesh("53394525"))
```

---

## Building ID lookup

If you know a specific building's GML ID and its mesh code:

```python
from gml2step.plateau.fetcher import search_building_by_id_and_mesh

result = search_building_by_id_and_mesh(
    building_id="bldg_12345",
    mesh_code="53394525",
)
```

---

## Geocoding

The geocoder wraps Nominatim with Japan-specific validation:

```python
from gml2step.plateau.fetcher import geocode_address

result = geocode_address("東京駅")
if result:
    print(result.latitude, result.longitude, result.display_name)
```

Rate-limited to 1 request per second per Nominatim's usage policy.

### `GeocodingResult` fields

| Field | Type | Description |
|---|---|---|
| `query` | str | Original query string |
| `latitude` | float | Geocoded latitude |
| `longitude` | float | Geocoded longitude |
| `display_name` | str | Nominatim display name |
| `osm_type` | str | OSM feature type |
| `osm_id` | str | OSM feature ID |

---

## Caching

CityGML downloads can be cached locally to avoid re-fetching.

| Environment variable | Default | Description |
|---|---|---|
| `CITYGML_CACHE_ENABLED` | `false` | Set to `true` to enable |
| `CITYGML_CACHE_DIR` | `<package>/data/citygml_cache` | Cache directory path |

When enabled, downloaded GML files are stored in the cache directory. Subsequent requests for the same mesh code read from cache instead of making API calls.

---

## Mesh-to-municipality mapping

gml2step includes an offline JSON file (`mesh2_municipality.json`) that maps 2nd-level mesh codes to municipality codes. This avoids needing extra API calls to resolve which municipality a mesh belongs to.

```python
from gml2step.plateau.mesh_mapping import get_municipality_from_mesh2

code = get_municipality_from_mesh2("533945")  # -> "13101" (Chiyoda-ku)
```
