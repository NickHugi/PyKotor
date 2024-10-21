from __future__ import annotations

import unittest

from utility.common.misc_string.mutable_str import WrappedStr


class TestMutableStr(unittest.TestCase):
    def test_init(self):
        ws: WrappedStr = WrappedStr("Test")
        assert ws._content == "Test"

    def test_str(self):
        ws: WrappedStr = WrappedStr("Test")
        assert str(ws) == "Test"

    def test_repr(self):
        ws: WrappedStr = WrappedStr("Test")
        assert repr(ws) == f"{ws.__class__.__name__}('Test')"

    def test_eq(self):
        ws1: WrappedStr = WrappedStr("Test")
        ws2: WrappedStr = WrappedStr("Test")
        assert ws1 == ws2
        assert ws1 == "Test"
        assert ws1 != "test"

    def test_ne(self):
        ws1: WrappedStr = WrappedStr("Test")
        ws2: WrappedStr = WrappedStr("Other")
        assert ws1 != ws2
        assert ws1 != "other"

    def test_lt(self):
        ws1: WrappedStr = WrappedStr("abc")
        ws2: WrappedStr = WrappedStr("def")
        assert ws1 < ws2
        assert ws1 < "def"

    def test_le(self):
        ws1: WrappedStr = WrappedStr("abc")
        ws2: WrappedStr = WrappedStr("abc")
        assert ws1 <= ws2
        assert ws1 <= "abc"

    def test_gt(self):
        ws1: WrappedStr = WrappedStr("def")
        ws2: WrappedStr = WrappedStr("abc")
        assert ws1 > ws2
        assert ws1 > "abc"

    def test_ge(self):
        ws1: WrappedStr = WrappedStr("def")
        ws2: WrappedStr = WrappedStr("def")
        assert ws1 >= ws2
        assert ws1 >= "def"

    def test_hash(self):
        ws: WrappedStr = WrappedStr("Test")
        assert hash(ws) == hash("Test")

    def test_bool(self):
        assert bool(WrappedStr("Test"))
        assert not bool(WrappedStr(""))

    def test_getitem(self):
        ws: WrappedStr = WrappedStr("Test")
        assert ws[0] == WrappedStr("T")
        assert ws[1:3] == WrappedStr("es")

    def test_len(self):
        ws: WrappedStr = WrappedStr("Test")
        assert len(ws) == 4

    def test_contains(self):
        ws: WrappedStr = WrappedStr("Test")
        assert "e" in ws
        assert "E" not in ws

    def test_add(self):
        ws1: WrappedStr = WrappedStr("Test")
        ws2: WrappedStr = WrappedStr("ing")
        assert ws1 + ws2 == WrappedStr("Testing")
        assert ws1 + "ing" == WrappedStr("Testing")

    def test_mul(self):
        ws: WrappedStr = WrappedStr("Test")
        assert ws * 3 == WrappedStr("TestTestTest")

    def test_mod(self):
        ws: WrappedStr = WrappedStr("Hello, %s")
        assert ws % "World" == WrappedStr("Hello, World")

    def test_capitalize(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.capitalize() == WrappedStr("Test")

    def test_casefold(self):
        ws: WrappedStr = WrappedStr("TeSt")
        assert ws.casefold() == WrappedStr("test")

    def test_center(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.center(10) == WrappedStr("   test   ")
        assert ws.center(10, "*") == WrappedStr("***test***")

    def test_count(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.count("t") == 2
        assert ws.count("T") == 0

    def test_encode(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.encode() == b"test"

    def test_endswith(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.endswith("st")
        assert not ws.endswith("ST")

    def test_expandtabs(self):
        ws: WrappedStr = WrappedStr("t\te\tst")
        assert ws.expandtabs(4) == WrappedStr("t   e   st")

    def test_find(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.find("e") == 1
        assert ws.find("E") == -1

    def test_format(self):
        ws: WrappedStr = WrappedStr("Hello, {}")
        assert ws.format("World") == WrappedStr("Hello, World")

    def test_format_map(self):
        ws: WrappedStr = WrappedStr("Hello, {name}")
        assert ws.format_map({"name": "World"}) == WrappedStr("Hello, World")

    def test_index(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.index("e") == 1
        with self.assertRaises(ValueError):
            ws.index("E")

    def test_isalnum(self):
        assert WrappedStr("Test123").isalnum()
        assert not WrappedStr("Test 123").isalnum()

    def test_isalpha(self):
        assert WrappedStr("Test").isalpha()
        assert not WrappedStr("Test123").isalpha()

    def test_isascii(self):
        assert WrappedStr("Test").isascii()
        assert not WrappedStr("Tést").isascii()

    def test_isdecimal(self):
        assert WrappedStr("123").isdecimal()
        assert not WrappedStr("Test123").isdecimal()

    def test_isdigit(self):
        assert WrappedStr("123").isdigit()
        assert not WrappedStr("Test123").isdigit()

    def test_isidentifier(self):
        assert WrappedStr("Test").isidentifier()
        assert not WrappedStr("123Test").isidentifier()

    def test_islower(self):
        assert WrappedStr("test").islower()
        assert not WrappedStr("Test").islower()

    def test_isnumeric(self):
        assert WrappedStr("123").isnumeric()
        assert not WrappedStr("Test123").isnumeric()

    def test_isprintable(self):
        assert WrappedStr("Test").isprintable()
        assert not WrappedStr("Test\n").isprintable()

    def test_isspace(self):
        assert WrappedStr("   ").isspace()
        assert not WrappedStr("Test").isspace()

    def test_istitle(self):
        assert WrappedStr("Test Title").istitle()
        assert not WrappedStr("Test title").istitle()

    def test_isupper(self):
        assert WrappedStr("TEST").isupper()
        assert not WrappedStr("Test").isupper()

    def test_join(self):
        ws: WrappedStr = WrappedStr(",")
        assert ws.join(["a", "b", "c"]) == WrappedStr("a,b,c")

    def test_ljust(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.ljust(10) == WrappedStr("test      ")
        assert ws.ljust(10, "*") == WrappedStr("test******")

    def test_lower(self):
        ws: WrappedStr = WrappedStr("TEST")
        assert ws.lower() == WrappedStr("test")

    def test_lstrip(self):
        ws: WrappedStr = WrappedStr("   test")
        assert ws.lstrip() == WrappedStr("test")
        assert WrappedStr("xxxtest").lstrip("x") == WrappedStr("test")

    def test_partition(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.partition("e") == (WrappedStr("t"), WrappedStr("e"), WrappedStr("st"))
        assert ws.partition("E") == (WrappedStr("test"), WrappedStr(""), WrappedStr(""))

    def test_removeprefix(self):
        ws: WrappedStr = WrappedStr("TestPrefix")
        assert ws.removeprefix("Test") == WrappedStr("Prefix")
        assert ws.removeprefix("TEST") == WrappedStr("TestPrefix")

    def test_removesuffix(self):
        ws: WrappedStr = WrappedStr("TestSuffix")
        assert ws.removesuffix("Suffix") == WrappedStr("Test")
        assert ws.removesuffix("SUFFIX") == WrappedStr("TestSuffix")

    def test_replace(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.replace("t", "x") == WrappedStr("xesx")
        assert ws.replace("T", "x") == WrappedStr("test")

    def test_rfind(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.rfind("t") == 3
        assert ws.rfind("T") == -1

    def test_rindex(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.rindex("t") == 3
        with self.assertRaises(ValueError):
            ws.rindex("T")

    def test_rjust(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.rjust(10) == WrappedStr("      test")
        assert ws.rjust(10, "*") == WrappedStr("******test")

    def test_rpartition(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.rpartition("t") == (WrappedStr("tes"), WrappedStr("t"), WrappedStr(""))
        assert ws.rpartition("T") == (WrappedStr(""), WrappedStr(""), WrappedStr("test"))

    def test_rsplit(self):
        ws: WrappedStr = WrappedStr("test test test")
        assert ws.rsplit() == [WrappedStr("test"), WrappedStr("test"), WrappedStr("test")]
        assert ws.rsplit("e") == [WrappedStr("t"), WrappedStr("st t"), WrappedStr("st t"), WrappedStr("st")]

    def test_rstrip(self):
        ws: WrappedStr = WrappedStr("test   ")
        assert ws.rstrip() == WrappedStr("test")
        assert WrappedStr("testxxx").rstrip("x") == WrappedStr("test")

    def test_split(self):
        ws: WrappedStr = WrappedStr("test test test")
        assert ws.split() == [WrappedStr("test"), WrappedStr("test"), WrappedStr("test")]
        assert ws.split("e") == [WrappedStr("t"), WrappedStr("st t"), WrappedStr("st t"), WrappedStr("st")]

    def test_splitlines(self):
        ws: WrappedStr = WrappedStr("test\ntest\rtest")
        assert ws.splitlines() == [WrappedStr("test"), WrappedStr("test"), WrappedStr("test")]

    def test_startswith(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.startswith("te")
        assert not ws.startswith("TE")

    def test_strip(self):
        ws: WrappedStr = WrappedStr("   test   ")
        assert ws.strip() == WrappedStr("test")
        assert WrappedStr("xxxtestxxx").strip("x") == WrappedStr("test")

    def test_swapcase(self):
        ws: WrappedStr = WrappedStr("TeSt")
        assert ws.swapcase() == WrappedStr("tEsT")

    def test_title(self):
        ws: WrappedStr = WrappedStr("test title")
        assert ws.title() == WrappedStr("Test Title")

    def test_translate(self):
        ws: WrappedStr = WrappedStr("test")
        trans_table: dict[int, int | None] = str.maketrans("tes", "123")
        assert ws.translate(trans_table) == WrappedStr("1231")

    def test_upper(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.upper() == WrappedStr("TEST")

    def test_zfill(self):
        ws: WrappedStr = WrappedStr("42")
        assert ws.zfill(5) == WrappedStr("00042")

    # Additional magic methods

    def test_iter(self):
        ws: WrappedStr = WrappedStr("test")
        assert list(iter(ws)) == [WrappedStr("t"), WrappedStr("e"), WrappedStr("s"), WrappedStr("t")]

    def test_reversed(self):
        ws: WrappedStr = WrappedStr("test")
        assert list(reversed(ws)) == [WrappedStr("t"), WrappedStr("s"), WrappedStr("e"), WrappedStr("t")]

    def test_getstate(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.__getstate__() == "test"

    def test_getnewargs(self):
        ws: WrappedStr = WrappedStr("test")
        assert ws.__getnewargs__() == ("test",)

    def test_sizeof(self):
        ws: WrappedStr = WrappedStr("test")
        assert isinstance(ws.__sizeof__(), int)

    def test_reduce(self):
        ws: WrappedStr = WrappedStr("test")
        reduced: tuple[Any, ...] = ws.__reduce__()
        assert reduced[0] == WrappedStr
        assert reduced[1] == ("test",)

    def test_reduce_ex(self):
        ws: WrappedStr = WrappedStr("test")
        reduced: tuple[Any, ...] = ws.__reduce_ex__(2)
        assert reduced[0] == WrappedStr
        assert reduced[1] == ("test",)

    def test_format_spec(self):
        ws: WrappedStr = WrappedStr("test")
        assert format(ws, "<10") == "test      "
        assert format(ws, ">10") == "      test"
        assert format(ws, "^10") == "   test   "

    def test_dir(self):
        ws: WrappedStr = WrappedStr("test")
        dir_list: list[str] = dir(ws)
        assert "lower" in dir_list
        assert "upper" in dir_list
        assert "_content" in dir_list

    def test_subclasshook(self):
        assert issubclass(WrappedStr, str)


if __name__ == "__main__":
    try:
        import pytest
    except ImportError:
        unittest.main()
    else:
        pytest.main(["-v", __file__])
