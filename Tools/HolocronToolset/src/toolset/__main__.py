#!/usr/bin/env python3
from __future__ import annotations

try:
    from toolset.main_app import main
except ImportError:
    import sys

    from pathlib import Path
    sys.path.append(str(Path(__file__).resolve().parent.parent))  # ./Tools/HolocronToolset/src/
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent.joinpath("Tools", "KotorDiff", "src")))  # ./Tools/KotorDiff/src/
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent.joinpath("Libraries", "PyKotor", "src")))  # ./Libraries/PyKotor/src/
    sys.path.append(str(Path(__file__).resolve().parent.parent.parent.parent.parent.joinpath("Libraries", "PyKotorGL", "src")))  # ./Libraries/PyKotorGL/src/
    from toolset.main_app import main
from toolset.main_init import main_init

if __name__ == "__main__":
    main_init()
    main()
