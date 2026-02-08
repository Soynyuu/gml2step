---
title: 変換ガイド
description: CityGML から STEP への変換の仕組み
---

## 変換方式

4つの方式があります。入力データの特性に応じて使い分けます。

### `solid` (デフォルト)

メインの方式。LoD サーフェスを抽出してシェルを組み立て、ソリッドとして検証・修復します。

**LoD2/LoD3** のデータ向き。WallSurface, RoofSurface, GroundSurface が閉じた立体を構成している場合に最適です。

### `sew`

境界面のポリゴン (Wall/Roof/GroundSurface) を全部集めて、OpenCASCADE の sewing アルゴリズムで縫い合わせ、ソリッドにします。

ジオメトリがほぼ閉じているけど小さな隙間がある場合に有効。

### `extrude`

LoD0 のフットプリント (2D ポリゴン) を推定高さで垂直方向に押し出して、単純な箱型ソリッドを作ります。

2D のフットプリントデータしかないファイル用のフォールバック。

### `auto`

**solid -> sew -> extrude** の順に試して、最初に成功したものを使います。入力データの品質がわからないときに一番安全。

```bash
gml2step convert building.gml output.step --method auto
```

---

## 処理パイプライン

`convert` は建物ごとに7つのフェーズを実行します。

### Phase 0: リセンタリング

座標を原点付近に移動します。CityGML は実世界座標 (例: X=140000, Y=36000 m) を使うので、そのまま OpenCASCADE に渡すと浮動小数点の精度が落ちます。最初の建物の重心を引いて原点付近にシフトします。

### Phase 1: LoD 選択

その建物で使える一番詳細な LoD を選びます。

**LoD3 -> LoD2 -> LoD1 -> LoD0** の順に探して、見つかったものを使います。

### Phase 1.5: CRS 検出

GML の `srsName` 属性から CRS を自動判定します。地理座標系 (WGS84, JGD2000, JGD2011) だった場合、適切な平面直角座標系に再投影します。

### Phase 2: ジオメトリ抽出

選んだ変換方式でフェースを取り出します。`solid` なら全境界面を収集、`extrude` ならフットプリントと高さを取得。

### Phase 3: シェル構築

抽出したフェースを縫い合わせて OCCT のシェルにします。1回目の sewing で失敗したら、許容誤差を上げてリトライします。

### Phase 4: ソリッド検証

シェルが閉じているか、面の向きが正しいか、自己交差がないかを検証して、BRep ソリッドを構築します。

### Phase 5: 自動修復

検証に失敗したら段階的に修復します。指定レベルで直らなければ自動的に次のレベルに上がります:

| レベル | 内容 |
|---|---|
| **minimal** | `ShapeFix_Solid` のみ |
| **standard** | + `ShapeUpgrade_UnifySameDomain` |
| **aggressive** | + 許容誤差を緩めて再構築 |
| **ultra** | + `ShapeFix_Shape` (フル修復) |

### Phase 6: パーツ統合

`BuildingPart` がある場合、ブーリアン結合で1つにまとめます。結合に失敗したらコンパウンド (未結合のまとめ) にフォールバック。

### Phase 7: STEP 出力

AP214CD スキーマ、ミリメートル単位で STEP ファイルを書き出します。

---

## 精度モード

`precision_mode` でジオメトリ構築時の座標許容誤差を変えられます。

| モード | ファクター | 相対許容誤差 | いつ使う |
|---|---|---|---|
| `standard` | 0.0001 | 0.01% | 普通はこれで十分 |
| `high` | 0.00001 | 0.001% | 細かい建築モデル |
| `maximum` | 0.000001 | 0.0001% | 高精度 CAD |
| `ultra` | 0.0000001 | 0.00001% | 最大精度 (遅くなる場合あり) |

```python
convert("input.gml", "output.step", precision_mode="high")
```

許容誤差が小さいほどジオメトリの一致判定が厳密になります。`standard` で変換に失敗したら `high` を試してみてください。

---

## LoD サポート

CityGML の LoD0〜3 に対応しています。

| LoD | 内容 | CityGML 要素 |
|---|---|---|
| **LoD3** | 建築ディテール | `lod3Solid`, `lod3MultiSurface`, `lod3Geometry` |
| **LoD2** | 標準建物モデル | `lod2Solid`, `lod2MultiSurface`, `lod2Geometry`, `boundedBy` |
| **LoD1** | 単純ブロック | `lod1Solid` |
| **LoD0** | 2D フットプリント | `lod0FootPrint`, `lod0RoofEdge`, `GroundSurface` |

境界面タイプ6種に対応:

- `WallSurface`
- `RoofSurface`
- `GroundSurface`
- `OuterCeilingSurface`
- `OuterFloorSurface`
- `ClosureSurface`

PLATEAU のデータは主に **LoD2** で、WallSurface / RoofSurface / GroundSurface を使っています。
