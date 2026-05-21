"""Allow ``python -m travelogue`` (same as ``python -m travelogue.cli``)."""

from travelogue.cli import main

if __name__ == "__main__":
    main()
