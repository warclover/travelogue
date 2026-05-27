"""PyInstaller entry point: Travelogue Studio exe."""

from __future__ import annotations

import sys


def main() -> None:
    if len(sys.argv) == 1:
        sys.argv.append("studio")
    from travelogue.cli import app

    app()


if __name__ == "__main__":
    main()
