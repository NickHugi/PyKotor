from configparser import ConfigParser
from typing import List, Dict

from pykotor.common.stream import BinaryReader

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tslpatcher.mods.gff import ModificationsGFF
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.ssf import ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.twoda import Modifications2DA


class PatcherConfig:
    """

    Attributes:
        patches_str: Map Patcher Token (key) to Append.tlk StrRef (value).
        patches_2da: Map Patcher Token (key) to Changes class (value).
    """

    def __init__(self):
        self.patches_2da: List[Modifications2DA] = []
        self.patches_gff: List[ModificationsGFF] = []
        self.patches_ssf: List[ModificationsSSF] = []
        self.patches_tlk: ModificationsTLK = ModificationsTLK()

    def load(self, ini_text: str, append: TLK) -> None:
        from pykotor.tslpatcher.reader import ConfigReader

        ini = ConfigParser()
        ini.optionxform = str
        ini.read_string(ini_text)

        ConfigReader(ini, append).load(self)

    def apply(self) -> None:
        append_tlk = read_tlk(self.input_path + "/append.tlk")
        dialog_tlk = read_tlk(self.installation.path() + "dialog.tlk")
        twodas = {}

        dialog_tlk = self.apply_tlk(append_tlk, dialog_tlk)
        write_tlk(dialog_tlk, self.output_path + "/output.tlk")

        for patch in self.patches_2da:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = self.installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            twoda = twodas[patch.filename] = read_2da(search.data)
            patch.apply(twoda, self.memory)
            write_2da(twoda, "{}/{}".format(self.installation.override_path(), patch.filename))

        for patch in self.patches_gff:
            ...


class ModInstaller:
    def __init__(self, mod_path: str, game_path: str):
        self.game_path: str = game_path
        self.mod_path: str = mod_path
        self.output_path: str = game_path

    def install(self) -> None:
        append_tlk = read_tlk(self.mod_path + "/append.tlk")
        ini_text = BinaryReader.load_file(self.mod_path + "/changes.ini").decode()

        installation = Installation(self.game_path)
        memory = PatcherMemory()
        twodas = {}

        config = PatcherConfig()
        config.load(ini_text, append_tlk)

        # Apply changes to dialog.tlk
        dialog_tlk = read_tlk(installation.path() + "dialog.tlk")
        config.patches_tlk.apply(dialog_tlk, memory)
        write_tlk(dialog_tlk, self.output_path + "/output.tlk")

        # Apply changes to 2DA files
        for patch in config.patches_2da:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            twoda = twodas[patch.filename] = read_2da(search.data)
            patch.apply(twoda, memory)
            write_2da(twoda, "{}/{}".format(installation.override_path(), patch.filename))
