"""Template registry — single entry for template metadata and health checks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from travelogue.paths import ROOT

TemplateLifecycle = Literal["experimental", "beta", "ga", "deprecated", "disabled"]

DEFAULT_TEMPLATE_ID = "visual-journal"
EVENT_RECAP_TEMPLATE_ID = "event-recap"
REGISTRY_VERSION = "registry-v2"
KNOWN_RENDER_ADAPTERS = frozenset({DEFAULT_TEMPLATE_ID, EVENT_RECAP_TEMPLATE_ID})


@dataclass(frozen=True)
class TemplateRecord:
    template_id: str
    version: str
    template_dir: Path
    manifest_path: Path
    fallback_template_id: str | None = None
    lifecycle: TemplateLifecycle = "ga"
    capabilities: tuple[str, ...] = ()
    revision: int = 1
    render_adapter: str = DEFAULT_TEMPLATE_ID
    curation_adapter: str = DEFAULT_TEMPLATE_ID
    shared_partials_from: str | None = None
    shared_assets_from: str | None = None
    discovery: dict | None = None


class TemplateRegistryError(Exception):
    code = "E_TEMPLATE_REGISTRY"


class TemplateRegistry:
    def __init__(self) -> None:
        self._records: dict[str, TemplateRecord] = {}
        self._version = REGISTRY_VERSION

    @property
    def version(self) -> str:
        return self._version

    def register(self, record: TemplateRecord) -> None:
        self._records[record.template_id] = record

    def get(self, template_id: str) -> TemplateRecord:
        rec = self._records.get(template_id)
        if rec is None:
            raise TemplateRegistryError(f"unknown template: {template_id}")
        return rec

    def list_ids(self) -> list[str]:
        return sorted(self._records.keys())

    def list_for_consumer(
        self,
        *,
        include_beta: bool = False,
        allowlist: frozenset[str] | None = None,
    ) -> list[TemplateRecord]:
        from travelogue.templating.admin_store import get_effective_lifecycle

        out: list[TemplateRecord] = []
        for tid in self.list_ids():
            rec = self.get(tid)
            lifecycle = get_effective_lifecycle(tid, default=rec.lifecycle)
            if lifecycle == "disabled":
                continue
            if lifecycle in ("experimental", "deprecated"):
                continue
            if lifecycle == "beta" and not include_beta:
                if allowlist is None or tid not in allowlist:
                    continue
            if allowlist is not None and lifecycle == "beta" and tid not in allowlist:
                continue
            if not check_template_health(tid, registry=self)[0]:
                continue
            out.append(rec)
        return out

    def admin_snapshot(self) -> dict:
        from travelogue.templating.admin_store import get_effective_lifecycle, get_store_revision

        rows: list[dict] = []
        for tid in self.list_ids():
            rec = self.get(tid)
            healthy, errs = check_template_health(tid, registry=self)
            lc = get_effective_lifecycle(tid, default=rec.lifecycle)
            disc = rec.discovery or {}
            rows.append(
                {
                    "templateId": tid,
                    "version": rec.version,
                    "lifecycle": lc,
                    "registryLifecycle": rec.lifecycle,
                    "revision": rec.revision,
                    "healthy": healthy,
                    "healthErrors": errs,
                    "capabilities": list(rec.capabilities),
                    "category": disc.get("category"),
                    "tags": list(disc.get("tags") or ()),
                    "curationAdapter": rec.curation_adapter,
                }
            )
        return {"revision": get_store_revision(), "templates": rows}


def _record_from_dir(
    template_id: str,
    *,
    lifecycle: TemplateLifecycle,
    capabilities: tuple[str, ...],
    curation_adapter: str | None = None,
    render_adapter: str | None = None,
    fallback: str | None = None,
    shared_partials_from: str | None = None,
    shared_assets_from: str | None = None,
) -> TemplateRecord:
    from travelogue.templating.manifest_meta import load_template_meta

    tdir = ROOT / "templates" / template_id
    manifest_path = tdir / "manifest.json"
    meta = load_template_meta(str(manifest_path))
    version = "1.0.0"
    if manifest_path.is_file():
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
            version = str(raw.get("version") or version)
        except (OSError, json.JSONDecodeError):
            pass
    return TemplateRecord(
        template_id=template_id,
        version=version,
        template_dir=tdir,
        manifest_path=manifest_path,
        fallback_template_id=fallback,
        lifecycle=lifecycle,
        capabilities=capabilities,
        revision=1,
        render_adapter=render_adapter or DEFAULT_TEMPLATE_ID,
        curation_adapter=curation_adapter or template_id,
        shared_partials_from=shared_partials_from,
        shared_assets_from=shared_assets_from,
        discovery={
            "category": meta.get("category"),
            "tags": meta.get("tags"),
            "style": meta.get("style"),
            "complexity": meta.get("complexity"),
            "bestFor": meta.get("bestFor"),
        },
    )


def _visual_journal_record() -> TemplateRecord:
    return _record_from_dir(
        DEFAULT_TEMPLATE_ID,
        lifecycle="ga",
        capabilities=("map", "voice", "video", "route", "screens"),
        curation_adapter=DEFAULT_TEMPLATE_ID,
        render_adapter=DEFAULT_TEMPLATE_ID,
    )


def _event_recap_record() -> TemplateRecord:
    return _record_from_dir(
        EVENT_RECAP_TEMPLATE_ID,
        lifecycle="experimental",
        capabilities=("video", "event", "screens"),
        curation_adapter=EVENT_RECAP_TEMPLATE_ID,
        render_adapter=DEFAULT_TEMPLATE_ID,
        fallback=DEFAULT_TEMPLATE_ID,
        shared_partials_from=DEFAULT_TEMPLATE_ID,
        shared_assets_from=DEFAULT_TEMPLATE_ID,
    )


def bootstrap_registry() -> TemplateRegistry:
    reg = TemplateRegistry()
    reg.register(_visual_journal_record())
    reg.register(_event_recap_record())
    return reg


_REGISTRY: TemplateRegistry | None = None


def get_registry() -> TemplateRegistry:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = bootstrap_registry()
    return _REGISTRY


def reset_registry_for_tests(registry: TemplateRegistry | None = None) -> None:
    global _REGISTRY
    _REGISTRY = registry


def check_template_health(
    template_id: str,
    *,
    registry: TemplateRegistry | None = None,
) -> tuple[bool, list[str]]:
    """registry + manifest + adapter + assets gate (PRD §5.1)."""
    reg = registry or get_registry()
    errors: list[str] = []
    try:
        rec = reg.get(template_id)
    except TemplateRegistryError as exc:
        return False, [str(exc)]

    if not rec.template_dir.is_dir():
        errors.append(f"missing template_dir: {rec.template_dir}")
    main_hbs = rec.template_dir / "journal.hbs"
    if not main_hbs.is_file():
        errors.append(f"missing renderer entry: {main_hbs}")
    if not rec.manifest_path.is_file():
        errors.append(f"missing manifest: {rec.manifest_path}")
    else:
        try:
            json.loads(rec.manifest_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            errors.append(f"invalid manifest json: {exc}")

    if rec.render_adapter not in KNOWN_RENDER_ADAPTERS:
        errors.append(f"unknown render adapter: {rec.render_adapter}")

    assets_demo = rec.template_dir / "assets" / "demo"
    if not assets_demo.is_dir() and rec.shared_assets_from:
        try:
            shared = reg.get(rec.shared_assets_from)
            assets_demo = shared.template_dir / "assets" / "demo"
        except TemplateRegistryError:
            errors.append(f"shared assets template missing: {rec.shared_assets_from}")
    if not assets_demo.is_dir():
        errors.append(f"missing assets/demo under {rec.template_dir}")

    from travelogue.templating.admin_store import get_effective_lifecycle
    from travelogue.templating.guardrails import ga_guardrail_errors

    lc = get_effective_lifecycle(template_id, default=rec.lifecycle)
    errors.extend(ga_guardrail_errors(template_id, lifecycle=lc, manifest_path=str(rec.manifest_path)))

    return len(errors) == 0, errors
