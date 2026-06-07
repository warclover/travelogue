"""Strategy Pack JSON Schema validation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PACKAGE_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_ROOT / "lse_strategy.schema.json"


@dataclass
class ValidationIssue:
    path: str
    message: str


@dataclass
class ValidationReport:
    ok: bool
    issues: list[ValidationIssue]

    @classmethod
    def success(cls) -> ValidationReport:
        return cls(ok=True, issues=[])

    @classmethod
    def failure(cls, issues: list[ValidationIssue]) -> ValidationReport:
        return cls(ok=False, issues=issues)


def schema_path() -> Path:
    return SCHEMA_PATH


def load_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def validate_strategy_doc(doc: dict[str, Any]) -> ValidationReport:
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return ValidationReport.failure(
            [ValidationIssue("", "jsonschema package required for LSE validation")]
        )
    validator = Draft202012Validator(load_schema())
    issues: list[ValidationIssue] = []
    for err in sorted(validator.iter_errors(doc), key=lambda e: list(e.path)):
        path = ".".join(str(p) for p in err.path) or "(root)"
        issues.append(ValidationIssue(path=path, message=err.message))
    if issues:
        return ValidationReport.failure(issues)
    return ValidationReport.success()


def validate_strategy_file(path: Path) -> ValidationReport:
    with path.open(encoding="utf-8") as f:
        doc = yaml.safe_load(f) or {}
    if not isinstance(doc, dict):
        return ValidationReport.failure([ValidationIssue("", "strategy YAML must be a mapping")])
    return validate_strategy_doc(doc)
