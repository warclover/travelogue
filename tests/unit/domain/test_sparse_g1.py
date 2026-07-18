"""Share-Face Closeout W1 · Sparse G1 门控（AC-SFC-08/09）。"""

from travelogue.domain.sparse_g1 import is_sparse_quick_share, resolve_g1_pending


def test_sparse_quick_share_band() -> None:
    assert is_sparse_quick_share("quick_share", 6)
    assert is_sparse_quick_share("quick_share", 1)
    assert is_sparse_quick_share("quick_share", 9)
    assert not is_sparse_quick_share("quick_share", 10)
    assert not is_sparse_quick_share("fine_craft", 6)
    assert not is_sparse_quick_share("quick_share", 0)


def test_default_skips_g1_for_sparse() -> None:
    pending, suppressed = resolve_g1_pending(
        import_mode="quick_share",
        kept_n=6,
        g1_confirm_structure=False,
    )
    assert pending is False
    assert suppressed is True


def test_experimental_allows_g1_for_sparse() -> None:
    pending, suppressed = resolve_g1_pending(
        import_mode="quick_share",
        kept_n=6,
        g1_confirm_structure=True,
    )
    assert pending is True
    assert suppressed is False


def test_fine_craft_follows_flag() -> None:
    pending, suppressed = resolve_g1_pending(
        import_mode="fine_craft",
        kept_n=6,
        g1_confirm_structure=True,
    )
    assert pending is True
    assert suppressed is False
    pending2, suppressed2 = resolve_g1_pending(
        import_mode="fine_craft",
        kept_n=6,
        g1_confirm_structure=False,
    )
    assert pending2 is False
    assert suppressed2 is False
