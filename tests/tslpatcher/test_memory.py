from unittest import TestCase

from pykotor.common.language import LocalizedString, Gender, Language
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.gff import (
    FieldValue2DAMemory,
    FieldValueConstant,
    FieldValueTLKMemory,
    LocalizedStringDelta,
)


class TestLocalizedStringDelta(TestCase):
    def test_apply_stringref_2damemory(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta(FieldValueConstant("2DAMEMORY5"))

        memory = PatcherMemory()
        memory.memory_2da[5] = "123"

        delta.apply(locstring, memory)

        self.assertEqual(123, locstring.stringref)

    def test_apply_stringref_tlkmemory(self):
        locstring = LocalizedString(0)

        delta = LocalizedStringDelta("StrRef5")

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
        locstring.set(Language.ENGLISH, Gender.MALE, "a")
        locstring.set(Language.FRENCH, Gender.MALE, "b")

        delta = LocalizedStringDelta()
        delta.set(Language.ENGLISH, Gender.MALE, "1")
        delta.set(Language.GERMAN, Gender.MALE, "2")

        memory = PatcherMemory()

        delta.apply(locstring, memory)

        self.assertEqual(3, len(locstring))
        self.assertEqual("1", locstring.get(Language.ENGLISH, Gender.MALE))
        self.assertEqual("2", locstring.get(Language.GERMAN, Gender.MALE))
        self.assertEqual("b", locstring.get(Language.FRENCH, Gender.MALE))
