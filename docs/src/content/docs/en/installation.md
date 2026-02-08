---
title: Installation
description: How to install gml2step
---

## Requirements

- Python 3.10 or later
- For STEP conversion: [pythonocc-core](https://github.com/tpaviot/pythonocc-core) (OpenCASCADE bindings)

## Core package

Parsing, streaming, and footprint extraction work without OpenCASCADE.

```bash
pip install gml2step
```

## With PLATEAU support

Adds address geocoding, PLATEAU API client, and mesh code utilities.

```bash
pip install "gml2step[plateau]"
```

**Additional dependencies:** `requests`, `shapely`, `aiohttp`

## With STEP conversion

STEP conversion requires [pythonocc-core](https://github.com/tpaviot/pythonocc-core), which wraps the OpenCASCADE kernel. It is not reliably pip-installable on all platforms, so use conda or Docker.

### conda

```bash
conda install -c conda-forge pythonocc-core
pip install gml2step
```

### Docker

The included Dockerfile provides a complete environment with pythonocc pre-installed.

```bash
docker build -t gml2step .
docker run --rm -v $(pwd):/data gml2step convert /data/input.gml /data/output.step
```

The image is based on `mambaorg/micromamba:1.5.8-jammy` with Python 3.10 and pythonocc-core from conda-forge.

## What needs OCCT and what doesn't

| Feature | OCCT required |
|---|---|
| `parse` | No |
| `stream-parse` | No |
| `extract-footprints` | No |
| `convert` | **Yes** |
| PLATEAU data fetching | No |

## Development install

```bash
git clone https://github.com/Soynyuu/gml2step.git
cd gml2step
pip install -e ".[dev,plateau]"
```
