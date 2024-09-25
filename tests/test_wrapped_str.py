from __future__ import annotations

import unittest

from utility.common.misc_string.mutable_str import WrappedStr


class TestMutableStr(unittest.TestCase):

    def test_assert_str_type(self):
        assert WrappedStr._assert_str_or_none_type("test") == "test"
        assert WrappedStr._assert_str_or_none_type(WrappedStr("test")) == "test"
        with self.assertRaises(TypeError):
            WrappedStr._assert_str_or_none_type(123)

    def test_cast(self):
        assert WrappedStr.cast("test") == WrappedStr("test")
        assert WrappedStr.cast(WrappedStr("test")) == WrappedStr("test")

    def test_init(self):
        assert WrappedStr("test")._content == "test"
        with self.assertRaises(RuntimeError):
            WrappedStr(None)

    def test_maketrans(self):
        trans_table: dict[int, int | None] = WrappedStr.maketrans("abc", "123", "d")
        assert trans_table == str.maketrans("abc", "123", "d")

    def test_setattr(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        with self.assertRaises(RuntimeError):
            wrapped_str._content = "new"

    def test_len(self):
        assert len(WrappedStr("test")) == 4

    def test_repr(self):
        assert repr(WrappedStr("test")) == "MutableStr(test)"

    def test_str(self):
        assert str(WrappedStr("test")) == "test"

    def test_eq(self):
        assert WrappedStr("test") == "test"
        assert WrappedStr("test") == WrappedStr("test")
        assert not WrappedStr("test") == "TEST"

    def test_hash(self):
        assert hash(WrappedStr("test")) == hash("test")

    def test_ne(self):
        assert WrappedStr("test") != "TEST"
        assert not WrappedStr("test") != "test"

    def test_iter(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        assert list(iter(wrapped_str)) == [WrappedStr("t"), WrappedStr("e"), WrappedStr("s"), WrappedStr("t")]

    def test_deepcopy(self):
        import copy
        wrapped_str: WrappedStr = WrappedStr("test")
        assert copy.deepcopy(wrapped_str) == wrapped_str

    def test_getitem(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        assert wrapped_str[1] == WrappedStr("e")
        assert wrapped_str[1:3] == WrappedStr("es")

    def test_contains(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        assert "e" in wrapped_str
        assert not "x" in wrapped_str

    def test_add(self):
        assert WrappedStr("test") + "ing" == WrappedStr("testing")
        assert WrappedStr("test") + WrappedStr("ing") == WrappedStr("testing")

    def test_radd(self):
        assert "pre" + WrappedStr("fix") == WrappedStr("prefix")

    def test_mod(self):
        assert WrappedStr("Hello %s") % "World" == WrappedStr("Hello World")
        assert WrappedStr("Hello %s") % WrappedStr("World") == WrappedStr("Hello World")

    def test_mul(self):
        assert WrappedStr("test") * 3 == WrappedStr("testtesttest")

    def test_rmul(self):
        assert 3 * WrappedStr("test") == WrappedStr("testtesttest")

    def test_lt(self):
        assert WrappedStr("a") < "b"
        assert WrappedStr("a") < WrappedStr("b")

    def test_le(self):
        assert WrappedStr("a") <= "a"
        assert WrappedStr("a") <= WrappedStr("b")

    def test_gt(self):
        assert WrappedStr("b") > "a"
        assert WrappedStr("b") > WrappedStr("a")

    def test_ge(self):
        assert WrappedStr("b") >= "b"
        assert WrappedStr("b") >= WrappedStr("a")

    def test_capitalize(self):
        assert WrappedStr("test").capitalize() == WrappedStr("Test")

    def test_casefold(self):
        assert WrappedStr("TEST").casefold() == WrappedStr("test")

    def test_center(self):
        assert WrappedStr("test").center(10) == WrappedStr("   test   ")
        assert WrappedStr("test").center(10, "*") == WrappedStr("***test***")

    def test_count(self):
        assert WrappedStr("test").count("t") == 2
        assert WrappedStr("test").count(WrappedStr("t")) == 2

    def test_encode(self):
        assert WrappedStr("test").encode() == b"test"

    def test_endswith(self):
        assert WrappedStr("test").endswith("st")
        assert WrappedStr("test").endswith(WrappedStr("st"))

    def test_expandtabs(self):
        assert WrappedStr("t\te\tst").expandtabs(4) == WrappedStr("t   e   st")

    def test_find(self):
        assert WrappedStr("test").find("e") == 1
        assert WrappedStr("test").find(WrappedStr("e")) == 1

    def test_format(self):
        assert WrappedStr("Hello {}").format("World") == WrappedStr("Hello World")

    def test_format_map(self):
        assert WrappedStr("Hello {name}").format_map({"name": "World"}) == WrappedStr("Hello World")

    def test_index(self):
        assert WrappedStr("test").index("e") == 1
        assert WrappedStr("test").index(WrappedStr("e")) == 1

    def test_isalnum(self):
        assert WrappedStr("test123").isalnum()
        assert not WrappedStr("test 123").isalnum()

    def test_isalpha(self):
        assert WrappedStr("test").isalpha()
        assert not WrappedStr("test123").isalpha()

    def test_isascii(self):
        assert WrappedStr("test").isascii()
        assert not WrappedStr("tést").isascii()

    def test_isdecimal(self):
        assert WrappedStr("123").isdecimal()
        assert not WrappedStr("test123").isdecimal()

    def test_isdigit(self):
        assert WrappedStr("123").isdigit()
        assert not WrappedStr("test123").isdigit()

    def test_isidentifier(self):
        assert WrappedStr("test").isidentifier()
        assert not WrappedStr("123test").isidentifier()

    def test_islower(self):
        assert WrappedStr("test").islower()
        assert not WrappedStr("Test").islower()

    def test_isnumeric(self):
        assert WrappedStr("123").isnumeric()
        assert not WrappedStr("test123").isnumeric()

    def test_isprintable(self):
        assert WrappedStr("test").isprintable()
        assert not WrappedStr("test\n").isprintable()

    def test_isspace(self):
        assert WrappedStr("   ").isspace()
        assert not WrappedStr("test").isspace()

    def test_istitle(self):
        assert WrappedStr("Test").istitle()
        assert not WrappedStr("test").istitle()

    def test_isupper(self):
        assert WrappedStr("TEST").isupper()
        assert not WrappedStr("Test").isupper()

    def test_join(self):
        assert WrappedStr(",").join(["a", "b", "c"]) == WrappedStr("a,b,c")
        assert WrappedStr(",").join([WrappedStr("a"), WrappedStr("b"), WrappedStr("c")]) == WrappedStr("a,b,c")

    def test_ljust(self):
        assert WrappedStr("test").ljust(10) == WrappedStr("test      ")
        assert WrappedStr("test").ljust(10, "*") == WrappedStr("test******")

    def test_lower(self):
        assert WrappedStr("TEST").lower() == WrappedStr("test")

    def test_lstrip(self):
        assert WrappedStr("   test").lstrip() == WrappedStr("test")
        assert WrappedStr("xxxTEST").lstrip("x") == WrappedStr("TEST")

    def test_partition(self):
        assert WrappedStr("test").partition("e") == (WrappedStr("t"), WrappedStr("e"), WrappedStr("st"))

    def test_removeprefix(self):
        assert WrappedStr("test").removeprefix("te") == WrappedStr("st")

    def test_removesuffix(self):
        assert WrappedStr("test").removesuffix("st") == WrappedStr("te")

    def test_replace(self):
        assert WrappedStr("test").replace("t", "x") == WrappedStr("xesx")
        assert WrappedStr("test").replace(WrappedStr("t"), WrappedStr("x")) == WrappedStr("xesx")

    def test_rfind(self):
        assert WrappedStr("test").rfind("t") == 3
        assert WrappedStr("test").rfind(WrappedStr("t")) == 3

    def test_rindex(self):
        assert WrappedStr("test").rindex("t") == 3
        assert WrappedStr("test").rindex(WrappedStr("t")) == 3

    def test_rjust(self):
        assert WrappedStr("test").rjust(10) == WrappedStr("      test")
        assert WrappedStr("test").rjust(10, "*") == WrappedStr("******test")

    def test_rpartition(self):
        assert WrappedStr("test").rpartition("e") == (WrappedStr("t"), WrappedStr("e"), WrappedStr("st"))

    def test_rsplit(self):
        assert WrappedStr("a,b,c").rsplit(",") == [WrappedStr("a"), WrappedStr("b"), WrappedStr("c")]

    def test_rstrip(self):
        assert WrappedStr("test   ").rstrip() == WrappedStr("test")
        assert WrappedStr("TESTxxx").rstrip("x") == WrappedStr("TEST")

    def test_split(self):
        assert WrappedStr("a,b,c").split(",") == [WrappedStr("a"), WrappedStr("b"), WrappedStr("c")]

    def test_splitlines(self):
        assert WrappedStr("a\nb\nc").splitlines() == [WrappedStr("a"), WrappedStr("b"), WrappedStr("c")]

    def test_startswith(self):
        assert WrappedStr("test").startswith("te")
        assert WrappedStr("test").startswith(WrappedStr("te"))

    def test_strip(self):
        assert WrappedStr("   test   ").strip() == WrappedStr("test")
        assert WrappedStr("xxxTESTxxx").strip("x") == WrappedStr("TEST")

    def test_swapcase(self):
        assert WrappedStr("Test").swapcase() == WrappedStr("tEST")

    def test_title(self):
        assert WrappedStr("test title").title() == WrappedStr("Test Title")

    def test_translate(self):
        trans_table: dict[int, int | None] = str.maketrans("abc", "123", "d")
        assert WrappedStr("abcd").translate(trans_table) == WrappedStr("123")

    def test_upper(self):
        assert WrappedStr("test").upper() == WrappedStr("TEST")

    def test_zfill(self):
        assert WrappedStr("42").zfill(5) == WrappedStr("00042")

    def test_getnewargs(self):
        assert WrappedStr("test").__getnewargs__() == ("test",)

    def test_getstate(self):
        assert WrappedStr("test").__getstate__() == "test"


class TestCaseInsensImmutableStr(unittest.TestCase):

    def test_coerce_str(self):
        assert CaseInsensImmutableStr._coerce_str("Test") == "test"
        assert CaseInsensImmutableStr._coerce_str(CaseInsensImmutableStr("Test")) == "test"

    def test_init(self):
        assert CaseInsensImmutableStr("Test")._lower_content == "test"

    def test_contains(self):
        assert "test" in CaseInsensImmutableStr("Test")
        assert CaseInsensImmutableStr("test") in CaseInsensImmutableStr("Test")

    def test_eq(self):
        assert CaseInsensImmutableStr("Test") == "test"
        assert CaseInsensImmutableStr("Test") == CaseInsensImmutableStr("test")

    def test_ne(self):
        assert not CaseInsensImmutableStr("Test") != "test"
        assert not CaseInsensImmutableStr("Test") != CaseInsensImmutableStr("test")

    def test_hash(self):
        assert hash(CaseInsensImmutableStr("Test")) == hash("test")

    def test_find(self):
        assert CaseInsensImmutableStr("Test").find("test") == 0
        assert CaseInsensImmutableStr("Test").find(CaseInsensImmutableStr("test")) == 0

    def test_partition(self):
        assert CaseInsensImmutableStr("Test").partition("e") == (CaseInsensImmutableStr("T"), CaseInsensImmutableStr("e"), CaseInsensImmutableStr("st"))

    def test_replace(self):
        assert CaseInsensImmutableStr("Test").replace("t", "x") == CaseInsensImmutableStr("xesx")
        assert CaseInsensImmutableStr("Test").replace(CaseInsensImmutableStr("t"), CaseInsensImmutableStr("x")) == CaseInsensImmutableStr("xesx")

    def test_rpartition(self):
        assert CaseInsensImmutableStr("Test").rpartition("e") == (CaseInsensImmutableStr("T"), CaseInsensImmutableStr("e"), CaseInsensImmutableStr("st"))

    def test_endswith(self):
        assert CaseInsensImmutableStr("Test").endswith("st")
        assert CaseInsensImmutableStr("Test").endswith(CaseInsensImmutableStr("st"))

    def test_rfind(self):
        assert CaseInsensImmutableStr("Test").rfind("t") == 3
        assert CaseInsensImmutableStr("Test").rfind(CaseInsensImmutableStr("t")) == 3

    def test_rsplit(self):
        assert CaseInsensImmutableStr("a,b,c").rsplit(",") == [CaseInsensImmutableStr("a"), CaseInsensImmutableStr("b"), CaseInsensImmutableStr("c")]

    def test_split(self):
        assert CaseInsensImmutableStr("a,b,c").split(",") == [CaseInsensImmutableStr("a"), CaseInsensImmutableStr("b"), CaseInsensImmutableStr("c")]

    def test_split_by_indices(self):
        assert CaseInsensImmutableStr("a,b,c")._split_by_indices([1, 3], 2) == [CaseInsensImmutableStr("a"), CaseInsensImmutableStr(","), CaseInsensImmutableStr("b,c")]

if __name__ == "__main__":
    unittest.main()