from __future__ import annotations
import unittest
from utility.common.misc_string.mutable_str import WrappedStr

class TestMutableStr(unittest.TestCase):

    def test_assert_str_type(self):
        self.assertEqual(WrappedStr._assert_str_or_none_type("test"), "test")
        self.assertEqual(WrappedStr._assert_str_or_none_type(WrappedStr("test")), "test")
        with self.assertRaises(TypeError):
            WrappedStr._assert_str_or_none_type(123)

    def test_cast(self):
        self.assertEqual(WrappedStr.cast("test"), WrappedStr("test"))
        self.assertEqual(WrappedStr.cast(WrappedStr("test")), WrappedStr("test"))

    def test_init(self):
        self.assertEqual(WrappedStr("test")._content, "test")
        with self.assertRaises(RuntimeError):
            WrappedStr(None)

    def test_maketrans(self):
        trans_table: dict[int, int | None] = WrappedStr.maketrans("abc", "123", "d")
        self.assertEqual(trans_table, str.maketrans("abc", "123", "d"))

    def test_setattr(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        with self.assertRaises(RuntimeError):
            wrapped_str._content = "new"

    def test_len(self):
        self.assertEqual(len(WrappedStr("test")), 4)

    def test_repr(self):
        self.assertEqual(repr(WrappedStr("test")), "MutableStr(test)")

    def test_str(self):
        self.assertEqual(str(WrappedStr("test")), "test")

    def test_eq(self):
        self.assertTrue(WrappedStr("test") == "test")
        self.assertTrue(WrappedStr("test") == WrappedStr("test"))
        self.assertFalse(WrappedStr("test") == "TEST")

    def test_hash(self):
        self.assertEqual(hash(WrappedStr("test")), hash("test"))

    def test_ne(self):
        self.assertTrue(WrappedStr("test") != "TEST")
        self.assertFalse(WrappedStr("test") != "test")

    def test_iter(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        self.assertEqual(list(iter(wrapped_str)), [WrappedStr("t"), WrappedStr("e"), WrappedStr("s"), WrappedStr("t")])

    def test_deepcopy(self):
        import copy
        wrapped_str: WrappedStr = WrappedStr("test")
        self.assertEqual(copy.deepcopy(wrapped_str), wrapped_str)

    def test_getitem(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        self.assertEqual(wrapped_str[1], WrappedStr("e"))
        self.assertEqual(wrapped_str[1:3], WrappedStr("es"))

    def test_contains(self):
        wrapped_str: WrappedStr = WrappedStr("test")
        self.assertTrue("e" in wrapped_str)
        self.assertFalse("x" in wrapped_str)

    def test_add(self):
        self.assertEqual(WrappedStr("test") + "ing", WrappedStr("testing"))
        self.assertEqual(WrappedStr("test") + WrappedStr("ing"), WrappedStr("testing"))

    def test_radd(self):
        self.assertEqual("pre" + WrappedStr("fix"), WrappedStr("prefix"))

    def test_mod(self):
        self.assertEqual(WrappedStr("Hello %s") % "World", WrappedStr("Hello World"))
        self.assertEqual(WrappedStr("Hello %s") % WrappedStr("World"), WrappedStr("Hello World"))

    def test_mul(self):
        self.assertEqual(WrappedStr("test") * 3, WrappedStr("testtesttest"))

    def test_rmul(self):
        self.assertEqual(3 * WrappedStr("test"), WrappedStr("testtesttest"))

    def test_lt(self):
        self.assertTrue(WrappedStr("a") < "b")
        self.assertTrue(WrappedStr("a") < WrappedStr("b"))

    def test_le(self):
        self.assertTrue(WrappedStr("a") <= "a")
        self.assertTrue(WrappedStr("a") <= WrappedStr("b"))

    def test_gt(self):
        self.assertTrue(WrappedStr("b") > "a")
        self.assertTrue(WrappedStr("b") > WrappedStr("a"))

    def test_ge(self):
        self.assertTrue(WrappedStr("b") >= "b")
        self.assertTrue(WrappedStr("b") >= WrappedStr("a"))

    def test_capitalize(self):
        self.assertEqual(WrappedStr("test").capitalize(), WrappedStr("Test"))

    def test_casefold(self):
        self.assertEqual(WrappedStr("TEST").casefold(), WrappedStr("test"))

    def test_center(self):
        self.assertEqual(WrappedStr("test").center(10), WrappedStr("   test   "))
        self.assertEqual(WrappedStr("test").center(10, "*"), WrappedStr("***test***"))

    def test_count(self):
        self.assertEqual(WrappedStr("test").count("t"), 2)
        self.assertEqual(WrappedStr("test").count(WrappedStr("t")), 2)

    def test_encode(self):
        self.assertEqual(WrappedStr("test").encode(), b"test")

    def test_endswith(self):
        self.assertTrue(WrappedStr("test").endswith("st"))
        self.assertTrue(WrappedStr("test").endswith(WrappedStr("st")))

    def test_expandtabs(self):
        self.assertEqual(WrappedStr("t\te\tst").expandtabs(4), WrappedStr("t   e   st"))

    def test_find(self):
        self.assertEqual(WrappedStr("test").find("e"), 1)
        self.assertEqual(WrappedStr("test").find(WrappedStr("e")), 1)

    def test_format(self):
        self.assertEqual(WrappedStr("Hello {}").format("World"), WrappedStr("Hello World"))

    def test_format_map(self):
        self.assertEqual(WrappedStr("Hello {name}").format_map({"name": "World"}), WrappedStr("Hello World"))

    def test_index(self):
        self.assertEqual(WrappedStr("test").index("e"), 1)
        self.assertEqual(WrappedStr("test").index(WrappedStr("e")), 1)

    def test_isalnum(self):
        self.assertTrue(WrappedStr("test123").isalnum())
        self.assertFalse(WrappedStr("test 123").isalnum())

    def test_isalpha(self):
        self.assertTrue(WrappedStr("test").isalpha())
        self.assertFalse(WrappedStr("test123").isalpha())

    def test_isascii(self):
        self.assertTrue(WrappedStr("test").isascii())
        self.assertFalse(WrappedStr("tést").isascii())

    def test_isdecimal(self):
        self.assertTrue(WrappedStr("123").isdecimal())
        self.assertFalse(WrappedStr("test123").isdecimal())

    def test_isdigit(self):
        self.assertTrue(WrappedStr("123").isdigit())
        self.assertFalse(WrappedStr("test123").isdigit())

    def test_isidentifier(self):
        self.assertTrue(WrappedStr("test").isidentifier())
        self.assertFalse(WrappedStr("123test").isidentifier())

    def test_islower(self):
        self.assertTrue(WrappedStr("test").islower())
        self.assertFalse(WrappedStr("Test").islower())

    def test_isnumeric(self):
        self.assertTrue(WrappedStr("123").isnumeric())
        self.assertFalse(WrappedStr("test123").isnumeric())

    def test_isprintable(self):
        self.assertTrue(WrappedStr("test").isprintable())
        self.assertFalse(WrappedStr("test\n").isprintable())

    def test_isspace(self):
        self.assertTrue(WrappedStr("   ").isspace())
        self.assertFalse(WrappedStr("test").isspace())

    def test_istitle(self):
        self.assertTrue(WrappedStr("Test").istitle())
        self.assertFalse(WrappedStr("test").istitle())

    def test_isupper(self):
        self.assertTrue(WrappedStr("TEST").isupper())
        self.assertFalse(WrappedStr("Test").isupper())

    def test_join(self):
        self.assertEqual(WrappedStr(",").join(["a", "b", "c"]), WrappedStr("a,b,c"))
        self.assertEqual(WrappedStr(",").join([WrappedStr("a"), WrappedStr("b"), WrappedStr("c")]), WrappedStr("a,b,c"))

    def test_ljust(self):
        self.assertEqual(WrappedStr("test").ljust(10), WrappedStr("test      "))
        self.assertEqual(WrappedStr("test").ljust(10, "*"), WrappedStr("test******"))

    def test_lower(self):
        self.assertEqual(WrappedStr("TEST").lower(), WrappedStr("test"))

    def test_lstrip(self):
        self.assertEqual(WrappedStr("   test").lstrip(), WrappedStr("test"))
        self.assertEqual(WrappedStr("xxxTEST").lstrip("x"), WrappedStr("TEST"))

    def test_partition(self):
        self.assertEqual(WrappedStr("test").partition("e"), (WrappedStr("t"), WrappedStr("e"), WrappedStr("st")))

    def test_removeprefix(self):
        self.assertEqual(WrappedStr("test").removeprefix("te"), WrappedStr("st"))

    def test_removesuffix(self):
        self.assertEqual(WrappedStr("test").removesuffix("st"), WrappedStr("te"))

    def test_replace(self):
        self.assertEqual(WrappedStr("test").replace("t", "x"), WrappedStr("xesx"))
        self.assertEqual(WrappedStr("test").replace(WrappedStr("t"), WrappedStr("x")), WrappedStr("xesx"))

    def test_rfind(self):
        self.assertEqual(WrappedStr("test").rfind("t"), 3)
        self.assertEqual(WrappedStr("test").rfind(WrappedStr("t")), 3)

    def test_rindex(self):
        self.assertEqual(WrappedStr("test").rindex("t"), 3)
        self.assertEqual(WrappedStr("test").rindex(WrappedStr("t")), 3)

    def test_rjust(self):
        self.assertEqual(WrappedStr("test").rjust(10), WrappedStr("      test"))
        self.assertEqual(WrappedStr("test").rjust(10, "*"), WrappedStr("******test"))

    def test_rpartition(self):
        self.assertEqual(WrappedStr("test").rpartition("e"), (WrappedStr("t"), WrappedStr("e"), WrappedStr("st")))

    def test_rsplit(self):
        self.assertEqual(WrappedStr("a,b,c").rsplit(","), [WrappedStr("a"), WrappedStr("b"), WrappedStr("c")])

    def test_rstrip(self):
        self.assertEqual(WrappedStr("test   ").rstrip(), WrappedStr("test"))
        self.assertEqual(WrappedStr("TESTxxx").rstrip("x"), WrappedStr("TEST"))

    def test_split(self):
        self.assertEqual(WrappedStr("a,b,c").split(","), [WrappedStr("a"), WrappedStr("b"), WrappedStr("c")])

    def test_splitlines(self):
        self.assertEqual(WrappedStr("a\nb\nc").splitlines(), [WrappedStr("a"), WrappedStr("b"), WrappedStr("c")])

    def test_startswith(self):
        self.assertTrue(WrappedStr("test").startswith("te"))
        self.assertTrue(WrappedStr("test").startswith(WrappedStr("te")))

    def test_strip(self):
        self.assertEqual(WrappedStr("   test   ").strip(), WrappedStr("test"))
        self.assertEqual(WrappedStr("xxxTESTxxx").strip("x"), WrappedStr("TEST"))

    def test_swapcase(self):
        self.assertEqual(WrappedStr("Test").swapcase(), WrappedStr("tEST"))

    def test_title(self):
        self.assertEqual(WrappedStr("test title").title(), WrappedStr("Test Title"))

    def test_translate(self):
        trans_table: dict[int, int | None] = str.maketrans("abc", "123", "d")
        self.assertEqual(WrappedStr("abcd").translate(trans_table), WrappedStr("123"))

    def test_upper(self):
        self.assertEqual(WrappedStr("test").upper(), WrappedStr("TEST"))

    def test_zfill(self):
        self.assertEqual(WrappedStr("42").zfill(5), WrappedStr("00042"))

    def test_getnewargs(self):
        self.assertEqual(WrappedStr("test").__getnewargs__(), ("test",))

    def test_getstate(self):
        self.assertEqual(WrappedStr("test").__getstate__(), "test")


class TestCaseInsensImmutableStr(unittest.TestCase):

    def test_coerce_str(self):
        self.assertEqual(CaseInsensImmutableStr._coerce_str("Test"), "test")
        self.assertEqual(CaseInsensImmutableStr._coerce_str(CaseInsensImmutableStr("Test")), "test")

    def test_init(self):
        self.assertEqual(CaseInsensImmutableStr("Test")._lower_content, "test")

    def test_contains(self):
        self.assertTrue("test" in CaseInsensImmutableStr("Test"))
        self.assertTrue(CaseInsensImmutableStr("test") in CaseInsensImmutableStr("Test"))

    def test_eq(self):
        self.assertTrue(CaseInsensImmutableStr("Test") == "test")
        self.assertTrue(CaseInsensImmutableStr("Test") == CaseInsensImmutableStr("test"))

    def test_ne(self):
        self.assertFalse(CaseInsensImmutableStr("Test") != "test")
        self.assertFalse(CaseInsensImmutableStr("Test") != CaseInsensImmutableStr("test"))

    def test_hash(self):
        self.assertEqual(hash(CaseInsensImmutableStr("Test")), hash("test"))

    def test_find(self):
        self.assertEqual(CaseInsensImmutableStr("Test").find("test"), 0)
        self.assertEqual(CaseInsensImmutableStr("Test").find(CaseInsensImmutableStr("test")), 0)

    def test_partition(self):
        self.assertEqual(CaseInsensImmutableStr("Test").partition("e"), (CaseInsensImmutableStr("T"), CaseInsensImmutableStr("e"), CaseInsensImmutableStr("st")))

    def test_replace(self):
        self.assertEqual(CaseInsensImmutableStr("Test").replace("t", "x"), CaseInsensImmutableStr("xesx"))
        self.assertEqual(CaseInsensImmutableStr("Test").replace(CaseInsensImmutableStr("t"), CaseInsensImmutableStr("x")), CaseInsensImmutableStr("xesx"))

    def test_rpartition(self):
        self.assertEqual(CaseInsensImmutableStr("Test").rpartition("e"), (CaseInsensImmutableStr("T"), CaseInsensImmutableStr("e"), CaseInsensImmutableStr("st")))

    def test_endswith(self):
        self.assertTrue(CaseInsensImmutableStr("Test").endswith("st"))
        self.assertTrue(CaseInsensImmutableStr("Test").endswith(CaseInsensImmutableStr("st")))

    def test_rfind(self):
        self.assertEqual(CaseInsensImmutableStr("Test").rfind("t"), 3)
        self.assertEqual(CaseInsensImmutableStr("Test").rfind(CaseInsensImmutableStr("t")), 3)

    def test_rsplit(self):
        self.assertEqual(CaseInsensImmutableStr("a,b,c").rsplit(","), [CaseInsensImmutableStr("a"), CaseInsensImmutableStr("b"), CaseInsensImmutableStr("c")])

    def test_split(self):
        self.assertEqual(CaseInsensImmutableStr("a,b,c").split(","), [CaseInsensImmutableStr("a"), CaseInsensImmutableStr("b"), CaseInsensImmutableStr("c")])

    def test_split_by_indices(self):
        self.assertEqual(CaseInsensImmutableStr("a,b,c")._split_by_indices([1, 3], 2), [CaseInsensImmutableStr("a"), CaseInsensImmutableStr(","), CaseInsensImmutableStr("b,c")])

if __name__ == "__main__":
    unittest.main()