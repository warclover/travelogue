"""PyInstaller entry point: Travelogue Studio exe."""

from __future__ import annotations

import os
import sys


def main() -> None:
    # Desktop / packaged Studio: allow local folder-picker albums by default.
    # Operators can still set TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=0 to lock down.
    os.environ.setdefault("TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM", "1")
    if len(sys.argv) == 1:
        sys.argv.append("studio")
    from travelogue.cli import app

    app()


if __name__ == "__main__":
    main()
