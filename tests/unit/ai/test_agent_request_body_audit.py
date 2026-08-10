"""ACP W4 · AC-ACP-12 static audit: agents must not default-send pixels/base64."""

from __future__ import annotations

from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[3] / "travelogue" / "ai" / "agents"

# Substrings that indicate raw image / local file payloads in request construction.
FORBIDDEN = (
    "base64",
    "file://",
    "data:image",
    "image/png",
    "image/jpeg",
    "application/octet-stream",
)


def test_agent_sources_have_no_default_pixel_payloads() -> None:
    assert AGENT_DIR.is_dir()
    hits: list[str] = []
    for path in sorted(AGENT_DIR.glob("*.py")):
        if path.name == "__init__.py":
            continue
        text = path.read_text(encoding="utf-8")
        lower = text.lower()
        for token in FORBIDDEN:
            # Allow comments that mention the policy itself.
            for i, line in enumerate(lower.splitlines(), start=1):
                if token not in line:
                    continue
                stripped = line.strip()
                if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
                    continue
                if "d-acp-07" in line or "pixel-free" in line or "no pixels" in line:
                    continue
                # Explicit opt-in for downscaled thumbnails (aesthetic_mllm only).
                if "acp_thumbnail_allowed" in line:
                    continue
                hits.append(f"{path.name}:{i}:{token}:{line.strip()[:80]}")
    assert hits == [], "AC-ACP-12 violations:\n" + "\n".join(hits)
