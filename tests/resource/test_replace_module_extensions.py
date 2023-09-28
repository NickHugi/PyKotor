import unittest
import re

from pykotor.extract.installation import Installation

class TestReplaceModuleExtensions(unittest.TestCase):
    def test_replace_module_extensions(self):
        # Happy path tests
        self.assertEqual(Installation._replace_module_extensions(None, "module.mod"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module.erf"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module.rim"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s.mod"), "module_s")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s.erf"), "module_s")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s.rim"), "module_s")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg.mod"), "module_dlg")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg.erf"), "module_dlg")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg.rim"), "module_dlg")

        # Edge cases
        self.assertEqual(Installation._replace_module_extensions(None, ""), "")
        self.assertEqual(Installation._replace_module_extensions(None, "module"), "module")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s"), "module_s")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg"), "module_dlg")
        self.assertEqual(Installation._replace_module_extensions(None, "module_s_s"), "module_s_s")
        self.assertEqual(Installation._replace_module_extensions(None, "module_dlg_dlg"), "module_dlg_dlg")

        # Error cases
        self.assertIsNone(Installation._replace_module_extensions(None, None))
        self.assertIsNone(Installation._replace_module_extensions(None, 123))
        self.assertIsNone(Installation._replace_module_extensions(None, "module.mod.mod"))

if __name__ == "__main__":
    unittest.main()
