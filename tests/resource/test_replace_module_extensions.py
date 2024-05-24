from __future__ import annotations

import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__).resolve()
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "PyKotor", "src")
UTILITY_PATH = THIS_SCRIPT_PATH.parents[2].joinpath("Libraries", "Utility", "src")


def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)


if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.installation import Installation


class TestReplaceModuleExtensions(unittest.TestCase):
    def testreplace_module_extensions(self):
        # Happy path tests
        self.assertEqual(Installation.get_module_root("module.mod"), "module")
        self.assertEqual(Installation.get_module_root("module.erf"), "module")
        self.assertEqual(Installation.get_module_root("module.rim"), "module")
        self.assertEqual(Installation.get_module_root("module_s.mod"), "module")
        self.assertEqual(Installation.get_module_root("module_s.erf"), "module")
        self.assertEqual(Installation.get_module_root("module_s.rim"), "module")
        self.assertEqual(Installation.get_module_root("module_dlg.mod"), "module")
        self.assertEqual(Installation.get_module_root("module_dlg.erf"), "module")
        self.assertEqual(Installation.get_module_root("module_dlg.rim"), "module")

        # Edge cases
        self.assertEqual(Installation.get_module_root(""), "")
        self.assertEqual(Installation.get_module_root("module"), "module")
        self.assertEqual(Installation.get_module_root("module_s"), "module")
        self.assertEqual(Installation.get_module_root("module_dlg"), "module")
        self.assertEqual(Installation.get_module_root("module_s_s"), "module_s")
        self.assertEqual(Installation.get_module_root("module_dlg_dlg"), "module_dlg")
        self.assertEqual(Installation.get_module_root("module.mod.mod"), "module.mod")

        # Error cases
        self.assertRaises(TypeError, Installation.get_module_root, None)
        self.assertRaises(TypeError, Installation.get_module_root, 123)


if __name__ == "__main__":
    unittest.main()
