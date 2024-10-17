import unittest
from pykotor.resource.formats.txi.txi_data import parse_blending

class TestParseBlending(unittest.TestCase):
    def test_parse_blending_default(self):
        self.assertTrue(parse_blending("default"))
        self.assertTrue(parse_blending("DEFAULT"))
        self.assertTrue(parse_blending("Default"))

    def test_parse_blending_additive(self):
        self.assertTrue(parse_blending("additive"))
        self.assertTrue(parse_blending("ADDITIVE"))
        self.assertTrue(parse_blending("Additive"))

    def test_parse_blending_punchthrough(self):
        self.assertTrue(parse_blending("punchthrough"))
        self.assertTrue(parse_blending("PUNCHTHROUGH"))
        self.assertTrue(parse_blending("Punchthrough"))

    def test_parse_blending_invalid(self):
        self.assertFalse(parse_blending("invalid"))
        self.assertFalse(parse_blending(""))
        self.assertFalse(parse_blending("blend"))

    def test_parse_blending_case_insensitive(self):
        self.assertTrue(parse_blending("DeFaUlT"))
        self.assertTrue(parse_blending("AdDiTiVe"))
        self.assertTrue(parse_blending("PuNcHtHrOuGh"))

if __name__ == "__main__":
    unittest.main()
