"""Layout template registry — YAML load, index, cache (W1)."""

from __future__ import annotations

import hashlib
import json
import time
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from travelogue.layout_templates.css_gen import grid_templates_for
from travelogue.layout_templates.geometry import slot_aspect_table
from travelogue.layout_templates.legacy_bridge import (
    export_auto_flow_grids,
    export_explicit_grid_specs,
    export_forbidden_maps,
    export_mosaic_pattern,
    export_pattern_grid_class,
    export_stack_patterns,
    mosaic_pattern_id_groups,
)

PACKAGE_ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = PACKAGE_ROOT / "layout_template.schema.json"
DEFAULT_TEMPLATES_DIR = PACKAGE_ROOT / "templates"
DEFAULT_POLICY_PATH = PACKAGE_ROOT / "lte_policy.yaml"
DEFAULT_CACHE_PATH = PACKAGE_ROOT / "registry.cache.json"

_ACTIVE_STATUSES = frozenset({"experimental", "beta", "ga"})


from travelogue.layout_templates.models import TemplateDef, TemplateSlot, TemplateStage


def schema_path() -> Path:
    return SCHEMA_PATH


def templates_dir() -> Path:
    return DEFAULT_TEMPLATES_DIR


def _parse_stage(raw: dict[str, Any]) -> TemplateStage:
    grid_raw = raw.get("grid")
    grid = (int(grid_raw[0]), int(grid_raw[1])) if grid_raw else None
    cols_raw = raw.get("cols")
    rows_raw = raw.get("rows")
    cols = tuple(float(x) for x in cols_raw) if cols_raw else None
    rows = tuple(float(x) for x in rows_raw) if rows_raw else None
    gap = raw.get("gap")
    return TemplateStage(
        aspect=str(raw["aspect"]),
        grid=grid,
        cols=cols,
        rows=rows,
        gap=str(gap) if gap is not None else None,
    )


def _parse_slot(raw: dict[str, Any]) -> TemplateSlot:
    rect = tuple(int(x) for x in raw["rect"])
    vw = raw.get("visualWeight")
    da = raw.get("displayAspect")
    return TemplateSlot(
        index=int(raw["index"]),
        rect=(rect[0], rect[1], rect[2], rect[3]),
        role=str(raw["role"]),
        fit=str(raw["fit"]) if raw.get("fit") else None,
        visual_weight=float(vw) if vw is not None else None,
        display_aspect=float(da) if da is not None else None,
    )


def template_def_from_yaml(doc: dict[str, Any]) -> TemplateDef:
    mix = doc.get("mix") or {}
    render = doc["render"]
    photo = doc["photoCount"]
    return TemplateDef(
        id=str(doc["id"]),
        version=int(doc["version"]),
        status=str(doc["status"]),
        kind=str(doc["kind"]),
        display_name=str(doc["displayName"]),
        description=str(doc.get("description") or ""),
        aesthetic=str(doc["aesthetic"]) if doc.get("aesthetic") else None,
        balance_policy=str(doc["balancePolicy"]) if doc.get("balancePolicy") else None,
        stage=_parse_stage(doc["stage"]),
        photo_count_min=int(photo["min"]),
        photo_count_max=int(photo["max"]),
        mix_portrait=int(mix["portrait"]) if mix.get("portrait") is not None else None,
        mix_landscape=int(mix["landscape"]) if mix.get("landscape") is not None else None,
        slots=tuple(_parse_slot(s) for s in doc["slots"]),
        constraints=dict(doc.get("constraints") or {}),
        compatibility_hints=dict(doc.get("compatibilityHints") or {}),
        scoring=dict(doc.get("scoring") or {}),
        render_grid_class=str(render["gridClass"]),
        render_css_bundle=str(render["cssBundle"]),
        render_fit_policy=str(render["fitPolicy"]) if render.get("fitPolicy") else None,
        rollout=dict(doc.get("rollout") or {}),
        raw=doc,
    )


def _yaml_files(root: Path) -> list[Path]:
    files = sorted(root.glob("*.yaml")) + sorted(root.glob("*.yml"))
    return [p for p in files if not p.name.startswith("_")]


def _content_hash(root: Path) -> str:
    h = hashlib.sha256()
    for path in _yaml_files(root):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    policy = DEFAULT_POLICY_PATH
    if policy.is_file():
        h.update(policy.read_bytes())
    return h.hexdigest()


def _load_yaml_documents(root: Path) -> dict[str, TemplateDef]:
    templates: dict[str, TemplateDef] = {}
    for path in _yaml_files(root):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        if not isinstance(doc, dict):
            continue
        t = template_def_from_yaml(doc)
        templates[t.id] = t
    return templates


