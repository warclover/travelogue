"""Unit tests for Studio multipart form parsing."""

from __future__ import annotations

from travelogue.web.studio_multipart import parse_multipart_form


def _encode_multipart(
    boundary: bytes,
    *,
    fields: dict[str, str] | None = None,
    files: list[tuple[str, str, bytes]] | None = None,
) -> tuple[bytes, str]:
    parts: list[bytes] = []
    for name, value in (fields or {}).items():
        parts.append(
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="' + name.encode() + b'"\r\n\r\n'
            + value.encode("utf-8") + b"\r\n"
        )
    for name, filename, content in files or []:
        parts.append(
            b"--" + boundary + b"\r\n"
            b'Content-Disposition: form-data; name="' + name.encode()
            + b'"; filename="' + filename.encode() + b'"\r\n\r\n'
            + content + b"\r\n"
        )
    parts.append(b"--" + boundary + b"--\r\n")
    body = b"".join(parts)
    return body, f"multipart/form-data; boundary={boundary.decode()}"


def test_parse_multipart_text_field() -> None:
    boundary = b"----abc"
    body, ctype = _encode_multipart(boundary, fields={"title": "林芝"})
    fields, files = parse_multipart_form(body, ctype)
    assert fields == {"title": "林芝"}
    assert files == []


def test_parse_multipart_file_and_field() -> None:
    boundary = b"----xyz"
    body, ctype = _encode_multipart(
        boundary,
        fields={"tripId": "demo"},
        files=[("photos", "a.jpg", b"\xff\xd8\xff")],
    )
    fields, files = parse_multipart_form(body, ctype)
    assert fields["tripId"] == "demo"
    assert len(files) == 1
    assert files[0] == ("photos", "a.jpg", b"\xff\xd8\xff")


def test_parse_multipart_missing_boundary() -> None:
    fields, files = parse_multipart_form(b"body", "application/octet-stream")
    assert fields == {}
    assert files == []
