from unittest import TestCase

from pykotor.tslpatcher.config import PatcherConfig


class TestConfigReader(TestCase):
    def test(self):
        p = PatcherConfig("C:/Users/hugin/Desktop/MODS/Insanity Device/tslpatchdata/change",
                          "C:/Program Files (x86)/Steam/steamapps/common/swkotor")
        p.load()
        #p.apply()