def _write_cache(
    templates: dict[str, TemplateDef],
    *,
    cache_path: Path,
    content_hash: str,
) -> None:
    by_count: dict[str, list[str]] = {}
    for t in templates.values():
        for n in range(t.photo_count_min, t.photo_count_max + 1):
            by_count.setdefault(str(n), []).append(t.id)

    payload = {
        "contentHash": content_hash,
        "templateIds": sorted(templates),
        "byPhotoCount": {k: sorted(v) for k, v in sorted(by_count.items())},
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    cache_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _load_policy_doc() -> dict[str, Any]:
    if not DEFAULT_POLICY_PATH.is_file():
        return {}
    try:
        doc = yaml.safe_load(DEFAULT_POLICY_PATH.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return doc if isinstance(doc, dict) else {}


def load_policy_quotas() -> dict[int, dict[str, int]]:
    """Load per-photo-count active template quotas from lte_policy.yaml."""
    return _load_policy_quotas_cached()


@lru_cache(maxsize=1)
def _load_policy_quotas_cached() -> dict[int, dict[str, int]]:
    quotas_raw = _load_policy_doc().get("quotas") or {}
    out: dict[int, dict[str, int]] = {}
    if not isinstance(quotas_raw, dict):
        return out
    for key, limits in quotas_raw.items():
        try:
            photo_count = int(key)
        except (TypeError, ValueError):
            continue
        if not isinstance(limits, dict):
            continue
        parsed: dict[str, int] = {}
        for lk, lv in limits.items():
            try:
                parsed[str(lk)] = int(lv)
            except (TypeError, ValueError):
                continue
        if parsed:
            out[photo_count] = parsed
    return out


def _active_by_photo_count(
    active: list[TemplateDef],
) -> dict[int, dict[str, TemplateDef]]:
    """Group active templates by each photoCount they cover (id-deduped)."""
    by_count: dict[int, dict[str, TemplateDef]] = {}
    for tpl in active:
        for n in range(tpl.photo_count_min, tpl.photo_count_max + 1):
            by_count.setdefault(n, {})[tpl.id] = tpl
    return by_count


def _count_kind(group: dict[str, TemplateDef], kind: str | None) -> int:
    if kind is None:
        return len(group)
    return sum(1 for t in group.values() if t.kind == kind)


_QUOTA_LIMIT_KEYS: tuple[tuple[str | None, str], ...] = (
    (None, "max_active_total"),
    ("composite", "max_active_composite"),
    ("primitive", "max_active_primitive"),
)


def check_active_quotas(engine: LayoutTemplateEngine) -> list[str]:
    """Return human-readable quota violations for active templates."""
    quotas = load_policy_quotas()
    if not quotas:
        return []
    warnings: list[str] = []
    by_count = _active_by_photo_count(engine.list_active())
    for photo_count, limits in sorted(quotas.items()):
        group = by_count.get(photo_count, {})
        for kind, limit_key in _QUOTA_LIMIT_KEYS:
            limit = limits.get(limit_key)
            if limit is None:
                continue
            actual = _count_kind(group, kind)
            if actual > int(limit):
                label = kind or "total"
                warnings.append(
                    f"photoCount={photo_count}: active {label} {actual} > {limit_key}={limit}"
                )
    return warnings


_STATUS_KEEP_PRIORITY = {"ga": 0, "beta": 1, "experimental": 2}


def _quotas_would_trim(active: list[TemplateDef], quotas: dict[int, dict[str, int]]) -> bool:
    by_count = _active_by_photo_count(active)
    for photo_count, limits in quotas.items():
        group = by_count.get(photo_count, {})
        if not group:
            continue
        for kind, limit_key in _QUOTA_LIMIT_KEYS:
            limit = limits.get(limit_key)
            if limit is not None and _count_kind(group, kind) > int(limit):
                return True
    return False


def _apply_active_quotas(
    active: list[TemplateDef],
    quotas: dict[int, dict[str, int]],
) -> list[TemplateDef]:
    """Drop lowest-priority active templates when lte_policy quotas exceeded."""
    if not quotas or not active:
        return active
    if not _quotas_would_trim(active, quotas):
        return active
    kept_ids: set[str] = {t.id for t in active}
    by_count = _active_by_photo_count(active)

    for photo_count, limits in sorted(quotas.items()):
        group = by_count.get(photo_count, {})
        if not group:
            continue
        candidates = sorted(
            group.values(),
            key=lambda t: (_STATUS_KEEP_PRIORITY.get(t.status, 9), t.id),
        )

        def _trim(kind: str | None, limit_key: str) -> None:
            nonlocal kept_ids
            raw_limit = limits.get(limit_key)
            if raw_limit is None:
                return
            limit = int(raw_limit)
            pool = candidates if kind is None else [t for t in candidates if t.kind == kind]
            pool = [t for t in pool if t.id in kept_ids]
            if len(pool) <= limit:
                return
            for drop in pool[limit:]:
                kept_ids.discard(drop.id)

        for kind, limit_key in _QUOTA_LIMIT_KEYS:
            _trim(kind, limit_key)

    return [t for t in active if t.id in kept_ids]


class LayoutTemplateEngine:
    """Read-only LTE facade (PRD §3.3)."""

    def __init__(
        self,
        templates: dict[str, TemplateDef],
        *,
        content_hash: str = "",
        cache_path: Path | None = None,
    ) -> None:
        self._templates = templates
        self._content_hash = content_hash
        self._cache_path = cache_path or DEFAULT_CACHE_PATH
        self._by_photo_count: dict[int, list[str]] = {}
        for t in templates.values():
            for n in range(t.photo_count_min, t.photo_count_max + 1):
                self._by_photo_count.setdefault(n, []).append(t.id)
        for n in self._by_photo_count:
            self._by_photo_count[n] = sorted(set(self._by_photo_count[n]))

    @classmethod
    def load(
        cls,
        root: Path | None = None,
        *,
        cache_path: Path | None = None,
        rebuild_cache: bool = False,
    ) -> LayoutTemplateEngine:
        root = root or DEFAULT_TEMPLATES_DIR
        cache_path = cache_path or DEFAULT_CACHE_PATH
        digest = _content_hash(root)
        # registry.cache.json is a checked-in drift sentinel (contentHash +
        # photoCount index) for CI, not a runtime load fast-path: full
        # TemplateDefs are not serialized there, so YAML is always parsed and
        # the in-memory _by_photo_count index satisfies the p99<1ms goal.
        templates = _load_yaml_documents(root)
        if rebuild_cache or not cache_path.is_file():
            _write_cache(templates, cache_path=cache_path, content_hash=digest)
        else:
            try:
                cached = json.loads(cache_path.read_text(encoding="utf-8"))
                if cached.get("contentHash") != digest:
                    _write_cache(templates, cache_path=cache_path, content_hash=digest)
            except (OSError, json.JSONDecodeError):
                _write_cache(templates, cache_path=cache_path, content_hash=digest)
        return cls(templates, content_hash=digest, cache_path=cache_path)

    def list_active(
        self,
        *,
        window_size: int | None = None,
        tags: set[str] | None = None,
        enforce_quotas: bool = True,
    ) -> list[TemplateDef]:
        ids: list[str]
        if window_size is not None:
            ids = list(self._by_photo_count.get(window_size, ()))
        else:
            ids = sorted(self._templates)
        out: list[TemplateDef] = []
        for tid in ids:
            t = self._templates[tid]
            if t.status not in _ACTIVE_STATUSES:
                continue
            if tags:
                scoring_tags = set(t.scoring.get("tags") or [])
                if not (scoring_tags & tags):
                    continue
            out.append(t)
        if enforce_quotas:
            out = _apply_active_quotas(out, load_policy_quotas())
        return out

    def get(self, template_id: str, version: int | None = None) -> TemplateDef:
        t = self._templates[template_id]
        if version is not None and t.version != version:
            raise KeyError(f"{template_id} version {version} not found (have {t.version})")
        return t

    def slot_aspect_table(self, template_id: str) -> list:
        return slot_aspect_table(self.get(template_id))

    def export_legacy_registry(self) -> dict[str, Any]:
        from travelogue.layout_engine.mosaic.constants import PATTERN_GRID_CLASS
        from travelogue.layout_engine.mosaic.pattern_catalog import LEGACY_MOSAIC_REGISTRY_IDS

        mosaic_patterns = {
            tid: export_mosaic_pattern(t)
            for tid, t in self._templates.items()
            if tid in LEGACY_MOSAIC_REGISTRY_IDS
        }
        wide, tall = export_forbidden_maps(self._templates)
        grid_templates: dict[str, dict[str, str]] = {}
        for tid, t in self._templates.items():
            if tid not in PATTERN_GRID_CLASS:
                continue
            cols, rows = grid_templates_for(t)
            grid_templates[tid] = {
                "gridTemplateColumns": cols,
                "gridTemplateRows": rows,
            }
        return {
            "mosaic_patterns": mosaic_patterns,
            "explicit_grid_specs": export_explicit_grid_specs(self._templates),
            "auto_flow_grids": export_auto_flow_grids(self._templates),
            "stack_patterns": export_stack_patterns(self._templates),
            "pattern_grid_class": export_pattern_grid_class(self._templates),
            "portrait_forbidden_wide": wide,
            "landscape_forbidden_tall": tall,
            "mosaic_pattern_id_groups": mosaic_pattern_id_groups(),
            "grid_templates": grid_templates,
        }


@lru_cache(maxsize=1)
def get_engine() -> LayoutTemplateEngine:
    return LayoutTemplateEngine.load()


def get_layout_template(template_id: str):
    """Return one layout template by id (Studio admin / admission)."""
    return get_engine().get(template_id)


def reset_engine_cache_for_tests() -> None:
    get_engine.cache_clear()
    _load_policy_quotas_cached.cache_clear()
