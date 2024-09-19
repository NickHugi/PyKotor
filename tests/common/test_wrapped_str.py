from __future__ import annotations
import unittest

from utility.common.misc_string.mutable_str import WrappedStr
import sys


class TestMutableStr(unittest.TestCase):
    def test_init(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(ws._content, "Test")

    def test_str(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(str(ws), "Test")

    def test_repr(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(repr(ws), "MutableStr('Test')")

    def test_eq(self):
        ws1: WrappedStr = WrappedStr("Test")
        ws2: WrappedStr = WrappedStr("Test")
        self.assertEqual(ws1, ws2)
        self.assertEqual(ws1, "Test")
        self.assertNotEqual(ws1, "test")

    def test_ne(self):
        ws1: WrappedStr = WrappedStr("Test")
        ws2: WrappedStr = WrappedStr("Other")
        self.assertNotEqual(ws1, ws2)
        self.assertNotEqual(ws1, "other")

    def test_lt(self):
        ws1: WrappedStr = WrappedStr("abc")
        ws2: WrappedStr = WrappedStr("def")
        self.assertLess(ws1, ws2)
        self.assertLess(ws1, "def")

    def test_le(self):
        ws1: WrappedStr = WrappedStr("abc")
        ws2: WrappedStr = WrappedStr("abc")
        self.assertLessEqual(ws1, ws2)
        self.assertLessEqual(ws1, "abc")

    def test_gt(self):
        ws1: WrappedStr = WrappedStr("def")
        ws2: WrappedStr = WrappedStr("abc")
        self.assertGreater(ws1, ws2)
        self.assertGreater(ws1, "abc")

    def test_ge(self):
        ws1: WrappedStr = WrappedStr("def")
        ws2: WrappedStr = WrappedStr("def")
        self.assertGreaterEqual(ws1, ws2)
        self.assertGreaterEqual(ws1, "def")

    def test_hash(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(hash(ws), hash("Test"))

    def test_bool(self):
        self.assertTrue(bool(WrappedStr("Test")))
        self.assertFalse(bool(WrappedStr("")))

    def test_getitem(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(ws[0], WrappedStr("T"))
        self.assertEqual(ws[1:3], WrappedStr("es"))

    def test_len(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(len(ws), 4)

    def test_contains(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertIn("e", ws)
        self.assertNotIn("E", ws)

    def test_add(self):
        ws1: WrappedStr = WrappedStr("Test")
        ws2: WrappedStr = WrappedStr("ing")
        self.assertEqual(ws1 + ws2, WrappedStr("Testing"))
        self.assertEqual(ws1 + "ing", WrappedStr("Testing"))

    def test_mul(self):
        ws: WrappedStr = WrappedStr("Test")
        self.assertEqual(ws * 3, WrappedStr("TestTestTest"))

    def test_mod(self):
        ws: WrappedStr = WrappedStr("Hello, %s")
        self.assertEqual(ws % "World", WrappedStr("Hello, World"))

    def test_capitalize(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.capitalize(), WrappedStr("Test"))

    def test_casefold(self):
        ws: WrappedStr = WrappedStr("TeSt")
        self.assertEqual(ws.casefold(), WrappedStr("test"))

    def test_center(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.center(10), WrappedStr("   test   "))
        self.assertEqual(ws.center(10, "*"), WrappedStr("***test***"))

    def test_count(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.count("t"), 2)
        self.assertEqual(ws.count("T"), 0)

    def test_encode(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.encode(), b"test")

    def test_endswith(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertTrue(ws.endswith("st"))
        self.assertFalse(ws.endswith("ST"))

    def test_expandtabs(self):
        ws: WrappedStr = WrappedStr("t\te\tst")
        self.assertEqual(ws.expandtabs(4), WrappedStr("t   e   st"))

    def test_find(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.find("e"), 1)
        self.assertEqual(ws.find("E"), -1)

    def test_format(self):
        ws: WrappedStr = WrappedStr("Hello, {}")
        self.assertEqual(ws.format("World"), WrappedStr("Hello, World"))

    def test_format_map(self):
        ws: WrappedStr = WrappedStr("Hello, {name}")
        self.assertEqual(ws.format_map({"name": "World"}), WrappedStr("Hello, World"))

    def test_index(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.index("e"), 1)
        with self.assertRaises(ValueError):
            ws.index("E")

    def test_isalnum(self):
        self.assertTrue(WrappedStr("Test123").isalnum())
        self.assertFalse(WrappedStr("Test 123").isalnum())

    def test_isalpha(self):
        self.assertTrue(WrappedStr("Test").isalpha())
        self.assertFalse(WrappedStr("Test123").isalpha())

    def test_isascii(self):
        self.assertTrue(WrappedStr("Test").isascii())
        self.assertFalse(WrappedStr("Tést").isascii())

    def test_isdecimal(self):
        self.assertTrue(WrappedStr("123").isdecimal())
        self.assertFalse(WrappedStr("Test123").isdecimal())

    def test_isdigit(self):
        self.assertTrue(WrappedStr("123").isdigit())
        self.assertFalse(WrappedStr("Test123").isdigit())

    def test_isidentifier(self):
        self.assertTrue(WrappedStr("Test").isidentifier())
        self.assertFalse(WrappedStr("123Test").isidentifier())

    def test_islower(self):
        self.assertTrue(WrappedStr("test").islower())
        self.assertFalse(WrappedStr("Test").islower())

    def test_isnumeric(self):
        self.assertTrue(WrappedStr("123").isnumeric())
        self.assertFalse(WrappedStr("Test123").isnumeric())

    def test_isprintable(self):
        self.assertTrue(WrappedStr("Test").isprintable())
        self.assertFalse(WrappedStr("Test\n").isprintable())

    def test_isspace(self):
        self.assertTrue(WrappedStr("   ").isspace())
        self.assertFalse(WrappedStr("Test").isspace())

    def test_istitle(self):
        self.assertTrue(WrappedStr("Test Title").istitle())
        self.assertFalse(WrappedStr("Test title").istitle())

    def test_isupper(self):
        self.assertTrue(WrappedStr("TEST").isupper())
        self.assertFalse(WrappedStr("Test").isupper())

    def test_join(self):
        ws: WrappedStr = WrappedStr(",")
        self.assertEqual(ws.join(["a", "b", "c"]), WrappedStr("a,b,c"))

    def test_ljust(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.ljust(10), WrappedStr("test      "))
        self.assertEqual(ws.ljust(10, "*"), WrappedStr("test******"))

    def test_lower(self):
        ws: WrappedStr = WrappedStr("TEST")
        self.assertEqual(ws.lower(), WrappedStr("test"))

    def test_lstrip(self):
        ws: WrappedStr = WrappedStr("   test")
        self.assertEqual(ws.lstrip(), WrappedStr("test"))
        self.assertEqual(WrappedStr("xxxtest").lstrip("x"), WrappedStr("test"))

    def test_partition(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.partition("e"), (WrappedStr("t"), WrappedStr("e"), WrappedStr("st")))
        self.assertEqual(ws.partition("E"), (WrappedStr("test"), WrappedStr(""), WrappedStr("")))

    def test_removeprefix(self):
        ws: WrappedStr = WrappedStr("TestPrefix")
        self.assertEqual(ws.removeprefix("Test"), WrappedStr("Prefix"))
        self.assertEqual(ws.removeprefix("TEST"), WrappedStr("TestPrefix"))

    def test_removesuffix(self):
        ws: WrappedStr = WrappedStr("TestSuffix")
        self.assertEqual(ws.removesuffix("Suffix"), WrappedStr("Test"))
        self.assertEqual(ws.removesuffix("SUFFIX"), WrappedStr("TestSuffix"))

    def test_replace(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.replace("t", "x"), WrappedStr("xesx"))
        self.assertEqual(ws.replace("T", "x"), WrappedStr("test"))

    def test_rfind(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.rfind("t"), 3)
        self.assertEqual(ws.rfind("T"), -1)

    def test_rindex(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.rindex("t"), 3)
        with self.assertRaises(ValueError):
            ws.rindex("T")

    def test_rjust(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.rjust(10), WrappedStr("      test"))
        self.assertEqual(ws.rjust(10, "*"), WrappedStr("******test"))

    def test_rpartition(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.rpartition("t"), (WrappedStr("tes"), WrappedStr("t"), WrappedStr("")))
        self.assertEqual(ws.rpartition("T"), (WrappedStr(""), WrappedStr(""), WrappedStr("test")))

    def test_rsplit(self):
        ws: WrappedStr = WrappedStr("test test test")
        self.assertEqual(ws.rsplit(), [WrappedStr("test"), WrappedStr("test"), WrappedStr("test")])
        self.assertEqual(ws.rsplit("e"), [WrappedStr("t"), WrappedStr("st t"), WrappedStr("st t"), WrappedStr("st")])

    def test_rstrip(self):
        ws: WrappedStr = WrappedStr("test   ")
        self.assertEqual(ws.rstrip(), WrappedStr("test"))
        self.assertEqual(WrappedStr("testxxx").rstrip("x"), WrappedStr("test"))

    def test_split(self):
        ws: WrappedStr = WrappedStr("test test test")
        self.assertEqual(ws.split(), [WrappedStr("test"), WrappedStr("test"), WrappedStr("test")])
        self.assertEqual(ws.split("e"), [WrappedStr("t"), WrappedStr("st t"), WrappedStr("st t"), WrappedStr("st")])

    def test_splitlines(self):
        ws: WrappedStr = WrappedStr("test\ntest\rtest")
        self.assertEqual(ws.splitlines(), [WrappedStr("test"), WrappedStr("test"), WrappedStr("test")])

    def test_startswith(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertTrue(ws.startswith("te"))
        self.assertFalse(ws.startswith("TE"))

    def test_strip(self):
        ws: WrappedStr = WrappedStr("   test   ")
        self.assertEqual(ws.strip(), WrappedStr("test"))
        self.assertEqual(WrappedStr("xxxtestxxx").strip("x"), WrappedStr("test"))

    def test_swapcase(self):
        ws: WrappedStr = WrappedStr("TeSt")
        self.assertEqual(ws.swapcase(), WrappedStr("tEsT"))

    def test_title(self):
        ws: WrappedStr = WrappedStr("test title")
        self.assertEqual(ws.title(), WrappedStr("Test Title"))

    def test_translate(self):
        ws: WrappedStr = WrappedStr("test")
        trans_table: dict[int, int | None] = str.maketrans("tes", "123")
        self.assertEqual(ws.translate(trans_table), WrappedStr("1231"))

    def test_upper(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.upper(), WrappedStr("TEST"))

    def test_zfill(self):
        ws: WrappedStr = WrappedStr("42")
        self.assertEqual(ws.zfill(5), WrappedStr("00042"))

    # Additional magic methods

    def test_iter(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(list(iter(ws)), [WrappedStr("t"), WrappedStr("e"), WrappedStr("s"), WrappedStr("t")])

    def test_reversed(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(list(reversed(ws)), [WrappedStr("t"), WrappedStr("s"), WrappedStr("e"), WrappedStr("t")])

    def test_getstate(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.__getstate__(), "test")

    def test_getnewargs(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(ws.__getnewargs__(), ("test",))

    def test_sizeof(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertIsInstance(ws.__sizeof__(), int)

    def test_reduce(self):
        ws: WrappedStr = WrappedStr("test")
        reduced: tuple[Any, ...] = ws.__reduce__()
        self.assertEqual(reduced[0], WrappedStr)
        self.assertEqual(reduced[1], ("test",))

    def test_reduce_ex(self):
        ws: WrappedStr = WrappedStr("test")
        reduced: tuple[Any, ...] = ws.__reduce_ex__(2)
        self.assertEqual(reduced[0], WrappedStr)
        self.assertEqual(reduced[1], ("test",))

    def test_format_spec(self):
        ws: WrappedStr = WrappedStr("test")
        self.assertEqual(format(ws, "<10"), "test      ")
        self.assertEqual(format(ws, ">10"), "      test")
        self.assertEqual(format(ws, "^10"), "   test   ")

    def test_dir(self):
        ws: WrappedStr = WrappedStr("test")
        dir_list: list[str] = dir(ws)
        self.assertIn("lower", dir_list)
        self.assertIn("upper", dir_list)
        self.assertIn("_content", dir_list)

    def test_subclasshook(self):
        self.assertTrue(issubclass(WrappedStr, str))


if __name__ == "__main__":
    try:
        import pytest
    except ImportError:
        unittest.main()
    else:
        pytest.main(["-v", __file__])
