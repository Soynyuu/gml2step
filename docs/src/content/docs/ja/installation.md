---
title: インストール
description: gml2step のインストール方法
---

## 必要なもの

- Python 3.10 以上
- STEP 変換をする場合: [pythonocc-core](https://github.com/tpaviot/pythonocc-core) (OpenCASCADE バインディング)

## 基本パッケージ

パース、ストリーミング、フットプリント抽出は OpenCASCADE なしで動きます。

```bash
pip install gml2step
```

## PLATEAU 連携つき

住所ジオコーディング、PLATEAU API クライアント、メッシュコード変換が追加されます。

```bash
pip install "gml2step[plateau]"
```

**追加される依存:** `requests`, `shapely`, `aiohttp`

## STEP 変換 (OpenCASCADE 必要)

STEP 変換には [pythonocc-core](https://github.com/tpaviot/pythonocc-core) が必要です。pip だけだと環境によってはうまく入らないので、conda か Docker を使ってください。

### conda

```bash
conda install -c conda-forge pythonocc-core
pip install gml2step
```

### Docker

Dockerfile に pythonocc 入りの環境が用意してあります。

```bash
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

ベースイメージは `mambaorg/micromamba:1.5.8-jammy`、Python 3.10 + pythonocc-core (conda-forge) です。

## OCCT が必要な機能・不要な機能

| 機能 | OCCT |
|---|---|
| `parse` | 不要 |
| `stream-parse` | 不要 |
| `extract-footprints` | 不要 |
| `convert` | **必要** |
| PLATEAU データ取得 | 不要 |

## 開発用インストール

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
```
