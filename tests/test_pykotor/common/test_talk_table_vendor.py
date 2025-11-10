from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase


REPO_ROOT = Path(__file__).resolve().parents[3]
PYKOTOR_SRC = REPO_ROOT / "Libraries" / "PyKotor" / "src"
UTILITY_SRC = REPO_ROOT / "Libraries" / "Utility" / "src"
for candidate in (PYKOTOR_SRC, UTILITY_SRC):
    candidate_str = str(candidate)
    if candidate.exists() and candidate_str not in sys.path:
        sys.path.append(candidate_str)


from pykotor.common.language import Language
from pykotor.extract.talktable import TalkTable


TEST_FILES = REPO_ROOT / "tests" / "test_pykotor" / "test_files"


class TestTalkTableVendorPort(TestCase):
    def setUp(self) -> None:
        self.talk_table = TalkTable(TEST_FILES / "test.tlk")

    def test_strings_and_resrefs_are_correct(self) -> None:
        assert self.talk_table.string(0) == "abcdef"
        assert self.talk_table.sound(0) == "resref01"

        assert self.talk_table.string(1) == "ghijklmnop"
        assert self.talk_table.sound(1) == "resref02"

        assert self.talk_table.string(2) == "qrstuvwxyz"
        assert self.talk_table.sound(2) == ""

    def test_language_is_correct(self) -> None:
        assert self.talk_table.language() == Language.ENGLISH

    def test_size_is_correct(self) -> None:
        assert self.talk_table.size() == 3

