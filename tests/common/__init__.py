import pathlib
import sys

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists():
        sys.path.insert(0, str(pykotor_path.parent))
