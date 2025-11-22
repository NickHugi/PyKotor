from __future__ import annotations

import sys
import unittest
from typing import Any, Callable

from utility.common.misc_string.case_insens_str import CaseInsensImmutableStr


class TestCaseInsensImmutableStr(unittest.TestCase):
    def assert_ciws_function(
        self,
        ciws_func: Callable[..., Any],
        str_func: Callable[..., Any],
        input_value: Any,
        expected_output: Any,
        *args,
        _basic__: bool = False,
        _compare_str_result__: bool = True,
        **kwargs,
    ):
        ciws_input_value = CaseInsensImmutableStr(input_value)
        ciws_repr = f"CaseInsensImmutableStr({input_value!r})"
        ciws_result = ciws_func(ciws_input_value, *args, **kwargs)
        
        args_context = f"{args}"[1:-1] if args else ""
        kwargs_context = f",{kwargs}" if kwargs else ""
        all_test_args_context = f"{args_context}{kwargs_context}"
        ciws_func_call_context = f"{ciws_repr}.{ciws_func.__name__}({all_test_args_context})"
        str_func_call_context = f"str({input_value!r}).{str_func.__name__}({all_test_args_context})"

        assert ciws_result == expected_output, f"{ciws_func_call_context} == {expected_output}"
        if not _basic__:
            assert (
                str(ciws_result).lower() == str(expected_output).lower()
            ), f"Expected str({ciws_func_call_context}) to match the case-insensitive equivalent of {expected_output!r}, but got {ciws_result!r}"
        if _compare_str_result__ and isinstance(ciws_result, CaseInsensImmutableStr):
            str_result = str_func(str(input_value), *args, **kwargs)
            str_result = str(str_result)
            assert (
                ciws_result.lower() == str_result.lower()
            ), f"Expected {ciws_func_call_context} to return a case-insensitive equivalent to {str_func_call_context}, but got {ciws_result!r} (which does not equal str result {str_result!r})"

    def test_capitalize(self):
        self.assert_ciws_function(CaseInsensImmutableStr.capitalize, str.capitalize, "hello", "Hello")
        self.assert_ciws_function(CaseInsensImmutableStr.capitalize, str.capitalize, "HELLO", "Hello")
        self.assert_ciws_function(CaseInsensImmutableStr.capitalize, str.capitalize, "hElLo", "Hello")
        self.assert_ciws_function(CaseInsensImmutableStr.capitalize, str.capitalize, "123", "123")
        self.assert_ciws_function(CaseInsensImmutableStr.capitalize, str.capitalize, "", "")

    def test_casefold(self):
        self.assert_ciws_function(CaseInsensImmutableStr.casefold, str.casefold, "Hello", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.casefold, str.casefold, "HELLO", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.casefold, str.casefold, "hElLo", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.casefold, str.casefold, "Straße", "strasse")

    def test_center(self):
        self.assert_ciws_function(CaseInsensImmutableStr.center, str.center, "hello", "  hello  ", 9)
        self.assert_ciws_function(CaseInsensImmutableStr.center, str.center, "hello", "**hello**", 9, "*")
        self.assert_ciws_function(CaseInsensImmutableStr.center, str.center, "", "  ", 2)

    def test_count(self):
        self.assert_ciws_function(CaseInsensImmutableStr.count, str.count, "hello hello", 2, "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.count, str.count, "hello hello", 2, "HELLO")
        self.assert_ciws_function(CaseInsensImmutableStr.count, str.count, "hello hello", 1, "hello", 3)
        self.assert_ciws_function(CaseInsensImmutableStr.count, str.count, "hello hello", 0, "world")

    def test_encode(self):
        self.assert_ciws_function(CaseInsensImmutableStr.encode, str.encode, "hello", b"hello")
        self.assert_ciws_function(CaseInsensImmutableStr.encode, str.encode, "hello", b"hello", "utf-8")
        self.assert_ciws_function(CaseInsensImmutableStr.encode, str.encode, "こんにちは", b"\xe3\x81\x93\xe3\x82\x93\xe3\x81\xab\xe3\x81\xa1\xe3\x81\xaf", "utf-8")

    def test_endswith(self):
        self.assert_ciws_function(CaseInsensImmutableStr.endswith, str.endswith, "hello", True, "lo")
        self.assert_ciws_function(CaseInsensImmutableStr.endswith, str.endswith, "hello", True, "LO")
        self.assert_ciws_function(CaseInsensImmutableStr.endswith, str.endswith, "hello", False, "he")
        self.assert_ciws_function(CaseInsensImmutableStr.endswith, str.endswith, "hello", True, ("lo", "LO"))
        self.assert_ciws_function(CaseInsensImmutableStr.endswith, str.endswith, "hello", True, "lo", 2)
        self.assert_ciws_function(CaseInsensImmutableStr.endswith, str.endswith, "hello", False, "lo", 0, 3)

    def test_expandtabs(self):
        self.assert_ciws_function(CaseInsensImmutableStr.expandtabs, str.expandtabs, "hello\tworld", "hello   world")
        self.assert_ciws_function(CaseInsensImmutableStr.expandtabs, str.expandtabs, "hello\tworld", "hello world", 1)
        self.assert_ciws_function(CaseInsensImmutableStr.expandtabs, str.expandtabs, "\t", "        ")

    def test_find(self):
        self.assert_ciws_function(CaseInsensImmutableStr.find, str.find, "hello", 2, "l")
        self.assert_ciws_function(CaseInsensImmutableStr.find, str.find, "hello", 2, "L")
        self.assert_ciws_function(CaseInsensImmutableStr.find, str.find, "hello", -1, "x")
        self.assert_ciws_function(CaseInsensImmutableStr.find, str.find, "hello", 4, "o", 4)
        self.assert_ciws_function(CaseInsensImmutableStr.find, str.find, "hello", 3, "l", 3, 4)

    def test_format(self):
        self.assert_ciws_function(CaseInsensImmutableStr.format, str.format, "Hello, {name}!", "Hello, World!", name="World")
        self.assert_ciws_function(CaseInsensImmutableStr.format, str.format, "{} {}", "Hello World", "Hello", "World")
        self.assert_ciws_function(CaseInsensImmutableStr.format, str.format, "{:>10}", "     Hello", "Hello")

    def test_format_map(self):
        self.assert_ciws_function(CaseInsensImmutableStr.format_map, str.format_map, "Hello, {name}!", "Hello, World!", {"name": "World"})
        self.assert_ciws_function(CaseInsensImmutableStr.format_map, str.format_map, "{a} {b}", "1 2", {"a": 1, "b": 2})

    def test_index(self):
        self.assert_ciws_function(CaseInsensImmutableStr.index, str.index, "hello", 2, "l", _basic__=True)
        self.assert_ciws_function(CaseInsensImmutableStr.index, str.index, "hello", 2, "L", _basic__=True)
        self.assert_ciws_function(CaseInsensImmutableStr.index, str.index, "hello", 4, "o", 4, _basic__=True)
        with self.assertRaises(ValueError):
            CaseInsensImmutableStr("hello").index("x")
            "hello".index("x")

    def test_isalnum(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isalnum, str.isalnum, "hello123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isalnum, str.isalnum, "hello 123", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isalnum, str.isalnum, "", False)

    def test_isalpha(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isalpha, str.isalpha, "hello", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isalpha, str.isalpha, "hello123", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isalpha, str.isalpha, "", False)

    def test_isascii(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isascii, str.isascii, "hello", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isascii, str.isascii, "こんにちは", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isascii, str.isascii, "", True)

    def test_isdecimal(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isdecimal, str.isdecimal, "123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isdecimal, str.isdecimal, "12.3", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isdecimal, str.isdecimal, "", False)

    def test_isdigit(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isdigit, str.isdigit, "123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isdigit, str.isdigit, "12.3", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isdigit, str.isdigit, "", False)

    def test_isidentifier(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isidentifier, str.isidentifier, "hello", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isidentifier, str.isidentifier, "hello123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isidentifier, str.isidentifier, "123hello", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isidentifier, str.isidentifier, "", False)

    def test_islower(self):
        self.assert_ciws_function(CaseInsensImmutableStr.islower, str.islower, "hello", True)
        self.assert_ciws_function(CaseInsensImmutableStr.islower, str.islower, "Hello", False)
        self.assert_ciws_function(CaseInsensImmutableStr.islower, str.islower, "hello123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.islower, str.islower, "", False)

    def test_isnumeric(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isnumeric, str.isnumeric, "123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isnumeric, str.isnumeric, "12.3", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isnumeric, str.isnumeric, "", False)

    def test_isprintable(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isprintable, str.isprintable, "Hello, World!", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isprintable, str.isprintable, "Hello\nWorld", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isprintable, str.isprintable, "", True)

    def test_isspace(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isspace, str.isspace, " ", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isspace, str.isspace, "\t\n\r", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isspace, str.isspace, "Hello", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isspace, str.isspace, "", False)

    def test_istitle(self):
        self.assert_ciws_function(CaseInsensImmutableStr.istitle, str.istitle, "Hello World", True)
        self.assert_ciws_function(CaseInsensImmutableStr.istitle, str.istitle, "Hello world", False)
        self.assert_ciws_function(CaseInsensImmutableStr.istitle, str.istitle, "hello World", False)
        self.assert_ciws_function(CaseInsensImmutableStr.istitle, str.istitle, "", False)

    def test_isupper(self):
        self.assert_ciws_function(CaseInsensImmutableStr.isupper, str.isupper, "HELLO", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isupper, str.isupper, "Hello", False)
        self.assert_ciws_function(CaseInsensImmutableStr.isupper, str.isupper, "HELLO123", True)
        self.assert_ciws_function(CaseInsensImmutableStr.isupper, str.isupper, "", False)

    def test_join(self):
        self.assert_ciws_function(CaseInsensImmutableStr.join, str.join, ",", "a,b,c", ["a", "b", "c"])
        self.assert_ciws_function(CaseInsensImmutableStr.join, str.join, "", "abc", ["a", "b", "c"])
        self.assert_ciws_function(CaseInsensImmutableStr.join, str.join, "-", "", [])

    def test_ljust(self):
        self.assert_ciws_function(CaseInsensImmutableStr.ljust, str.ljust, "hello", "hello     ", 10)
        self.assert_ciws_function(CaseInsensImmutableStr.ljust, str.ljust, "hello", "hello*****", 10, "*")
        self.assert_ciws_function(CaseInsensImmutableStr.ljust, str.ljust, "hello", "hello", 3)

    def test_lower(self):
        self.assert_ciws_function(CaseInsensImmutableStr.lower, str.lower, "HELLO", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.lower, str.lower, "Hello", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.lower, str.lower, "hello", "hello")

    def test_lstrip(self):
        self.assert_ciws_function(CaseInsensImmutableStr.lstrip, str.lstrip, "  hello", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.lstrip, str.lstrip, "00hello", "hello", "0")
        self.assert_ciws_function(CaseInsensImmutableStr.lstrip, str.lstrip, "hello", "hello")

    def test_partition(self):
        assert tuple(str(x) for x in CaseInsensImmutableStr("hello world").partition(" ")) == ("hello", " ", "world")
        assert tuple(str(x) for x in CaseInsensImmutableStr("hello").partition("world")) == ("hello", "", "")
        assert tuple(str(x) for x in CaseInsensImmutableStr("hello WORLD").partition("world")) == ("hello ", "WORLD", "")

    @unittest.skipIf(not hasattr(str, "removeprefix"), f"removeprefix not available in python v{sys.version_info}")
    def test_removeprefix(self):
        self.assert_ciws_function(CaseInsensImmutableStr.removeprefix, str.removeprefix, "HelloWorld", "World", "Hello")  # pyright: ignore[reportAttributeAccessIssue]
        self.assert_ciws_function(CaseInsensImmutableStr.removeprefix, str.removeprefix, "HelloWorld", "HelloWorld", "HELLO")  # pyright: ignore[reportAttributeAccessIssue]
        self.assert_ciws_function(CaseInsensImmutableStr.removeprefix, str.removeprefix, "HelloWorld", "HelloWorld", "World")  # pyright: ignore[reportAttributeAccessIssue]

    @unittest.skipIf(not hasattr(str, "removesuffix"), f"removeprefix not available in python v{sys.version_info}")
    def test_removesuffix(self):
        self.assert_ciws_function(CaseInsensImmutableStr.removesuffix, str.removesuffix, "HelloWorld", "Hello", "World")  # pyright: ignore[reportAttributeAccessIssue]
        self.assert_ciws_function(CaseInsensImmutableStr.removesuffix, str.removesuffix, "HelloWorld", "HelloWorld", "WORLD")  # pyright: ignore[reportAttributeAccessIssue]
        self.assert_ciws_function(CaseInsensImmutableStr.removesuffix, str.removesuffix, "HelloWorld", "HelloWorld", "Hello")  # pyright: ignore[reportAttributeAccessIssue]

    def test_replace(self):
        ciws = CaseInsensImmutableStr("test")
        
        assert str(ciws.replace("e", "a")) == CaseInsensImmutableStr("tast"), 'str(ciws.replace("e", "a")) != CaseInsensImmutableStr("tast")'
        assert str(str(ciws.replace("e", "a"))).lower() == str(CaseInsensImmutableStr("tast")).lower(), 'str(str(ciws.replace("e", "a"))).lower() != str(CaseInsensImmutableStr("tast")).lower()'
        assert str(ciws.replace("e", "a")) == "tast", 'str(ciws.replace("e", "a")) != "tast"'
        assert str(str(ciws.replace("e", "a"))).lower() == "tast".lower(), 'str(str(ciws.replace("e", "a"))).lower() != str("tast").lower()'
        
        assert str(ciws.replace("", "x")) == CaseInsensImmutableStr("xtxexsxtx"), 'str(ciws.replace("", "x")) != CaseInsensImmutableStr("xtxexsxtx")'
        assert str(str(ciws.replace("", "x"))).lower() == str(CaseInsensImmutableStr("xtxexsxtx")).lower(), 'str(str(ciws.replace("", "x"))).lower() != str(CaseInsensImmutableStr("xtxexsxtx")).lower()'
        assert str(ciws.replace("", "x")) == "xtxexsxtx", 'str(ciws.replace("", "x")) != "xtxexsxtx"'
        assert str(str(ciws.replace("", "x"))).lower() == "xtxexsxtx".lower(), 'str(str(ciws.replace("", "x"))).lower() != str("xtxexsxtx").lower()'
        
        assert str(ciws.replace("T", "x")) == "xesx", 'str(ciws.replace("T", "x")) != "xesx"'
        assert str(str(ciws.replace("T", "x"))).lower() == "xesx".lower(), 'str(str(ciws.replace("T", "x"))).lower() != str("xesx").lower()'
        assert str(ciws.replace("E", "a")) == "tast", 'str(ciws.replace("E", "a")) != "tast"'
        assert str(str(ciws.replace("E", "a"))).lower() == "tast".lower(), 'str(str(ciws.replace("E", "a"))).lower() != str("tast").lower()'
        
        longer = CaseInsensImmutableStr("test test TEST")
        assert str(longer.replace("test", "exam")) == "exam exam EXAM", 'str(longer.replace("test", "exam")) != "exam exam EXAM"'
        assert str(str(longer.replace("test", "exam"))).lower() == "exam exam EXAM".lower(), 'str(str(longer.replace("test", "exam"))).lower() != str("exam exam EXAM").lower()'
        assert str(longer.replace("test", "exam", 2)) == "exam exam TEST", 'str(longer.replace("test", "exam", 2)) != "exam exam TEST"'
        assert str(str(longer.replace("test", "exam", 2))).lower() == "exam exam TEST".lower(), 'str(str(longer.replace("test", "exam", 2))).lower() != str("exam exam TEST").lower()'
        
        assert str(ciws.replace("t", "x")) == "xesx", 'str(ciws.replace("t", "x")) != "xesx"'
        assert str(str(ciws.replace("t", "x"))).lower() == "xesx".lower(), 'str(str(ciws.replace("t", "x"))).lower() != str("xesx").lower()'
        
        assert str(ciws.replace("t", "x", 1)) == "xest", 'str(ciws.replace("t", "x", 1)) != "xest"'
        assert str(str(ciws.replace("t", "x", 1))).lower() == "xest".lower(), 'str(str(ciws.replace("t", "x", 1))).lower() != str("xest").lower()'
        
        assert str(ciws.replace("z", "a")) == "test", 'str(ciws.replace("z", "a")) != "test"'
        assert str(str(ciws.replace("z", "a"))).lower() == "test".lower(), 'str(str(ciws.replace("z", "a"))).lower() != str("test").lower()'
        
        assert str(ciws.replace("t", "")) == "es", 'str(ciws.replace("t", "")) != "es"'
        assert str(str(ciws.replace("t", ""))).lower() == "es".lower(), 'str(str(ciws.replace("t", ""))).lower() != str("es").lower()'
        
        mixed_case = CaseInsensImmutableStr("TeSt")
        assert mixed_case.replace("t", "x") == "XeSx", 'mixed_case.replace("t", "x") != "XeSx"'
        assert str(mixed_case.replace("t", "x")).lower() == "TeSx".lower().replace("t", "x"), 'str(mixed_case.replace("t", "x")).lower() != str("TeSx").lower().replace("t", "x")'

        assert str(ciws.replace("t", "x")) == "xesx", 'str(ciws.replace("t", "x")) != "xesx"'
        assert str(str(ciws.replace("t", "x"))).lower() == "xesx".lower(), 'str(str(ciws.replace("t", "x"))).lower() != str("xesx").lower()'
        self.assert_ciws_function(CaseInsensImmutableStr.replace, str.replace, "hello world", "hello universe", "world", "universe")

    def test_replace_extras(self):
        self.assert_ciws_function(CaseInsensImmutableStr.replace, str.replace, "hello hello", "hi hi", "HELLO", "hi", _compare_str_result__=False)
        self.assert_ciws_function(CaseInsensImmutableStr.replace, str.replace, "hello hello hello", "hi hello hello", "hello", "hi", 1)

    def test_rfind(self):
        self.assert_ciws_function(CaseInsensImmutableStr.rfind, str.rfind, "hello", 3, "l", _basic__=True, _compare_str_result__=True)
        self.assert_ciws_function(CaseInsensImmutableStr.rfind, str.rfind, "hello", 3, "L", _basic__=True, _compare_str_result__=True)
        self.assert_ciws_function(CaseInsensImmutableStr.rfind, str.rfind, "hello", -1, "x", _basic__=True, _compare_str_result__=True)
        self.assert_ciws_function(CaseInsensImmutableStr.rfind, str.rfind, "hello", 1, "l", 1, 3, _basic__=True, _compare_str_result__=True)

    def test_rindex(self):
        self.assert_ciws_function(CaseInsensImmutableStr.rindex, str.rindex, "hello", 3, "l")
        self.assert_ciws_function(CaseInsensImmutableStr.rindex, str.rindex, "hello", 3, "L")
        self.assert_ciws_function(CaseInsensImmutableStr.rindex, str.rindex, "hello", 1, "l", 1, 3)
        with self.assertRaises(ValueError):
            CaseInsensImmutableStr("hello").rindex("x")

    def test_rjust(self):
        self.assert_ciws_function(CaseInsensImmutableStr.rjust, str.rjust, "hello", "     hello", 10)
        self.assert_ciws_function(CaseInsensImmutableStr.rjust, str.rjust, "hello", "*****hello", 10, "*")
        self.assert_ciws_function(CaseInsensImmutableStr.rjust, str.rjust, "hello", "hello", 3)

    def test_rpartition(self):
        self.assert_ciws_function(CaseInsensImmutableStr.rpartition, str.rpartition, "hello world world", ("hello world ", "world", ""), "world")
        self.assert_ciws_function(CaseInsensImmutableStr.rpartition, str.rpartition, "hello", ("", "", "hello"), "world")
        self.assert_ciws_function(CaseInsensImmutableStr.rpartition, str.rpartition, "HELLO world WORLD", ("HELLO world ", "WORLD", ""), "WORLD")

    def test_rsplit(self):
        self.assert_ciws_function(CaseInsensImmutableStr.rsplit, str.rsplit, "hello world", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.rsplit, str.rsplit, "hello  world", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.rsplit, str.rsplit, "hello world world", ["hello world", "world"], None, 1)
        self.assert_ciws_function(CaseInsensImmutableStr.rsplit, str.rsplit, "hello,world,universe", ["hello", "world", "universe"], ",")

    def test_rstrip(self):
        self.assert_ciws_function(CaseInsensImmutableStr.rstrip, str.rstrip, "hello  ", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.rstrip, str.rstrip, "hello00", "hello", "0")
        self.assert_ciws_function(CaseInsensImmutableStr.rstrip, str.rstrip, "hello", "hello")

    def test_split(self):
        self.assert_ciws_function(CaseInsensImmutableStr.split, str.split, "hello world", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.split, str.split, "hello  world", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.split, str.split, "hello world world", ["hello", "world world"], None, 1)
        self.assert_ciws_function(CaseInsensImmutableStr.split, str.split, "hello,world,universe", ["hello", "world", "universe"], ",")

    def test_splitlines(self):
        self.assert_ciws_function(CaseInsensImmutableStr.splitlines, str.splitlines, "hello\nworld", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.splitlines, str.splitlines, "hello\r\nworld", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.splitlines, str.splitlines, "hello\nworld\n", ["hello", "world"])
        self.assert_ciws_function(CaseInsensImmutableStr.splitlines, str.splitlines, "hello\nworld\n", ["hello\n", "world\n"], True)

    def test_startswith(self):
        self.assert_ciws_function(CaseInsensImmutableStr.startswith, str.startswith, "hello", True, "he")
        self.assert_ciws_function(CaseInsensImmutableStr.startswith, str.startswith, "hello", True, "HE")
        self.assert_ciws_function(CaseInsensImmutableStr.startswith, str.startswith, "hello", False, "wo")
        self.assert_ciws_function(CaseInsensImmutableStr.startswith, str.startswith, "hello", True, ("he", "wo"))
        self.assert_ciws_function(CaseInsensImmutableStr.startswith, str.startswith, "hello", True, "el", 1)

    def test_strip(self):
        self.assert_ciws_function(CaseInsensImmutableStr.strip, str.strip, "  hello  ", "hello")
        self.assert_ciws_function(CaseInsensImmutableStr.strip, str.strip, "00hello00", "hello", "0")
        self.assert_ciws_function(CaseInsensImmutableStr.strip, str.strip, "hello", "hello")

    def test_swapcase(self):
        self.assert_ciws_function(CaseInsensImmutableStr.swapcase, str.swapcase, "hELLO", "Hello")
        self.assert_ciws_function(CaseInsensImmutableStr.swapcase, str.swapcase, "Hello World", "hELLO wORLD")
        self.assert_ciws_function(CaseInsensImmutableStr.swapcase, str.swapcase, "12345", "12345")

    def test_title(self):
        self.assert_ciws_function(CaseInsensImmutableStr.title, str.title, "hello world", "Hello World")
        self.assert_ciws_function(CaseInsensImmutableStr.title, str.title, "HELLO WORLD", "Hello World")
        self.assert_ciws_function(CaseInsensImmutableStr.title, str.title, "hello123 world123", "Hello123 World123")

    def test_translate(self):
        trans_table = str.maketrans("aeiou", "AEIOU")
        self.assert_ciws_function(CaseInsensImmutableStr.translate, str.translate, "hello world", "hEllO wOrld", trans_table)
        delete_table = str.maketrans("", "", "aeiou")
        self.assert_ciws_function(CaseInsensImmutableStr.translate, str.translate, "hello world", "hll wrld", delete_table)

    def test_upper(self):
        self.assert_ciws_function(CaseInsensImmutableStr.upper, str.upper, "hello", "HELLO")
        self.assert_ciws_function(CaseInsensImmutableStr.upper, str.upper, "Hello", "HELLO")
        self.assert_ciws_function(CaseInsensImmutableStr.upper, str.upper, "HELLO", "HELLO")

    def test_zfill(self):
        self.assert_ciws_function(CaseInsensImmutableStr.zfill, str.zfill, "42", "0042", 4)
        self.assert_ciws_function(CaseInsensImmutableStr.zfill, str.zfill, "-42", "-0042", 5)
        self.assert_ciws_function(CaseInsensImmutableStr.zfill, str.zfill, "42", "42", 1)


if __name__ == "__main__":
    try:
        import pytest
    except ImportError:
        unittest.main()
    else:
        pytest.main(["-v", __file__])
