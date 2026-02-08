---
title: アーキテクチャ
description: 内部構造、ストリーミングパーサー、CRS 処理
---

## コードベース構造

```
src/gml2step/
├── __init__.py              # 公開 API
├── api.py                   # API 実装 (convert, parse, etc.)
├── cli.py                   # Typer CLI
├── coordinate_utils.py      # CRS 関連、平面直角座標系定義
├── data/
│   └── mesh2_municipality.json
├── citygml/
│   ├── core/                # 型、定数、名前空間
│   ├── parsers/             # 座標・ポリゴン抽出
│   ├── streaming/           # ストリーミングパーサー
│   ├── lod/                 # LoD0〜3 の抽出、フットプリント
│   ├── geometry/            # OCCT ジオメトリ構築、修復
│   ├── transforms/          # CRS 検出、再投影、リセンタリング
│   ├── utils/               # XLink、XML パーサー、ログ
│   └── pipeline/            # 7フェーズ変換パイプライン
└── plateau/                 # PLATEAU API、ジオコーディング、メッシュ
```

---

## ストリーミングパーサー

巨大な CityGML ファイル向けの SAX ベースのパーサーです。DOM パーサーがファイル全体をメモリに載せるのに対して、1棟ずつ処理するのでメモリ使用量がファイルサイズに依存しません。

### 仕組み

1. `iterparse` で XML を逐次読み込む
2. `<bldg:Building>` の開きタグを見つけたら、その要素の蓄積を開始
3. 閉じタグが来たら、完成した building 要素を yield
4. yield 後に要素をメモリから解放
5. XLink 参照は2層キャッシュで解決

### XLink 解決

CityGML では XLink (`xlink:href="#id"`) でジオメトリを共有します。ストリーミングパーサーは2つのキャッシュで対応しています:

- **ローカルキャッシュ** — 現在の building 内の XLink ターゲット (建物ごとにクリア)
- **グローバル LRU キャッシュ** — building をまたぐ XLink ターゲット (`max_xlink_cache_size` でサイズ制限、デフォルト 10,000)

### メモリ特性

ファイルサイズに関係なく O(1棟) のメモリ使用量です。トレードオフとして、現在の建物外の XLink ターゲットが LRU キャッシュから追い出されると再パースが必要になります。

> 正式なベンチマークはまだ取っていません。O(1) のメモリ特性はアーキテクチャ的なもの (一度に1棟だけメモリに載る) ですが、実際のメモリ使用量は建物の複雑さと XLink キャッシュサイズに依存します。

### 設定

```python
from gml2step.citygml.streaming.parser import StreamingConfig

config = StreamingConfig(
    limit=100,
    building_ids=["bldg_001", "bldg_002"],
    filter_attribute="gml:id",
    debug=False,
    enable_gc_per_building=True,   # 建物ごとに GC を強制
    max_xlink_cache_size=10000,    # グローバル XLink キャッシュのエントリ数
)
```

### NumPy 座標最適化

NumPy がインストールされていると、座標文字列のパースを高速化できます。Python で1つずつパースする代わりに、NumPy で一括変換します。

`gml2step.citygml.streaming.coordinate_optimizer` のオプション機能です。

---

## CRS 処理

### 自動検出

GML 要素の `srsName` 属性から CRS を読み取ります。よくある値:

- `http://www.opengis.net/def/crs/EPSG/0/6677` (平面直角座標系 第IX系)
- `EPSG:4326` (WGS84)
- `urn:ogc:def:crs:EPSG::4612` (JGD2000)

### 平面直角座標系

日本は19個の系 (EPSG:6669〜6687) を使っています。それぞれ歪みが最小になるように最適化された帯状のゾーンです。

gml2step は全19系の定義を持っていて、緯度経度から適切な系を自動で選びます。

### 再投影

ソース CRS が地理座標系 (緯度経度) の場合、[pyproj](https://pyproj4.github.io/pyproj/) を使って適切な平面直角座標系に自動再投影します。OpenCASCADE で使えるメートル単位の座標になります。

### リセンタリング

投影座標系でも X=140000, Y=36000 (m) のような値は OCCT で浮動小数点の精度問題を起こします。リセンタリングで最初の建物の重心を引いて、ジオメトリを原点付近にシフトします。

---

## 変換パイプラインの内部

パイプラインの実体は `gml2step.citygml.pipeline` にあります。[変換ガイド](/gml2step/ja/conversion/)で説明した7フェーズを実行します。

建物は逐次処理されます。各建物について:

1. `ConversionContext` を作成 (座標変換、精度設定、方式選択)
2. 各フェーズに building 要素を渡す
3. フェーズが失敗したらログを出して次の建物に移る
4. 変換成功したソリッドを蓄積
5. 全建物の処理後、コンパウンドにまとめて STEP ファイルに出力

### `ConversionContext`

パイプライン全体で状態を運ぶオブジェクト:

```python
@dataclass
class ConversionContext:
    method: str                    # "solid", "sew", "extrude", "auto"
    precision_mode: str            # 許容誤差ファクター
    shape_fix_level: str           # 修復の強さ
    sew_tolerance: Optional[float]
    source_crs: Optional[str]
    target_crs: Optional[str]
    auto_reproject: bool
    merge_building_parts: bool
    debug: bool
    # ... (その他の内部フィールド)
```

### `ExtractionResult`

各フェーズの出力:

```python
@dataclass
class ExtractionResult:
    faces: List                    # OCCT フェースオブジェクト
    shell: Optional[object]        # 構築されたシェル
    solid: Optional[object]        # 検証済みソリッド
    repair_applied: str            # 適用された修復レベル
    method_used: str               # 成功した変換方式
    lod_level: int                 # 抽出した LoD
```
