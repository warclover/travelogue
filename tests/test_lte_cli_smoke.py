"""Phase 16 LTE CLI smoke tests (W0)."""

from __future__ import annotations

import json
from io import StringIO
from unittest.mock import patch

import jsonschema
import pytest
import yaml

from travelogue.layout_templates import cli
from travelogue.layout_templates.registry import DEFAULT_TEMPLATES_DIR, schema_path


@pytest.mark.unit
def test_schema_is_valid_json_schema() -> None:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator.check_schema(schema)


@pytest.mark.unit
def test_example_yaml_passes_schema() -> None:
    schema = json.loads(schema_path().read_text(encoding="utf-8"))
    example = DEFAULT_TEMPLATES_DIR / "_example_mosaic-5-2p3l-equal.yaml"
    doc = yaml.safe_load(example.read_text(encoding="utf-8"))
    jsonschema.Draft202012Validator(schema).validate(doc)


@pytest.mark.unit
def test_cli_validate_ok() -> None:
    buf = StringIO()
    with patch("sys.stdout", buf):
        code = cli.main(["validate", "-v"])
    assert code == 0
    payload = json.loads(buf.getvalue())
    assert payload["ok"] is True
    assert payload["validated"] >= 1


@pytest.mark.unit
def test_cli_commands_exit_zero() -> None:
    buf = StringIO()
    with patch("sys.stdout", buf):
        code = cli.main(["export"])
    assert code == 0
    assert "generated CSS" in buf.getvalue()

    buf = StringIO()
    with patch("sys.stdout", buf):
        code = cli.main(["docgen", "--out", "docs/templates/slot-aspect"])
    assert code == 0
    assert "docgen" in buf.getvalue()

    buf = StringIO()
    with patch("sys.stdout", buf):
        code = cli.main(["solve-tracks"])
    assert code == 0
    assert "not implemented" in buf.getvalue()
