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

    - 快速分享 + kept_n∈1–9 + 未开实验选项 → 不打断（sparse_suppressed=True）
    - 开启「导入后先确认章节」→ 允许 G1（含 Sparse）
    - 精细制作 → 与实验选项一致（不享受 Sparse 默认跳过以外的特殊强制）
    """
    if not g1_confirm_structure:
        return False, is_sparse_quick_share(import_mode, kept_n)
    return True, False
