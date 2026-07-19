"""Share-Face Closeout W1 · Sparse 快速分享 G1 门控（D-SFC-07）。"""

from __future__ import annotations

SPARSE_KEPT_N_MAX = 9


def is_sparse_quick_share(import_mode: str, kept_n: int) -> bool:
    mode = (import_mode or "quick_share").strip().lower()
    return mode == "quick_share" and 1 <= int(kept_n) <= SPARSE_KEPT_N_MAX


def resolve_g1_pending(
    *,
    import_mode: str,
    kept_n: int,
    g1_confirm_structure: bool,
) -> tuple[bool, bool]:
    """Return ``(g1_pending, sparse_suppressed)``.

    Preview Chrome Unify（D-PCU-09～11）:
    - 默认（``g1_confirm_structure=False``）：一律不 pending（kept_n / 精细制作无关）→ 管线 auto-lock
    - 实验 ON：一律 pending（含 Sparse），前端开分章面板而非黄条
    - ``sparse_suppressed`` 仅作遥测：默认路径下 Sparse 快速分享记 True
    """
    if not g1_confirm_structure:
        return False, is_sparse_quick_share(import_mode, kept_n)
    return True, False
