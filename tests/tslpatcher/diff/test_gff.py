import pathlib
import sys
from unittest import TestCase

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.exists():
        sys.path.append(str(pykotor_path.parent))


class TestDiffGFF(TestCase):
    ...
