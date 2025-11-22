#!/usr/bin/env python3
from __future__ import annotations

try:
    from holopazaak.main_app import main
except ImportError:
    import sys

    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent))  # ./Tools/HoloPazaak/src/
    from holopazaak.main_app import main
from holopazaak.main_init import main_init

if __name__ == "__main__":
    main_init()
    main()

