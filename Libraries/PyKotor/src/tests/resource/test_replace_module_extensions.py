import os
import pathlib
import sys
import unittest

THIS_SCRIPT_PATH = pathlib.Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: pathlib.Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.extract.installation import Installation


class TestReplaceModuleExtensions(unittest.TestCase):
    def testreplace_module_extensions(self):
        # Happy path tests
        self.assertEqual(Installation.replace_module_extensions("module.mod"), "module")
        self.assertEqual(Installation.replace_module_extensions("module.erf"), "module")
        self.assertEqual(Installation.replace_module_extensions("module.rim"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_s.mod"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_s.erf"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_s.rim"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_dlg.mod"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_dlg.erf"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_dlg.rim"), "module")

        # Edge cases
        self.assertEqual(Installation.replace_module_extensions(""), "")
        self.assertEqual(Installation.replace_module_extensions("module"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_s"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_dlg"), "module")
        self.assertEqual(Installation.replace_module_extensions("module_s_s"), "module_s")
        self.assertEqual(Installation.replace_module_extensions("module_dlg_dlg"), "module_dlg")
        self.assertEqual(Installation.replace_module_extensions("module.mod.mod"), "module.mod")

        # Error cases
        self.assertRaises(TypeError, Installation.replace_module_extensions, None)
        self.assertRaises(TypeError, Installation.replace_module_extensions, 123)


if __name__ == "__main__":
    unittest.main()
