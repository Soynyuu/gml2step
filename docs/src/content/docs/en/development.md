---
title: Development Guide
description: Setting up the development environment, testing, and contributing
---

## Setup

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
```

For STEP conversion development, you also need pythonocc-core:

```bash
conda install -c conda-forge pythonocc-core
```

---

## Project structure

```
gml2step/
├── src/gml2step/          # Main package
│   ├── __init__.py        # Public API
│   ├── api.py             # API implementation
│   ├── cli.py             # Typer CLI
│   ├── coordinate_utils.py
│   ├── data/              # Package data (mesh mappings)
│   ├── citygml/           # CityGML parsing and conversion
│   └── plateau/           # PLATEAU API integration
├── tests/                 # pytest test suite
├── docs/                  # Astro/Starlight documentation site
├── Dockerfile
├── pyproject.toml
├── LICENSE                # AGPL-3.0-or-later
└── NOTICE
```

---

## Running tests

```bash
pytest
```

With coverage:

```bash
pytest --cov=gml2step
```

### Current test coverage

| File | Tests | Notes |
|---|---|---|
| `tests/test_api.py` | 3 tests | `parse`, `stream_parse`, `extract_footprints` |
| `tests/test_cli.py` | 2 tests | `parse`, `stream-parse` CLI commands |

Tests use inline CityGML fixtures (no external files needed). The `convert` function is not tested in CI because it requires pythonocc-core.

---

## Dependencies

### Core

| Package | Version | Purpose |
|---|---|---|
| `typer` | >=0.12.0 | CLI framework |
| `pyproj` | >=3.6.0 | CRS transformations |

### Optional: PLATEAU

| Package | Version | Purpose |
|---|---|---|
| `requests` | >=2.31.0 | HTTP client for PLATEAU API |
| `shapely` | >=2.0.0 | Geometry operations |
| `aiohttp` | >=3.9.0 | Async HTTP for batch mesh fetching |

### Optional: Development

| Package | Version | Purpose |
|---|---|---|
| `pytest` | >=8.0.0 | Test runner |
| `pytest-cov` | >=5.0.0 | Coverage reporting |

### Not on PyPI

| Package | Install via | Purpose |
|---|---|---|
| `pythonocc-core` | `conda install -c conda-forge pythonocc-core` | OpenCASCADE bindings for STEP conversion |

---

## Docker

The Dockerfile provides a complete environment including pythonocc-core:

```dockerfile
FROM mambaorg/micromamba:1.5.8-jammy
# Installs Python 3.10 + pythonocc-core via conda-forge
# pip installs gml2step
ENTRYPOINT ["gml2step"]
```

Build and use:

```bash
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

---

## License

AGPL-3.0-or-later. See [LICENSE](https://github.com/Soynyuu/gml2step/blob/main/LICENSE) and [NOTICE](https://github.com/Soynyuu/gml2step/blob/main/NOTICE).

gml2step was originally developed as part of [Paper-CAD](https://github.com/Soynyuu/Paper-CAD) and extracted as a standalone library.
