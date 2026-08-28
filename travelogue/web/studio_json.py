"""JSON body parsing for Studio HTTP handlers.

Failure is distinct from a legitimate empty object. Callers that have already
sent an error response raise ``StudioJsonBodyError`` so dispatch stops.
"""

from __future__ import annotations

import json


class StudioJsonBodyError(Exception):
    """JSON body was rejected; the HTTP error response is already sent."""


def parse_content_length(raw: object, *, max_bytes: int) -> int:
    if raw is None or raw == "":
        return 0
    try:
        length = int(raw)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        raise ValueError("invalid Content-Length") from None
    if length < 0:
        raise ValueError("invalid Content-Length")
    if length > max_bytes:
        raise OverflowError("request body too large")
    return length


def loads_json_object(body: bytes) -> dict:
    try:
        text = body.decode("utf-8") if body else ""
    except UnicodeDecodeError as exc:
        raise ValueError("invalid JSON") from exc
    if not text:
        return {}
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("invalid JSON")
    return payload
