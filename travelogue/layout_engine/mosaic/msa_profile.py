"""MSA · window-level aspect-ratio profile (S-MSA-01)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping, Sequence

from travelogue.config.mosaic import SlotAdaptationConfig

_PORT_LADDER: tuple[tuple[str, float], ...] = (
    ("two_three", 2 / 3),
    ("three_four", 0.75),
)

LADDER_TOL = 0.08
SINGLE_PEAK_FRACTION = 0.60


@dataclass(frozen=True)
class MsaProfile:
    n_land: int
    n_port: int
    n_other: int
    land_peak: str  # three_two | four_three | sixteen_nine | mixed | none
    port_peak: str  # two_three | three_four | mixed | none
    land_median_r: float | None
    r_hero_target: float | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "nLand": self.n_land,
            "nPort": self.n_port,
            "nOther": self.n_other,
            "landPeak": self.land_peak,
            "portPeak": self.port_peak,
            "landMedianR": self.land_median_r,
            "rHeroTarget": self.r_hero_target,
        }


def _asset_r(asset: Mapping[str, Any]) -> float | None:
    try:
        wf = float(asset.get("width"))
        hf = float(asset.get("height"))
    except (TypeError, ValueError):
        return None
    if wf <= 0 or hf <= 0:
        return None
    return wf / hf


def _nearest_ladder(
    r: float, ladder: Sequence[tuple[str, float]], *, tol: float
) -> str | None:
    best_label: str | None = None
    best_dist = float("inf")
    for label, nom in ladder:
        dist = abs(r - nom)
        if dist < best_dist:
            best_dist = dist
            best_label = label
    if best_label is None or best_dist > tol:
        return None
    return best_label


def _peak_from_labels(labels: list[str], *, single_frac: float) -> str:
    if not labels:
        return "none"
    counts: dict[str, int] = {}
    for lab in labels:
        counts[lab] = counts.get(lab, 0) + 1
    top_lab, top_n = max(counts.items(), key=lambda kv: kv[1])
    if top_n / len(labels) >= single_frac:
        return top_lab
    return "mixed"


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    n = len(ordered)
    mid = n // 2
    if n % 2:
        return ordered[mid]
    return 0.5 * (ordered[mid - 1] + ordered[mid])


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


def build_msa_profile(
    assets: Sequence[Mapping[str, Any]],
    *,
    cfg: SlotAdaptationConfig | None = None,
) -> MsaProfile:
    """Classify window AR peak and decide ``r_hero_target`` (seven-seat freeze)."""
    sa = cfg or SlotAdaptationConfig()
    peaks = sa.land_peaks or {}
    land_nom = {
        "three_two": float(peaks.get("three_two", 1.50)),
        "four_three": float(peaks.get("four_three", 1.3333)),
        "sixteen_nine": float(peaks.get("sixteen_nine", 1.7778)),
    }
    land_ladder = tuple(
        (k, land_nom[k]) for k in ("three_two", "four_three", "sixteen_nine")
    )
    clamp_lo, clamp_hi = sa.hero_target_clamp
    wide_frac = float(sa.wide_peak_fraction)

    land_rs: list[float] = []
    port_rs: list[float] = []
    n_other = 0
    land_labels: list[str] = []
    port_labels: list[str] = []

    for asset in assets:
        r = _asset_r(asset)
        if r is None:
            n_other += 1
            continue
        kind = str(asset.get("aspectKind") or asset.get("aspect_kind") or "").lower()
        if kind in ("square", "tall", "panorama"):
            n_other += 1
            continue
        if kind == "portrait" or r < 0.95:
            lab = _nearest_ladder(r, _PORT_LADDER, tol=LADDER_TOL)
            if lab is None:
                n_other += 1
                continue
            port_rs.append(r)
            port_labels.append(lab)
            continue
        if 0.95 <= r <= 1.05 and kind != "landscape":
            n_other += 1
            continue
        lab = _nearest_ladder(r, land_ladder, tol=LADDER_TOL)
        land_rs.append(r)
        if lab is not None:
            land_labels.append(lab)

    land_peak = _peak_from_labels(land_labels, single_frac=SINGLE_PEAK_FRACTION)
    if land_peak == "mixed" and land_labels:
        wide_n = sum(1 for lab in land_labels if lab == "sixteen_nine")
        if wide_n / len(land_labels) >= wide_frac:
            land_peak = "sixteen_nine"
    elif land_peak == "none" and land_rs:
        land_peak = "mixed"

    port_peak = _peak_from_labels(port_labels, single_frac=SINGLE_PEAK_FRACTION)
    land_median = _median(land_rs) if land_rs else None

    if land_peak in land_nom:
        r_hero: float | None = land_nom[land_peak]
    elif land_peak == "mixed" and land_median is not None:
        r_hero = _clamp(land_median, clamp_lo, clamp_hi)
    else:
        r_hero = None

    return MsaProfile(
        n_land=len(land_rs),
        n_port=len(port_rs),
        n_other=n_other,
        land_peak=land_peak,
        port_peak=port_peak,
        land_median_r=round(land_median, 4) if land_median is not None else None,
        r_hero_target=round(r_hero, 4) if r_hero is not None else None,
    )
