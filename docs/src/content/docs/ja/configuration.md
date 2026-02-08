---
title: 設定
description: 環境変数と設定パラメータ
---

## 環境変数

### PLATEAU モジュール

| 変数 | デフォルト | 説明 |
|---|---|---|
| `CITYGML_CACHE_ENABLED` | `false` | ダウンロードした CityGML のローカルキャッシュを有効化 |
| `CITYGML_CACHE_DIR` | `<package>/data/citygml_cache` | キャッシュディレクトリ |
| `PLATEAU_API_URL` | `https://api.plateauview.mlit.go.jp/datacatalog/plateau-datasets` | PLATEAU データカタログ API のエンドポイント |
| `PLATEAU_MESH2_MAPPING_PATH` | `<package>/data/mesh2_municipality.json` | メッシュ→市区町村マッピングファイルのパス |
| `PLATEAU_ALLOW_TOKYO_FALLBACK` | `true` | 東京23区のハードコードされたタイルセットをフォールバックとして許可 |
| `PLATEAU_DATASET_FETCH_CONCURRENCY` | `8` | データセット取得の最大同時接続数 |

### 例

```bash
# キャッシュを有効化して、ディレクトリを指定
export CITYGML_CACHE_ENABLED=true
export CITYGML_CACHE_DIR=/tmp/gml_cache

# バッチ処理の並行数を上げる
export PLATEAU_DATASET_FETCH_CONCURRENCY=16
```

---

## 変換パラメータ

`convert()` に渡すか、CLI フラグで設定します。

### 精度モード

| モード | ファクター | 相対許容誤差 |
|---|---|---|
| `standard` | 0.0001 | 0.01% |
| `high` | 0.00001 | 0.001% |
| `maximum` | 0.000001 | 0.0001% |
| `ultra` | 0.0000001 | 0.00001% |

ファクターは座標の大きさに掛けて、ジオメトリ操作 (縫合、検証、修復) の絶対許容誤差を決めます。

### 形状修復レベル

ジオメトリ検証に失敗すると、これらのレベルを自動的にエスカレーションします:

| レベル | 操作 |
|---|---|
| `minimal` | `ShapeFix_Solid` |
| `standard` | + `ShapeUpgrade_UnifySameDomain` |
| `aggressive` | + 許容誤差を緩めてシェルを再構築 |
| `ultra` | + `ShapeFix_Shape` (OCCT のフル修復) |

`shape_fix_level` で開始レベルを指定します。失敗したら自動的に次に上がります:

```
minimal -> standard -> aggressive -> ultra
```

### 変換方式

| 方式 | 位置づけ | 向いているデータ |
|---|---|---|
| `solid` | デフォルト | LoD2/LoD3、閉じたサーフェス |
| `sew` | フォールバック | ほぼ閉じているが隙間がある |
| `extrude` | 最終手段 | LoD0 フットプリントのみ |
| `auto` | 全部試す | データ品質が不明 |

---

## 内部定数

`gml2step.citygml.core.constants` で定義。実行時の変更はできません。

| 定数 | 値 | 説明 |
|---|---|---|
| `DEFAULT_BUILDING_HEIGHT` | 10.0 m | フットプリント押し出しのデフォルト高さ |
| `DEFAULT_COORDINATE_FILTER_RADIUS` | 100.0 m | 空間フィルタのデフォルト半径 |

---

## ストリーミングパーサー設定

Python API で `StreamingConfig` を使って直接設定できます:

| 設定 | デフォルト | 説明 |
|---|---|---|
| `limit` | None | 処理する建物数の上限 |
| `building_ids` | None | 特定の ID に絞る |
| `filter_attribute` | `gml:id` | ID マッチに使う XML 属性 |
| `debug` | False | デバッグ出力 |
| `enable_gc_per_building` | True | 建物ごとに GC を強制 |
| `max_xlink_cache_size` | 10000 | グローバル XLink LRU キャッシュのエントリ数上限 |
