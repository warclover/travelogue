"""SFI D-SFI-14 · Xiaohongshu copy pack；SNR D-SNR-10 升维 L0/L1。"""

from travelogue.domain.share_copy_pack import build_share_copy_pack


def test_l0_when_no_narrative() -> None:
    trip = {"meta": {"title": "武大 米娜", "places": ["武大"]}, "chapters": []}
    pack = build_share_copy_pack(trip, llm_available=False)
    assert pack["title"]
    assert pack["body"] == ""
    assert pack["level"] == "L0"
    assert "#旅行日记" in pack["topics"]
    assert "#武大" in pack["topics"]


def test_l1_reuses_hook_as_body_even_without_key() -> None:
    """SNR · 版心已有 hook 即 L1，不再以 Key 门控 body。"""
    trip = {"meta": {"title": "仙本那", "hook": "深蓝海面"}}
    pack = build_share_copy_pack(trip, llm_available=False)
    assert pack["body"] == "深蓝海面"
    assert pack["level"] == "L1"


def test_nas_out04_share_copy_pack_no_banned_terms() -> None:
    """NAS · S6 / OUT-04：有/无 Key 的 pack 字段不含 AI 面禁词。"""
    banned = (
        "AI 文案",
        "写作引擎",
        "配置写作引擎",
        "重新生成文案",
        "杂志感文案",
    )
    trip = {
        "meta": {
            "title": "武大春樱",
            "hook": "樱花大道漫步",
            "places": ["武大"],
        }
    }
    for llm in (False, True):
        pack = build_share_copy_pack(trip, llm_available=llm)
        blob = " ".join(
            str(pack.get(k) or "") for k in ("title", "body", "topics", "caption")
        )
        for term in banned:
            assert term not in blob, f"llm={llm} hit {term!r} in {pack!r}"
