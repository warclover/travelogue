"""Share-Face Closeout W1/W2 · 用户面主词契约（AC-SFC-06/10/11）。"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
STUDIO = ROOT / "templates" / "studio"


def test_stale_label_is_share_face_copy() -> None:
    targets = [
        STUDIO / "homepage-v2" / "bento.js",
        STUDIO / "homepage-v2" / "shelf.js",
        STUDIO / "homepage-v2" / "bento-preview-picker-logic.js",
        STUDIO / "preview-toolbar-v3-task-dock.js",
        STUDIO / "js" / "help-onboarding.js",
        STUDIO / "preview-toolbar" / "longshot.js",
    ]
    for path in targets:
        text = path.read_text(encoding="utf-8")
        assert "长图可更新" not in text, path.name
        assert "长图待更新" not in text, path.name
        assert "长图已过期" not in text, path.name
    bento = (STUDIO / "homepage-v2" / "bento.js").read_text(encoding="utf-8")
    dictionary = (STUDIO / "js" / "copy-dictionary.js").read_text(encoding="utf-8")
    assert "COPY_DICTIONARY.shelfStale" in bento
    assert 'shelfStale: "长图需更新"' in dictionary
    assert "分享图需更新" in (STUDIO / "js" / "help-onboarding.js").read_text(encoding="utf-8")


def test_media_label_is_photo_type() -> None:
    features = (STUDIO / "preview-toolbar" / "features.js").read_text(encoding="utf-8")
    assert 'label.textContent = "照片类型"' in features
    assert 'label.textContent = "媒资"' not in features


def test_chapter_titles_still_forbid_xu_suffix() -> None:
    src = (ROOT / "travelogue" / "curation" / "chapter_titles.py").read_text(encoding="utf-8")
    assert 'f"{base}续"' not in src
    assert "（" in src or "(2)" in src or "daypart" in src.lower()


def test_no_preview_artifact_expired_jargon() -> None:
    longshot = (STUDIO / "preview-toolbar" / "longshot.js").read_text(encoding="utf-8")
    assert "预览产物已过期" not in longshot
