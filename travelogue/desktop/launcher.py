"""PyInstaller entry point: Travelogue Studio exe."""

from __future__ import annotations

import sys


def main() -> None:
    # Desktop / packaged Studio: allow local folder-picker albums by default.
    # Operators can still set TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0 to lock down.
    from travelogue.web.studio_handlers.import_handlers import ensure_studio_trust_local_album

    ensure_studio_trust_local_album()
    if len(sys.argv) == 1:
        sys.argv.append("studio")
    from travelogue.cli import app

    app()


if __name__ == "__main__":
    main()
