import os
import sys
import unittest
from pathlib import Path
from unittest import TestCase

THIS_SCRIPT_PATH = Path(__file__)
PYKOTOR_PATH = THIS_SCRIPT_PATH.parents[2]
UTILITY_PATH = THIS_SCRIPT_PATH.parents[4].joinpath("Utility", "src")
def add_sys_path(p: Path):
    working_dir = str(p)
    if working_dir not in sys.path:
        sys.path.append(working_dir)
if PYKOTOR_PATH.joinpath("pykotor").exists():
    add_sys_path(PYKOTOR_PATH)
    os.chdir(PYKOTOR_PATH.parent)
if UTILITY_PATH.joinpath("utility").exists():
    add_sys_path(UTILITY_PATH)

from pykotor.common.language import Gender, Language, LocalizedString
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.gff import FieldValue2DAMemory, FieldValueConstant, FieldValueTLKMemory, LocalizedStringDelta


class TestLocalizedStringDelta(TestCase):
    def test_apply_stringref_2damemory(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValue2DAMemory(5))

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_tlkmemory(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValueTLKMemory(5))

        memory = PatcherMemory()
        memory.memory_str[5] = 123

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_int(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValueConstant(123))

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_none(self):
        locstring = LocalizedString(123)

        delta = LocalizedStringDelta(None)

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_substring(self):
        locstring = LocalizedString(0)
        locstring.set_data(Language.ENGLISH, Gender.MALE, "a")
        locstring.set_data(Language.FRENCH, Gender.MALE, "b")

        delta = LocalizedStringDelta()
        delta.set_data(Language.ENGLISH, Gender.MALE, "1")
        delta.set_data(Language.GERMAN, Gender.MALE, "2")

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(3, len(locstring))
        self.assertEqual("1", locstring.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("2", locstring.get(Language.GERMAN, Gender.MALE))
        self.assertEqual("b", locstring.get(Language.FRENCH, Gender.MALE))


if __name__ == "__main__":
    unittest.main()
