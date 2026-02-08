---
title: CLI リファレンス
description: コマンドラインインターフェースの全コマンド
---

gml2step は Typer ベースの CLI で、4つのコマンドがあります。

## `gml2step convert`

CityGML を STEP に変換します。

```
gml2step convert INPUT_GML OUTPUT_STEP [OPTIONS]
```

| オプション | 型 | デフォルト | 説明 |
|---|---|---|---|
| `--limit N` | int | なし | 変換する建物数の上限 |
| `--method` | str | `solid` | 変換方式: `solid`, `sew`, `extrude`, `auto` |
| `--debug` | flag | False | デバッグログ出力 |
| `--use-streaming / --no-use-streaming` | flag | True | ストリーミングパーサーを使う |

**pythonocc-core (OpenCASCADE) が必要です。**

### 例

```bash
# デフォルト設定で変換 (solid, ストリーミング有効)
gml2step convert building.gml output.step

# 全方式を順に試す
gml2step convert building.gml output.step --method auto

# 最初の50棟だけ変換
gml2step convert building.gml output.step --limit 50

# ストリーミングを無効化 (DOM 全体を読み込む)
gml2step convert building.gml output.step --no-use-streaming
```

---

## `gml2step parse`

CityGML をパースして JSON で概要を出力します。

```
gml2step parse INPUT_GML [--limit N]
```

| オプション | 型 | デフォルト | 説明 |
|---|---|---|---|
| `--limit N` | int | なし | 出力する建物数の上限 |

OCCT **不要**。

### 出力

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

建物 ID をメモリ一定でストリーム出力します。

```
gml2step stream-parse INPUT_GML [OPTIONS]
```

| オプション | 型 | デフォルト | 説明 |
|---|---|---|---|
| `--limit N` | int | なし | 出力する建物数の上限 |
| `--building-id ID` | str (複数指定可) | なし | 指定した建物 ID だけに絞る |
| `--filter-attribute` | str | `gml:id` | ID のマッチに使う属性 |

OCCT **不要**。

### 出力

1行に1つの建物 ID、最後に合計:

```
bldg_001
bldg_002
bldg_003
total=3
```

---

## `gml2step extract-footprints`

建物の 2D フットプリントを高さ推定つきで抽出します。

```
gml2step extract-footprints INPUT_GML [OPTIONS]
```

| オプション | 型 | デフォルト | 説明 |
|---|---|---|---|
| `--output-json PATH` | path | なし | JSON ファイルに書き出す |
| `--limit N` | int | なし | 建物数の上限 |
| `--default-height` | float | `10.0` | 高さ情報がないときのデフォルト値 |

OCCT **不要**。

### 高さの決め方

1. CityGML の `measuredHeight` 属性
2. Z 座標の範囲 (最大 - 最小)
3. `--default-height` の値 (フォールバック)

### 出力

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
