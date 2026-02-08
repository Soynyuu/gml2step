---
title: PLATEAU 連携
description: 国交省 3D 都市モデルからのデータ取得
---

## PLATEAU とは

[PLATEAU](https://www.mlit.go.jp/plateau/) は国交省が進めている、日本全国の 3D 都市モデルを CityGML で整備・公開するプロジェクトです。建物、道路、地形などのデータが [JIS X 0410 標準地域メッシュ](https://www.stat.go.jp/data/mesh/m_tuite.html) 単位で整理されています。

## gml2step の PLATEAU 機能

`pip install "gml2step[plateau]"` で使える PLATEAU 関連機能は、2つの公開 API を叩くための便利関数です。独自のバックエンドサーバーはありません:

- **[PLATEAU データカタログ API](https://api.plateauview.mlit.go.jp/)** (国交省運営) — メッシュコードや自治体から CityGML ファイルの URL を取得
- **[Nominatim](https://nominatim.openstreetmap.org/)** (OpenStreetMap) — 日本語住所を緯度経度に変換

---

## 住所で建物検索

メインの機能。住所を渡すと、ジオコーディング → メッシュコード変換 → PLATEAU API 問い合わせ → CityGML ダウンロード・パース → ランキングまで一気にやります。

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

### ランキングモード

| モード | ランキング方法 |
|---|---|
| `distance` | ジオコーディング地点からの距離 |
| `name` | 名前の類似度 (レーベンシュタイン距離 + トークンマッチ) |
| `hybrid` | 距離と名前の複合スコア |

### `BuildingInfo` のフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `building_id` | str | CityGML 建物 ID |
| `gml_id` | str | GML ID 属性 |
| `latitude` | float | 建物重心の緯度 |
| `longitude` | float | 建物重心の経度 |
| `distance_meters` | float | 検索地点からの距離 |
| `height` | float | 建物高さ |
| `measured_height` | float | CityGML の `measuredHeight` |
| `name` | str | 建物名 (あれば) |
| `usage` | str | 用途 |
| `has_lod2` | bool | LoD2 データがあるか |
| `has_lod3` | bool | LoD3 データがあるか |
| `relevance_score` | float | 総合ランキングスコア |
| `name_similarity` | float | 名前一致スコア (0-1) |
| `match_reason` | str | ランキング理由 |

---

## メッシュコードで取得

PLATEAU データはメッシュコード単位で管理されています。メッシュコードを直接指定してデータを取得できます。

### 緯度経度からメッシュコード

```python
from gml2step.plateau.mesh_utils import (
    latlon_to_mesh_1st,     # 1次メッシュ 80km (4桁)
    latlon_to_mesh_2nd,     # 2次メッシュ 10km (6桁)
    latlon_to_mesh_3rd,     # 3次メッシュ 1km (8桁)
    latlon_to_mesh_half,    # 2分の1メッシュ 500m (9桁)
    latlon_to_mesh_quarter, # 4分の1メッシュ 250m (10桁)
)

mesh = latlon_to_mesh_3rd(35.6812, 139.7671)  # 東京駅 -> "53394525"
```

### 隣接メッシュ

メッシュ境界付近の検索用に、3x3 の周辺メッシュを取得できます:

```python
from gml2step.plateau.mesh_utils import get_neighboring_meshes_3rd

neighbors = get_neighboring_meshes_3rd("53394525")  # 9個のメッシュコード
```

### メッシュコードからデータセット取得

```python
import asyncio
from gml2step.plateau.api_client import fetch_plateau_datasets_by_mesh

datasets = asyncio.run(fetch_plateau_datasets_by_mesh("53394525"))
```

---

## 建物 ID で取得

建物の GML ID とメッシュコードがわかっている場合:

```python
from gml2step.plateau.fetcher import search_building_by_id_and_mesh

result = search_building_by_id_and_mesh(
    building_id="bldg_12345",
    mesh_code="53394525",
)
```

---

## ジオコーディング

Nominatim のラッパーで、日本向けのバリデーションつきです:

```python
from gml2step.plateau.fetcher import geocode_address

result = geocode_address("東京駅")
if result:
    print(result.latitude, result.longitude, result.display_name)
```

Nominatim の利用ポリシーに従い 1req/sec にレート制限しています。

### `GeocodingResult` のフィールド

| フィールド | 型 | 説明 |
|---|---|---|
| `query` | str | 元のクエリ文字列 |
| `latitude` | float | 緯度 |
| `longitude` | float | 経度 |
| `display_name` | str | Nominatim の表示名 |
| `osm_type` | str | OSM フィーチャタイプ |
| `osm_id` | str | OSM フィーチャ ID |

---

## キャッシュ

CityGML のダウンロードをローカルにキャッシュできます。

| 環境変数 | デフォルト | 説明 |
|---|---|---|
| `CITYGML_CACHE_ENABLED` | `false` | `true` で有効化 |
| `CITYGML_CACHE_DIR` | `<package>/data/citygml_cache` | キャッシュディレクトリ |

有効にすると、ダウンロードした GML ファイルがキャッシュに保存されます。同じメッシュコードへのリクエストは API を叩かずキャッシュから読みます。

---

## メッシュ→市区町村マッピング

2次メッシュコードから市区町村コードへのオフラインマッピング (`mesh2_municipality.json`) を同梱しています。メッシュがどの自治体に属するかを API 呼び出しなしで解決できます。

```python
from gml2step.plateau.mesh_mapping import get_municipality_from_mesh2

code = get_municipality_from_mesh2("533945")  # -> "13101" (千代田区)
```
