from __future__ import annotations

from configparser import ConfigParser
from unittest import TestCase

from pykotor.resource.formats.gff import GFF, GFFStruct, GFFList
from pykotor.tslpatcher.config import PatcherConfig
from pykotor.tslpatcher.logger import PatchLogger
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.reader import ConfigReader


class TestChangesIni(TestCase):
    def setUp(self):
        self.config = PatcherConfig()
        self.ini = ConfigParser(
            delimiters=("="),
            allow_no_value=True,
            strict=False,
            interpolation=None,
        )
        self.ini.optionxform = lambda optionstr: optionstr  # use case sensitive keys

    def test_partyswap_sample_1(self):
        """Test that an existing struct will be targeted based on the TypeID value rather than creating a new struct."""

        ini_text = """
            [GFFList]
            File0=test.gff

            [test.gff]
            AddField0=gff_pcdead2_EntriesList_3_1

            [gff_pcdead2_EntriesList_3_1]
            FieldType=Struct
            Path=ReplyList\\2\\EntriesList
            Label=
            TypeId=3
            """

        self.ini.read_string(ini_text)

        config = PatcherConfig()
        data = ConfigReader(self.ini, "").load(config)

        gff = GFF()
        reply_list = gff.root.set_list("ReplyList", GFFList())
        for i in range(17):
            reply_list.add(i)

        reply_2 = reply_list.at(2)
        reply_2_entries_list = reply_2.set_list("EntriesList", GFFList())
        for i in range(4):
            reply_2_entries_list.add(i)

        data.patches_gff[0].apply(gff, PatcherMemory(), PatchLogger())

        modified_size = len(gff.root.get_list("ReplyList").at(2).get_list("EntriesList"))
        self.assertEqual(4, modified_size)

