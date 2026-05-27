"""Parse multipart form uploads for Studio import."""

from __future__ import annotations


def parse_multipart_form(body: bytes, content_type: str) -> tuple[dict[str, str], list[tuple[str, bytes]]]:
    boundary = _extract_boundary(content_type)
    if not boundary:
        return {}, []

    delimiter = ("--" + boundary).encode("utf-8")
    fields: dict[str, str] = {}
    files: list[tuple[str, bytes]] = []

    for part in body.split(delimiter):
        part = part.strip(b"\r\n")
        if not part or part == b"--":
            continue
        header_block, _, content = part.partition(b"\r\n\r\n")
        if not header_block:
            continue
        content = content.rstrip(b"\r\n")
        headers = header_block.decode("utf-8", errors="replace")
        name = _header_value(headers, "name")
        if not name:
            continue
        filename = _header_value(headers, "filename")
        if filename:
            files.append((filename, content))
        else:
            fields[name] = content.decode("utf-8", errors="replace")
    return fields, files


def _extract_boundary(content_type: str) -> str | None:
    for token in content_type.split(";"):
        token = token.strip()
        if token.startswith("boundary="):
            value = token.split("=", 1)[1].strip().strip('"')
            return value
    return None


def _header_value(headers: str, key: str) -> str | None:
    key = key.lower()
    for line in headers.split("\r\n"):
        if not line.lower().startswith("content-disposition:"):
            continue
        for piece in line.split(";")[1:]:
            piece = piece.strip()
            if piece.lower().startswith(f"{key}="):
                return piece.split("=", 1)[1].strip().strip('"')
    return None
