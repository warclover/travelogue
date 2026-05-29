"""P5-MP-1 · API-MINIAPP draft stays field-aligned with trip.schema.json + share render.

Acceptance: 无 schema 冲突 — fields the API doc treats as native must exist in the
schema, and fields the doc treats as cloud-only siblings must NOT collide with the
schema's `additionalProperties: false` top level.
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
API_DOC = ROOT / "docs" / "API-MINIAPP.md"
SCHEMA = ROOT / "schemas" / "trip.schema.json"


def _schema() -> dict:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _doc() -> str:
    return API_DOC.read_text(encoding="utf-8")


def test_pipeline_status_enum_matches_schema() -> None:
    schema = _schema()
    enum = schema["$defs"]["pipeline"]["properties"]["status"]["enum"]
    doc = _doc()
    state_machine = doc.split("### 9.3")[1]
    for status in enum:
        assert status in state_machine, f"pipeline status {status} missing from §9.3"


def test_native_fields_exist_in_schema() -> None:
    """Fields §4.1 claims are schema-native must really be in the schema."""
    schema = _schema()
    top = schema["properties"]
    assert "publishedAt" in top
    assert "slug" in top
    assert "displayFile" in schema["$defs"]["asset"]["properties"]
    assert "confirmedAt" in schema["$defs"]["privacy"]["properties"]
    assert "longShot" in schema["$defs"]["exportOptions"]["properties"]


def test_cloud_only_fields_are_not_in_schema() -> None:
    """§4.2 cloud-only siblings must not collide with additionalProperties:false."""
    schema = _schema()
    assert schema.get("additionalProperties") is False
    top = schema["properties"]
    for cloud_only in ("ownerId", "shareId", "publish"):
        assert cloud_only not in top, (
            f"{cloud_only} is documented as a cloud-only sibling but exists in schema "
            "top-level; this is a schema conflict"
        )


def test_doc_declares_sibling_envelope() -> None:
    doc = _doc()
    assert "additionalProperties: false" in doc
    assert "同级兄弟键" in doc
    section = doc.split("### 4.2")[1].split("## 5.")[0]
    for cloud_only in ("ownerId", "shareId", "publish"):
        assert cloud_only in section


def test_render_job_documents_phase5_flags() -> None:
    doc = _doc()
    for flag in ("fontTheme", "copyDisplay", "readingProfile"):
        assert flag in doc, f"render Job options missing P5 flag {flag}"


def test_share_bundle_documents_phase5_reading_and_chrome() -> None:
    doc = _doc()
    assert "export.reading.profile" in doc
    assert "preview-toolbar.js" in doc


def test_webview_checklist_section_present() -> None:
    """P5-MP-2: §11 local serve + web-view manual checklist is documented."""
    doc = _doc()
    assert "本地 serve + web-view 模拟手测清单" in doc
    section = doc.split("## 11. 本地")[1].split("## 12. 实现路线")[0]
    for marker in ("MP-WV-01", "MP-WV-11", "--mode share", "?share=1"):
        assert marker in section, f"web-view checklist missing {marker}"


def test_webview_share_markers_match_code() -> None:
    """Doc share-mode triggers must match studio_chrome.SHARE_QUERY_MARKERS."""
    from travelogue.web.studio_chrome import SHARE_QUERY_MARKERS

    doc = _doc()
    for marker in SHARE_QUERY_MARKERS:
        assert marker in doc, f"share marker {marker} not documented in API-MINIAPP §11"


def test_webview_acceptance_record_exists() -> None:
    record = ROOT / "docs" / "acceptance-records" / "phase5-webview-manual.json"
    assert record.exists()
    data = json.loads(record.read_text(encoding="utf-8"))
    assert data["protocol"] == "P5-MP-2"
    assert "MP-WV-01" in data["checks"]
