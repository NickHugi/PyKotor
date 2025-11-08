import unittest
from pykotor.resource.formats.txi.txi_data import TXI

class TestTXI(unittest.TestCase):
    def test_parse_blending_default(self):
        self.assertTrue(TXI.parse_blending("default"))
        self.assertTrue(TXI.parse_blending("DEFAULT"))
        self.assertTrue(TXI.parse_blending("Default"))

    def test_parse_blending_additive(self):
        self.assertTrue(TXI.parse_blending("additive"))
        self.assertTrue(TXI.parse_blending("ADDITIVE"))
        self.assertTrue(TXI.parse_blending("Additive"))

    def test_parse_blending_punchthrough(self):
        self.assertTrue(TXI.parse_blending("punchthrough"))
        self.assertTrue(TXI.parse_blending("PUNCHTHROUGH"))
        self.assertTrue(TXI.parse_blending("Punchthrough"))

    def test_parse_blending_invalid(self):
        self.assertFalse(TXI.parse_blending("invalid"))
        self.assertFalse(TXI.parse_blending(""))
        self.assertFalse(TXI.parse_blending("blend"))

    def test_parse_blending_case_insensitive(self):
        self.assertTrue(TXI.parse_blending("DeFaUlT"))
        self.assertTrue(TXI.parse_blending("AdDiTiVe"))
        self.assertTrue(TXI.parse_blending("PuNcHtHrOuGh"))

if __name__ == "__main__":
    unittest.main()
