"""Face detection helpers (no OpenCV required for unit tests)."""

from __future__ import annotations

from PIL import Image

from travelogue.media.subject_detect import analyze_subject, focal_from_faces


def test_focal_from_largest_face_box():
    focal = focal_from_faces([(10, 20, 100, 120)], img_w=400, img_h=600)
    assert 0.1 < focal[0] < 0.5
    assert 0.1 < focal[1] < 0.5


def test_analyze_subject_disabled_returns_no_tags():
    img = Image.new("RGB", (200, 300), (128, 128, 128))
    r = analyze_subject(img, enabled=False)
    assert not r.has_face
    assert r.tags == ()


def test_analyze_subject_without_opencv_is_noop():
    img = Image.new("RGB", (200, 300), (128, 128, 128))
    r = analyze_subject(img, enabled=True)
    # When opencv not installed, safe no-op
    from travelogue.media.subject_detect import _opencv_available

    if not _opencv_available():
        assert not r.has_face
    else:
        assert isinstance(r.has_face, bool)
