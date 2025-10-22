"""Allow running spec_tools as a module: python -m spec_tools"""

from .cli import main

if __name__ == "__main__":
    raise SystemExit(main())
