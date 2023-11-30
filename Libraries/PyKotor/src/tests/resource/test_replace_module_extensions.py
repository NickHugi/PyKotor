import pathlib
import sys
import unittest

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
