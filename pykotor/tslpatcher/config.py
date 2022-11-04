from configparser import ConfigParser
from typing import List, Dict

from pykotor.common.stream import BinaryReader

from pykotor.extract.file import ResourceIdentifier
from pykotor.extract.installation import Installation, SearchLocation
from pykotor.resource.formats.gff import read_gff, write_gff
from pykotor.resource.formats.ssf import read_ssf, write_ssf
from pykotor.resource.formats.tlk import TLK, read_tlk, write_tlk
from pykotor.resource.formats.twoda import read_2da, write_2da
from pykotor.tslpatcher.mods.gff import ModificationsGFF
from pykotor.tslpatcher.memory import PatcherMemory
from pykotor.tslpatcher.mods.ssf import ModificationsSSF
from pykotor.tslpatcher.mods.tlk import ModificationsTLK
from pykotor.tslpatcher.mods.twoda import Modifications2DA


class PatcherConfig:
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
        soundsets = {}
        templates = {}

        config = PatcherConfig()
        config.load(ini_text, append_tlk)

        # Apply changes to dialog.tlk
        dialog_tlk = read_tlk(installation.path() + "dialog.tlk")
        config.patches_tlk.apply(dialog_tlk, memory)
        write_tlk(dialog_tlk, self.output_path + "/dialog.tlk")

        # Apply changes to 2DA files
        for patch in config.patches_2da:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            twoda = twodas[patch.filename] = read_2da(search.data)
            patch.apply(twoda, memory)
            write_2da(twoda, "{}/override/{}".format(self.output_path, patch.filename))

        # Apply changes to SSF files
        for patch in config.patches_ssf:
            resname, restype = ResourceIdentifier.from_path(patch.filename)
            search = installation.resource(resname, restype, [SearchLocation.OVERRIDE, SearchLocation.CHITIN])
            soundset = soundsets[patch.filename] = read_ssf(search.data)
            patch.apply(soundset, memory)
            write_ssf(soundset, "{}/override/{}".format(self.output_path, patch.filename))

        # Apply changes to GFF files
        for patch in config.patches_gff:
            resname, restype = ResourceIdentifier.from_path(patch.filename)

            search = installation.resource(
                resname,
                restype,
                [SearchLocation.OVERRIDE, SearchLocation.CHITIN, SearchLocation.MODULES, SearchLocation.CUSTOM_FOLDERS],
                folders=[self.mod_path]
            )
            print(patch.filename)
            template = templates[patch.filename] = read_gff(search.data)
            patch.apply(template, memory)
            write_gff(template, "{}/override/{}".format(self.output_path, patch.filename))
