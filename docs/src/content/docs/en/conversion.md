---
title: Conversion Guide
description: How gml2step converts CityGML to STEP
---

## Conversion methods

gml2step provides four methods for converting CityGML geometry to STEP solids. Each suits different input data characteristics.

### `solid` (default)

The primary method. Extracts LoD surfaces from the CityGML building, constructs shells from faces, validates them as solids, and applies auto-repair if needed.

Best for **LoD2 and LoD3** data where surfaces (WallSurface, RoofSurface, GroundSurface) form a closed volume.

### `sew`

Collects all boundary surface polygons (WallSurface, RoofSurface, GroundSurface), sews them into a shell using OpenCASCADE's sewing algorithm, then attempts to form a solid.

Useful when the geometry is almost closed but has small gaps that sewing can repair.

### `extrude`

Takes the LoD0 footprint (2D polygon) and extrudes it vertically to the estimated building height. This produces a simple box-like solid.

Fallback for files that only contain 2D footprint data (LoD0).

### `auto`

Tries methods in order: **solid -> sew -> extrude**. Uses the first one that succeeds. This is the safest option when you don't know the input data quality.

```bash
gml2step convert building.gml output.step --method auto
```

---

## Processing pipeline

The `convert` command processes each building through 7 phases:

### Phase 0: Recentering

Translates coordinates near the origin. CityGML files use real-world coordinates (e.g., X=140000, Y=36000 in meters), which cause floating-point precision loss in OpenCASCADE. Recentering subtracts the centroid of the first building from all coordinates.

### Phase 1: LoD selection

Selects the most detailed Level of Detail available in the building element. The fallback order is:

**LoD3 -> LoD2 -> LoD1 -> LoD0**

If LoD3 surfaces are present, they are used. Otherwise falls back to LoD2, and so on.

### Phase 1.5: CRS detection

Auto-detects the coordinate reference system from the GML `srsName` attribute. If the source CRS is geographic (WGS84, JGD2000, JGD2011), it reprojects to an appropriate Japan Plane Rectangular CS zone.

### Phase 2: Geometry extraction

Extracts faces from the building using the selected conversion method. For `solid`, this means collecting all boundary surfaces. For `extrude`, this means extracting the footprint polygon and computing height.

### Phase 3: Shell construction

Builds OCCT shells from the extracted faces. Uses multi-pass sewing with increasing tolerance if the first pass fails to produce a valid shell.

### Phase 4: Solid validation

Validates the shell geometry and constructs a BRep solid. Checks for closure, orientation, and self-intersection.

### Phase 5: Auto-repair

If validation fails, applies progressive repair. The repair level escalates automatically:

| Level | What it does |
|---|---|
| **minimal** | `ShapeFix_Solid` only |
| **standard** | + `ShapeUpgrade_UnifySameDomain` |
| **aggressive** | + Rebuild with relaxed tolerance |
| **ultra** | + `ShapeFix_Shape` (full repair) |

### Phase 6: Part merging

If a building has `BuildingPart` children, merges them into a single solid via Boolean union. Falls back to a compound (ungrouped collection) if Boolean union fails.

### Phase 7: STEP export

Writes the final geometry as an AP214CD STEP file with millimeter units.

---

## Precision modes

The `precision_mode` parameter controls coordinate tolerance during geometry construction.

| Mode | Relative tolerance | When to use |
|---|---|---|
| `standard` | 0.01% (factor 0.0001) | General use, sufficient for most models |
| `high` | 0.001% (factor 0.00001) | Detailed architectural models |
| `maximum` | 0.0001% (factor 0.000001) | High-precision CAD workflows |
| `ultra` | 0.00001% (factor 0.0000001) | Maximum fidelity, may be slower |

```python
convert("input.gml", "output.step", precision_mode="high")
```

Lower tolerance means tighter geometry matching. This affects sewing, validation, and repair. If conversion fails at `standard`, try `high` — some models need tighter tolerances to produce valid solids.

---

## LoD support

gml2step supports CityGML Level of Detail 0 through 3.

| LoD | Description | CityGML elements |
|---|---|---|
| **LoD3** | Architectural detail | `lod3Solid`, `lod3MultiSurface`, `lod3Geometry` |
| **LoD2** | Standard building | `lod2Solid`, `lod2MultiSurface`, `lod2Geometry`, `boundedBy` |
| **LoD1** | Simple block | `lod1Solid` |
| **LoD0** | 2D footprint | `lod0FootPrint`, `lod0RoofEdge`, `GroundSurface` |

All 6 CityGML 2.0 boundary surface types are recognized:

- `WallSurface`
- `RoofSurface`
- `GroundSurface`
- `OuterCeilingSurface`
- `OuterFloorSurface`
- `ClosureSurface`

PLATEAU datasets primarily use **LoD2** with WallSurface, RoofSurface, and GroundSurface.
