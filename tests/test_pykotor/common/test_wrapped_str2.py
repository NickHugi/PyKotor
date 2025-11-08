from __future__ import annotations

import unittest

from utility.common.misc_string.mutable_str import WrappedStr
from utility.common.misc_string.case_insens_str import CaseInsensImmutableStr

class TestCaseInsensImmutableStr(unittest.TestCase):

    def test_coerce_str(self):
        assert CaseInsensImmutableStr._coerce_str("Test") == "test"
        assert CaseInsensImmutableStr._coerce_str(CaseInsensImmutableStr("Test")) == "test"

    def test_init(self):
        assert CaseInsensImmutableStr("Test")._casefold_content == "test"

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
    try:
        import pytest
    except ImportError: # pragma: no cover
        unittest.main()
    else:
        pytest.main(["-v", __file__])
