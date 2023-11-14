import pathlib
import sys
import unittest

if getattr(sys, "frozen", False) is False:
    pykotor_path = pathlib.Path(__file__).parents[2] / "pykotor"
    if pykotor_path.joinpath("__init__.py").exists() and str(pykotor_path) not in sys.path:
        working_dir = str(pykotor_path.parent)
        if working_dir in sys.path:
            sys.path.remove(working_dir)
        sys.path.insert(0, str(pykotor_path.parent))

from pykotor.extract.installation import Installation


class TestReplaceModuleExtensions(unittest.TestCase):
    def test_replace_module_extensions(self):
        # Happy path tests
        self.assertEqual(Installation._replace_module_extensions(None, "module.mod"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module.erf"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module.rim"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s.mod"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s.erf"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s.rim"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg.mod"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg.erf"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg.rim"), "module")

        # Edge cases
        self.assertEqual(Installation._replace_module_extensions(None, ""), "")
        self.assertEqual(Installation._replace_module_extensions(None, "module"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s_s"), "module_s")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg_dlg"), "module_dlg")
        self.assertEqual(Installation._replace_module_extensions(None, "module.mod.mod"), "module.mod")

        # Error cases
        self.assertRaises(TypeError, Installation._replace_module_extensions, None, None)
        self.assertRaises(TypeError, Installation._replace_module_extensions, None, 123)


if __name__ == "__main__":
    unittest.main()
