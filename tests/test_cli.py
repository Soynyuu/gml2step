import json
import tempfile

from typer.testing import CliRunner

from gml2step.cli import app
from tests.conftest import SAMPLE_GML_RICH


runner = CliRunner()

SAMPLE_GML = """<?xml version="1.0" encoding="UTF-8"?>
<CityModel xmlns="http://www.opengis.net/citygml/2.0"
           xmlns:bldg="http://www.opengis.net/citygml/building/2.0"
           xmlns:gml="http://www.opengis.net/gml">
  <cityObjectMember>
    <bldg:Building gml:id="BLD_001"/>
  </cityObjectMember>
</CityModel>
"""


def write_sample_gml() -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".gml", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_GML)
        return f.name


def write_rich_gml() -> str:
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".gml", delete=False, encoding="utf-8"
    ) as f:
        f.write(SAMPLE_GML_RICH)
        return f.name


def test_cli_parse() -> None:
    gml_path = write_sample_gml()
    result = runner.invoke(app, ["parse", gml_path])
    assert result.exit_code == 0
    assert '"total_buildings": 1' in result.stdout


def test_cli_stream_parse() -> None:
    gml_path = write_sample_gml()
    result = runner.invoke(app, ["stream-parse", gml_path])
    assert result.exit_code == 0
    assert "BLD_001" in result.stdout
    assert "total=1" in result.stdout


def test_cli_extract_footprints() -> None:
    gml_path = write_rich_gml()
    result = runner.invoke(app, ["extract-footprints", gml_path])
    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert len(payload) >= 1
    assert payload[0]["building_id"] == "BLD_001"


def test_cli_extract_footprints_json_output(tmp_path) -> None:
    gml_path = write_rich_gml()
    out_json = str(tmp_path / "footprints.json")
    result = runner.invoke(
        app, ["extract-footprints", gml_path, "--output-json", out_json]
    )
    assert result.exit_code == 0
    with open(out_json) as f:
        data = json.load(f)
    assert len(data) >= 1


def test_cli_convert_fails_gracefully(tmp_path) -> None:
    """convert should fail with a clear error when pythonocc-core is not installed."""
    gml_path = write_sample_gml()
    out_step = str(tmp_path / "out.step")
    result = runner.invoke(app, ["convert", gml_path, out_step])
    # Should exit with error (exit code 1) because OCCT is not available
    assert result.exit_code != 0


def test_cli_stream_parse_with_limit() -> None:
    gml_path = write_rich_gml()
    result = runner.invoke(app, ["stream-parse", gml_path, "--limit", "1"])
    assert result.exit_code == 0
    assert "total=1" in result.stdout


def test_cli_parse_with_limit() -> None:
    gml_path = write_rich_gml()
    result = runner.invoke(app, ["parse", gml_path, "--limit", "1"])
    assert result.exit_code == 0
    data = json.loads(result.stdout)
    assert data["total_buildings"] == 2
    assert len(data["listed_building_ids"]) == 1
