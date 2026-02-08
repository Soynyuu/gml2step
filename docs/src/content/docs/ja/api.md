---
title: Python API リファレンス
description: gml2step の公開 Python API
---

トップレベルパッケージから4つの関数をエクスポートしています。

```python
from gml2step import convert, parse, stream_parse, extract_footprints
```

---

## `convert()`

CityGML を STEP に変換します。

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

**pythonocc-core が必要。**

### パラメータ

| パラメータ | 型 | デフォルト | 説明 |
|---|---|---|---|
| `gml_path` | str | (必須) | 入力 CityGML ファイルのパス |
| `out_step` | str | (必須) | 出力 STEP ファイルのパス |
| `limit` | int \| None | None | 変換する建物数の上限 |
| `method` | str | `"solid"` | `"solid"`, `"sew"`, `"extrude"`, `"auto"` |
| `debug` | bool | False | デバッグログ |
| `sew_tolerance` | float \| None | None | 縫合の許容誤差 (カスタム) |
| `reproject_to` | str \| None | None | 変換先 CRS (例: `"EPSG:6677"`) |
| `source_crs` | str \| None | None | ソース CRS を上書き |
| `auto_reproject` | bool | True | CRS 自動検出・再投影 |
| `precision_mode` | str | `"standard"` | `"standard"`, `"high"`, `"maximum"`, `"ultra"` |
| `shape_fix_level` | str | `"minimal"` | `"minimal"`, `"standard"`, `"aggressive"`, `"ultra"` |
| `building_ids` | list \| None | None | 特定の建物 ID に絞る |
| `filter_attribute` | str | `"gml:id"` | ID マッチに使う属性 |
| `merge_building_parts` | bool | True | BuildingPart をブーリアン結合 |
| `target_latitude` | float \| None | None | 空間フィルタの緯度 |
| `target_longitude` | float \| None | None | 空間フィルタの経度 |
| `radius_meters` | float | 100 | 空間フィルタの半径 (m) |
| `use_streaming` | bool | True | ストリーミングパーサーを使う |

### 戻り値

`Tuple[bool, str]` — `(成功したか, メッセージ or 出力パス)`

### 例

```python
ok, result = convert(
    "input.gml",
    "output.step",
    method="auto",
    precision_mode="high",
    limit=10,
)
if ok:
    print(f"出力: {result}")
```

---

## `parse()`

CityGML をパースして概要を dict で返します。

```python
def parse(
    gml_path: str,
    limit: Optional[int] = None,
) -> Dict[str, Any]
```

OCCT **不要**。

### 戻り値

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

### 例

```python
summary = parse("building.gml")
print(f"CRS: {summary['detected_source_crs']}")
print(f"建物数: {summary['total_buildings']}")
```

---

## `stream_parse()`

建物を1棟ずつストリーム処理します。メモリ使用量はファイルサイズに依存しません。

```python
def stream_parse(
    gml_path: str,
    limit: Optional[int] = None,
    building_ids: Optional[List[str]] = None,
    filter_attribute: str = "gml:id",
    debug: bool = False,
) -> Iterator[Tuple[ET.Element, Dict[str, ET.Element]]]
```

OCCT **不要**。

### yield

`Tuple[Element, dict]` — `(building 要素, ローカル XLink インデックス)`

- `<bldg:Building>` の XML 要素
- その建物スコープ内で解決された XLink ターゲットの dict

### 例

```python
for building, xlinks in stream_parse("large_file.gml", limit=100):
    bid = building.get("{http://www.opengis.net/gml}id")
    print(bid)
```

---

## `extract_footprints()`

2D フットプリントを高さ推定つきで抽出します。

```python
def extract_footprints(
    gml_path: str,
    default_height: float = 10.0,
    limit: Optional[int] = None,
) -> List[Footprint]
```

OCCT **不要**。

### 戻り値

`List[Footprint]`:

| フィールド | 型 | 説明 |
|---|---|---|
| `building_id` | str | GML 建物 ID |
| `exterior` | list[tuple[float, float]] | 外周リングの座標 |
| `holes` | list[list[tuple[float, float]]] | 内周リング (穴) |
| `height` | float | 推定高さ (m) |

### 例

```python
footprints = extract_footprints("building.gml", default_height=15.0)
for fp in footprints:
    print(f"{fp.building_id}: {fp.height}m, {len(fp.exterior)} vertices")
```

---

## 主要な型

### `Footprint`

```python
@dataclass
class Footprint:
    exterior: List[Tuple[float, float]]
    holes: List[List[Tuple[float, float]]]
    height: float
    building_id: str
```

`gml2step.citygml.lod.footprint_extractor` で定義。

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

`gml2step.citygml.streaming.parser` で定義。ストリーミングパーサーの動作を制御します。
