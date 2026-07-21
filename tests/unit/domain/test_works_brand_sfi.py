"""SFI D-SFI-13 · works brand three-state."""

from travelogue.domain.works_brand import resolve_works_brand


def test_default_brand() -> None:
    r = resolve_works_brand({})
    assert r["showWorksBrand"] is True
    assert r["worksBrandLine"] == "Travelogue"
    assert r["worksBrandCustom"] is False


def test_custom_brand() -> None:
    r = resolve_works_brand({"worksBrandMode": "custom", "worksBrandText": "米娜游记"})
    assert r["showWorksBrand"] is True
    assert r["worksBrandLine"] == "米娜游记"
    assert r["worksBrandCustom"] is True


def test_hidden_brand() -> None:
    r = resolve_works_brand({"worksBrandMode": "hidden"})
    assert r["showWorksBrand"] is False
    assert r["worksBrandLine"] == ""
