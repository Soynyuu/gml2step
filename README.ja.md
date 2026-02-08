# gml2step

[![CI](https://github.com/Soynyuu/gml2step/actions/workflows/ci.yml/badge.svg)](https://github.com/Soynyuu/gml2step/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/gml2step)](https://pypi.org/project/gml2step/)
[![License: AGPL v3](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](https://www.gnu.org/licenses/agpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Docs](https://github.com/Soynyuu/gml2step/actions/workflows/deploy-docs.yml/badge.svg)](https://soynyuu.github.io/gml2step/)
[![CityGML 2.0](https://img.shields.io/badge/CityGML-2.0-green.svg)](https://www.ogc.org/standard/citygml/)
[![STEP ISO 10303](https://img.shields.io/badge/STEP-ISO_10303--21-green.svg)](https://en.wikipedia.org/wiki/ISO_10303-21)
[![PLATEAU](https://img.shields.io/badge/PLATEAU-supported-orange.svg)](https://www.mlit.go.jp/plateau/)

**[English README](README.md)**

CityGML ファイルをパースして STEP (ISO 10303-21) に変換するツールです。[Paper-CAD](https://github.com/Soynyuu/Paper-CAD) から切り出しました。

ドキュメント: **https://soynyuu.github.io/gml2step/**
## 概要

CityGML 2.0 の建物データを読み込んで、CAD/BIM で扱える STEP ファイルに変換します。国交省 [PLATEAU](https://www.mlit.go.jp/plateau/) の大規模データにも対応しています。

**できること:**

- **CityGML パース** — ストリーミング対応で巨大ファイルも処理可能
- **STEP 変換** — OpenCASCADE ベース、LoD の自動フォールバック (LoD3 -> LoD2 -> LoD1 -> LoD0)
- **4つの変換方式** — solid / sew / extrude / auto
- **7フェーズの変換パイプライン** — 段階的な自動修復つき
- **PLATEAU データ取得** — 公開 API (国交省データカタログ API + OSM Nominatim) 経由
- **フットプリント抽出** — OCCT なしで 2D 外形 + 高さ推定
- **CRS 自動検出** — 平面直角座標系 全19系に対応

## 目次

- [概要](#概要)
- [インストール](#インストール)
- [クイックスタート](#クイックスタート)
- [CLI リファレンス](#cli-リファレンス)
- [変換方式](#変換方式)
- [処理パイプライン](#処理パイプライン)
- [LoD サポート](#lod-サポート)
- [ストリーミングパーサー](#ストリーミングパーサー)
- [CRS・座標処理](#crs座標処理)
- [PLATEAU 連携](#plateau-連携)
- [アーキテクチャ](#アーキテクチャ)
- [開発](#開発)
- [ライセンス](#ライセンス)



## インストール

### 基本 (パース・フットプリント抽出)

```bash
pip install gml2step
```

### PLATEAU 連携つき

```bash
pip install "gml2step[plateau]"
```

### STEP 変換 (OpenCASCADE 必要)

[pythonocc-core](https://github.com/tpaviot/pythonocc-core) が必要です。pip だけだと環境によっては入らないので conda か Docker を使ってください。

```bash
# conda
conda install -c conda-forge pythonocc-core
pip install gml2step

# Docker
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

> パース・ストリーミング・フットプリント抽出は OCCT なしで動きます。OCCT が必要なのは `convert` だけです。

## クイックスタート

### CLI

```bash
# パースして JSON で概要を出力
gml2step parse ./input.gml

# 1棟ずつストリーム処理 (メモリ一定)
gml2step stream-parse ./input.gml --limit 100

# 2D フットプリント抽出
gml2step extract-footprints ./input.gml --output-json ./footprints.json

# STEP 変換
gml2step convert ./input.gml ./output.step --method solid
```

### Python API

```python
from gml2step import parse, stream_parse, extract_footprints, convert

# パース (OCCT 不要)
summary = parse("input.gml")
print(summary["total_buildings"])
print(summary["detected_source_crs"])

# ストリーム処理
for building, xlink_index in stream_parse("input.gml", limit=10):
    bid = building.get("{http://www.opengis.net/gml}id")
    print(bid)

# フットプリント抽出
footprints = extract_footprints("input.gml", limit=100)
for fp in footprints:
    print(fp.building_id, fp.height, len(fp.exterior))

# STEP 変換
ok, result = convert("input.gml", "output.step", method="auto")
```

## CLI リファレンス

### `gml2step convert`

```
gml2step convert INPUT_GML OUTPUT_STEP [OPTIONS]
```

| オプション | デフォルト | 説明 |
|---|---|---|
| `--limit N` | なし | 変換する建物数の上限 |
| `--method` | `solid` | 変換方式: `solid`, `sew`, `extrude`, `auto` |
| `--debug` | False | デバッグログ出力 |
| `--use-streaming / --no-use-streaming` | True | ストリーミングパーサーを使う |
| `--building-id ID` | なし | 特定の建物IDでフィルタ（複数回指定可） |
| `--filter-attribute` | `gml:id` | 建物IDフィルタでマッチする属性 |

### `gml2step parse`

```
gml2step parse INPUT_GML [--limit N]
```

CRS・建物数・建物 ID を含む JSON を出力します。

### `gml2step stream-parse`

```
gml2step stream-parse INPUT_GML [--limit N] [--building-id ID ...] [--filter-attribute gml:id]
```

建物 ID を1行ずつ出力します。メモリ使用量はファイルサイズに依存しません。

### `gml2step extract-footprints`

```
gml2step extract-footprints INPUT_GML [--output-json PATH] [--limit N] [--default-height 10.0]
```

建物の 2D フットプリントを高さ推定つきで抽出します。高さは `measuredHeight` > Z座標範囲 > デフォルト値の優先順位で決まります。

## 変換方式

| 方式 | 説明 |
|---|---|
| **solid** | メインの方式。LoD サーフェスからシェルを組み立てて、ソリッドとして検証・修復する。LoD2/LoD3 向き。 |
| **sew** | Wall/Roof/GroundSurface のポリゴンを集めて縫合し、ソリッドにする。 |
| **extrude** | LoD0 のフットプリントを高さ方向に押し出す。2D データしかないとき用。 |
| **auto** | solid -> sew -> extrude の順に試して、最初に成功したものを使う。 |

## 処理パイプライン

`convert` は建物ごとに以下の7フェーズを実行します:

| フェーズ | やること |
|---|---|
| **0. リセンタリング** | 座標を原点付近に移動 (OCCT の数値安定性のため) |
| **1. LoD 選択** | 使える中で一番詳細な LoD を選ぶ (LoD3 -> LoD2 -> LoD1) |
| **1.5. CRS 検出** | CRS を自動判定して、必要なら再投影 |
| **2. ジオメトリ抽出** | 選んだ方式でフェースを取り出す |
| **3. シェル構築** | フェースを縫い合わせて OCCT シェルにする |
| **4. ソリッド検証** | ジオメトリが正しいか検証してソリッド化 |
| **5. 自動修復** | 壊れていたら段階的に修復 (minimal -> standard -> aggressive -> ultra) |
| **6. パーツ統合** | BuildingPart をブーリアン結合で1つにまとめる |
| **7. STEP 出力** | AP214CD / mm 単位で書き出し |

### 精度モード

`precision_mode` で座標の許容誤差を変えられます:

| モード | 相対許容誤差 | 用途 |
|---|---|---|
| `standard` | 0.01% | 普通はこれで十分 |
| `high` | 0.001% | 細かいモデル |
| `maximum` | 0.0001% | 高精度 CAD |
| `ultra` | 0.00001% | 最大精度 |

### 形状修復レベル

`shape_fix_level` で修復の強さを指定します。失敗すると自動的に次のレベルに上がります:

1. **minimal** — ShapeFix_Solid のみ
2. **standard** — + ShapeUpgrade_UnifySameDomain
3. **aggressive** — + 許容誤差を緩めて再構築
4. **ultra** — + ShapeFix_Shape (フル修復)

## LoD サポート

CityGML の LoD0〜3 に対応しています:

| LoD | 内容 | 対応要素 |
|---|---|---|
| **LoD3** | 建築ディテールモデル | lod3Solid, lod3MultiSurface, lod3Geometry |
| **LoD2** | 標準建物モデル (PLATEAU のメイン) | lod2Solid, lod2MultiSurface, lod2Geometry, boundedBy |
| **LoD1** | 単純ブロック | lod1Solid |
| **LoD0** | 2D フットプリント | lod0FootPrint, lod0RoofEdge, GroundSurface |

境界面タイプ6種に対応: WallSurface, RoofSurface, GroundSurface, OuterCeilingSurface, OuterFloorSurface, ClosureSurface

## ストリーミングパーサー

PLATEAU のような巨大な CityGML を扱うための SAX ベースのストリーミングパーサーです。DOM パーサーがファイル全体をメモリに載せるのに対して、こちらは1棟ずつ処理するのでメモリ使用量がファイルサイズに依存しません。

- **O(1棟) のメモリ使用量** (DOM は O(ファイル全体))
- 2層の XLink キャッシュ (建物ローカル + グローバル LRU)
- NumPy による座標パース高速化 (オプション)

> 正式なベンチマークはまだ取っていません。メモリ削減量や速度向上はファイルサイズや建物の複雑さに依存します。理論上は、ファイルがどれだけ大きくなってもメモリ使用量がほぼ一定に保たれるのが利点です。

```python
for building, xlinks in stream_parse("large_plateau_file.gml"):
    process(building)
```

## CRS・座標処理

- GML の `srsName` から **CRS を自動検出**
- **平面直角座標系 全19系** (EPSG:6669〜6687) 対応、緯度経度から系を自動選択
- 地理座標系 (WGS84, JGD2000, JGD2011) → 投影座標系への**自動再投影**
- OCCT の浮動小数点誤差を抑える**座標リセンタリング**

## PLATEAU 連携

[PLATEAU](https://www.mlit.go.jp/plateau/) は国交省が進めている、日本全国の 3D 都市モデルを CityGML で整備・公開するプロジェクトです。

gml2step ではオプション (`pip install "gml2step[plateau]"`) で PLATEAU のデータを取得する機能を提供しています。中身は以下の2つの公開 API を叩いているだけで、独自のバックエンドサーバーはありません:

- **[PLATEAU データカタログ API](https://api.plateauview.mlit.go.jp/)** (国交省運営) — メッシュコードや自治体から CityGML ファイルの URL を取得
- **[Nominatim](https://nominatim.openstreetmap.org/)** (OpenStreetMap) — 日本語住所のジオコーディング (緯度経度変換)

### 処理の流れ

1. **住所検索**: 住所を Nominatim でジオコーディング → 緯度経度を JIS X 0410 メッシュコードに変換 → PLATEAU API でそのメッシュの CityGML ファイル URL を取得 → ダウンロード・パースして距離や名前の類似度でランキング
2. **メッシュコード指定**: メッシュコードを直接渡して CityGML ファイルを取得
3. **建物 ID 指定**: 建物 ID + メッシュコードで特定の建物だけを取得

### 建物検索

```python
from gml2step.plateau.fetcher import search_buildings_by_address

buildings = search_buildings_by_address(
    "東京都千代田区霞が関3-2-1",
    ranking_mode="hybrid",  # "distance", "name", "hybrid"
    limit=10,
)
for b in buildings:
    print(b.building_id, b.name, b.height, b.lod_level)
```

### メッシュコード

PLATEAU データは [JIS X 0410 標準地域メッシュ](https://www.stat.go.jp/data/mesh/m_tuite.html) で管理されています。緯度経度からメッシュコードへの変換関数を用意しています:

```python
from gml2step.plateau.mesh_utils import (
    latlon_to_mesh_1st,    # 1次メッシュ 80km (4桁)
    latlon_to_mesh_2nd,    # 2次メッシュ 10km (6桁)
    latlon_to_mesh_3rd,    # 3次メッシュ 1km (8桁)
    latlon_to_mesh_half,   # 2分の1メッシュ 500m (9桁)
    latlon_to_mesh_quarter # 4分の1メッシュ 250m (10桁)
)

mesh = latlon_to_mesh_3rd(35.6812, 139.7671)  # 東京駅
```

### 非同期 API クライアント

```python
import asyncio
from gml2step.plateau.api_client import fetch_plateau_datasets_by_mesh

result = asyncio.run(fetch_plateau_datasets_by_mesh("53394525"))
```

### その他の機能

- Nominatim によるジオコーディング (Nominatim ポリシーに従い 1req/sec に制限、日本向けバリデーションつき)
- 3モードの建物ランキング: 距離 / 名前類似度 (レーベンシュタイン距離 + トークンマッチ) / ハイブリッド
- JIS X 0410 メッシュコード変換 (1次〜4分の1メッシュ)
- 隣接メッシュ列挙 (3x3) — メッシュ境界付近の検索用
- 非同期バッチ処理 (並行数制御つき)
- ローカル CityGML キャッシュ (環境変数 `CITYGML_CACHE_ENABLED` / `CITYGML_CACHE_DIR` で有効化)
- メッシュ→市区町村コードのオフラインマッピング (パッケージデータとして同梱、API 呼び出し不要)

## アーキテクチャ

```
src/gml2step/
├── __init__.py              # 公開 API: convert, parse, stream_parse, extract_footprints
├── api.py                   # API 実装
├── cli.py                   # Typer CLI
├── coordinate_utils.py      # CRS 関連、平面直角座標系の定義
├── data/
│   └── mesh2_municipality.json  # メッシュ→市区町村コードマッピング
├── citygml/
│   ├── core/                # 型、定数、名前空間
│   ├── parsers/             # 座標・ポリゴン抽出
│   ├── streaming/           # ストリーミングパーサー、XLink キャッシュ、座標最適化
│   ├── lod/                 # LoD0〜3 の抽出、フットプリント
│   ├── geometry/            # OCCT ジオメトリ構築、シェル/ソリッド、修復
│   ├── transforms/          # CRS 検出、再投影、リセンタリング
│   ├── utils/               # XLink、XML パーサー、ログ
│   └── pipeline/            # 7フェーズ変換パイプライン
└── plateau/                 # PLATEAU API、ジオコーディング、メッシュ、建物検索
```

## 開発

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
pytest
```

## ライセンス

[AGPL-3.0-or-later](LICENSE) です。

もともと [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) の一部として開発したものを、独立したライブラリとして切り出しました。帰属表示の詳細は [NOTICE](NOTICE) を参照してください。

## 謝辞

- [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) — 元の親プロジェクト
- [PLATEAU](https://www.mlit.go.jp/plateau/) — 国交省 3D 都市モデル
- [OpenCASCADE](https://www.opencascade.com/) / [pythonocc-core](https://github.com/tpaviot/pythonocc-core) — STEP 変換の CAD カーネル
- [pyproj](https://pyproj4.github.io/pyproj/) — 座標参照系変換
- [未踏ジュニア](https://jr.mitou.org/) — 独創的アイデアと卓越した技術を持つ 17 歳以下のクリエータ支援プログラム
