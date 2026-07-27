"""Face detection helpers (no OpenCV required for unit tests)."""

from __future__ import annotations

from PIL import Image

from travelogue.media.subject_detect import (
    analyze_subject,
    faces_norm_from_faces,
    focal_from_faces,
    protect_box_from_faces,
)


def test_focal_from_union_single_face():
    focal = focal_from_faces([(10, 20, 100, 120)], img_w=400, img_h=600)
    assert 0.1 < focal[0] < 0.5
    assert 0.1 < focal[1] < 0.5


def test_focal_from_union_two_faces_centers_between():
    # Left face + right face → union center near mid-x
    faces = [(10, 40, 40, 40), (200, 40, 40, 40)]
    focal = focal_from_faces(faces, img_w=400, img_h=200)
    assert 0.25 < focal[0] < 0.45


def test_protect_box_expands_up_and_down():
    box = protect_box_from_faces([(100, 100, 50, 50)], img_w=400, img_h=400)
    assert box is not None
    # Top pad 0.35*50, bottom pad 1.6*50, x pad 0.25*50
    assert box["y"] < 100 / 400
    assert box["y"] + box["h"] > (100 + 50) / 400
    assert box["w"] > 50 / 400


def test_faces_norm_from_faces():
    norms = faces_norm_from_faces([(100, 50, 40, 60)], img_w=400, img_h=200)
    assert len(norms) == 1
    assert norms[0]["x"] == 0.25
    assert norms[0]["y"] == 0.25


def test_analyze_subject_disabled_returns_no_tags():
    img = Image.new("RGB", (200, 300), (128, 128, 128))
    r = analyze_subject(img, enabled=False)
    assert not r.has_face
    assert r.tags == ()
    assert r.faces_norm == ()
    assert r.protect_box is None


def test_analyze_subject_without_opencv_is_noop():
    img = Image.new("RGB", (200, 300), (128, 128, 128))
    r = analyze_subject(img, enabled=True)
    # When opencv not installed, safe no-op
    from travelogue.media.subject_detect import _opencv_available

    if not _opencv_available():
        assert not r.has_face
    else:
        assert isinstance(r.has_face, bool)
