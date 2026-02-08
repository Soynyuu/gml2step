---
title: 開発ガイド
description: 開発環境のセットアップ、テスト、コントリビュート
---

## セットアップ

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
```

STEP 変換の開発をする場合は pythonocc-core も入れてください:

```bash
conda install -c conda-forge pythonocc-core
```

---

## プロジェクト構造

```
gml2step/
├── src/gml2step/          # メインパッケージ
│   ├── __init__.py        # 公開 API
│   ├── api.py             # API 実装
│   ├── cli.py             # Typer CLI
│   ├── coordinate_utils.py
│   ├── data/              # パッケージデータ (メッシュマッピング)
│   ├── citygml/           # CityGML パース・変換
│   └── plateau/           # PLATEAU API 連携
├── tests/                 # pytest テスト
├── docs/                  # Astro/Starlight ドキュメントサイト
├── Dockerfile
├── pyproject.toml
├── LICENSE                # AGPL-3.0-or-later
└── NOTICE
```

---

## テスト

```bash
pytest
```

カバレッジつき:

```bash
pytest --cov=gml2step
```

### 現在のテスト状況

| ファイル | テスト数 | 内容 |
|---|---|---|
| `tests/test_api.py` | 3 | `parse`, `stream_parse`, `extract_footprints` |
| `tests/test_cli.py` | 2 | `parse`, `stream-parse` CLI コマンド |

テストはインラインの CityGML フィクスチャを使っています (外部ファイル不要)。`convert` は pythonocc-core が必要なので CI ではテストしていません。

---

## 依存関係

### コア

| パッケージ | バージョン | 用途 |
|---|---|---|
| `typer` | >=0.12.0 | CLI |
| `pyproj` | >=3.6.0 | CRS 変換 |

### オプション: PLATEAU

| パッケージ | バージョン | 用途 |
|---|---|---|
| `requests` | >=2.31.0 | PLATEAU API への HTTP |
| `shapely` | >=2.0.0 | ジオメトリ操作 |
| `aiohttp` | >=3.9.0 | バッチメッシュ取得の非同期 HTTP |

### オプション: 開発

| パッケージ | バージョン | 用途 |
|---|---|---|
| `pytest` | >=8.0.0 | テストランナー |
| `pytest-cov` | >=5.0.0 | カバレッジ |

### PyPI にないもの

| パッケージ | インストール方法 | 用途 |
|---|---|---|
| `pythonocc-core` | `conda install -c conda-forge pythonocc-core` | STEP 変換の OpenCASCADE バインディング |

---

## Docker

Dockerfile に pythonocc-core 入りの環境が用意してあります:

```dockerfile
FROM mambaorg/micromamba:1.5.8-jammy
# Python 3.10 + pythonocc-core (conda-forge)
# pip install gml2step
ENTRYPOINT ["gml2step"]
```

ビルドと使い方:

```bash
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

---

## ライセンス

AGPL-3.0-or-later。[LICENSE](https://github.com/Soynyuu/gml2step/blob/main/LICENSE) と [NOTICE](https://github.com/Soynyuu/gml2step/blob/main/NOTICE) を参照。

gml2step は [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) の一部として開発し、スタンドアロンライブラリとして切り出しました。
