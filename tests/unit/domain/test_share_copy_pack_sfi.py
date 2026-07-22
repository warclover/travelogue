"""SFI D-SFI-14 · Xiaohongshu copy pack / OQ-2 no-Key body gate."""

from travelogue.domain.share_copy_pack import build_share_copy_pack


def test_no_key_omits_body_even_if_hook_present() -> None:
    trip = {
        "meta": {
            "title": "武大 米娜",
            "hook": "两日漫步湖边",
            "places": ["武大"],
        }
    }
    pack = build_share_copy_pack(trip, llm_available=False)
    assert pack["title"]
    assert pack["body"] == ""
    assert "#旅行日记" in pack["topics"]
    assert "#武大" in pack["topics"]


def test_with_key_reuses_hook_as_body() -> None:
    trip = {"meta": {"title": "仙本那", "hook": "深蓝海面"}}
    pack = build_share_copy_pack(trip, llm_available=True)
    assert pack["body"] == "深蓝海面"
