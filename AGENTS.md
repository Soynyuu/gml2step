# Repository Guidelines

## Project Structure & Module Organization
Core Python code lives under `src/gml2step/`:
- `api.py` and `cli.py` expose the public API and Typer CLI.
- `citygml/` contains parsing, LoD extraction, transforms, streaming, and conversion pipeline logic.
- `plateau/` contains optional PLATEAU API and mesh/geocoding helpers.
- `data/` stores packaged JSON assets (for example `mesh2_municipality.json`).

Tests are in `tests/` (`pytest`), docs are in `docs/` (Astro/Starlight), and release/build outputs appear in `dist/`. Keep generated artifacts and local debug logs out of commits.

## Build, Test, and Development Commands
- `pip install -e ".[dev,plateau]"`: editable install with test and PLATEAU extras.
- `pytest`: run the full test suite.
- `pytest --cov --cov-report=term-missing --cov-report=xml`: run tests with coverage (matches CI behavior).
- `python -m build`: build wheel and sdist for publishing.
- `cd docs && npm ci && npm run dev`: run docs locally.
- `cd docs && npm run build`: build docs for GitHub Pages.

If you need STEP conversion locally, install OpenCASCADE bindings separately (for example `conda install -c conda-forge pythonocc-core`).

## Coding Style & Naming Conventions
Target Python 3.10+ and follow PEP 8 with 4-space indentation. Keep functions/modules in `snake_case`, classes in `PascalCase`, and prefer explicit type hints on public APIs. Match existing CLI patterns (`*_cmd` handlers in `cli.py`) and keep modules focused by domain (`streaming`, `lod`, `transforms`, etc.). No mandatory formatter/linter is enforced in CI, so consistency with surrounding code is required.

## Testing Guidelines
Use `pytest` with files named `tests/test_*.py` and test functions `test_*`. Reuse fixtures from `tests/conftest.py` when possible, and prefer minimal inline CityGML samples for deterministic tests. Add tests with every behavior change; include edge cases for CRS detection, XML parsing, and building ID filtering.

## Commit & Pull Request Guidelines
Recent history follows Conventional Commit-style prefixes: `feat:`, `fix:`, `docs:`, `test:`, `chore:`. Keep subject lines short and imperative; reference issues when relevant (example: `closes #10`). For PRs, include:
- what changed and why,
- test commands run (and results),
- doc updates for CLI/API behavior changes.

## Configuration & Data Tips
PLATEAU-related behavior is controlled by env vars such as `CITYGML_CACHE_ENABLED`, `CITYGML_CACHE_DIR`, and `PLATEAU_DATASET_FETCH_CONCURRENCY`. Do not commit local cache data or downloaded CityGML files.
