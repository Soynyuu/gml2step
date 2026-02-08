# gml2step

[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

**[English README](README.md)**

[CityGML](https://www.ogc.org/standard/citygml/) ファイルを解析し、3D建物ジオメトリを [STEP](https://ja.wikipedia.org/wiki/ISO_10303) (ISO 10303-21) CADフォーマットに変換するスタンドアロンツールキットです。[Paper-CAD](https://github.com/Soynyuu/Paper-CAD) から抽出されました。

## 概要

gml2step は CityGML 2.0 ファイルを読み込み、CAD/CAM/BIM ワークフローで利用可能な STEP ファイルを出力します。国土交通省の [PLATEAU](https://www.mlit.go.jp/plateau/) プロジェクトの大規模データセットにも対応しています。

**主な機能:**

- 任意サイズのファイルに対応する**ストリーミングパーサー**による CityGML 解析
- OpenCASCADE を利用した **STEP 変換**（LoD3 -> LoD2 -> LoD1 -> LoD0 の自動フォールバック）
- **4つの変換方式**: solid, sew, extrude, auto（順次試行）
- 段階的な自動修復を含む **7フェーズのジオメトリパイプライン**
- PLATEAU 3D都市モデルから CityGML データを取得する **PLATEAU 連携機能**
- OCCT 不要の **2Dフットプリント抽出**
- 日本の平面直角座標系 全19系に対応した **CRS自動検出**

## インストール

### 基本機能（解析・フットプリント抽出）

```bash
pip install gml2step
```

### PLATEAU 連携機能付き

```bash
pip install "gml2step[plateau]"
```

### STEP 変換（OpenCASCADE が必要）

STEP 変換には [pythonocc-core](https://github.com/tpaviot/pythonocc-core) が必要ですが、全プラットフォームで pip インストールが安定しているわけではありません。conda または Docker をお使いください。

```bash
# conda
conda install -c conda-forge pythonocc-core
pip install gml2step

# Docker（フル機能の変換にはこちらを推奨）
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

> **補足:** 解析、ストリーミング、フットプリント抽出は OCCT なしで動作します。`convert` コマンドのみ OCCT が必要です。

## クイックスタート

### CLI

```bash
# CityGML ファイルを解析してサマリーを JSON で出力
gml2step parse ./input.gml

# 建物を1棟ずつストリーム解析（メモリ一定）
gml2step stream-parse ./input.gml --limit 100

# 2D フットプリントを高さ推定付きで抽出
gml2step extract-footprints ./input.gml --output-json ./footprints.json

# CityGML を STEP に変換
gml2step convert ./input.gml ./output.step --method solid
```

### Python API

```python
from gml2step import parse, stream_parse, extract_footprints, convert

# 軽量サマリー（OCCT 不要）
summary = parse("input.gml")
print(summary["total_buildings"])
print(summary["detected_source_crs"])

# メモリ一定でストリーム解析
for building, xlink_index in stream_parse("input.gml", limit=10):
    bid = building.get("{http://www.opengis.net/gml}id")
    print(bid)

# 2D フットプリント抽出（高さ付き）
footprints = extract_footprints("input.gml", limit=100)
for fp in footprints:
    print(fp.building_id, fp.height, len(fp.exterior))

# CityGML -> STEP 変換
ok, result = convert("input.gml", "output.step", method="auto")
```

## CLI リファレンス

### `gml2step convert`

```
gml2step convert INPUT_GML OUTPUT_STEP [OPTIONS]
```

| オプション | デフォルト | 説明 |
|---|---|---|
| `--limit N` | なし | 変換する建物の最大数 |
| `--method` | `solid` | 変換方式: `solid`, `sew`, `extrude`, `auto` |
| `--debug` | False | デバッグログの有効化 |
| `--use-streaming / --no-use-streaming` | True | ストリーミングパーサーの使用 |

### `gml2step parse`

```
gml2step parse INPUT_GML [--limit N]
```

検出された CRS、建物数、建物 ID を含む JSON サマリーを出力します。

### `gml2step stream-parse`

```
gml2step stream-parse INPUT_GML [--limit N] [--building-id ID ...] [--filter-attribute gml:id]
```

メモリ一定で建物 ID を1行ずつストリーム出力します。建物 ID によるフィルタリングに対応。

### `gml2step extract-footprints`

```
gml2step extract-footprints INPUT_GML [--output-json PATH] [--limit N] [--default-height 10.0]
```

建物の2Dフットプリントを高さ推定付きで抽出します。高さは `measuredHeight`、Z座標の範囲、または指定したデフォルト値から取得されます。

## 変換方式

| 方式 | 説明 |
|---|---|
| **solid** | 主要方式。LoD サーフェスを抽出し、シェルを構築、ソリッドを検証、自動修復。LoD2/LoD3 に最適。 |
| **sew** | WallSurface/RoofSurface/GroundSurface のポリゴンを収集し、面を縫合してソリッド化を試行。 |
| **extrude** | LoD0 フットプリントを推定高さで押し出し。2D データのみのファイル向けフォールバック。 |
| **auto** | solid -> sew -> extrude の順に試行し、最初に成功した方式を採用。 |

## 処理パイプライン

`convert` コマンドは各建物を7つのフェーズで処理します：

| フェーズ | 説明 |
|---|---|
| **0. リセンタリング** | OCCT の数値安定性のため、座標を原点付近に平行移動 |
| **1. LoD 選択** | 利用可能な最良の LoD を選択（LoD3 -> LoD2 -> LoD1 のフォールバック） |
| **1.5. CRS 検出** | ソース CRS を自動検出し、必要に応じて再投影 |
| **2. ジオメトリ抽出** | 選択した変換方式でフェースを抽出 |
| **3. シェル構築** | フェースからマルチパス縫合で OCCT シェルを構築 |
| **4. ソリッド検証** | ジオメトリの検証とソリッドの構築 |
| **5. 自動修復** | 4段階の段階的修復: minimal -> standard -> aggressive -> ultra |
| **6. パーツ統合** | BuildingPart をブーリアン結合で融合（コンパウンドにフォールバック） |
| **7. STEP 出力** | AP214CD スキーマ、ミリメートル単位で STEP ファイルを出力 |

### 精度モード

`precision_mode` パラメータで座標の許容誤差を制御します：

| モード | 相対許容誤差 | 用途 |
|---|---|---|
| `standard` | 0.01% | 一般的な利用 |
| `high` | 0.001% | 詳細なモデル |
| `maximum` | 0.0001% | 高精度CAD |
| `ultra` | 0.00001% | 最大忠実度 |

### 形状修復レベル

`shape_fix_level` パラメータで自動修復の積極性を制御します。指定レベルで修復に失敗した場合、自動的にエスカレーションします：

1. **minimal** — ShapeFix_Solid のみ
2. **standard** — + ShapeUpgrade_UnifySameDomain
3. **aggressive** — + 緩和された許容誤差で再構築
4. **ultra** — + ShapeFix_Shape（完全修復）

## LoD サポート

gml2step は CityGML の Level of Detail 0〜3 に対応しています：

| LoD | 説明 | 対応サーフェス |
|---|---|---|
| **LoD3** | 建築ディテールモデル | lod3Solid, lod3MultiSurface, lod3Geometry |
| **LoD2** | 標準建物モデル（PLATEAU の主要 LoD） | lod2Solid, lod2MultiSurface, lod2Geometry, boundedBy |
| **LoD1** | 単純ブロックモデル | lod1Solid |
| **LoD0** | 2D フットプリント | lod0FootPrint, lod0RoofEdge, GroundSurface |

CityGML 2.0 の境界面タイプ6種すべてに対応: WallSurface, RoofSurface, GroundSurface, OuterCeilingSurface, OuterFloorSurface, ClosureSurface

## ストリーミングパーサー

大規模な CityGML ファイル（PLATEAU データセットでは一般的）向けに、SAX スタイルのストリーミングパーサーを提供しています：

- **O(1棟) のメモリ使用量** — DOM 解析の O(ファイル全体) に対して
- PLATEAU データセットでの**約98%のメモリ削減**
- DOM 解析比で **3〜5倍の高速化**
- 2層 XLink 解決キャッシュ（建物ローカル + グローバル LRU）
- NumPy による座標パース高速化（オプション、10〜20倍高速）

```python
# 20GB の PLATEAU ファイルを約100MB のメモリで処理
for building, xlinks in stream_parse("huge_plateau_file.gml"):
    process(building)
```

## CRS・座標処理

- GML の `srsName` 属性からの **CRS 自動検出**
- **日本の平面直角座標系 全19系**（EPSG:6669〜6687）に対応し、緯度・経度から適切な系を自動選択
- 地理座標系（WGS84, JGD2000, JGD2011）から適切な投影座標系への**自動再投影**
- OCCT の浮動小数点精度損失を防ぐための**座標リセンタリング**

## PLATEAU 連携

[PLATEAU](https://www.mlit.go.jp/plateau/) は国土交通省が推進する、日本全国の3D都市モデルをCityGMLフォーマットで整備・オープンデータ化するプロジェクトです。

gml2step はオプションで PLATEAU との連携機能を提供しています（`pip install "gml2step[plateau]"`）。

### 建物検索

住所から建物を検索し、CityGML データの取得・解析・ランキングを一括で行います：

```python
from gml2step.plateau.fetcher import search_buildings_by_address

# 住所で検索 — ジオコーディング → CityGML取得 → 解析 → ランキング
buildings = search_buildings_by_address(
    "東京都千代田区霞が関3-2-1",
    ranking_mode="hybrid",  # "distance", "name", "hybrid"
    limit=10,
)
for b in buildings:
    print(b.building_id, b.name, b.height, b.lod_level)
```

### メッシュコードユーティリティ

PLATEAU データは [JIS X 0410 標準地域メッシュ](https://www.stat.go.jp/data/mesh/m_tuite.html)で整理されています。gml2step は5段階のメッシュレベルに対応する変換関数を提供しています：

```python
from gml2step.plateau.mesh_utils import (
    latlon_to_mesh_1st,    # 第1次メッシュ 80km (4桁)
    latlon_to_mesh_2nd,    # 第2次メッシュ 10km (6桁)
    latlon_to_mesh_3rd,    # 第3次メッシュ 1km (8桁)
    latlon_to_mesh_half,   # 2分の1メッシュ 500m (9桁)
    latlon_to_mesh_quarter # 4分の1メッシュ 250m (10桁)
)

mesh = latlon_to_mesh_3rd(35.6812, 139.7671)  # 東京駅
```

### 非同期APIクライアント

```python
import asyncio
from gml2step.plateau.api_client import fetch_plateau_datasets_by_mesh

# メッシュコードから PLATEAU データセットの URL を取得
result = asyncio.run(fetch_plateau_datasets_by_mesh("53394525"))
```

### 機能一覧

- Nominatim を利用した**ジオコーディング**（日本固有のバリデーション・関連度スコアリング付き）
- 3つのランキングモードに対応した**建物検索**: 距離、名称類似度（レーベンシュタイン距離 + トークンマッチング）、ハイブリッド
- **JIS X 0410 メッシュコード**変換（第1次〜4分の1メッシュ）
- 境界付近の検索のための**隣接メッシュ列挙**（3×3グリッド）
- 並行性制御付きの**非同期バッチメッシュ解決**
- **CityGMLキャッシュ**（環境変数 `CITYGML_CACHE_ENABLED` / `CITYGML_CACHE_DIR` でオプトイン）
- **全国メッシュ→市区町村コードマッピング**をパッケージデータとして同梱

## アーキテクチャ

```
src/gml2step/
├── __init__.py              # 公開API: convert, parse, stream_parse, extract_footprints
├── api.py                   # API 実装
├── cli.py                   # Typer CLI
├── coordinate_utils.py      # CRS ユーティリティ、日本の座標系ゾーン定義
├── data/
│   └── mesh2_municipality.json  # 全国メッシュ→市区町村コードマッピング
├── citygml/
│   ├── core/                # 型定義、定数、CityGML 名前空間
│   ├── parsers/             # 座標・ポリゴン抽出
│   ├── streaming/           # SAXスタイルストリーミングパーサー、XLinkキャッシュ、座標最適化
│   ├── lod/                 # LoD0〜LoD3 抽出戦略、フットプリント抽出
│   ├── geometry/            # OCCT ジオメトリビルダー、シェル/ソリッド構築、自動修復
│   ├── transforms/          # CRS検出、再投影、リセンタリング
│   ├── utils/               # XLinkリゾルバ、XMLパーサー、ロギング
│   └── pipeline/            # オーケストレーター（7フェーズ変換パイプライン）
└── plateau/                 # PLATEAU APIクライアント、ジオコーディング、メッシュユーティリティ、建物検索
```

## 開発

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
pytest
```

## ライセンス

このプロジェクトは [GNU Affero General Public License v3.0](LICENSE) (AGPL-3.0-or-later) の下でライセンスされています。

gml2step は [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) の一部として開発され、スタンドアロンライブラリとして抽出されました。詳細な帰属表示は [NOTICE](NOTICE) をご覧ください。

## 謝辞

- [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) — gml2step の抽出元となった親プロジェクト
- [PLATEAU](https://www.mlit.go.jp/plateau/) — 国土交通省の3D都市モデルプロジェクト
- [OpenCASCADE](https://www.opencascade.com/) / [pythonocc-core](https://github.com/tpaviot/pythonocc-core) — STEP 変換用3D CADカーネル
- [pyproj](https://pyproj4.github.io/pyproj/) — 座標参照系変換
